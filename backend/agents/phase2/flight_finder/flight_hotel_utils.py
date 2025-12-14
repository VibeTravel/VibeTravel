# flight_utils.py

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from concurrent.futures import ThreadPoolExecutor
# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


### Find Ariport codes using LLM

def find_airports(city: str, country: str):
    """Find up to 2 international airport codes for a city using LLM."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"What are the 2 best international airport IATA codes for {city}, {country}? Reply with ONLY the codes separated by comma, nothing else. If only 1 exists, return just that one."
        }],
        temperature=0
    )
    codes = response.choices[0].message.content.strip()
    return [c.strip() for c in codes.split(",") if c.strip()]


### Scrape flights using SerpAPI
def search_flights(
    departure_codes: list[str],
    arrival_codes: list[str],
    date: str,
    adults: int = 1
) -> dict:
    """Search one-way flights using SerpAPI Google Flights."""
    params = {
        "engine": "google_flights",
        "departure_id": ",".join(departure_codes),
        "arrival_id": ",".join(arrival_codes),
        "outbound_date": date,
        "adults": adults,
        "type": 2,  # One way
        "currency": "USD",
        "api_key": SERPAPI_API_KEY
    }
    search = GoogleSearch(params)
    return search.get_dict()

### Get the top N best flights using GPT
# def get_all_flights(results: dict, n: int = 2) -> list[dict]:
#     """Use GPT to analyze flights and pick the top n in ranked order (best first)."""
#     flights = results.get("best_flights", []) + results.get("other_flights", [])
#     if not flights:
#         return []
    
#     # Simplify flight data for GPT
#     simplified = []
#     for i, f in enumerate(flights[:max(10, n)]):  # Limit to 10 or n, whichever is greater
#         legs = f.get("flights", [])
#         simplified.append({
#             "index": i,
#             "price": f.get("price"),
#             "total_duration": f.get("total_duration"),
#             "stops": len(legs) - 1,
#             "airlines": [leg.get("airline") for leg in legs],
#             "route": " → ".join([legs[0].get("departure_airport", {}).get("id")] + 
#                                [leg.get("arrival_airport", {}).get("id") for leg in legs])
#         })
#     return simplified
    
### Fallback for flight scraping
def fallback_scraper(
    departures: list[str],
    arrivals: list[str],
    date: str,
    adults: int = 1
):
    """
    Search all combinations of departures/arrivals, collect and parse up to 5 flights.
    Returns parsed flight data ready for bestflight_agent.
    """
    all_flights = []
    booking_url = None
    for dep in departures:
        for arr in arrivals:
            if len(all_flights) >= 5:
                break
            results = search_flights([dep], [arr], date, adults)
            if not booking_url:
                booking_url = results.get("search_metadata", {}).get("google_flights_url", "")
            flights = results.get("best_flights", []) + results.get("other_flights", [])
            for f in flights:
                if len(all_flights) < 5:
                    all_flights.append(f)
                else:
                    break
        if len(all_flights) >= 5:
            break
    
    # Parse flights before returning
    parsed_flights = [parse_flight_option(f, booking_url) for f in all_flights]
    return parsed_flights

# def parse_all_flights(flights, booking_url):
#     return [parse_flight_option(f, booking_url) for f in flights]
def parse_flight_option(flight_data, booking_url):
    """
    Extracts key flight information from a single SerpAPI Google Flights result.
    
    Expected structure:
      flight_data = {
         "flights": [...legs...],
         "total_duration": ...,
         "price": ...,
         "booking_token": ...,
         ...
      }
      
    Returns a clean dictionary with:
      airline, airplane,
      departure_airport_name, departure_airport_code,
      arrival_airport_name, arrival_airport_code,
      departure_time, arrival_time,
      total_duration, stops, price, booking_url
    """
    
    legs = flight_data.get("flights", [])
    if not legs:
        return {"error": "No legs found in this flight option."}
    
    # First leg = departure info
    first_leg = legs[0]
    dep_airport = first_leg.get("departure_airport", {})
    departure_airport_name = dep_airport.get("name")
    departure_airport_code = dep_airport.get("id")
    departure_time = dep_airport.get("time")

    # Last leg = arrival info
    last_leg = legs[-1]
    arr_airport = last_leg.get("arrival_airport", {})
    arrival_airport_name = arr_airport.get("name")
    arrival_airport_code = arr_airport.get("id")
    arrival_time = arr_airport.get("time")

    # Airline + airplane from first leg (SerpAPI does not provide consistent airline per entire route)
    airline = first_leg.get("airline")
    airplane = first_leg.get("airplane")

    # Stops = number of layovers = number of legs - 1
    stops = max(0, len(legs) - 1)

    # Total duration
    total_duration = flight_data.get("total_duration")

    # Price
    price = flight_data.get("price")
    return {
        "airline": airline,
        "airplane": airplane,
        "departure_airport_name": departure_airport_name,
        "departure_airport_code": departure_airport_code,
        "departure_time": departure_time,
        "arrival_airport_name": arrival_airport_name,
        "arrival_airport_code": arrival_airport_code,
        "arrival_time": arrival_time,
        "total_duration_minutes": total_duration,
        "stops": stops,
        "price_usd": price,
        "booking_url": booking_url
    }


def scrape_hotels(city: str, check_in: str, check_out: str, adults: int = 2, currency: str = "USD") -> Dict[str, Any]:
    """Parallel hotel scraper using SerpAPI Google Hotels - 3x faster!

    Returns a dict with consistent category keys:
      - 'cheapest'
      - 'highest_rated'
      - 'most_expensive'

    The values are the raw SerpAPI result dictionaries for each sort order.
    Runs all 3 searches in parallel using ThreadPoolExecutor.
    """
    params_base = {
        "engine": "google_hotels",
        "q": city,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "currency": currency,
        "api_key": SERPAPI_API_KEY
    }
    
    def fetch_hotels(sort_by: int, label: str):
        """Helper function to fetch hotels for a specific sort order"""
        params = params_base.copy()
        params["sort_by"] = sort_by
        search = GoogleSearch(params)
        results = search.get_dict()
        hotels = return_top_hotels(results, label=label)
        return (label, hotels)
    
    # Run all 3 searches in parallel (3x faster than sequential!)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_hotels, 3, "cheapest"),
            executor.submit(fetch_hotels, 8, "highest rated"),
            executor.submit(fetch_hotels, 13, "most expensive")
        ]
        results = [f.result() for f in futures]
    
    # Convert results list to dict
    return {
        "cheapest": results[0][1],
        "highest_rated": results[1][1],
        "most_expensive": results[2][1]
    }

def return_top_hotels(results, label="", top_n=2):
    """Return up to `top_n` hotels extracted from SerpAPI results.
    Each entry is a dict with keys: name, price, rating, reviews, link."""
    hotels = results.get("properties", [])
    top = []
    for h in hotels:
        name = h.get("name")
        rating = h.get("overall_rating")
        reviews = h.get("reviews")
        link = h.get("link")
        price = (
            h.get("rate_per_night", {}).get("lowest")
            or h.get("total_rate", {}).get("lowest")
        )
        if (
            not name
            or name == "N/A"
            or not price
            or price == "N/A"
            or not rating
            or rating == "N/A"
            or not reviews
            or reviews == "N/A"
            or not link
        ):
            continue  # skip if any essential info is missing
        entry = {
            "name": h.get("name", "N/A"),
            "price": price,
            "rating": h.get("overall_rating", "N/A"),
            "reviews": h.get("reviews", "N/A"),
            "link": h.get("link", ""),
        }
        top.append(entry)
        if len(top) >= top_n:
            break
    return top
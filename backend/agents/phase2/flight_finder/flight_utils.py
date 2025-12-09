# flight_utils.py

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


### Find Ariport codes using LLM

def find_airports(city: str, country: str) -> list[str]:
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

    
### Fallback for flight scraping
def fallback_scraper(
    departures: list[str],
    arrivals: list[str],
    date: str,
    adults: int = 1
) -> list[dict]:
    """
    Search all combinations of departures/arrivals, collect up to 10 flights (no LLM ranking).
    """
    all_flights = []
    for dep in departures:
        for arr in arrivals:
            if len(all_flights) >= 10:
                break
            results = search_flights([dep], [arr], date, adults)
            print(f"DEBUG - Search {dep} → {arr}:")
            print(f"  Keys in results: {list(results.keys())}")
            print(f"  best_flights count: {len(results.get('best_flights', []))}")
            print(f"  other_flights count: {len(results.get('other_flights', []))}")
            if 'error' in results:
                print(f"  ERROR: {results['error']}")
            flights = results.get("best_flights", []) + results.get("other_flights", [])
            for f in flights:
                if len(all_flights) < 10:
                    all_flights.append(f)
                else:
                    break
        if len(all_flights) >= 10:
            break
    return all_flights
# agents/phase2/flight_finder/agent.py

import os
from typing import List
from serpapi import GoogleSearch
# from agents.utils.data_models import Flight, FlightSearchResults

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

### remove these after testing
from pydantic import BaseModel, Field, PositiveInt
from typing import Optional, List
class Flight(BaseModel):
    """Individual flight option"""
    airline: str
    departure_time: str
    arrival_time: str
    duration: str
    price: float
    booking_url: str
    stops: int
    departure_airport: str
    arrival_airport: str


class FlightSearchResults(BaseModel):
    """Results from Flight Search Agent"""
    origin: str
    destination: str
    outbound_date: str
    return_date: str
    flights: List[Flight]



    #remove until here after testing
class FlightSearchAgent:
    """Agent for searching flights using SerpApi Google Flights"""
    
    def __init__(self, api_key: str = None):
        self.api_key = SERPAPI_KEY
        # self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SerpApi key is required. Set SERPAPI_KEY env variable or pass api_key parameter")
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        outbound_date: str,
        return_date: str = None,
        max_results: int = 5
    ) -> FlightSearchResults:
        """
        Search for flights using SerpApi
        
        Args:
            origin: Origin airport code or city (e.g., "JFK" or "New York")
            destination: Destination airport code or city
            outbound_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD) - optional for one-way
            max_results: Maximum number of flights to return
        
        Returns:
            FlightSearchResults with list of Flight objects
        """
        print(f"[FlightAgent] Searching flights from {origin} to {destination}")
        print(f"[FlightAgent] Dates: {outbound_date} to {return_date}")
        
        # Build SerpApi parameters
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": outbound_date,
            "currency": "USD",
            "hl": "en",
            "api_key": self.api_key
        }
        
        # Add return date if provided (round trip)
        if return_date:
            params["return_date"] = return_date
            params["type"] = "1"  # Round trip
        else:
            params["type"] = "2"  # One way
        
        try:
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Parse results
            flights = self._parse_flight_results(results, max_results)
            
            return FlightSearchResults(
                origin=origin,
                destination=destination,
                outbound_date=outbound_date,
                return_date=return_date or "",
                flights=flights
            )
            
        except Exception as e:
            print(f"[FlightAgent] Error searching flights: {str(e)}")
            # Return empty results on error
            return FlightSearchResults(
                origin=origin,
                destination=destination,
                outbound_date=outbound_date,
                return_date=return_date or "",
                flights=[]
            )
    
    def _parse_flight_results(self, results: dict, max_results: int) -> List[Flight]:
        """Parse SerpApi flight results into Flight objects"""
        flights = []
        
        # Get best flights from results
        best_flights = results.get("best_flights", [])
        other_flights = results.get("other_flights", [])
        
        # Combine and limit results
        all_flights = best_flights + other_flights
        
        for flight_data in all_flights[:max_results]:
            try:
                # Extract flight information
                flights_info = flight_data.get("flights", [])
                if not flights_info:
                    continue
                
                # Get first leg for basic info (could expand for multi-leg)
                first_leg = flights_info[0]
                
                # Extract departure and arrival info
                departure_airport = first_leg.get("departure_airport", {}).get("id", "N/A")
                arrival_airport = first_leg.get("arrival_airport", {}).get("id", "N/A")
                
                # Create Flight object
                flight = Flight(
                    airline=first_leg.get("airline", "Unknown"),
                    departure_time=first_leg.get("departure_airport", {}).get("time", "N/A"),
                    arrival_time=first_leg.get("arrival_airport", {}).get("time", "N/A"),
                    duration=f"{flight_data.get('total_duration', 0)} min",
                    price=float(flight_data.get("price", 0)),
                    booking_url=flight_data.get("booking_token", ""),
                    stops=len(flights_info) - 1,  # Number of stops
                    departure_airport=departure_airport,
                    arrival_airport=arrival_airport
                )
                
                flights.append(flight)
                
            except Exception as e:
                print(f"[FlightAgent] Error parsing flight: {str(e)}")
                continue
        
        print(f"[FlightAgent] Found {len(flights)} flights")
        return flights


# Example usage and testing
if __name__ == "__main__":
    # Test the agent
    agent = FlightSearchAgent()
    
    # Test search
    results = agent.search_flights(
        origin="JFK",
        destination="KTM",  # Kathmandu
        outbound_date="2025-12-01",
        return_date="2025-12-05",
        max_results=5
    )
    
    print(f"\nFound {len(results.flights)} flights:")
    for i, flight in enumerate(results.flights, 1):
        print(f"\n{i}. {flight.airline}")
        print(f"   {flight.departure_airport} -> {flight.arrival_airport}")
        print(f"   Departure: {flight.departure_time}")
        print(f"   Arrival: {flight.arrival_time}")
        print(f"   Duration: {flight.duration}")
        print(f"   Stops: {flight.stops}")
        print(f"   Price: ${flight.price}")
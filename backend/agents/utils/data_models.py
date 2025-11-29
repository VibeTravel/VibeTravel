# agents/utils/data_models.py

from pydantic import BaseModel, Field, PositiveInt
from typing import Optional, List

class TripDuration(BaseModel):
    """Defines trip length, using either days or dates."""
    days: Optional[PositiveInt] = Field(
        None,
        description="Total number of days for the trip (must be at least 1)."
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date (YYYY-MM-DD format)."
    )
    end_date: Optional[str] = Field(
        None,
        description="End date (YYYY-MM-DD format)."
    )

class TripDetails(BaseModel):
    """The complete set of validated user trip requirements."""
    user_location: str = Field(..., description="User's current or starting location.")

    interests: List[str] = Field(
        ...,
        min_length=1,
        description="List of preferred activities or travel themes (must contain at least one item)."
    )

    budget: str = Field(
        ...,
        description="User's total budget (e.g., '5000 USD' or 'mid-range')."
    )

    trip_duration: TripDuration
    search_mode: Optional[str] = Field(
        "global",
        description="Scope of search: 'local' or 'global'."
    )


    # utils/data_models.py (Snippet)
class LocationSuggestion(BaseModel):
    """Details for a single preliminary location suggestion."""
    destination: str
    country: str
    recommended_activities: List[str]
    description: str
    image_url: Optional[str] = Field(None, description="A direct link to an image of the destination.")
    estimated_budget: str = Field(..., description="Estimated cost range for a trip to this location.")

class PreliminarySuggestions(BaseModel):
    """The list outputted by the Location Finder Agent."""
    preliminary_location_suggestions: List[LocationSuggestion] = Field(..., min_length=10)

# Flight Models

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

# Hotel Models
class Hotel(BaseModel):
    name: str
    rating: float
    price_per_night: float
    total_price: float
    location: str
    booking_url: str
    amenities: List[str]
    max_occupancy: int  # ← How many people this room fits
    room_type: str  # e.g., "Double Room", "Suite"
    description: Optional[str] = None


class HotelSearchResults(BaseModel):
    destination: str
    check_in: str
    check_out: str
    num_guests: int  # ← How many people searching for
    hotels: List[Hotel]


# Activity Models

class Activity(BaseModel):
    """Individual activity/attraction"""
    name: str
    description: str
    category: str  # e.g., "museum", "hiking", "restaurant", "attraction"
    estimated_duration: Optional[str] = None
    url: Optional[str] = None


class ActivitySearchResults(BaseModel):
    """Results from Activities Agent"""
    destination: str
    activities: List[Activity]

# Itinerary Models
class DayPlan(BaseModel):
    """Plan for a single day"""
    day_number: int
    date: str
    morning_activity: Optional[Activity] = None
    afternoon_activity: Optional[Activity] = None
    evening_activity: Optional[Activity] = None
    meals_suggestion: Optional[str] = None
    notes: Optional[str] = None


class CompleteItinerary(BaseModel):
    """Final complete itinerary with all details"""
    destination: str
    country: str
    
    # Search results from sub-agents
    flights: FlightSearchResults
    hotels: HotelSearchResults
    activities: ActivitySearchResults
    
    # Generated itinerary
    daily_plans: List[DayPlan]
    
    # Summary
    total_estimated_cost: float
    trip_duration_days: int
    
    # Status tracking
    status: str  # "generating", "complete", "failed"
    created_at: str
    completed_at: Optional[str] = None


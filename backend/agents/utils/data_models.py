# agents/utils/data_models.py

from pydantic import BaseModel, Field, PositiveInt
from typing import Optional, List, Any

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
    """
    Slimmed-down trip details for the Location Finder agent.

    This is built from SearchRequest and contains only the fields
    the agent actually needs.
    """
    location: str = Field(..., description="User's starting location.")
    numDays: int = Field(..., description="Number of effective trip days (excluding flight days).")
    budget_per_person: float = Field(
        ...,
        description="Effective budget per traveler in USD."
    )
    activities: List[str] = Field(
        ...,
        min_length=1,
        description="Preferred activities or interests."
    )
    additionalDetails: Optional[List[str]] = Field(
        default=None,
        description="Optional extra constraints or preferences."
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


# ========================================
# Phase 2 - Itinerary Planning Models
# ========================================

class SelectedDestination(BaseModel):
    """
    Information about the destination selected by user from Phase 1.
    This comes from the rated/preferred destinations.
    """
    destination: str = Field(..., description="Name of the city")
    country: str = Field(..., description="Country where the city is located")
    recommended_activities: List[str] = Field(
        ...,
        description="List of recommended activities from Phase 1 agent"
    )
    description: str = Field(..., description="Description of the destination")
    estimated_budget: str = Field(..., description="Budget estimate from Phase 1")


class UserTripContext(BaseModel):
    """
    Original trip context from the user's initial search.
    This is retrieved from LAST_SEARCH_REQUEST in Phase 1.
    """
    origin_location: str = Field(..., description="User's starting/current location")
    numTravelers: int = Field(..., description="Number of travelers", ge=1)
    total_budget: float = Field(..., description="Total budget for the entire trip in USD")
    budget_per_person: float = Field(..., description="Budget per person in USD")
    startDate: str = Field(..., description="Trip start date (YYYY-MM-DD)")
    endDate: str = Field(..., description="Trip end date (YYYY-MM-DD)")
    numDays: int = Field(..., description="Number of days at destination (excluding flight days)")
    additionalDetails: Optional[List[str]] = Field(
        default=[],
        description="Additional user preferences or constraints"
    )


class Phase2PlanningRequest(BaseModel):
    """
    Complete request for Phase 2 itinerary planning.
    Combines selected destination info with original trip context.
    """
    # Selected destination from Phase 1
    selected_destination: SelectedDestination
    
    # Original trip context
    trip_context: UserTripContext



# In data_models.py

# Activity Models
class ActivityDetail(BaseModel):
    """Individual activity with pricing and duration"""
    name: str
    description: str
    estimated_duration: str  # e.g., "2 hours", "3 days", "Half day"
    estimated_cost_per_person: float  # in USD
    category: str  # e.g., "museum", "hiking", "cultural"
    
class ActivitySearchResults(BaseModel):
    """Results from Activity Planner Agent"""
    destination: str
    activities: List[ActivityDetail]


# Flight Models
class FlightOption(BaseModel):
    """Single flight option"""
    airline: str
    departure_time: str
    arrival_time: str
    departure_date: str
    arrival_date: str  # Important: could be same or next day
    duration: str
    price_per_person: float
    total_price: float  # price * numTravelers
    stops: int
    departure_airport: str
    arrival_airport: str
    booking_url: Optional[str] = None

class FlightRecommendations(BaseModel):
    """4 flight options: 2 outbound, 2 return"""
    outbound_flights: List[FlightOption] = Field(..., min_length=2, max_length=2)
    return_flights: List[FlightOption] = Field(..., min_length=2, max_length=2)
    # origin_airport_code: str
    # destination_airport_code: str


# Hotel Models
class HotelOption(BaseModel):
    """Single hotel recommendation"""
    name: str
    rating: float
    price_per_night: float
    total_price: float  # for entire stay
    location: str
    amenities: List[str]
    room_type: str
    max_occupancy: int
    booking_url: Optional[str] = None

class HotelScenario(BaseModel):
    """Hotel options for a specific check-in date"""
    check_in_date: str  # "YYYY-MM-DD"
    check_out_date: str
    num_nights: int
    hotels: List[HotelOption] = Field(..., min_length=4, max_length=4)

class HotelRecommendations(BaseModel):
    """Hotel options for both landing date scenarios"""
    scenario_A: HotelScenario  # Land on departure date
    scenario_B: HotelScenario  # Land next day


# Phase 2 Complete Response
class Phase2Response(BaseModel):
    """Complete response from Phase 2 with all agent results"""
    status: str  # "success", "partial", "error"
    
    # Results from parallel agents
    activities: Optional[ActivitySearchResults] = None
    flights: Optional[FlightRecommendations] = None
    hotels: Optional[HotelRecommendations] = None
    
    # Pricing summary
    estimated_total_cost: Optional[float] = None
    
    # Error handling
    errors: List[str] = Field(default=[])
    warnings: List[str] = Field(default=[])
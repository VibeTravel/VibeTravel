# agents/utils/data_models.py

from pydantic import BaseModel, Field, PositiveInt
from typing import Optional, List, Any, Dict

# ========================================
# Phase 1 - Location Search Models
# ========================================

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
# Phase 2 - Request Models (Input)
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


class TripContext(BaseModel):
    """
    Original trip context from the user's initial search.
    This is retrieved from LAST_SEARCH_REQUEST in Phase 1.
    """
    origin_location: str = Field(..., description="User's starting/current location")
    numTravelers: int = Field(..., description="Number of travelers", ge=1)
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
    selected_destination: SelectedDestination
    trip_context: TripContext


# ========================================
# Phase 2 - Activity Models
# ========================================

class Activity(BaseModel):
    """Individual activity with pricing and duration"""
    name: str
    description: str
    estimated_duration: str  # e.g., "2 hours", "3 days", "Half day"
    estimated_cost_per_person: float  # in USD
    category: str  # e.g., "museum", "hiking", "cultural"
    

class ActivitySearchResults(BaseModel):
    """Results from Activity Finder Agent"""
    destination: str  # "City, Country"
    activities: List[Activity]


# ========================================
# Phase 2 - Flight Models
# ========================================

class FlightOption(BaseModel):
    """Single flight option"""
    airline: str
    airplane: Optional[str] = Field(default="N/A", description="Aircraft model (if available)")
    departure_airport_name: str
    departure_airport_code: str
    departure_time: str  # "YYYY-MM-DD HH:MM"
    arrival_airport_name: str
    arrival_airport_code: str
    arrival_time: str    # "YYYY-MM-DD HH:MM"
    total_duration_minutes: int
    stops: int
    price_usd: float
    booking_url: str
    
    @property
    def total_price(self) -> float:
        """Alias for price_usd for consistency"""
        return self.price_usd


class FlightRecommendations(BaseModel):
    """Roundtrip flight options"""
    outbound_flights: List[FlightOption]  # Top 2 outbound
    return_flights: List[FlightOption]    # Top 2 return


# ========================================
# Phase 2 - Hotel Models
# ========================================

class HotelOption(BaseModel):
    """Single hotel option"""
    name: str
    price: float
    rating: float
    reviews: int
    link: str
    
    @property
    def total_price(self) -> float:
        """Alias for price for consistency"""
        return self.price


class HotelCategory(BaseModel):
    """Hotels organized by category"""
    hotels: List[HotelOption]
    category: str  # "cheapest", "highest_rated", "most_expensive", etc.


class HotelRecommendations(BaseModel):
    """
    Hotel options for both flight scenarios.
    
    scenario_A: Hotels for first outbound flight's arrival date
    scenario_B: Hotels for second outbound flight's arrival date
    """
    scenario_A: HotelCategory  # For outbound flight 1
    scenario_B: HotelCategory  # For outbound flight 2


# ========================================
# Phase 2 - Response Model (Output)
# ========================================

class Phase2Response(BaseModel):
    """
    Complete Phase 2 response to frontend.
    
    Contains:
    - status: "success", "partial", or "error"
    - activities: Activities at destination (if found)
    - flights: Roundtrip flight options (if found)
    - hotels: Hotel options for both scenarios (if found)
    - estimated_total_cost: Rough cost estimate
    - errors: List of error messages
    - warnings: List of warning messages
    """
    status: str  # "success" | "partial" | "error"
    activities: Optional[ActivitySearchResults] = None
    flights: Optional[FlightRecommendations] = None
    hotels: Optional[HotelRecommendations] = None
    estimated_total_cost: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ========================================
# Phase 3 - Itinerary Planner Models
# ========================================

class Phase3Input(BaseModel):
    """
    Input for Phase 3 Itinerary Planner Agent.
    Contains the user's selections from Phase 2 (flights, hotel, activities) 
    AND the complete trip context including budget.
    """
    # Trip context (from Phase 1/2)
    destination: str = Field(..., description="City, Country")
    origin_location: str = Field(..., description="User's home location")
    trip_start_date: str = Field(..., description="Trip start date (YYYY-MM-DD)")
    trip_end_date: str = Field(..., description="Trip end date (YYYY-MM-DD)")
    num_travelers: int = Field(..., description="Number of travelers", ge=1)
    num_days: int = Field(..., description="Number of days at destination (excluding flight days)", ge=1)
    budget_per_person: float = Field(..., description="Budget per person in USD")
    additional_details: Optional[List[str]] = Field(
        default=[],
        description="Additional user preferences/constraints"
    )
    
    # User selections from Phase 2
    outbound_flight: FlightOption = Field(..., description="Selected outbound flight")
    return_flight: FlightOption = Field(..., description="Selected return flight")
    selected_hotel: HotelOption = Field(..., description="Selected hotel")
    selected_activities: List[Activity] = Field(..., description="Activities user wants to include")


class DayPlan(BaseModel):
    """Single day in the itinerary"""
    day_number: int = Field(..., description="Day number (1, 2, 3, etc.)")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    title: str = Field(..., description="Title for the day (e.g., 'Arrival & Exploration')")
    activities: List[str] = Field(..., description="List of activities for this day")
    meals: Optional[List[str]] = Field(default=[], description="Meal suggestions")
    notes: Optional[str] = Field(default="", description="Additional notes or tips for the day")


class Phase3Response(BaseModel):
    """
    Complete Phase 3 response - the final itinerary.
    
    Contains:
    - Day-by-day plan
    - Selected flights, hotel, activities
    - Budget breakdown
    """
    status: str = Field(..., description="success, partial, or error")
    
    # Trip summary
    destination: str
    dates: str = Field(..., description="e.g., 'Dec 20, 2025 - Dec 28, 2025'")
    num_travelers: int
    
    # Selections
    outbound_flight: FlightOption
    return_flight: FlightOption
    hotel: HotelOption
    activities: List[Activity]
    
    # The itinerary
    daily_plans: List[DayPlan] = Field(..., description="Day-by-day itinerary")
    
    # Budget
    total_cost: float = Field(..., description="Total estimated cost for entire trip")
    cost_breakdown: Dict[str, float] = Field(
        ...,
        description="Breakdown: flights, hotel, activities, meals, misc"
    )
    
    # Metadata
    created_at: str = Field(..., description="Timestamp when itinerary was created")
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
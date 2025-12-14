# backend/routes/phase2.py

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from agents.utils.data_models import (
    SelectedDestination,
    TripContext,
    Phase2PlanningRequest,
    Phase2Response  # 
)
from agents.phase2.supervisor import phase2_supervisor

router = APIRouter(prefix="/phase2", tags=["phase2"])


@router.post("/plan")
async def plan_itinerary(request: Phase2PlanningRequest) -> Phase2Response:  # ← FIXED
    """
    Phase 2: Generate complete itinerary including flights, hotels, and activities.
    
    Receives:
    - Selected destination from Phase 1 (destination, country, recommended_activities, etc.)
    - Original trip context (origin, dates, budget, travelers, etc.)
    
    Process:
    1. Activity Planner Agent (parallel) - Find activity details (duration, cost)
    2. Flight Pipeline (parallel):
       - Airport Code Finder → Find airport codes for origin and destination
       - Flight Scraper → Scrape 5-10 flights using SerpAPI
       - Flight Selector → LLM selects 4 best (2 outbound, 2 return)
    3. Hotel Finder (sequential after flights):
       - Scenario A: Hotels if landing on departure date
       - Scenario B: Hotels if landing next day
    
    Returns:
    - activities: List of activities with duration and cost
    - flights: 2 outbound + 2 return flight options
    - hotels: 4 hotels for scenario A, 4 hotels for scenario B
    - estimated_total_cost: Rough cost estimate
    """
    
    print(f"[Phase2] ===== Starting Itinerary Planning =====")
    print(f"[Phase2] Destination: {request.selected_destination.destination}, {request.selected_destination.country}")
    print(f"[Phase2] Origin: {request.trip_context.origin_location}")
    print(f"[Phase2] Dates: {request.trip_context.startDate} to {request.trip_context.endDate}")
    print(f"[Phase2] Travelers: {request.trip_context.numTravelers}")
    print(f"[Phase2] Budget per person: ${request.trip_context.budget_per_person}")
    print(f"[Phase2] Recommended Activities: {len(request.selected_destination.recommended_activities)}")
    
    try:
        # Call Phase 2 Supervisor
        result = await phase2_supervisor.run(request)
        return result
        
    except Exception as e:
        print(f"[Phase2] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Phase2Response(
            status="error",
            activities=None,
            flights=None,
            hotels=None,
            estimated_total_cost=None,
            errors=[str(e)],
            warnings=[]
        )


@router.get("/health")
async def phase2_health():
    """Health check for Phase 2 routes"""
    return {
        "status": "Phase 2 routes active",
        "endpoints": ["/plan"],
        "agents": {
            "activity_planner": "pending",
            "airport_finder": "pending",
            "flight_scraper": "pending",
            "hotel_finder": "pending"
        }
    }
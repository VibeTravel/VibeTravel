# backend/routes/activity_finder.py

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.utils.data_models import ActivityFinderRequest
from agents.phase2.activity_finder.supervisor import activity_finder_supervisor

router = APIRouter(prefix="/activity-finder", tags=["activity-finder"])


@router.post("/search")
async def search_activities(req: ActivityFinderRequest):
    """
    Research activities and find detailed information including pricing and duration.
    
    Input:
    - activities: List of activity names to research
    - city: Destination city
    - num_days: Number of days for the trip
    - budget_per_person: Budget per person in USD for activities
    
    Returns:
    - ActivitySearchResults with detailed information for each activity
    """
    
    try:
        result = await activity_finder_supervisor.run(req)
        return result
        
    except Exception as e:
        print(f"[Activity Finder Route] Error: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Activity finder failed: {str(e)}"
        )

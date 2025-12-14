# backend/routes/phase1.py

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from agents.phase1.supervisor import phase1_supervisor

router = APIRouter(prefix="/phase1", tags=["phase1"])

# Global storage for the last search request
LAST_SEARCH_REQUEST: Dict[str, Any] = {}


class SearchRequest(BaseModel):
    location: str
    numTravelers: int
    activities: List[str]
    budget: float
    dateMode: str                        # always "date_range" in your use-case now
    startDate: str                       # "YYYY-MM-DD"
    endDate: str                        # "YYYY-MM-DD"
    additionalDetails: Optional[List[str]] = []

    # Computed server-side fields
    budget_per_person: Optional[float] = None
    numDays: Optional[int] = None        # computed automatically


@router.post("/search")
async def search_locations(req: SearchRequest):
    """
    Runs Phase 1 ADK location-finder.
    Stores ONLY user request, computes:
      - budget_per_person
      - numDays = (endDate - startDate) - 2 flight days
    """

    global LAST_SEARCH_REQUEST

    # 1. Compute budget_per_person
  
    budget_per_person = req.budget / req.numTravelers


    # 2. Compute numDays from date difference
   
    start = datetime.strptime(req.startDate, "%Y-%m-%d")
    end = datetime.strptime(req.endDate, "%Y-%m-%d")
    day_diff = (end - start).days
    numDays = max(day_diff - 2, 0)   # ensure it's never negative

    # 3. Build stored request with computed fields included
   
    stored_req = req.dict()
    stored_req["budget_per_person"] = budget_per_person
    stored_req["numDays"] = numDays

    # Save for future access
    LAST_SEARCH_REQUEST = stored_req

    # 4. Pass enriched request to supervisor
   
    enriched_req = SearchRequest(**stored_req)
    result = await phase1_supervisor.run(enriched_req)

   
    # 5. Return response structure required by frontend
  
    response = {
        "destinations": result.get("destinations", []),
        "storedRequest": LAST_SEARCH_REQUEST
    }
    
    # Include error info if present (for debugging)
    if "error" in result:
        response["error"] = result.get("error")
        response["source"] = result.get("source")
    
    return response


@router.get("/last-search")
async def get_last_search():
    """Retrieve the last stored user search input."""
    return LAST_SEARCH_REQUEST

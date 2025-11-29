# backend/routes/phase1.py

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from agents.phase1.supervisor import phase1_supervisor

router = APIRouter(prefix="/phase1", tags=["phase1"])

class SearchRequest(BaseModel):
    location: str
    activities: List[str]
    budget: float
    dateMode: str                    # "number_of_days" or "date_range"
    numDays: Optional[int] = None
    startDate: Optional[str] = None  # "YYYY-MM-DD" if used
    endDate: Optional[str] = None    # "YYYY-MM-DD" if used


@router.post("/search")
async def search_locations(req: SearchRequest):
    """Runs Phase 1 ADK location-finder pipeline."""
    result = await phase1_supervisor.run(req)
    return result
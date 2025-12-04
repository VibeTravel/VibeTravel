from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from agents.phase2.supervisor import phase2_supervisor
from agents.phase2.flight_finder.agent import flight_finder

router = APIRouter(prefix="/phase2", tags=["phase2"])

class Phase2SupervisorRequest(BaseModel):
    currentCity: str
    destinationCity: str
    totalBudget: float = Field(..., gt=0)
    travellers: int = Field(..., gt=0)
    outboundDate: str
    returnDate: Optional[str] = None


@router.post("/itinerary")
async def itinerary(req: Phase2SupervisorRequest):
    return await phase2_supervisor.run(req)


@router.get("/itinerary")
async def itinerary_get(
    currentCity: str,
    destinationCity: str,
    totalBudget: float = Query(..., gt=0),
    travellers: int = Query(..., gt=0),
    outboundDate: str = Query(...),
    returnDate: Optional[str] = Query(default=None),
):
    request = Phase2SupervisorRequest(
        currentCity=currentCity,
        destinationCity=destinationCity,
        totalBudget=totalBudget,
        travellers=travellers,
        outboundDate=outboundDate,
        returnDate=returnDate,
    )
    return await phase2_supervisor.run(request)


class FlightFinderRequest(BaseModel):
    fromCity: str
    toCity: str
    budgetForFlightFinder: float = Field(..., gt=0)
    travellers: int = Field(..., gt=0)
    outboundDate: str
    returnDate: Optional[str] = None


@router.post("/flights/test")
async def flight_test(req: FlightFinderRequest):
    try:
        result = await flight_finder(req.model_dump())
        return {
            "status": "success",
            "data": result,
        }
    except ValueError as exc:
        return {
            "status": "error",
            "error": str(exc),
        }


@router.get("/flights/test")
async def flight_test_get():
    raise HTTPException(
        status_code=405,
        detail="Use POST /phase2/flights/test with a JSON body to run the flight finder.",
    )

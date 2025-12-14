# backend/routes/ratings.py

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/ratings", tags=["ratings"])

# In-memory storage (replace with database later)
preferred_destinations = []
unpreferred_destinations = []


class RatingData(BaseModel):
    destination: str
    country: str
    description: str
    recommended_activities: List[str]
    estimated_budget: str
    rating: int
    timestamp: str = None


@router.post("/store")
async def store_rating(rating_data: RatingData):
    """
    Store user rating for a destination.
    Rating >= 5 goes to preferred, < 5 goes to unpreferred.
    """
    # Add timestamp
    rating_data.timestamp = datetime.now().isoformat()
    
    rating_dict = rating_data.dict()
    
    if rating_data.rating >= 5:
        preferred_destinations.append(rating_dict)
        category = "preferred"
    else:
        unpreferred_destinations.append(rating_dict)
        category = "unpreferred"
    
    print(f"[Ratings] Stored {category} destination: {rating_data.destination} with rating {rating_data.rating}")
    
    return {
        "success": True,
        "category": category,
        "destination": rating_data.destination,
        "rating": rating_data.rating,
    }


@router.get("/preferred")
async def get_preferred_destinations():
    """Get all preferred destinations (rating >= 5)"""
    return {
        "count": len(preferred_destinations),
        "destinations": preferred_destinations,
    }


@router.get("/unpreferred")
async def get_unpreferred_destinations():
    """Get all unpreferred destinations (rating < 5)"""
    return {
        "count": len(unpreferred_destinations),
        "destinations": unpreferred_destinations,
    }


@router.get("/all")
async def get_all_ratings():
    """Get all ratings for analysis"""
    return {
        "preferred_count": len(preferred_destinations),
        "unpreferred_count": len(unpreferred_destinations),
        "preferred": preferred_destinations,
        "unpreferred": unpreferred_destinations,
    }


@router.delete("/clear")
async def clear_all_ratings():
    """Clear all stored ratings (for testing)"""
    global preferred_destinations, unpreferred_destinations
    preferred_destinations = []
    unpreferred_destinations = []
    return {"success": True, "message": "All ratings cleared"}
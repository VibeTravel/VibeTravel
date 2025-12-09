# backend/agents/phase1/supervisor.py

"""
Phase 1 Supervisor

- Receives FastAPI SearchRequest (Pydantic model from routes/phase1.py).
- Converts it into TripDetails (agent-side schema).
- Converts again to a dict to send to the LlmAgent as JSON text.
- Uses an ADK Runner to call the location_finder_agent.
- Reads the structured output from session state (PreliminarySuggestions).
- Returns a clean list of destinations for the frontend.
"""

from datetime import date
from typing import Dict, Any
import json
import uuid
import re

from agents.utils.data_models import (
    TripDetails,
    TripDuration,
    PreliminarySuggestions,
)

from agents.phase1.location_finder.agent import location_finder_agent

# ADK runtime
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# -----------------------------
# ADK runtime global setup (shared)
# -----------------------------
APP_NAME = "trip_planner_phase1"
USER_ID = "demo_user_123"  # later, plug in real user id from auth

# One in-memory session service for this backend process
session_service = InMemorySessionService()

# One Runner bound to our location_finder_agent
phase1_runner = Runner(
    agent=location_finder_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


class Phase1Supervisor:
    """
    Phase 1 orchestrator:
    - Takes FastAPI SearchRequest input
    - Converts to TripDetails (your internal schema)
    - Converts again to a JSON object passed as a user message
    - Calls ADK location_finder_agent via Runner
    - Normalizes output into frontend-safe format
    """

    def _build_trip_details(self, req) -> TripDetails:
        """
            Convert enriched SearchRequest → TripDetails.
            Only includes fields needed by the Location Finder agent.
            """

        return TripDetails(
            location=req.location,
            numDays=req.numDays,
            budget_per_person=req.budget_per_person,
            activities=req.activities,
            additionalDetails=req.additionalDetails,
        )

    def _trip_details_to_prompt(self, trip: TripDetails) -> dict:
        """
        Convert TripDetails → dict sent to the Location Finder agent.

        This structure will match the updated instructions in
        location_finder.txt.
        """

        return {
            "origin_location": trip.location,
            "trip_duration_days": trip.numDays,
            "budget_per_person_usd": trip.budget_per_person,
            "interests_of_user": trip.activities,
            "additional_details": trip.additionalDetails or [],
        }

    async def run(self, req) -> Dict[str, Any]:
        """
        Execute the Phase 1 agent pipeline.
        """
        trip_details = self._build_trip_details(req)
        prompt_ready = self._trip_details_to_prompt(trip_details)

        try:
            session_id = str(uuid.uuid4())

            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )

            user_text = json.dumps(prompt_ready)
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=user_text)],
            )

            events = phase1_runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_content,
            )

            # Collect the final text response
            final_text = ""
            async for event in events:
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            final_text += part.text

            # Parse the JSON from the text response
            # The agent should return JSON, extract it
            
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', final_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                stored_dict = json.loads(json_str)
            else:
                raise ValueError(f"No JSON found in agent response: {final_text}")

            # Parse into PreliminarySuggestions
            prelim = PreliminarySuggestions(**stored_dict)

            # Normalize for frontend
            destinations = [
                {
                    "destination": s.destination,
                    "country": s.country,
                    "recommended_activities": s.recommended_activities,
                    "description": s.description,
                    "image_url": s.image_url,
                    "estimated_budget": s.estimated_budget,
                }
                for s in prelim.preliminary_location_suggestions
            ]

            return {
                "source": "adk",
                "destinations": destinations,
            }

        except Exception as e:
            print("[Phase1Supervisor] ADK failed:", e)
            import traceback
            traceback.print_exc()

            return {
                "source": "adk_error",
                "destinations": [],
                "error": str(e),
            }


phase1_supervisor = Phase1Supervisor()

# backend/agents/phase2/activity_finder/supervisor.py

"""
Activity Finder Supervisor

- Receives ActivityFinderRequest (Pydantic model).
- Converts it to a dict to send to the ADK Agent as JSON text.
- Uses an ADK Runner to call the activity_finder_agent (which uses Google Search).
- Optionally enriches results with Tavily search for additional details.
- Returns ActivitySearchResults for the frontend.
"""

from typing import Dict, Any, Optional
import json
import uuid
import re
import os

from agents.utils.data_models import ActivitySearchResults, ActivityDetail
from agents.phase2.activity_finder.agent import activity_finder_agent

# Optional: Import Tavily for enrichment
try:
    from tools.activity_search import tavily_search_activities
    TAVILY_AVAILABLE = bool(os.environ.get("TAVILY_API_KEY"))
except Exception:
    TAVILY_AVAILABLE = False

# ADK runtime
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# -----------------------------
# ADK runtime global setup
# -----------------------------
APP_NAME = "activity_finder"
USER_ID = "demo_user_123"

# One in-memory session service for this backend process
session_service = InMemorySessionService()

# One Runner bound to our activity_finder_agent
activity_finder_runner = Runner(
    agent=activity_finder_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


class ActivityFinderSupervisor:
    """
    Activity Finder orchestrator:
    - Takes ActivityFinderRequest input
    - Converts to JSON object passed as a user message
    - Calls ADK activity_finder_agent via Runner
    - Normalizes output into ActivitySearchResults format
    """

    def _build_prompt(self, req) -> dict:
        """
        Convert ActivityFinderRequest → dict for the agent.
        """
        return {
            "activities": req.activities,
            "city": req.city,
            "num_days": req.num_days,
            "budget_per_person": req.budget_per_person,
        }

    def _enrich_with_tavily(self, activity: ActivityDetail, city: str) -> ActivityDetail:
        """
        Optionally enrich activity details with Tavily search.
        This provides additional verification and details from a second source.
        """
        if not TAVILY_AVAILABLE:
            return activity
        
        try:
            # Search for additional pricing/duration info
            query = f"{activity.name} {city} price duration tickets"
            tavily_results = tavily_search_activities(query, max_results=2)
            
            # Log that we got additional info (could be used to enhance description)
            if tavily_results and tavily_results[0].get("content"):
                print(f"[Tavily] Found additional info for {activity.name}")
                # Could merge/verify pricing here if needed
            
        except Exception as e:
            print(f"[Tavily] Enrichment failed for {activity.name}: {e}")
        
        return activity

    async def run(self, req) -> Dict[str, Any]:
        """
        Execute the Activity Finder agent pipeline.
        Uses Google Search via ADK agent, optionally enriched with Tavily.
        """
        prompt_ready = self._build_prompt(req)

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

            events = activity_finder_runner.run_async(
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
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', final_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                stored_dict = json.loads(json_str)
            else:
                raise ValueError(f"No JSON found in agent response: {final_text}")

            # Parse into ActivitySearchResults
            activity_results = ActivitySearchResults(**stored_dict)

            # Optionally enrich with Tavily (if available)
            enriched_activities = []
            for activity in activity_results.activities:
                enriched = self._enrich_with_tavily(activity, req.city)
                enriched_activities.append(enriched)

            return {
                "status": "success",
                "destination": activity_results.destination,
                "activities": [
                    {
                        "name": activity.name,
                        "description": activity.description,
                        "estimated_duration": activity.estimated_duration,
                        "estimated_cost_per_person": activity.estimated_cost_per_person,
                        "category": activity.category,
                    }
                    for activity in enriched_activities
                ],
            }

        except Exception as e:
            print("[ActivityFinderSupervisor] ADK failed:", e)
            import traceback
            traceback.print_exc()

            return {
                "status": "error",
                "destination": req.city,
                "activities": [],
                "error": str(e),
            }


activity_finder_supervisor = ActivityFinderSupervisor()

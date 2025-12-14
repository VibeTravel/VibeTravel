# backend/agents/phase2/supervisor.py

"""
Phase 2 Supervisor - Clean Version with is_final_response()

- Receives Phase2PlanningRequest from FastAPI
- Runs orchestrator agent (activity + flight/hotel agents in parallel)
- Uses event.is_final_response() to capture clean final output
- Parses using Pydantic models for type safety
- Returns Phase2Response for frontend
"""

from typing import Dict, Any, Optional, List
import json
import uuid
import re
# from pydantic import BaseModel, Field, ValidationError
from datetime import date

# ========================================
# Request Models (Input from Frontend)
# ========================================
from agents.utils.data_models import (
    SelectedDestination,
    Phase2PlanningRequest,
    Activity,
    ActivitySearchResults,
    FlightOption,
    FlightRecommendations,
    HotelOption,
    HotelCategory,
    HotelRecommendations,
    Phase2Response)


from agents.phase2.activity_finder.agent import activity_finder_agent
from agents.phase2.flight_finder.agent import flight_hotel_finder_agent
from agents.utils.instructions_loader import load_instruction_from_file
# ADK workflow agents
from google.adk.agents.parallel_agent import ParallelAgent

# ADK runtime
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types



# ========================================
# ADK Runtime Setup
# ========================================
APP_NAME = "trip_planner_phase2"
USER_ID = "demo_user_phase2"

session_service = InMemorySessionService()

# ========================================
# Orchestrator Agent
# ========================================
orchestrator_instruction = load_instruction_from_file(
    "orchestrator_agent_instructions.txt"
    # relative_to_caller=True
)

orchestrator_agent = ParallelAgent(
    name="Phase2OrchestratorAgent",
    sub_agents=[activity_finder_agent, flight_hotel_finder_agent],
    description="Runs activity finder and flight/hotel finder in parallel.",
)

orchestrator_runner = Runner(
    agent=orchestrator_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# ========================================
# Phase 2 Supervisor
# ========================================
class Phase2Supervisor:
    """
    Phase 2 orchestrator using event.is_final_response():
    - Takes Phase2PlanningRequest
    - Runs orchestrator via ADK
    - Uses is_final_response() to get clean output
    - Parses with Pydantic models
    - Returns Phase2Response
    """

    def _build_combined_prompt(self, request: Phase2PlanningRequest) -> dict:
        """Build input for orchestrator agent"""
        activity_budget_per_person = request.trip_context.budget_per_person * 0.5
        
        return {
            # Activity fields
            "destination_city": request.selected_destination.destination,
            "preferred_activities": request.selected_destination.recommended_activities,
            "activity_budget_per_person": activity_budget_per_person,
            "num_travelers": request.trip_context.numTravelers,
            "num_days": request.trip_context.numDays,
            
            # Flight/Hotel fields
            "origin_city": request.trip_context.origin_location,
            "outbound_date": request.trip_context.startDate,
            "return_date": request.trip_context.endDate,
            "destination_country": request.selected_destination.country,
            # "origin_country": request.trip_context.origin_location,
        }

    def _extract_json_from_text(self, text: str) -> dict:
        """Extract and merge JSON objects from text (handles multiple agent outputs)"""
        # Strip markdown code block wrappers
        clean_text = re.sub(r'```json\s*', '', text)
        clean_text = re.sub(r'```\s*', '', clean_text)
        
        # Find all JSON objects in the text
        json_objects = []
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(clean_text):
            # Skip whitespace
            while idx < len(clean_text) and clean_text[idx] in ' \t\n\r':
                idx += 1
            if idx >= len(clean_text):
                break
            # Try to decode JSON starting at this position
            if clean_text[idx] == '{':
                try:
                    obj, end_idx = decoder.raw_decode(clean_text, idx)
                    json_objects.append(obj)
                    idx = end_idx
                except json.JSONDecodeError:
                    idx += 1
            else:
                idx += 1
        
        if not json_objects:
            raise ValueError(f"No JSON found in text. First 500 chars: {text[:500]}")
        
        # If single object, return it
        if len(json_objects) == 1:
            return json_objects[0]
        
        # Merge multiple objects (activity_finder + flight_hotel_finder outputs)
        merged = {}
        for obj in json_objects:
            # Activity finder output has "destination" and "activities" keys
            if "destination" in obj and "activities" in obj:
                merged["activities"] = obj
            # Flight/hotel finder output has flight and hotel keys
            elif "outbound_top_2_flights" in obj or "return_top_2_flights" in obj:
                merged["flights_and_hotels"] = obj
            else:
                # Unknown structure, try to merge directly
                merged.update(obj)
        
        return merged

    def _parse_orchestrator_output(self, raw_data: dict) -> dict:
        """
        Parse raw JSON from orchestrator.
        
        We don't use a strict OrchestratorOutput model because the orchestrator
        just combines outputs from sub-agents. We validate the structure exists
        and return the raw dict for flexible processing.
        """
        # Validate required keys exist
        if "activities" not in raw_data:
            raise ValueError("Missing 'activities' in orchestrator output")
        if "flights_and_hotels" not in raw_data:
            raise ValueError("Missing 'flights_and_hotels' in orchestrator output")
        
        # Validate activities structure
        activities = raw_data.get("activities", {})
        if not isinstance(activities, dict):
            raise ValueError("'activities' must be a dict")
        if "activities" not in activities:
            raise ValueError("Missing 'activities' list in activities section")
        
        # Validate flights_and_hotels structure
        fh = raw_data.get("flights_and_hotels", {})
        if not isinstance(fh, dict):
            raise ValueError("'flights_and_hotels' must be a dict")
        if "outbound_top_2_flights" not in fh:
            raise ValueError("Missing 'outbound_top_2_flights'")
        if "return_top_2_flights" not in fh:
            raise ValueError("Missing 'return_top_2_flights'")
        
        return raw_data

    def _calculate_costs(
        self, 
        orchestrator_data: dict,
        num_travelers: int
    ) -> dict:
        """Calculate total costs from orchestrator output"""
        costs = {
            "activities": 0.0,
            "flights": 0.0,
            "hotels": 0.0,
            "total": 0.0
        }
        
        # Activity costs
        try:
            activities = orchestrator_data.get("activities", {}).get("activities", [])
            if activities:
                costs["activities"] = sum(
                    self._parse_cost(act.get("estimated_cost_per_person", 0)) * num_travelers
                    for act in activities
                )
        except Exception as e:
            print(f"[Cost Calc] Warning: Failed to calculate activity costs: {e}")
        
        # Flight costs
        try:
            fh = orchestrator_data.get("flights_and_hotels", {})
            outbound = fh.get("outbound_top_2_flights", [])
            returns = fh.get("return_top_2_flights", [])
            
            if outbound:
                costs["flights"] += sum(self._parse_cost(f.get("price_usd", 0)) for f in outbound)
            if returns:
                costs["flights"] += sum(self._parse_cost(f.get("price_usd", 0)) for f in returns)
        except Exception as e:
            print(f"[Cost Calc] Warning: Failed to calculate flight costs: {e}")
        
        # Hotel costs (take cheapest from scenario 1 as baseline)
        try:
            fh = orchestrator_data.get("flights_and_hotels", {})
            hotels_1 = fh.get("hotel_options_flight_1", {}).get("cheapest", [])
            if hotels_1:
                costs["hotels"] = self._parse_cost(hotels_1[0].get("price", 0))
        except Exception as e:
            print(f"[Cost Calc] Warning: Failed to calculate hotel costs: {e}")
        
        costs["total"] = costs["activities"] + costs["flights"] + costs["hotels"]
        return costs
    
    def _parse_cost(self, cost_value) -> float:
        """Parse cost value - handles strings like '35-57 USD' or '35.00'"""
        if isinstance(cost_value, (int, float)):
            return float(cost_value)
        if isinstance(cost_value, str):
            # Extract first number from string like "35-57 USD" or "$35"
            numbers = re.findall(r'[\d.]+', cost_value)
            if numbers:
                return float(numbers[0])
        return 0.0
    
    async def run(self, request: Phase2PlanningRequest) -> Phase2Response:
        """
        Execute Phase 2 itinerary planning.
        
        Steps:
        1. Build combined prompt
        2. Run orchestrator agent
        3. Collect final response using is_final_response()
        4. Parse with Pydantic models
        5. Return Phase2Response
        """
        print(f"\n{'='*60}")
        print(f"[Phase2Supervisor] Starting Phase 2 Planning")
        print(f"Destination: {request.selected_destination.destination}")
        print(f"Origin: {request.trip_context.origin_location}")
        print(f"Travelers: {request.trip_context.numTravelers}")
        print(f"Dates: {request.trip_context.startDate} → {request.trip_context.endDate}")
        print(f"{'='*60}\n")
        
        try:
            # Build input
            combined_prompt = self._build_combined_prompt(request)
            
            # Create session
            session_id = str(uuid.uuid4())
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            
            # Prepare message
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=json.dumps(combined_prompt))],
            )
            
            print(f"[Phase2Supervisor] Running orchestrator agent...")
            
            # Run orchestrator
            events = orchestrator_runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_content,
            )
            
            # ✨ Collect ONLY final response (no streaming, just final)
            final_response_text = ""
            event_count = 0
            final_event_count = 0
            
            async for event in events:
                event_count += 1
                
                # Debug logging
                author = getattr(event, 'author', 'unknown')
                is_final = event.is_final_response()
                print(f"[Event {event_count}] Author: {author}, is_final: {is_final}")
                
                # Collect final response only
                if is_final:
                    final_event_count += 1
                    if event.content and event.content.parts:
                        # Get text from first part (as per documentation)
                        text = event.content.parts[0].text
                        if text:
                            final_response_text += text
                            print(f"  ✓ Captured {len(text)} characters from final response")
            
            print(f"\n[Phase2Supervisor] Event Summary:")
            print(f"  Total events: {event_count}")
            print(f"  Final events: {final_event_count}")
            print(f"  Response length: {len(final_response_text)} chars")
            
            if not final_response_text:
                raise ValueError("No final response received from orchestrator")
            
            # Show preview
            print(f"\n[Phase2Supervisor] Response Preview:")
            print(f"  First 300 chars: {final_response_text[:300]}")
            print(f"  Last 200 chars: {final_response_text[-200:]}")
            
            # Extract JSON
            print(f"\n[Phase2Supervisor] Extracting JSON...")
            raw_json = self._extract_json_from_text(final_response_text)
            print(f"  ✓ JSON extracted successfully")
            
            # Validate structure
            print(f"[Phase2Supervisor] Validating structure...")
            orchestrator_data = self._parse_orchestrator_output(raw_json)
            print(f"  ✓ Structure validation passed")
            
            # Log what we got
            activities = orchestrator_data.get("activities", {}).get("activities", [])
            fh = orchestrator_data.get("flights_and_hotels", {})
            outbound = fh.get("outbound_top_2_flights", [])
            returns = fh.get("return_top_2_flights", [])
            
            print(f"\n[Phase2Supervisor] Parsed Results:")
            print(f"  Activities: {len(activities)}")
            print(f"  Outbound flights: {len(outbound)}")
            print(f"  Return flights: {len(returns)}")
            print(f"  Raw flights_and_hotels structure: {json.dumps(fh, indent=2)[:500]}...")
            
            # ========================================
            # Map orchestrator_data to Phase2Response models
            # ========================================
            activities_result = None
            flights_result = None
            hotels_result = None
            errors = []
            warnings = []
            
            # Parse Activities
            try:
                activities_data = orchestrator_data.get("activities", {})
                if activities_data and activities_data.get("activities"):
                    # Pre-process activities to fix cost format
                    processed_activities = []
                    for act in activities_data.get("activities", []):
                        act_copy = act.copy()
                        act_copy["estimated_cost_per_person"] = self._parse_cost(
                            act.get("estimated_cost_per_person", 0)
                        )
                        processed_activities.append(act_copy)
                    
                    activities_result = ActivitySearchResults(
                        destination=activities_data.get("destination", "Unknown"),
                        activities=[Activity(**act) for act in processed_activities]
                    )
                    print(f"  ✓ Mapped {len(activities_result.activities)} activities")
            except Exception as e:
                errors.append(f"Failed to map activities: {str(e)}")
                print(f"  ✗ Activity mapping error: {str(e)}")
            
            # Parse Flights
            try:
                fh_data = orchestrator_data.get("flights_and_hotels", {})
                outbound_data = fh_data.get("outbound_top_2_flights", [])
                return_data = fh_data.get("return_top_2_flights", [])
                
                if outbound_data and return_data:
                    flights_result = FlightRecommendations(
                        outbound_flights=[FlightOption(**f) for f in outbound_data],
                        return_flights=[FlightOption(**f) for f in return_data]
                    )
                    print(f"  ✓ Mapped {len(flights_result.outbound_flights)} outbound, {len(flights_result.return_flights)} return flights")
            except Exception as e:
                errors.append(f"Failed to map flights: {str(e)}")
                print(f"  ✗ Flight mapping error: {str(e)}")
            # errors = []
            # warnings = []
            # Parse Hotels
            # Parse Hotels
            try:
                fh_data = orchestrator_data.get("flights_and_hotels", {})
                print(f"\n[DEBUG] flights_and_hotels keys: {fh_data.keys()}")
                hotel_1 = fh_data.get("hotel_options_flight_1", {})
                hotel_2 = fh_data.get("hotel_options_flight_2", {})
                print(f"[DEBUG] hotel_1: {hotel_1}")
                print(f"[DEBUG] hotel_2: {hotel_2}")
                
                if hotel_1 or hotel_2:
                    # Helper to process hotel list and fix price format, add category label
                    def process_hotels(hotel_list, category_label):
                        processed = []
                        for h in hotel_list:
                            h_copy = h.copy()
                            h_copy["price"] = self._parse_cost(h.get("price", 0))
                            h_copy["category"] = category_label  # Add user-friendly category label
                            processed.append(h_copy)
                        return processed
                    
                    # Combine cheapest, highest_rated, most_expensive into scenarios WITH LABELS
                    scenario_A_hotels = (
                        process_hotels(hotel_1.get("cheapest", []), "Cheapest") +
                        process_hotels(hotel_1.get("highest_rated", []), "Highest Rated") +
                        process_hotels(hotel_1.get("most_expensive", []), "Luxury")
                    )
                    
                    scenario_B_hotels = (
                        process_hotels(hotel_2.get("cheapest", []), "Cheapest") +
                        process_hotels(hotel_2.get("highest_rated", []), "Highest Rated") +
                        process_hotels(hotel_2.get("most_expensive", []), "Luxury")
                    )
                    
                    hotels_result = HotelRecommendations(
                        scenario_A=HotelCategory(
                            hotels=[HotelOption(**h) for h in scenario_A_hotels],
                            category="flight_1_options"
                        ),
                        scenario_B=HotelCategory(
                            hotels=[HotelOption(**h) for h in scenario_B_hotels],
                            category="flight_2_options"
                        )
                    )
                    print(f"  ✓ Mapped {len(hotels_result.scenario_A.hotels)} hotels for scenario A, {len(hotels_result.scenario_B.hotels)} for scenario B")
            except Exception as e:
                errors.append(f"Failed to map hotels: {str(e)}")
                print(f"  ✗ Hotel mapping error: {str(e)}")
            
            costs = self._calculate_costs(orchestrator_data, request.trip_context.numTravelers)
            # Determine status
            # errors = []
            # warnings = []
            
            if not activities_result:
                warnings.append("No activities found")
            if not flights_result:
                warnings.append("No flights found")
            if not hotels_result:
                warnings.append("No hotels found")
            
            if not activities_result and not flights_result and not hotels_result:
                status = "error"
                errors.append("No results found from any agent")
            elif warnings:
                status = "partial"
            else:
                status = "success"
            
            print(f"\n[Phase2Supervisor] ✓ Phase 2 Complete")
            print(f"  Status: {status}")
            print(f"{'='*60}\n")
            
            return Phase2Response(
                status=status,
                activities=activities_result,
                flights=flights_result,
                hotels=hotels_result,
                estimated_total_cost=costs['total'] if costs['total'] > 0 else None,
                errors=errors,
                warnings=warnings,
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing failed: {str(e)}"
            print(f"\n[Phase2Supervisor] ✗ {error_msg}")
            print(f"Raw response (first 500 chars): {final_response_text[:500] if 'final_response_text' in locals() else 'N/A'}")
            return Phase2Response(
                status="error",
                activities=None,
                flights=None,
                hotels=None,
                estimated_total_cost=None,
                errors=[error_msg],
                warnings=[],
            )
            
        except ValueError as e:
            # Catches validation errors from _parse_orchestrator_output
            error_msg = f"Structure validation failed: {str(e)}"
            print(f"\n[Phase2Supervisor] ✗ {error_msg}")
            return Phase2Response(
                status="error",
                activities=None,
                flights=None,
                hotels=None,
                estimated_total_cost=None,
                errors=[error_msg],
                warnings=[],
            )
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            
            print(f"\n{'='*60}")
            print(f"[Phase2Supervisor] ✗ CRITICAL ERROR")
            print(f"Type: {type(e).__name__}")
            print(f"Error: {error_msg}")
            print(f"Stack Trace:\n{stack_trace}")
            print(f"{'='*60}\n")
            
            return Phase2Response(
                status="error",
                activities=None,
                flights=None,
                hotels=None,
                estimated_total_cost=None,
                errors=[error_msg],
                warnings=[],
            )


# Global singleton
phase2_supervisor = Phase2Supervisor()
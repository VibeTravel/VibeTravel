# backend/agents/phase3/supervisor.py

"""
Phase 3 Supervisor - Itinerary Planner

- Receives Phase3Input from FastAPI (user selections from Phase 2)
- Runs itinerary planner agent
- Parses the narrative output into structured Phase3Response
- Returns complete itinerary for frontend
"""

from typing import Dict, Any
import json
import uuid
import re
from datetime import datetime

from agents.utils.data_models import (
    Phase3Input,
    Phase3Response,
    DayPlan,
)

from agents.phase3.agent import root_agent as itinerary_planner_agent

# ADK runtime
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# ========================================
# ADK Runtime Setup
# ========================================
APP_NAME = "trip_planner_phase3"
USER_ID = "demo_user_phase3"

session_service = InMemorySessionService()

# Create runner
phase3_runner = Runner(
    agent=itinerary_planner_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# ========================================
# Phase 3 Supervisor
# ========================================
class Phase3Supervisor:
    """
    Phase 3 orchestrator:
    - Takes Phase3Input (user selections)
    - Runs itinerary planner agent
    - Parses narrative output into structured response
    - Returns Phase3Response
    """

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text"""
        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # Remove italic (*text* or _text_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # Remove leftover single/double asterisks or underscores
        text = re.sub(r'^\*+\s*', '', text)  # Leading asterisks
        text = re.sub(r'\s*\*+$', '', text)  # Trailing asterisks
        
        return text.strip()
    
    def _parse_narrative_to_structured(
        self, 
        narrative: str, 
        input_data: Phase3Input
    ) -> Phase3Response:
        """
        Parse the agent's narrative Markdown output into structured Phase3Response.
        
        The agent outputs:
        - Reasoning summary
        - ## Day 1 (Date)
        - ## Day 2 (Date)
        - etc.
        - Cost breakdown
        """
        
        # Extract daily plans using regex
        day_pattern = r'## Day (\d+) \(([^)]+)\)(.*?)(?=## Day \d+|## Activities Not Included|$)'
        matches = re.finditer(day_pattern, narrative, re.DOTALL)
        
        daily_plans = []
        for match in matches:
            day_num = int(match.group(1))
            date = match.group(2).strip()
            content = match.group(3).strip()
            
            # Extract activities from bullet points
            activities = []
            # Section headers to skip (case-insensitive)
            section_headers = {
                'morning', 'afternoon', 'evening', 'full day', 
                'morning/afternoon', 'afternoon/evening',
                'morning (optional)', 'afternoon (optional)', 'evening (optional)'
            }
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    # Clean the line - remove leading bullet and markdown
                    cleaned = line.lstrip('-*').strip()
                    cleaned = self._clean_markdown(cleaned)
                    
                    # Skip empty lines, malformed entries, or section headers
                    if cleaned and len(cleaned) > 3:
                        # Check if it's just a section header
                        cleaned_lower = cleaned.lower().strip(':').strip()
                        if cleaned_lower not in section_headers:
                            activities.append(cleaned)
            
            # Generate title from first activity or generic
            title = f"Day {day_num}"
            if activities:
                first_activity = activities[0].split(':')[0] if ':' in activities[0] else activities[0]
                title = self._clean_markdown(first_activity[:50])  # First 50 chars
            
            daily_plans.append(DayPlan(
                day_number=day_num,
                date=date,
                title=title,
                activities=activities,
                meals=[],
                notes=""
            ))
        
        # Calculate costs
        flight_cost = input_data.outbound_flight.price_usd + input_data.return_flight.price_usd
        
        # Calculate number of nights (from check-in to check-out)
        start_date = datetime.strptime(input_data.trip_start_date, "%Y-%m-%d")
        end_date = datetime.strptime(input_data.trip_end_date, "%Y-%m-%d")
        num_nights = (end_date - start_date).days
        
        hotel_cost = input_data.selected_hotel.price * num_nights
        activities_cost = sum(act.estimated_cost_per_person for act in input_data.selected_activities)
        
        # Estimate meals and misc (30% of activities)
        meals_misc = activities_cost * 0.3
        
        total_per_person = flight_cost + hotel_cost + activities_cost + meals_misc
        total_cost = total_per_person * input_data.num_travelers
        
        cost_breakdown = {
            "flights": flight_cost * input_data.num_travelers,
            "hotel": hotel_cost * input_data.num_travelers,
            "activities": activities_cost * input_data.num_travelers,
            "meals_and_misc": meals_misc * input_data.num_travelers,
        }
        
        # Format dates
        dates_str = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        
        return Phase3Response(
            status="success",
            destination=input_data.destination,
            dates=dates_str,
            num_travelers=input_data.num_travelers,
            outbound_flight=input_data.outbound_flight,
            return_flight=input_data.return_flight,
            hotel=input_data.selected_hotel,
            activities=input_data.selected_activities,
            daily_plans=daily_plans,
            total_cost=total_cost,
            cost_breakdown=cost_breakdown,
            created_at=datetime.now().isoformat(),
            errors=[],
            warnings=[]
        )

    async def run(self, request: Phase3Input) -> Phase3Response:
        """
        Execute Phase 3 itinerary planning.
        
        Steps:
        1. Build input JSON
        2. Run itinerary planner agent
        3. Collect narrative output
        4. Parse into structured response
        5. Return Phase3Response
        """
        print(f"\n{'='*60}")
        print(f"[Phase3Supervisor] Starting Itinerary Planning")
        print(f"Destination: {request.destination}")
        print(f"Dates: {request.trip_start_date} → {request.trip_end_date}")
        print(f"Travelers: {request.num_travelers}")
        print(f"Selected Activities: {len(request.selected_activities)}")
        print(f"{'='*60}\n")
        
        try:
            # Create session
            session_id = str(uuid.uuid4())
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
            )
            
            # Prepare message (send full Phase3Input as JSON)
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=request.model_dump_json(indent=2))],
            )
            
            print(f"[Phase3Supervisor] Running itinerary planner agent...")
            
            # Run agent
            events = phase3_runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_content,
            )
            
            # Collect final response
            final_response_text = ""
            event_count = 0
            
            async for event in events:
                event_count += 1
                
                if event.is_final_response():
                    if event.content and event.content.parts:
                        text = event.content.parts[0].text
                        if text:
                            final_response_text += text
                            print(f"  ✓ Captured {len(text)} characters from final response")
            
            print(f"\n[Phase3Supervisor] Event Summary:")
            print(f"  Total events: {event_count}")
            print(f"  Response length: {len(final_response_text)} chars")
            
            if not final_response_text:
                raise ValueError("No final response received from itinerary planner")
            
            # Show preview
            print(f"\n[Phase3Supervisor] Response Preview:")
            print(f"  First 300 chars: {final_response_text[:300]}")
            
            # Parse narrative to structured response
            print(f"\n[Phase3Supervisor] Parsing narrative to structured format...")
            result = self._parse_narrative_to_structured(final_response_text, request)
            print(f"  ✓ Parsed {len(result.daily_plans)} days")
            
            print(f"\n[Phase3Supervisor] ✓ Phase 3 Complete")
            print(f"{'='*60}\n")
            
            # Store in memory for PDF generation
            ITINERARY_STORAGE[result.created_at] = result
            print(f"[Phase3Supervisor] Stored itinerary with key: {result.created_at}")
            
            return result
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            
            print(f"\n{'='*60}")
            print(f"[Phase3Supervisor] ✗ CRITICAL ERROR")
            print(f"Type: {type(e).__name__}")
            print(f"Error: {error_msg}")
            print(f"Stack Trace:\n{stack_trace}")
            print(f"{'='*60}\n")
            
            # Return error response
            return Phase3Response(
                status="error",
                destination=request.destination,
                dates=f"{request.trip_start_date} - {request.trip_end_date}",
                num_travelers=request.num_travelers,
                outbound_flight=request.outbound_flight,
                return_flight=request.return_flight,
                hotel=request.selected_hotel,
                activities=request.selected_activities,
                daily_plans=[],
                total_cost=0.0,
                cost_breakdown={},
                created_at=datetime.now().isoformat(),
                errors=[error_msg],
                warnings=[]
            )


# Global singleton
phase3_supervisor = Phase3Supervisor()

# In-memory storage for generated itineraries (for PDF generation)
# Key: created_at timestamp, Value: Phase3Response
ITINERARY_STORAGE = {}


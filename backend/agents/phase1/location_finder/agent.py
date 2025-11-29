

# # backend/agents/phase1/location_finder/agent.py
# """
# Phase 1 – Location Finder Agent

# This ADK agent:
# - Takes structured TripDetails as context (user_location, interests, budget, duration).
# - Uses google_search tool to search the web.
# - Returns a structured list of candidate destinations.
# """

# from google.adk.agents import Agent
# from google.adk.tools import google_search

# from agents.utils.instructions_loader import load_instruction_from_file
# from agents.utils.data_models import PreliminarySuggestions

# MODEL_NAME = "gemini-2.5-flash"#"gemini-2.5-flash"

# # Load instructions (we'll update this file later)
# location_finder_instructions = load_instruction_from_file(
#     "location_finder.txt",
#     relative_to_caller=True
# )

# location_finder_agent = Agent(
#     name="location_finder_agent",
#     model=MODEL_NAME,
#     instruction=location_finder_instructions,
#     description="Searches the web and proposes travel destinations based on trip details.",
#     output_schema=PreliminarySuggestions,
#     output_key="preliminary_location_suggestions",   # MUST match the Pydantic model
#     tools=[google_search],
# )
# backend/agents/phase1/location_finder/agent.py

# backend/agents/phase1/location_finder/agent.py
# backend/agents/phase1/location_finder/agent.py

from google.adk.agents import Agent
from google.adk.tools import google_search  # ← Add this back

from agents.utils.instructions_loader import load_instruction_from_file
from agents.utils.data_models import PreliminarySuggestions

MODEL_NAME = "gemini-2.5-flash"  # ← Keep this model

location_finder_instructions = load_instruction_from_file(
    "location_finder.txt",
    relative_to_caller=True
)

location_finder_agent = Agent(
    name="location_finder_agent",
    model=MODEL_NAME,
    instruction=location_finder_instructions,
    description="Searches the web and proposes travel destinations based on trip details.",
    # output_schema=PreliminarySuggestions,
    output_key="preliminary_location_suggestions",
    tools=[google_search],  # ← Add this back
)
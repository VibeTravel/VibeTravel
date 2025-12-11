from google.adk.agents import Agent
from google.adk.tools import google_search  # ← Add this back

from agents.utils.instructions_loader import load_instruction_from_file

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
    tools=[],  # ← Temporarily disabled google_search to avoid rate limits
)
# backend/agents/phase2/activity_finder/agent.py

from google.adk.agents import Agent
from google.adk.tools import google_search

from agents.utils.instructions_loader import load_instruction_from_file

MODEL_NAME = "gemini-2.5-flash"

activity_finder_instructions = load_instruction_from_file(
    "activity_finder_instructions.txt",
    relative_to_caller=True
)

activity_finder_agent = Agent(
    name="activity_finder_agent",
    model=MODEL_NAME,
    instruction=activity_finder_instructions,
    description="Researches activities in a destination and provides pricing, duration, and descriptions suitable for travel itineraries.",
    output_key="activities",
    tools=[google_search],
)
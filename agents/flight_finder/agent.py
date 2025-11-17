from google.adk.agents import Agent
from google.adk.tools import google_search
from agents.utils.instructions_loader import load_instruction_from_file
import os
from dotenv import load_dotenv

load_dotenv()

# Load prompt
flight_instructions = load_instruction_from_file( "flight_prompt.txt")

# Define agent
flight_search_agent = Agent(
    name="flight_search_agent",
    model="gemini-2.0-flash",  # or LiteLlm fallback later
    instruction=flight_instructions,
    description="Searches for flights for each preferred destination.",
    tools=[google_search],  # We will override this in fallback logic
    output_key="flight_search_results",
)

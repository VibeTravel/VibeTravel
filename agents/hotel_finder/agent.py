from google.adk.agents import Agent
from google.adk.tools import google_search
from agents.utils.instructions_loader import load_instruction_from_file
import os
from dotenv import load_dotenv

load_dotenv()

hotel_instructions = load_instruction_from_file("hotel_prompt.txt")


hotel_search_agent = Agent(
    name="hotel_search_agent",
    model="gemini-2.0-flash",
    instruction=hotel_instructions,
    description="Finds hotel/accommodation options for each preferred destination.",
    tools=[google_search],
    output_key="hotel_search_results",
)

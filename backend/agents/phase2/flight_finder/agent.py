# agent.py - Google ADK Flight Finder Agent

from typing import List, Dict, Any
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .flight_hotel_utils import (
    find_airports,
    fallback_scraper,
    scrape_hotels,
)
from agents.utils.instructions_loader import load_instruction_from_file

bestflight_agent = Agent(
    name="bestflight_agent",
    model="gemini-2.5-pro",
    instruction=load_instruction_from_file(
        "best_flight_agent_instructions.txt"
    ),
    description="Finds the best roundtrip flights between cities using airport lookup, flight search, and intelligent selection.",
)


flight_hotel_finder_instructions = load_instruction_from_file(
    "flight_hotel_finder_agent_instructions.txt"
)

# Create the Flight Finder Agent
flight_hotel_finder_agent = Agent(
    name="flight_hotel_finder_agent",
    model="gemini-2.5-pro",
    instruction=flight_hotel_finder_instructions,
    description="Finds the best roundtrip flights between cities using airport lookup, flight search, and intelligent selection and also provides appropriate hotel choices for the duration of stay.",
    tools=[
        FunctionTool(find_airports),
        FunctionTool(fallback_scraper),
        FunctionTool(scrape_hotels),
        AgentTool(bestflight_agent),
    ]
)
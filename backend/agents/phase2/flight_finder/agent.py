# agent.py - Google ADK Flight Finder Agent

from typing import List, Dict, Any
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .flight_utils import (
    find_airports,
    fallback_scraper,
    get_all_flights
)
from agents.utils.instructions_loader import load_instruction_from_file
# Agent instructions
flight_finder_instructions = load_instruction_from_file(
    "flight_finder.txt")

bestflight_agent = Agent(
    name="bestflight_agent",
    model="gemini-2.0-flash",
    instruction=""" Given all the flight options, pick the TOP 2 best flights considering:
      1. Price (lower is better)
      2. Duration (shorter is better)  
      3. Number of stops (fewer is better)
      Return only 2 flights in the following format. Remember that the following are just examples.
      You must analyze the flight data available to you and pick the best 2 flights. The example below is just for reference.
      [
      {departure_airport: 'John F. Kennedy International Airport(JFK)' 
      departure_time:'2020-01-06 23:20' 
      arrival_airport: 'Hamad International Airport(DOH)' 
      arrival_time: '2020-01-07 06:40'
      duration: '740'
      airplane: 'Boeing 777'
      airline: 'Qatar Airways',
      price: '$2970'},
      {departure_airport:'John F. Kennedy International Airport(JFK)' 
      departure_time:'2020-01-06 15:30' 
      arrival_airport: 'Hamad International Airport(DOH)' 
      arrival_time: '2020-01-07 02:10'
      duration: '800'
      airplane: 'Airbus A350'
      airline: 'Qatar Airways',
      price: '$2508'}
      ]

   """,
    description="Finds the best roundtrip flights between cities using airport lookup, flight search, and intelligent selection.",
)




# Create the Flight Finder Agent
root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction=flight_finder_instructions,
    description="Finds the best roundtrip flights between cities using airport lookup, flight search, and intelligent selection.",
    tools=[
        FunctionTool(find_airports),
        FunctionTool(fallback_scraper),
        AgentTool(bestflight_agent),
    ]
)
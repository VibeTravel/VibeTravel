# from google.adk.agents import Agent
# from google.adk.tools import AgentTool

# from agents.location_finder import root_agent as location_agent
# from agents.flight_finder import root_agent as flight_agent
# from agents.hotel_finder import root_agent as hotel_agent
# from agents.itinerary_generator import root_agent as itinerary_agent
# from agents.trip_detail_parser import root_agent as parser_agent
# from utils.instructions_loader import load_instruction_from_file



# #this needs to be thought of since we are passing them as subagents

# location_tool = AgentTool(agent=location_agent)
# flight_tool   = AgentTool(agent=flight_agent)
# hotel_tool    = AgentTool(agent=hotel_agent)
# itinerary_tool = AgentTool(agent=itinerary_agent)
# parser_tool    = AgentTool(agent=parser_agent)


# root_agent = Agent(
#     name="main_agent",
#     model="gemini-2.5-flash",
#     instructions=load_instruction_from_file("Main_Agent_Instructions.txt"),
    
#     tools=[location_tool, flight_tool, hotel_tool, itinerary_tool, parser_tool],
# )

from google.adk.agents import SequentialAgent, ParallelAgent, Agent

# Import all partial agents
from agents.location_finder.agent import (
    trip_input_agent,
    location_finder_agent,
    destination_rater_agent
)

from agents.flight_finder.agent import flight_search_agent
from agents.hotel_finder.agent import hotel_search_agent
from agents.itinerary_generator.agent import itinerary_agent


# Supervisor agent
# from agents.main_agent.supervisor import supervisor_agent   # when we create one


supervisor_instructions = """
You are the supervisor agent.

Your job:
- Read `destination_rating_results`.
- If at least 1 preferred destination exists:
    Output {"should_search": true}
- Otherwise:
    Output {"should_search": false}
"""

supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-2.0-flash",
    instruction=supervisor_instructions,
    output_key="search_trigger"
)




# Parallel agent
flight_and_hotel_parallel = ParallelAgent(
    name="flight_and_hotel_parallel",
    sub_agents=[flight_search_agent, hotel_search_agent]
)

# Final root agent
root_agent = SequentialAgent(
    name="location_finder_root_agent",
    sub_agents=[
        trip_input_agent,
        location_finder_agent,
        destination_rater_agent,
        supervisor_agent,
        flight_and_hotel_parallel,
        itinerary_agent
    ]
)

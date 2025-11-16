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


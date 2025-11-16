from google.adk.agents import Agent, SequentialAgent
# from google.adk.utils import load_instruction_from_file
# from google.adk.models.lite_llm import LiteLlm
from agents.utils.instructions_loader import load_instruction_from_file
from dotenv import load_dotenv
from google.adk.tools import google_search
load_dotenv()
# MODEL
# model = LiteLlm(model="openai/gpt-4o-mini")
model='gemini-2.5-flash'
# LOAD INSTRUCTIONS
trip_input_instructions = load_instruction_from_file(
    "trip_input.txt"
)

location_finder_instructions = load_instruction_from_file(
    "location_finder.txt"
)

# TRIP INPUT AGENT
trip_input_agent = Agent(
    name="trip_input_agent",
    model=model,
    instruction=trip_input_instructions,
    description="Collects mandatory trip details from the user: location, interests, budget, duration.",
    output_key = "trip_details",
)

# LOCATION FINDER AGENT (placeholder for now)
location_finder_agent = Agent(
    name="location_finder_agent",
    model=model,
    instruction=location_finder_instructions,
    description="Suggests travel destinations and activities using {trip_details} and web search.",
    output_key = "preliminary_location_suggestions",
    tools=[google_search],
)

rating_instructions = load_instruction_from_file("destination_rating.txt")

destination_rater_agent = Agent(
    name="destination_rater_agent",
    model="gemini-2.5-flash",
    instruction=rating_instructions,
    description="Shows destinations one-by-one, asks user for ratings, and classifies into preferred/unpreferred lists.",
    output_key="destination_rating_results"
)
root_agent = SequentialAgent(
    name="location_finder_root_agent",
    sub_agents=[
        trip_input_agent,
        location_finder_agent,
        destination_rater_agent
    ],
    description="Collects trip details → finds locations → rates destinations."
)

# Expose the agent you want ADK to load when selecting this app folder
# root_agent = location_finder_agent

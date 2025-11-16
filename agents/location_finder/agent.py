from google.adk.agents import Agent
# from google.adk.utils import load_instruction_from_file
# from google.adk.models.lite_llm import LiteLlm
from agents.utils.instructions_loader import load_instruction_from_file
from dotenv import load_dotenv
load_dotenv()
# MODEL
# model = LiteLlm(model="openai/gpt-4o-mini")

# LOAD INSTRUCTIONS
trip_input_instructions = load_instruction_from_file(
    "trip_input.txt"
)

# location_finder_instructions = load_instruction_from_file(
#     "location_finder.txt"
# )

# TRIP INPUT AGENT
trip_input_agent = Agent(
    name="trip_input_agent",
    model='gemini-2.5-flash',
    instruction=trip_input_instructions,
    description="Collects mandatory trip details from the user: location, interests, budget, duration.",
    output_key = "trip_details",
)

# # LOCATION FINDER AGENT (placeholder for now)
# location_finder_agent = Agent(
#     name="location_finder_agent",
#     model=model,
#     instructions=location_finder_instructions,
#     description="Suggests travel destinations and activities.",
#     output_key = "preliminary_location_suggestions",
# )

# Expose the agent you want ADK to load when selecting this app folder
root_agent = trip_input_agent

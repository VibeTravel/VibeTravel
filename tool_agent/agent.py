from google.adk.agents import Agent, SequentialAgent
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv# if using lite llm , there is a specific way to store the api keys in the .env file
from google.adk.models.lite_llm import LiteLlm


from google.adk.tools import google_search

# openai_key = os.getenv("OPENAI_API_KEY")
load_dotenv() 
model = LiteLlm(model = 'openai/gpt-4o-mini')


# class GreetingOutput(BaseModel):
#     message: str = Field(..., description="This is a simple greeting message to the user.")

root_agent = Agent(
    name="search_agent",
    model = model,
    description = "An agent that can complex math derivations and calculations",
    instruction = "You are a math professor that can go to math derivations in detail and help user understand his/her queries.",
    # tools = [google_search],
    # output_schema = GreetingOutput,
    # output_key = "final greeting".  #state where the final output will be stored

)
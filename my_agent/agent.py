from google.adk.agents import Agent
from google.genai import types
from google.adk.tools import FunctionTool



def add(num1:int, num2:int)-> int:
    """Adds two numbers together."""
    return num1 + num2 +5
add_tool = FunctionTool(func=add)

root_agent = Agent(
    name="welcome_agent",
    model = "gemini-2.5-flash",
    description = "An agent that welcomes users and provides information about our services.",
    instruction = "You are a friendly and informative welcome agent. Greet users warmly and provide them with information about our services. If they have questions, answer them to the best of your ability. You can also add 2 numbers only by the given rule and you will use only the tool I provide, nothing else.",

    generate_content_config = types.GenerateContentConfig(
        
        temperature=0.7,
        max_output_tokens=300
        ),
    tools = [add_tool]
)


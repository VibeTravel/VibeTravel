# # agents/location_finder_agent.py

# import os
# from dotenv import load_dotenv
# import requests
# import google.generativeai as genai

# # Load API keys
# load_dotenv()
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# if not TAVILY_API_KEY or not GOOGLE_API_KEY:
#     raise ValueError("Missing API keys in .env file!")

# # Configure Gemini
# genai.configure(api_key=GOOGLE_API_KEY)


# class LocationFinderAgent:
#     def __init__(self, model_name="models/gemini-2.5-flash"):
#         self.model = genai.GenerativeModel(model_name)

#     def search_with_tavily(self, query: str, max_results: int = 15):
#         """
#         Query the Tavily API to get real-time travel destination data.
#         """
#         url = "https://api.tavily.com/search"
#         payload = {
#             "api_key": TAVILY_API_KEY,
#             "query": query,
#             "max_results": max_results
#         }
#         response = requests.post(url, json=payload)
#         response.raise_for_status()
#         return response.json()

#     def find_destinations(self, current_location: str, duration_days: int, activities: list, budget: str, search_mode: str = "global" ): # can be "local" or "global"

#         print("TAVILY_API_KEY:", TAVILY_API_KEY)  # Debugging line
#         print("GOOGLE_API_KEY:", GOOGLE_API_KEY)  # Debugging line
#         """
#         Use Tavily + Gemini to find suitable destinations for the given preferences.

#         Parameters:
#             current_location (str): User's current city/country
#             duration_days (int): Number of days for the trip
#             activities (list): List of user interests (e.g., ["hiking", "wine tasting"])
#             budget (str): Budget level ("low", "moderate", "high")
#             search_mode (str): "local" to search near current_location, "global" for anywhere

#         Returns:
#             str: JSON-formatted string with recommended destinations
#         """
#         # Step 1: Build search query
#         activity_str = ", ".join(activities)
#         if search_mode == "local":
#             search_query = (
#                 f"Best destinations near {current_location} for {activity_str} "
#                 f"within a {budget} budget for a {duration_days}-day trip"
#             )
#         else:  # global
#             search_query = (
#                 f"Best destinations around the world for {activity_str} "
#                 f"within a {budget} USD budget for a {duration_days}-day trip"
#             )

#         # Step 2: Query Tavily
#         tavily_results = self.search_with_tavily(search_query)
#         print("Tavily Results:", tavily_results)  # Debugging line

#         # Step 3: Summarize and structure results with Gemini
#         prompt = f"""
#         You are an intelligent travel planning AI. Your job is to analyze the travel destination data and provide a summary of the best options.
#         The user wants to go on a {duration_days}-day trip focused on these activities: {activity_str}, with a {budget} budget(in USD).
#         Your specialty is in finding the travel destinations based on the activities that the user wants.
#         The data you provide will be used to create a webpage with travel destination recommendations. Your job is to provide **10 distinct destinations** 
#         with diverse locations and experiences based on the Tavily web search results.
#         THIS IS IMPORTANT: PROVIDE AT LEAST 10 DISTINCT DESTINATIONS IN THE RESULTS. Else your job will be incomplete.

#         Based on the following web search results from Tavily:
#         {tavily_results}

      
#         Return ONLY valid JSON with the following structure:
#         {
#           "results": [
#             {
#               "destination": "...",
#               "country": "...",
#               "recommended_activities": ["...", "..."],
#               "description": "...",
#               "image_url": "...",
#               "estimated_budget": "..."
#             },
#             {
#               "destination": "...",
#               "country": "...",
#               "recommended_activities": ["...", "..."],
#               "description": "...",
#               "image_url": "...",
#               "estimated_budget": "..."
#             },
#             ...
#             (repeat at least 10 times)
#           ]
#         }
#         """

#         # response = self.model.generate_content(prompt)
#         response = self.model.generate_content(
#           prompt,
#           max_output_tokens=10000 ) # optional, adjust as needed)
#         return response.text
    

# # Example usage:
# agent = LocationFinderAgent()
# result = agent.find_destinations(
#     current_location="Nepal",
#     duration_days=5,
#     activities=["hiking", "art", "wine tasting"], 
#     budget="moderate"
# )





import os
from dotenv import load_dotenv
import requests
import google.generativeai as genai

# Load API keys
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    raise ValueError("Missing API keys in .env file!")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)


class LocationFinderAgent:
    def __init__(self, model_name="models/gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    def search_with_tavily(self, query: str, max_results: int = 15):
        """
        Query the Tavily API to get real-time travel destination data.
        """
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def find_destinations(self, current_location: str, duration_days: int, activities: list, budget: str, search_mode: str = "global" ): # can be "local" or "global"

   
        """
        Use Tavily + Gemini to find suitable destinations for the given preferences.

        Parameters:
            current_location (str): User's current city/country
            duration_days (int): Number of days for the trip
            activities (list): List of user interests (e.g., ["hiking", "wine tasting"])
            budget (str): Budget level ("low", "moderate", "high")
            search_mode (str): "local" to search near current_location, "global" for anywhere

        Returns:
            str: JSON-formatted string with recommended destinations
        """
        # Step 1: Build search query
        activity_str = ", ".join(activities)
        if search_mode == "local":
            search_query = (
                f"Best destinations near {current_location} for {activity_str} "
                f"within a {budget} budget including travel costs for a {duration_days}-day trip"
            )
        else:  # global
            search_query = (
                f"Best destinations around the world for {activity_str} "
                f"within a {budget} USD budget including travel costs for a {duration_days}-day trip"
            )

        # Step 2: Query Tavily
        tavily_results = self.search_with_tavily(search_query)
      

        # Step 3: Summarize and structure results with Gemini
        prompt = f"""
        You are an intelligent travel planning AI. Your job is to analyze the travel destination data and provide a summary of the best options.
        The user wants to go on a {duration_days}-day trip focused on these activities: {activity_str}, with a {budget} budget(in USD).

        Provide **10 distinct destinations** with diverse locations based on the Tavily web search results.

        Based on the following web search results from Tavily:
        {tavily_results}

        Return ONLY valid JSON with the following structure:
        DONOT RETURN ANY MADE UP FACTS. IF YOU ARE UNSURE, RETURN INFORMATION FROM THE TAVILY RESULTS ONLY.
        {{
        "results": [
            {{
            "destination": "...",
            "country": "...",
            "recommended_activities": ["...", "..."],
            "description": "...",
            "image_url": "...",
            "estimated_budget": "..."
            }},
            {{
            "destination": "...",
            "country": "...",
            "recommended_activities": ["...", "..."],
            "description": "...",
            "image_url": "...",
            "estimated_budget": "..."
            }}
            // repeat at least 10 times
        ]
        }}
        """


        # response = self.model.generate_content(prompt)
        response = self.model.generate_content(
          prompt)
        #   max_output_tokens=10000 ) # optional, adjust as needed)
        return response.text
    

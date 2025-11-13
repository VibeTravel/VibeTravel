# agents/explorer_agent.py

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class ExplorerAgent:
    def __init__(self, model_name="models/gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    def explore(self, destination, days=3, interests=None, budget="moderate"):
        """
        Explore a destination and return a structured itinerary proposal.
        """
        if interests is None:
            interests = ["culture", "food", "nature"]

        prompt = f"""
        You are a professional travel planner AI called 'Vibe Explorer'.

        Create a {days}-day itinerary for a trip to {destination}.
        Traveler interests: {', '.join(interests)}.
        Budget level: {budget}.

        For each day, include:
        - A short title (like "Exploring the Old Town")
        - 3–4 activities (morning, afternoon, evening)
        - Local dining suggestions
        - Cultural or offbeat experiences
        - Short travel tips (e.g., timing, weather, transportation)

        Return the response as **valid JSON** with the structure:
        {{
          "destination": "...",
          "days": [
            {{
              "day": 1,
              "title": "...",
              "activities": ["...", "...", "..."],
              "dining": ["..."],
              "tips": ["..."]
            }}
          ]
        }}
        """

        response = self.model.generate_content(prompt)

        return response.text

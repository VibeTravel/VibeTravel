"""
Simple test script for the Activity Finder endpoint
"""

import requests
import json

# Test data
test_request = {
    "activities": [
        "Eiffel Tower visit",
        "Louvre Museum",
        "Seine River cruise"
    ],
    "city": "Paris",
    "num_days": 3,
    "budget_per_person": 300.0
}

# Make the request
url = "http://localhost:8000/activity-finder/search"
print(f"Testing endpoint: {url}")
print(f"Request data: {json.dumps(test_request, indent=2)}")
print("\n" + "="*50 + "\n")

try:
    response = requests.post(url, json=test_request)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.ConnectionError:
    print("❌ Error: Could not connect to the server.")
    print("Make sure the server is running with: uvicorn main:app --reload")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if response:
        print(f"Response text: {response.text}")

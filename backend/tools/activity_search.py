"""
Tavily search tool for activity research.
"""

import os
from typing import List, Dict, Any
from tavily import TavilyClient


def tavily_search_activities(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for activity information using Tavily API.
    
    Args:
        query: Search query string (e.g., "Eiffel Tower tour prices Paris")
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        List of search results with title, content, and url
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")
    
    client = TavilyClient(api_key=api_key)
    
    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )
        
        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
                "score": result.get("score", 0.0)
            })
        
        # Include the AI-generated answer if available
        if response.get("answer"):
            results.insert(0, {
                "title": "Summary",
                "content": response["answer"],
                "url": "",
                "score": 1.0
            })
        
        return results
        
    except Exception as e:
        print(f"[Tavily Search] Error: {e}")
        return [{"title": "Error", "content": str(e), "url": "", "score": 0.0}]

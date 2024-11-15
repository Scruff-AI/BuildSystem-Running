"""Web search functionality using Tavily."""

import os
from typing import List, Dict
import httpx
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_API_URL = "https://api.tavily.com/search"

async def search(query: str) -> List[Dict[str, str]]:
    """Search the web using Tavily API.
    
    Args:
        query: The search query string
        
    Returns:
        List of search results, each containing title, url, and snippet
    """
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": TAVILY_API_KEY
    }
    
    params = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "include_domains": ["github.com", "stackoverflow.com", "python.org"],
        "exclude_domains": []
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TAVILY_API_URL,
                headers=headers,
                json=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
    except httpx.RequestError as e:
        raise ValueError(f"Network error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error during web search: {str(e)}")

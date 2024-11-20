"""Web search functionality using Tavily API with Brave Search as failover."""

import os
import json
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv
from utils.logging_config import server_logger as logger
from functools import lru_cache
import asyncio
from tavily import TavilyClient

load_dotenv()

class SearchManager:
    """Manages web search capabilities using Tavily API with Brave Search failover."""
    
    def __init__(self):
        """Initialize search manager with API keys."""
        tavily_key = os.getenv("TAVILY_API_KEY")
        brave_key = os.getenv("BRAVE_API_KEY")
        
        if not tavily_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        if not brave_key:
            logger.warning("BRAVE_API_KEY not found - failover search will be disabled")
            
        self.tavily_client = TavilyClient(api_key=tavily_key)
        self.brave_api_key = brave_key
        self.brave_search_url = "https://api.search.brave.com/res/v1/web/search"
    
    async def tavily_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Perform search using Tavily API."""
        try:
            logger.info(f"Performing Tavily search for: {query}")
            # Run Tavily search in a thread pool since it's not async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results
                )
            )
            
            # Format results to match our standard structure
            results = []
            for result in response.get('results', []):
                formatted_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("relevance_score", 0.0)
                }
                results.append(formatted_result)
                
            logger.info(f"Tavily search completed successfully. Found {len(results)} results.")
            return results
            
        except Exception as e:
            error_msg = f"Tavily search failed: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    async def brave_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Perform failover search using Brave Search API."""
        if not self.brave_api_key:
            raise ValueError("Brave Search API key not configured for failover")
            
        headers = {
            "X-Subscription-Token": self.brave_api_key
        }
        
        params = {
            "q": query,
            "count": max_results
        }
        
        try:
            logger.info(f"Performing Brave failover search for: {query}")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.brave_search_url,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                search_result = response.json()
            
            results = []
            for result in search_result.get('web', {}).get('results', []):
                formatted_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("description", ""),
                    "score": result.get("score", 0.0)
                }
                results.append(formatted_result)
            
            logger.info(f"Brave failover search completed successfully. Found {len(results)} results.")
            return results
            
        except Exception as e:
            error_msg = f"Brave failover search failed: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

# Initialize search manager
search_manager = SearchManager()

async def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search the web using Tavily API with Brave Search failover."""
    try:
        logger.info(f"Processing search request: {query}")
        try:
            # Try Tavily search first
            results = await search_manager.tavily_search(query, max_results)
        except Exception as e:
            logger.warning(f"Tavily search failed, falling back to Brave: {str(e)}")
            # Fallback to Brave search
            results = await search_manager.brave_search(query, max_results)
        
        # Ensure results are properly formatted
        formatted_results = []
        for result in results:
            formatted_result = {
                "title": result["title"],
                "url": result["url"],
                "content": result["content"]
            }
            if result.get("score", 0) > 0:
                formatted_result["relevance_score"] = result["score"]
            formatted_results.append(formatted_result)
            
        logger.info(f"Search completed successfully. Returning {len(formatted_results)} results.")
        return formatted_results
        
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Parallel processing for multiple queries
async def parallel_search(queries: List[str], max_results: int = 5) -> List[Dict[str, str]]:
    """Perform multiple searches in parallel."""
    tasks = [search(query, max_results) for query in queries]
    results = await asyncio.gather(*tasks)
    return results

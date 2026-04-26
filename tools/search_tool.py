"""Web search tool — wraps the Tavily API for keyword-based web search."""

import os
from typing import List, Dict, Any
from tavily import TavilyClient

def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using Tavily API and return results.
    Returns a list of dicts with keys: title, url, snippet, score.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Warning: TAVILY_API_KEY environment variable not set")
        return []
        
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results)
        
        results = []
        for res in response.get("results", []):
            results.append({
                "title": res.get("title", ""),
                "url": res.get("url", ""),
                "snippet": res.get("content", ""),
                "score": res.get("score", 0.0)
            })
        return results
    except Exception as e:
        print(f"Error during Tavily search: {e}")
        return []

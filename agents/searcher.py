import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any
from tools.search_tool import search_web

def search_sub_question(sub_question: str) -> List[Dict[str, Any]]:
    """
    Takes a sub-question, uses the Tavily tool to search, 
    returns top 4 URLs with snippets.
    """
    results = search_web(query=sub_question, max_results=4)
    
    formatted_results = []
    for res in results[:4]:
        formatted_results.append({
            "url": res["url"],
            "title": res["title"],
            "snippet": res["snippet"]
        })
        
    return formatted_results

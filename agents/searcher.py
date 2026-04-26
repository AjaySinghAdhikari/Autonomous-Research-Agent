"""Searcher agent — searches the web for each sub-question using Tavily."""

import os
from dotenv import load_dotenv

load_dotenv()

from typing import List, Dict, Any
from tools.search_tool import search_web


def search_sub_question(sub_question: str) -> List[Dict[str, Any]]:
    """
    Takes a sub-question, uses the Tavily search tool,
    and returns the top 4 results with URL, title, and snippet.
    """
    results = search_web(query=sub_question, max_results=4)

    return [
        {"url": res["url"], "title": res["title"], "snippet": res["snippet"]}
        for res in results[:4]
    ]

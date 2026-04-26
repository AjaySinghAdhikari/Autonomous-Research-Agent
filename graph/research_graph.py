"""LangGraph pipeline — orchestrates the five research agents in sequence."""

import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

# Import the agents
from agents.planner import plan_research
from agents.searcher import search_sub_question
from agents.reader import read_and_store
from agents.critic import find_contradictions
from agents.writer import write_report

# Define the state
class ResearchState(TypedDict):
    topic: str
    sub_questions: List[str]
    search_results: List[Dict[str, Any]]
    scraped_content: Dict[str, str]
    contradictions: List[Dict[str, Any]]
    final_report: str
    status: str
    current_step: str

# Define nodes
def planner_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Planner...")
    topic = state["topic"]
    plan = plan_research(topic)
    return {
        "sub_questions": plan["sub_questions"],
        "status": "Plan created: " + plan["research_strategy"],
        "current_step": "planner"
    }

def searcher_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Searcher...")
    all_results = []
    for sq in state.get("sub_questions", []):
        results = search_sub_question(sq)
        all_results.extend(results)
    
    unique_results = list({res['url']: res for res in all_results}.values())
    
    return {
        "search_results": unique_results,
        "status": f"Found {len(unique_results)} search results.",
        "current_step": "searcher"
    }

def reader_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Reader...")
    urls = [res["url"] for res in state.get("search_results", [])]
    scraped_content = read_and_store(urls)
    
    return {
        "scraped_content": scraped_content,
        "status": f"Scraped {len(scraped_content)} web pages.",
        "current_step": "reader"
    }

def critic_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Critic...")
    scraped_content = state.get("scraped_content", {})
    contradictions = find_contradictions(scraped_content)
    
    return {
        "contradictions": contradictions,
        "status": f"Found {len(contradictions)} contradictions.",
        "current_step": "critic"
    }

def writer_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Writer...")
    topic = state["topic"]
    scraped_content = state.get("scraped_content", {})
    contradictions = state.get("contradictions", [])
    
    final_report = write_report(topic, scraped_content, contradictions)
    
    return {
        "final_report": final_report,
        "status": "Report complete.",
        "current_step": "writer"
    }

# Build the graph
workflow = StateGraph(ResearchState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("reader", reader_node)
workflow.add_node("critic", critic_node)
workflow.add_node("writer", writer_node)

# Add edges
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "searcher")
workflow.add_edge("searcher", "reader")
workflow.add_edge("reader", "critic")
workflow.add_edge("critic", "writer")
workflow.add_edge("writer", END)

# Compile the graph
app = workflow.compile()

def run_research(topic: str) -> ResearchState:
    """
    Invokes the research graph and returns the final state.
    """
    initial_state = {
        "topic": topic,
        "sub_questions": [],
        "search_results": [],
        "scraped_content": {},
        "contradictions": [],
        "final_report": "",
        "status": "Starting research process...",
        "current_step": "START"
    }
    
    final_state = app.invoke(initial_state)
    return final_state

import os
import time
import functools
from dotenv import load_dotenv
load_dotenv()

# LAYER 1: LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "autonomous-research-agent"

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

# Import the agents
from agents.planner import plan_research
from agents.searcher import search_sub_question
from agents.reader import read_and_store
from agents.critic import find_contradictions
from agents.writer import write_report
from memory.vector_store import VectorStore

# LAYER 2: Google Cloud Logging
def get_logger():
    try:
        from google.cloud import logging as gcloud_logging
        client = gcloud_logging.Client()
        return client.logger("research-agent")
    except Exception as e:
        print(f"Warning: Google Cloud Logging disabled. ({e})")
        return None

logger = get_logger()

def log_node_event(node: str, state_summary: dict, duration_ms: int, error: str = None):
    log_data = {
        "node": node,
        "topic": state_summary.get("topic", "unknown"),
        "duration_ms": duration_ms,
        "n_results": len(state_summary.get("search_results", [])) if "search_results" in state_summary else 0,
        "error": error
    }
    
    if logger:
        logger.log_struct(log_data, severity="ERROR" if error else "INFO")
    else:
        # Fallback to stdout if GCP is unavailable
        status = "ERROR" if error else "INFO"
        print(f"[{status}] Node: {node} | Duration: {duration_ms}ms | Error: {error}")

# LAYER 3: Timing and Error Recovery Decorator
def traced_node(node_name: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(state):
            t0 = time.time()
            try:
                result = fn(state)
                # Merge input and output to extract the topic for logging
                merged_state = {**state, **result}
                log_node_event(node_name, merged_state, int((time.time() - t0) * 1000))
                return result
            except Exception as e:
                log_node_event(node_name, state, int((time.time() - t0) * 1000), error=str(e))
                # Return safe partial state so the graph can continue seamlessly
                return {"status": f"ERROR in {node_name}: {e}", "current_step": node_name}
        return wrapper
    return decorator

# Define the state
class ResearchState(TypedDict):
    topic: str
    sub_questions: List[str]
    search_results: List[Dict[str, Any]]
    scraped_content: Dict[str, str]
    contradictions: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    final_report: str
    status: str
    current_step: str
    complexity_score: int
    search_expanded: bool
    rewrite_count: int

# Define nodes with decorators

@traced_node("planner")
def planner_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Planner...")
    topic = state["topic"]
    plan = plan_research(topic)
    return {
        "sub_questions": plan.get("sub_questions", []),
        "complexity_score": plan.get("complexity_score", 5),
        "status": "Plan created: " + plan.get("research_strategy", "Strategy created."),
        "current_step": "planner"
    }

@traced_node("searcher")
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

@traced_node("expand_search")
def expand_searcher_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Expand Searcher...")
    topic = state["topic"]
    new_queries = [
        f"{topic} latest news developments",
        f"{topic} expert opinions and controversies",
        f"{topic} comprehensive review analysis"
    ]
    
    all_results = state.get("search_results", [])
    for sq in new_queries:
        results = search_sub_question(sq)
        all_results.extend(results)
        
    unique_results = list({res['url']: res for res in all_results}.values())
    
    return {
        "search_results": unique_results,
        "search_expanded": True,
        "status": f"Expanded search. Now have {len(unique_results)} results.",
        "current_step": "expand_search"
    }

@traced_node("reader")
def reader_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Reader...")
    urls = [res["url"] for res in state.get("search_results", [])]
    scraped_content = read_and_store(urls)
    
    return {
        "scraped_content": scraped_content,
        "status": f"Scraped {len(scraped_content)} web pages.",
        "current_step": "reader"
    }

@traced_node("critic")
def critic_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Critic...")
    scraped_content = state.get("scraped_content", {})
    contradictions = find_contradictions(scraped_content)
    
    return {
        "contradictions": contradictions,
        "status": f"Found {len(contradictions)} contradictions.",
        "current_step": "critic"
    }

@traced_node("deep_critic")
def deep_critic_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Deep Critic...")
    scraped_content = state.get("scraped_content", {})
    contradictions = find_contradictions(scraped_content)
    
    return {
        "contradictions": contradictions,
        "status": f"Deep critic evaluated {len(contradictions)} contradictions.",
        "current_step": "deep_critic"
    }

@traced_node("retriever")
def retriever_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Retriever...")
    store = VectorStore()
    sub_questions = state.get("sub_questions", [])
    
    all_chunks = []
    for sq in sub_questions:
        results = store.query_for_report(sq, n_results=5)
        all_chunks.extend(results)
        
    seen = set()
    unique_chunks = []
    for chunk in all_chunks:
        content = chunk.get("content", chunk.get("text", ""))
        url = chunk.get("url", "")
        
        dedupe_key = f"{url}::{content}"
        if dedupe_key not in seen:
            seen.add(dedupe_key)
            unique_chunks.append(chunk)
            
    top_25 = unique_chunks[:25]
    
    return {
        "retrieved_chunks": top_25,
        "status": f"Retrieved {len(top_25)} chunks from VectorStore.",
        "current_step": "retriever"
    }

@traced_node("writer")
def writer_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Writer...")
    topic = state["topic"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    contradictions = state.get("contradictions", [])
    sub_questions = state.get("sub_questions", [])
    
    final_report = write_report(topic, retrieved_chunks, contradictions, sub_questions)
    
    return {
        "final_report": final_report,
        "status": "Report complete.",
        "current_step": "writer"
    }

@traced_node("rewrite")
def rewrite_node(state: ResearchState) -> Dict[str, Any]:
    print("Executing Rewrite...")
    topic = state["topic"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    contradictions = state.get("contradictions", [])
    sub_questions = state.get("sub_questions", [])
    
    enhanced_topic = f"{topic}\n\nIMPORTANT INSTRUCTION: The previous draft was too short. Expand each section with more detail and evidence."
    final_report = write_report(enhanced_topic, retrieved_chunks, contradictions, sub_questions)
    
    return {
        "final_report": final_report,
        "rewrite_count": state.get("rewrite_count", 0) + 1,
        "status": "Rewrite complete.",
        "current_step": "rewrite"
    }

# Conditional Edges Logic
def should_expand_search(state: ResearchState) -> str:
    n_results = len(state.get("search_results", []))
    complexity = state.get("complexity_score", 5)
    threshold = max(8, complexity * 2)
    if n_results < threshold and not state.get("search_expanded", False):
        return "expand_search"
    return "reader"

def route_after_critic(state: ResearchState) -> str:
    n_contradictions = len(state.get("contradictions", []))
    if n_contradictions > 5:
        return "deep_critic"
    return "retriever"

def quality_gate(state: ResearchState) -> str:
    report = state.get("final_report", "")
    rewrite_count = state.get("rewrite_count", 0)
    if (len(report) < 1500 or "References" not in report) and rewrite_count < 1:
        return "rewrite"
    return END

# Build the graph
workflow = StateGraph(ResearchState)

workflow.add_node("planner", planner_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("expand_search", expand_searcher_node)
workflow.add_node("reader", reader_node)
workflow.add_node("critic", critic_node)
workflow.add_node("deep_critic", deep_critic_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("writer", writer_node)
workflow.add_node("rewrite", rewrite_node)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "searcher")

workflow.add_conditional_edges(
    "searcher",
    should_expand_search,
    {
        "expand_search": "expand_search",
        "reader": "reader"
    }
)
workflow.add_edge("expand_search", "reader")
workflow.add_edge("reader", "critic")

workflow.add_conditional_edges(
    "critic",
    route_after_critic,
    {
        "deep_critic": "deep_critic",
        "retriever": "retriever"
    }
)
workflow.add_edge("deep_critic", "retriever")
workflow.add_edge("retriever", "writer")

workflow.add_conditional_edges(
    "writer",
    quality_gate,
    {
        "rewrite": "rewrite",
        END: END
    }
)
workflow.add_edge("rewrite", END)

app = workflow.compile()

def run_research(topic: str) -> ResearchState:
    initial_state = {
        "topic": topic,
        "sub_questions": [],
        "search_results": [],
        "scraped_content": {},
        "contradictions": [],
        "retrieved_chunks": [],
        "final_report": "",
        "status": "Starting research process...",
        "current_step": "START",
        "complexity_score": 5,
        "search_expanded": False,
        "rewrite_count": 0
    }
    
    final_state = app.invoke(initial_state)
    return final_state

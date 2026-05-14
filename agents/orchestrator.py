import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

# Import the main research graph
from graph.research_graph import run_research

# --- Pydantic Models for Parsing ---

class SubTopicsList(BaseModel):
    sub_topics: list[str] = Field(description="3 to 5 focused, non-overlapping sub-topics.")

class KnowledgeGraph(BaseModel):
    entities: list[Dict[str, str]] = Field(description="List of dicts with 'name' and 'type'.")
    relationships: list[Dict[str, str]] = Field(description="List of dicts with 'from', 'to', and 'label'.")

# --- Core Functions ---

def decompose_goal(goal: str) -> List[str]:
    """Uses Gemini Flash to break goal into 3-5 focused, non-overlapping sub-topics."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
    parser = JsonOutputParser(pydantic_object=SubTopicsList)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert research director. Break the high-level goal into 3 to 5 focused, non-overlapping sub-topics for deep investigation.\n\n{format_instructions}"),
        ("user", "High-Level Goal: {goal}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser
    try:
        res = chain.invoke({"goal": goal})
        return res.get("sub_topics", [])
    except Exception as e:
        print(f"Error decomposing goal: {e}")
        # Fallback to single goal
        return [goal]

def _run_single_research(sub_topic: str) -> tuple:
    """Helper to run the synchronous research graph and return (topic, state)."""
    try:
        state = run_research(sub_topic)
        return sub_topic, state
    except Exception as e:
        print(f"Error researching {sub_topic}: {e}")
        return sub_topic, {"final_report": f"Error generating report for {sub_topic}: {e}", "status": "Failed"}

async def run_parallel_research(sub_topics: List[str]) -> Dict[str, Any]:
    """Uses ThreadPoolExecutor to run research graphs in parallel."""
    loop = asyncio.get_running_loop()
    individual_reports = {}
    
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            loop.run_in_executor(pool, _run_single_research, topic)
            for topic in sub_topics
        ]
        results = await asyncio.gather(*futures)
        
        for topic, state in results:
            individual_reports[topic] = state
            
    return individual_reports

def synthesize_reports(goal: str, individual_reports: Dict[str, Any]) -> str:
    """Uses Gemini 2.5 Pro with ALL reports in context to write a master synthesis."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3, max_output_tokens=8192)
    
    combined_context = ""
    for idx, (topic, state) in enumerate(individual_reports.items()):
        report_text = state.get("final_report", "No report generated.")
        combined_context += f"--- SUB-TOPIC {idx+1}: {topic} ---\n{report_text}\n\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Principal Intelligence Analyst. Your task is to synthesize multiple sub-reports into a cohesive MASTER REPORT.
        
Requirements:
1. Identify and expand upon common themes across all sub-topics.
2. Explicitly highlight any contradictions, differing opinions, or conflicting data found between the sub-reports.
3. Provide a unified conclusion addressing the original High-Level Goal.
4. Include a final Confidence Assessment based on the depth and agreement of the data.
5. Use highly professional, structured Markdown formatting."""),
        ("user", "High-Level Goal: {goal}\n\nSub-Reports Content:\n{context}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    master_report = chain.invoke({"goal": goal, "context": combined_context})
    return master_report

def extract_knowledge_graph(reports: Dict[str, Any]) -> Dict[str, Any]:
    """Uses Gemini to extract entities and relationships."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.1)
    parser = JsonOutputParser(pydantic_object=KnowledgeGraph)
    
    combined_context = ""
    for topic, state in reports.items():
        combined_context += state.get("final_report", "") + "\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an ontology extraction engine. Extract key entities and their relationships from the text.\n\n{format_instructions}"),
        ("user", "Text Content:\n{context}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser
    try:
        # The 1M token context of Flash can handle massive combined strings easily
        kg = chain.invoke({"context": combined_context[:50000]})  # Cap at 50k chars just in case
        return kg
    except Exception as e:
        print(f"Error extracting KG: {e}")
        return {"entities": [], "relationships": []}

async def orchestrate(goal: str) -> dict:
    """
    Master entrypoint. Runs decomposition, parallel research, synthesis, and KG extraction.
    """
    sub_topics = decompose_goal(goal)
    individual_reports = await run_parallel_research(sub_topics)
    master_report = synthesize_reports(goal, individual_reports)
    knowledge_graph = extract_knowledge_graph(individual_reports)
    
    return {
        "sub_topics": sub_topics,
        "individual_reports": individual_reports,
        "master_report": master_report,
        "knowledge_graph": knowledge_graph
    }

async def orchestrate_ui(goal: str):
    """
    Generator function that yields status updates for Streamlit st.empty() live display.
    """
    loop = asyncio.get_running_loop()
    
    yield {"status": "Decomposing high-level goal...", "type": "info"}
    sub_topics = await loop.run_in_executor(None, decompose_goal, goal)
    
    yield {
        "status": f"Goal decomposed into {len(sub_topics)} sub-topics. Launching parallel graphs...", 
        "data": sub_topics, 
        "type": "sub_topics"
    }
    
    yield {"status": "Running parallel research graphs (this may take a while)...", "type": "info"}
    individual_reports = await run_parallel_research(sub_topics)
    
    yield {"status": "Parallel research complete. Synthesizing master report...", "type": "info"}
    master_report = await loop.run_in_executor(None, synthesize_reports, goal, individual_reports)
    
    yield {"status": "Master report generated. Extracting knowledge graph...", "type": "info"}
    knowledge_graph = await loop.run_in_executor(None, extract_knowledge_graph, individual_reports)
    
    yield {
        "status": "Orchestration Complete!", 
        "type": "complete",
        "result": {
            "sub_topics": sub_topics,
            "individual_reports": individual_reports,
            "master_report": master_report,
            "knowledge_graph": knowledge_graph
        }
    }

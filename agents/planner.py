import os
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class PlannerOutput(BaseModel):
    sub_questions: list[str] = Field(description="3 to 8 focused, independently searchable sub-questions.")
    research_strategy: str = Field(description="A brief research strategy string.")
    complexity_score: int = Field(description="1-10, indicating how complex this topic is.")
    estimated_sources_needed: int = Field(description="Hint for searcher on number of sources needed.")

def plan_research(topic: str) -> Dict[str, Any]:
    """
    Takes a research topic, returns a dynamically sized list of sub-questions,
    research strategy, complexity score, and estimated sources needed using Groq.
    """
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    parser = JsonOutputParser(pydantic_object=PlannerOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert research planner. Given a research topic, dynamically generate an appropriate number of focused sub-questions, a research strategy, a complexity score, and estimated sources needed.

Instructions:
- Simple factual topics: generate exactly 3 sub-questions.
- Complex multifaceted topics: generate up to 8 sub-questions.
- Each question must be independently searchable (do not use "and" to combine questions).
- Questions should comprehensively cover: definitions, mechanisms, current state, controversies, and future outlook.

{format_instructions}"""),
        ("user", "Research topic: {topic}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser
    result = chain.invoke({"topic": topic})
    
    return result

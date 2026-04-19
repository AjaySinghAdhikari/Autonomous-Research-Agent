import os
from dotenv import load_dotenv
load_dotenv()

import json
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class PlannerOutput(BaseModel):
    sub_questions: list[str] = Field(description="Exactly 5 focused sub-questions for the research topic.")
    research_strategy: str = Field(description="A brief research strategy string.")

def plan_research(topic: str) -> Dict[str, Any]:
    """
    Takes a research topic, returns a JSON list of exactly 5 focused sub-questions 
    and a brief research strategy string using Groq (Llama 3.3).
    """
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.2)
    parser = JsonOutputParser(pydantic_object=PlannerOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert research planner. Given a research topic, generate exactly 5 focused sub-questions and a brief research strategy.\n{format_instructions}"),
        ("user", "Research topic: {topic}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    # Correct chain using pipe operator
    chain = prompt | llm | parser
    result = chain.invoke({"topic": topic})
    
    return result

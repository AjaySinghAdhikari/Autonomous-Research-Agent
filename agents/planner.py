"""Planner agent — decomposes a research topic into focused sub-questions."""

import os
from dotenv import load_dotenv

load_dotenv()

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
    Takes a research topic and returns exactly 5 focused sub-questions
    plus a brief research strategy using Groq (Llama 3.3 70B).
    """
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.2)
    parser = JsonOutputParser(pydantic_object=PlannerOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert research planner. Given a research topic, generate exactly 5 focused sub-questions and a brief research strategy.\n{format_instructions}"),
        ("user", "Research topic: {topic}")
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    return chain.invoke({"topic": topic})

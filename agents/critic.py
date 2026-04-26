"""Critic agent — identifies contradictions between research sources."""

import os
from dotenv import load_dotenv

load_dotenv()

from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class Contradiction(BaseModel):
    claim_a: str = Field(description="The first conflicting claim")
    source_a: str = Field(description="Source URL for the first claim")
    claim_b: str = Field(description="The second conflicting claim")
    source_b: str = Field(description="Source URL for the second claim")
    explanation: str = Field(description="Explanation of the contradiction")


class CriticOutput(BaseModel):
    contradictions: list[Contradiction] = Field(default_factory=list)


def find_contradictions(findings: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Analyses all scraped findings and returns a list of contradictions
    found across sources using Groq (Llama 3.3 70B).
    """
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
    parser = JsonOutputParser(pydantic_object=CriticOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert fact-checker and research critic. Analyze the findings and identify explicit contradictions.\n{format_instructions}"),
        ("user", "Here are the findings:\n\n{findings_text}")
    ]).partial(format_instructions=parser.get_format_instructions())

    findings_text = "".join(
        f"Source URL: {url}\nContent: {content[:10000]}\n\n"
        for url, content in findings.items()
    )

    chain = prompt | llm | parser

    try:
        result = chain.invoke({"findings_text": findings_text})
        return result.get("contradictions", [])
    except Exception as e:
        print(f"Error in critic agent: {e}")
        return []

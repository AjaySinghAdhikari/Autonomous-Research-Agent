import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def write_report(topic: str, findings: Dict[str, str], contradictions: List[Dict[str, Any]]) -> str:
    """
    Writes a structured markdown research report using Groq Llama 3.3 70B.
    """
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical writer. Create a structured markdown research report based on the provided topic, findings, and contradictions. 
The report MUST include the following exact sections:
1. TL;DR
2. Key Findings (use inline citations referencing the sources, e.g., [1], [2])
3. Contradictions Found (discuss any conflicting information)
4. Confidence Assessment (assess the overall reliability of the findings)
5. References (a table mapping citation numbers to source URLs)"""),
        ("user", "Research Topic: {topic}\n\nFindings:\n{findings}\n\nContradictions:\n{contradictions}")
    ])
    
    findings_text = ""
    for idx, (url, content) in enumerate(findings.items()):
        findings_text += f"[{idx+1}] Source URL: {url}\nContent Extract: {content[:3000]}...\n\n"
        
    contradictions_text = ""
    for c in contradictions:
        contradictions_text += f"- Claim A: {c.get('claim_a')} (Source: {c.get('source_a')})\n  vs\n  Claim B: {c.get('claim_b')} (Source: {c.get('source_b')})\n  Explanation: {c.get('explanation')}\n\n"
        
    if not contradictions:
        contradictions_text = "No major contradictions found across sources."
        
    # Correct chain using pipe operator
    chain = prompt | llm | StrOutputParser()
    report = chain.invoke({
        "topic": topic,
        "findings": findings_text,
        "contradictions": contradictions_text
    })
    
    return report

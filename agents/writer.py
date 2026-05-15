import os
import re
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field

class ReportOutline(BaseModel):
    sections: list[str] = Field(description="List of exact section headers for the report (e.g., TL;DR, Key Findings, etc).")
    angle: str = Field(description="The primary analytical angle or narrative thrust.")
    key_claim: str = Field(description="The single most important takeaway.")

def _post_process_report(report: str, num_sources: int) -> str:
    """
    Ensures citations are resolvable, replaces bad citations, and adds metadata headers.
    """
    # 1. Ensure all [N] citations are resolvable
    def citation_replacer(match):
        citation_num = int(match.group(1))
        # 2. Replace any [N] where N > len(sources) with [see references]
        if citation_num > num_sources or citation_num < 1:
            return "[see references]"
        return match.group(0)
    
    processed_report = re.sub(r'\[(\d+)\]', citation_replacer, report)
    
    # 3. Add a word count and confidence score to the report header
    word_count = len(processed_report.split())
    
    # Heuristic confidence score (example based on sources density and length)
    confidence_score = min(98, max(45, 60 + (num_sources * 3) + (word_count // 150)))
    
    header = (
        "| Report Metadata |\n"
        "|-----------------|\n"
        f"| **Word Count**  | {word_count} words |\n"
        f"| **Confidence**  | {confidence_score}% |\n"
        f"| **Sources**     | {num_sources} indexed |\n\n"
        "---\n\n"
    )
    
    return header + processed_report

def write_report(
    topic: str, 
    retrieved_chunks: List[Dict[str, Any]], 
    contradictions: List[Dict[str, Any]], 
    sub_questions: Optional[List[str]] = None
) -> str:
    """
    Writes a structured markdown research report using Gemini 2.5 Pro via a two-pass RAG generation.
    """
    if sub_questions is None:
        sub_questions = []
        
    llm_fast = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    llm_pro = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
    
    # Build context from retrieved chunks
    url_chunks = {}
    for item in retrieved_chunks:
        text = item.get("content", item.get("text", ""))
        url = item.get("url", "unknown")
        
        if not text:
            continue
            
        if url not in url_chunks:
            url_chunks[url] = []
            
        if len(url_chunks[url]) < 3:
            url_chunks[url].append(text)
            
    # Format context and count unique sources
    findings_text = ""
    idx = 1
    for url, chunks in url_chunks.items():
        chunk_text = "\n...\n".join(chunks)
        formatted_entry = f"[{idx}] ({url})\n{chunk_text}\n\n"
        
        if len(findings_text) + len(formatted_entry) > 30000: # Groq context limit adjustment
            break
            
        findings_text += formatted_entry
        idx += 1
        
    num_sources = idx - 1
        
    # Format contradictions
    contradictions_text = ""
    for c in contradictions:
        contradictions_text += f"- Claim A: {c.get('claim_a')} (Source: {c.get('source_a')})\n  vs\n  Claim B: {c.get('claim_b')} (Source: {c.get('source_b')})\n  Explanation: {c.get('explanation')}\n\n"
        
    if not contradictions:
        contradictions_text = "No major contradictions found across sources."
        
    # PASS 1: Outline (fast, using gemini-2.0-flash)
    parser = JsonOutputParser(pydantic_object=ReportOutline)
    outline_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a master strategist. Generate a highly structured research report outline based on the topic, retrieved chunks, and sub-questions. Focus on analytical angle and structure.\n\n{format_instructions}"),
        ("user", "Topic: {topic}\nSub-Questions: {sub_questions}\n\nFindings context:\n{findings}\n\nContradictions:\n{contradictions}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    outline_chain = outline_prompt | llm_fast | parser
    try:
        # Cap findings text size for the outline pass to save time/tokens
        outline_dict = outline_chain.invoke({
            "topic": topic,
            "sub_questions": ", ".join(sub_questions),
            "findings": findings_text[:10000], 
            "contradictions": contradictions_text
        })
    except Exception as e:
        # Graceful fallback
        outline_dict = {
            "sections": ["TL;DR", "Key Findings", "Contradictions Found", "Confidence Assessment", "References"],
            "angle": "Comprehensive objective overview.",
            "key_claim": "The research spans multiple perspectives requiring deep synthesis."
        }
        
    # PASS 2: Full report (gemini-2.5-pro, using outline as guide)
    report_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite technical writer and intelligence analyst. Write the full comprehensive research report.
        
CRITICAL INSTRUCTION: Write the full report following this outline and analytical angle:
{outline}

Requirements:
1. Ensure the narrative flows logically through all provided sections.
2. Weave the 'key_claim' into the narrative core.
3. Use strict inline citations referencing the retrieved source indices, e.g., [1], [2].
4. Discuss the provided contradictions openly and transparently.
5. End with a References table mapping citation numbers to their URLs."""),
        ("user", "Research Topic: {topic}\n\nRetrieved Context:\n{findings}\n\nContradictions:\n{contradictions}")
    ])
    
    report_chain = report_prompt | llm_pro | StrOutputParser()
    raw_report = report_chain.invoke({
        "outline": str(outline_dict),
        "topic": topic,
        "findings": findings_text[:20000], 
        "contradictions": contradictions_text
    })
    
    # Post-processing
    final_report = _post_process_report(raw_report, num_sources)
    
    return final_report

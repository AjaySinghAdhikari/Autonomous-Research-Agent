import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any
from tools.scraper_tool import scrape_url
from memory.vector_store import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

def read_and_store(urls: List[str]) -> Dict[str, str]:
    """
    Takes a list of URLs, scrapes each with trafilatura, chunks the content, 
    stores in ChromaDB, returns cleaned text per source.
    """
    vector_store = VectorStore()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    scraped_data = {}
    
    for url in urls:
        text = scrape_url(url)
        if text:
            cleaned_text = " ".join(text.split())
            scraped_data[url] = cleaned_text
            
            chunks = text_splitter.split_text(cleaned_text)
            
            metadatas = [{"url": url, "chunk_index": i} for i in range(len(chunks))]
            vector_store.add_findings(documents=chunks, metadatas=metadatas)
            
    return scraped_data

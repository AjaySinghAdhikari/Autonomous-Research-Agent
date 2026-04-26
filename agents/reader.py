"""Reader agent — scrapes URLs, chunks content, and stores it in ChromaDB."""

import os
from dotenv import load_dotenv

load_dotenv()

from typing import List, Dict
from tools.scraper_tool import scrape_url
from memory.vector_store import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter


def read_and_store(urls: List[str]) -> Dict[str, str]:
    """
    Scrapes each URL with trafilatura, splits content into chunks,
    stores them in ChromaDB, and returns the cleaned text keyed by URL.
    """
    vector_store = VectorStore()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    scraped_data: Dict[str, str] = {}

    for url in urls:
        text = scrape_url(url)
        if text:
            cleaned_text = " ".join(text.split())
            scraped_data[url] = cleaned_text

            chunks = text_splitter.split_text(cleaned_text)
            metadatas = [{"url": url, "chunk_index": i} for i in range(len(chunks))]
            vector_store.add_findings(documents=chunks, metadatas=metadatas)

    return scraped_data

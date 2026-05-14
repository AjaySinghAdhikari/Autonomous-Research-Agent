import os
import uuid
import chromadb
from typing import List, Dict, Any, Optional
import google.generativeai as genai

# Configure GenAI
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))

def embed(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=texts,
        task_type=task_type
    )
    return result["embedding"]

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and get/create collection."""
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="research_findings")
        
    def add_findings(self, documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None):
        """Add findings (documents) to the vector store."""
        if not documents:
            return
            
        if ids is None:
            # Generate unique IDs for each document if not provided
            ids = [str(uuid.uuid4()) for _ in documents]
            
        try:
            # Generate embeddings
            embeddings = embed(documents, task_type="RETRIEVAL_DOCUMENT")
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Error adding to ChromaDB: {e}")
            
    def query_similar_content(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """Query for similar content to avoid duplicates."""
        try:
            query_embedding = embed([query], task_type="RETRIEVAL_QUERY")
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}

    def deduplicate_by_url(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Keep the highest-scoring chunk per URL."""
        if not results or not results.get("documents") or not results["documents"][0]:
            return []
            
        seen_urls = set()
        unique_results = []
        
        # ChromaDB query results are lists of lists
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else []
        
        # Results are inherently sorted by score/distance from Chroma
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            url = meta.get("url", "")
            
            # If no URL exists, we might still want to include it, 
            # but we use its content as the unique key to avoid pure duplication.
            dedupe_key = url if url else doc[:100]
            
            if dedupe_key not in seen_urls:
                seen_urls.add(dedupe_key)
                unique_results.append({
                    "content": doc,
                    "url": url,
                    "metadata": meta
                })
                
        return unique_results

    def query_for_report(self, topic: str, n_results: int = 15) -> List[Dict[str, Any]]:
        """
        Embeds the query with task_type="RETRIEVAL_QUERY", queries ChromaDB,
        and returns the top-n chunks with their source URLs, deduplicated by URL.
        """
        try:
            query_embedding = embed([topic], task_type="RETRIEVAL_QUERY")
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            deduped = self.deduplicate_by_url(results)
            return deduped
            
        except Exception as e:
            print(f"Error querying for report: {e}")
            return []

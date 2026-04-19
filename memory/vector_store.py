import uuid
import chromadb
from typing import List, Dict, Any, Optional

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
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Error adding to ChromaDB: {e}")
        
    def query_similar_content(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """Query for similar content to avoid duplicates."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}

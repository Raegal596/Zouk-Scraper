import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List
import google.generativeai as genai

# Initialize ChromaDB
# For simplicity, using persistent client in a local folder
CHROMA_DATA_PATH = "chroma_db"

class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
        
        # Retrieve or create collection
        # We can use Google's embedding model or a default one. 
        # For simplicity and speed, let's use the default all-MiniLM-L6-v2 which Chroma provides by default if no ef is specified.
        # But for better performance with Gemini, we might want to use Gemini embeddings.
        # For now, default sentence-transformers is fine and easier to set up without extra API calls for embeddings.
        self.collection = self.client.get_or_create_collection(name="zouk_transcripts")

    def add_documents(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        if not documents:
            return
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        # results['documents'] is a list of lists (one list per query)
        if results and results['documents']:
            return results['documents'][0]
        return []

    def clear_collection(self):
        self.client.delete_collection("zouk_transcripts")
        self.collection = self.client.get_or_create_collection(name="zouk_transcripts")

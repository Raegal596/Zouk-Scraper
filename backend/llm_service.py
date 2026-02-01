from google import genai
import os
from typing import List

class LLMService:
    def __init__(self):
        # Gemeni 3 Flash Preview
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-3-flash-preview" 

    def generate_response(self, query: str, context: List[str], uploaded_documents: List[str] = [], history: List[dict] = []) -> str:
        # Construct context string
        context_str = "\n\n".join(context)
        uploaded_docs_str = "\n\n".join(uploaded_documents)
        
        prompt = f"""You are a helpful Zouk assistant. Use the following context and uploaded documents to answer the user's question. 
If the answer is not in the context, say you don't know but try to be helpful based on general knowledge if applicable, 
but clarify what is from context and what is general.

Context from RAG:
{context_str}

Uploaded Documents:
{uploaded_docs_str}

User Question: {query}
"""
        try:
            # Simple chat generation
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
             return f"Error generating response: {str(e)}"


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from typing import List

class LLMService:
    def __init__(self):
        # Env variable GEMINI_API_KEY is automatically used by ChatGoogleGenerativeAI 
        # as long as it's set in os.environ (loaded by main.py)
        
        # Using Gemini 3 Flash Preview as requested
        # Note: langchain-google-genai uses 'model' parameter
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=os.getenv("GEMINI_API_KEY") 
        )

        template = """You are a helpful Zouk assistant. Use the following context to answer the user's question. 
If the answer is not in the context, say you don't know but try to be helpful based on general knowledge if applicable, 
but clarify what is from context and what is general.

Context:
{context}

User Question: {question}
"""
        self.prompt = PromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_response(self, query: str, context: List[str], history: List[dict] = []) -> str:
        # Construct context string
        context_str = "\n\n".join(context)
        
        # We invoke the chain
        try:
            response = self.chain.invoke({
                "context": context_str,
                "question": query
            })
            return response
        except Exception as e:
             return f"Error generating response: {str(e)}"

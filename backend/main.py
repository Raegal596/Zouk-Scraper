from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import shutil
from typing import List
from .models import ChatRequest, ChatResponse, UploadResponse
from .rag_service import RAGService
from .llm_service import LLMService
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

load_dotenv()

# Resolve paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Initialize Services
rag_service = RAGService()
llm_service = LLMService()

# Global state for uploaded documents (temporary)
uploaded_documents_content = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: could run ingestion here or separately
    print("Startup: services initialized.")
    yield
    # Shutdown
    print("Shutdown")

app = FastAPI(title="Zouk RAG Chatbot", lifespan=lifespan)

# CORS Middleware to allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Retrieve relevant info
    context_docs = rag_service.query(request.message)
    
    # 2. Generate response with uploaded documents in context
    response_text = llm_service.generate_response(request.message, context_docs, uploaded_documents_content, request.history)
    
    return ChatResponse(response=response_text, sources=context_docs)

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    allowed_extensions = {'.txt', '.pdf', '.docx'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")

    try:
        # Save file to bric_transcripts
        TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "..", "bric_transcripts")
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        
        file_location = os.path.join(TRANSCRIPTS_DIR, file.filename)
        
        # Save uploaded file
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        extracted_text = ""

        if file_ext == '.txt':
            with open(file_location, 'r', encoding='utf-8') as f:
                extracted_text = f.read()

        elif file_ext == '.pdf':
            loader = PyPDFLoader(file_location)
            pages = loader.load()
            extracted_text = "\n".join([page.page_content for page in pages])

        elif file_ext == '.docx':
            loader = Docx2txtLoader(file_location)
            docs = loader.load()
            extracted_text = "\n".join([d.page_content for d in docs])
        
        # Add to context
        if extracted_text:
            uploaded_documents_content.append(f"Document: {file.filename}\n{extracted_text}")

        return UploadResponse(filename=file.filename, status="Uploaded and added to context.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

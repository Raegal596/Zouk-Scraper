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

load_dotenv()

# Resolve paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Initialize Services
rag_service = RAGService()
llm_service = LLMService()

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
    
    # 2. Generate response
    response_text = llm_service.generate_response(request.message, context_docs, request.history)
    
    return ChatResponse(response=response_text, sources=context_docs)

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported currently.")

    try:
        # Save file to bric_transcripts
        TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "..", "bric_transcripts")
        file_location = os.path.join(TRANSCRIPTS_DIR, file.filename)
        
        # Ensure directory exists
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        # Trigger ingestion for this file (basic implementation)
        # In a real app, we'd process just this file.
        # Here we re-run ingestion or add specifically.
        # For simplicity in this script, let's just acknowledge upload. 
        # Ideally we call rag_service.add_documents with this file's content.
        
        return UploadResponse(filename=file.filename, status="Uploaded successfully. Please restart/re-ingest to index (for now).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
import glob
from rag_service import RAGService

# Get absolute path to the directory containing this script (backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Transcripts are in ../bric_transcripts relative to backend/
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "..", "bric_transcripts") 

def ingest_transcripts():
    print("Starting ingestion...")
    rag_service = RAGService()
    
    # Find all txt files
    file_pattern = os.path.join(TRANSCRIPT_DIR, "*.txt")
    files = glob.glob(file_pattern)
    
    if not files:
        print(f"No files found in {TRANSCRIPT_DIR}")
        return

    documents = []
    metadatas = []
    ids = []

    for file_path in files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple chunking: split by paragraphs or just take snippets if files are small.
            # Given these are transcripts, they might be continuous.
            # Let's chunk by 1000 characters for now with overlap.
            chunk_size = 1000
            overlap = 200
            
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                chunk_id = f"{filename}_{i}"
                
                documents.append(chunk)
                metadatas.append({"source": filename, "chunk_index": i})
                ids.append(chunk_id)
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Add to Chroma
    if documents:
        print(f"Adding {len(documents)} chunks to Vector Store...")
        rag_service.add_documents(documents, metadatas, ids)
        print("Ingestion complete.")
    else:
        print("No content to ingest.")

if __name__ == "__main__":
    # Ensure this runs from backend dir or handle paths correctly
    # Adjusted path in variable above assumes running from backend/
    ingest_transcripts()

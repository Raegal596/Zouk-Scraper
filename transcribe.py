import os
import io
import time
import assemblyai as aai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
TRANSCRIPT_DIR = "bric_transcripts"

# Configure AssemblyAI
aai.settings.api_key = API_KEY

def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def resolve_folder_id(service, folder_identifier):
    # Try to find a folder by name
    query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_identifier}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    if files:
        print(f"Found folder '{folder_identifier}' with ID: {files[0]['id']}")
        return files[0]['id']
    
    # If not found by name, assume it is an ID
    return folder_identifier

def list_files_in_folder(service, folder_id):
    # Resolve the ID first
    actual_folder_id = resolve_folder_id(service, folder_id)
    
    results = service.files().list(
        q=f"'{actual_folder_id}' in parents and mimeType contains 'video/' and trashed = false",
        pageSize=100,
        fields="nextPageToken, files(id, name)").execute()
    return results.get('files', [])

def download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    print(f"Downloading {file_name}...")
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    return fh

def transcribe_audio(audio_file):
    transcriber = aai.Transcriber()
    # AssemblyAI accepts a file object (binary)
    transcript = transcriber.transcribe(audio_file)
    return transcript

def save_transcript(file_name, transcript_text):
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(TRANSCRIPT_DIR, f"{base_name}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)
    print(f"Saved transcript to {output_path}")

def main():
    if not FOLDER_ID:
        print("Error: GOOGLE_DRIVE_FOLDER_ID not set in .env")
        return
    
    if not os.path.exists('credentials.json') and not os.path.exists('token.json'):
         print("Error: credentials.json not found. Please place it in the project root.")
         return

    if not os.path.exists(TRANSCRIPT_DIR):
        os.makedirs(TRANSCRIPT_DIR)

    print("Authenticating with Google Drive...")
    service = authenticate_google_drive()

    print(f"Listing files in folder {FOLDER_ID}...")
    files = list_files_in_folder(service, FOLDER_ID)
    
    if not files:
        print("No video files found.")
        return

    print(f"Found {len(files)} files.")

    for file in files:
        file_id = file['id']
        file_name = file['name']
        
        # Check if transcript already exists to skip
        base_name = os.path.splitext(file_name)[0]
        if os.path.exists(os.path.join(TRANSCRIPT_DIR, f"{base_name}.txt")):
             print(f"Skipping {file_name}, transcript already exists.")
             continue

        print(f"Processing {file_name}...")
        
        # Download to memory (Buffer)
        # Note: For very large files, we might want to save to temp disk, but start with memory for simplicity
        try:
            file_buffer = download_file(service, file_id, file_name)
            file_buffer.seek(0) # Reset buffer position
            
            print("Uploading and transcribing...")
            transcript = transcribe_audio(file_buffer)
            
            if transcript.status == aai.TranscriptStatus.error:
                 print(f"Error transcribing {file_name}: {transcript.error}")
            else:
                 save_transcript(file_name, transcript.text)
                 
        except Exception as e:
            print(f"An error occurred with {file_name}: {e}")

if __name__ == '__main__':
    main()

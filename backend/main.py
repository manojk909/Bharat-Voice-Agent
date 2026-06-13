from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import tempfile
import uuid
import logging

from storage.vultr_client import VultrStorageClient
from services.sarvam_service import SarvamAIService
from services.gemini_service import GeminiService
from services.elevenlabs_service import ElevenLabsService
from db.mongo_client import db_client
from db.schemas import UserProfileInDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bharat Voice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vultr = VultrStorageClient()
sarvam = SarvamAIService()
gemini = GeminiService()
elevenlabs = ElevenLabsService()

@app.post("/upload-asset")
async def upload_asset(file: UploadFile = File(...), file_type: str = Form(...)):
    """
    Phase 1: Secure Ingestion. 
    Uploads raw audio or images to Vultr S3 and returns the presigned URL.
    """
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    object_name = f"{file_type}s/{file_id}.{ext}"
    
    try:
        presigned_url = vultr.upload_file_obj(file.file, object_name)
        return {"url": presigned_url, "object_name": object_name}
    except Exception as e:
        logger.error(f"Failed to upload asset: {e}")
        raise HTTPException(status_code=500, detail="Storage upload failed")

@app.post("/evaluate-profile")
async def evaluate_profile(audio_url: str = Form(...), doc_url: Optional[str] = Form(None)):
    """
    Phase 2 & 3: Vernacular Processing & Event-Driven Automation.
    Processes audio and docs, extracts intents, checks eligibility, and saves to MongoDB.
    """
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_audio.close() # Dummy file logic

    # 1. Transcribe Audio (Sarvam)
    transcript = sarvam.transcribe_audio(temp_audio.name)

    # 2. Extract Document Text if provided (Gemini Vision)
    doc_text = ""
    if doc_url:
        doc_text = gemini.extract_document_info(b"dummy image bytes")

    # 3. Extract Intent & Build Profile (Gemini)
    combined_context = f"Transcript: {transcript}\nDocument Data: {doc_text}"
    extracted_data = gemini.extract_intent(combined_context)
    
    # Generate Embedding for Vector Search later
    embedding = gemini.generate_embedding(combined_context)

    # Business Logic for Eligibility
    eligible_schemes = []
    status = "verified"
    if extracted_data.get("occupation", "").lower() == "farmer" and float(extracted_data.get("land_size_acres", 100)) < 5:
        eligible_schemes.append("PM-Kisan Samman Nidhi")
        status = "eligible" # This triggers the Atlas Trigger!

    # 4. Save to MongoDB Atlas
    profile_dict = {
        "name": extracted_data.get("name"),
        "occupation": extracted_data.get("occupation"),
        "land_size_acres": extracted_data.get("land_size_acres"),
        "location": extracted_data.get("location"),
        "raw_audio_url": audio_url,
        "document_urls": [doc_url] if doc_url else [],
        "status": status,
        "eligible_schemes": eligible_schemes,
        "embedding": embedding
    }
    
    result = db_client.profiles.insert_one(profile_dict)
    
    # 5. Provide audio feedback
    audio_response_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    elevenlabs.generate_speech(f"Thank you. Your profile is being evaluated. Current status: {status}.", audio_response_path)
    
    return {
        "profile_id": str(result.inserted_id),
        "status": status,
        "extracted_data": extracted_data,
        "eligible_schemes": eligible_schemes,
        "audio_response_path": audio_response_path 
    }

@app.post("/handle-hitl-approval")
async def handle_hitl_approval(profile_id: str = Form(...), approved: bool = Form(...)):
    """
    Phase 4: Action Orchestration & HITL.
    n8n will hit this endpoint if HITL is required, or frontend will hit it directly
    after an n8n ping.
    """
    new_status = "submitted" if approved else "rejected"
    db_client.profiles.update_one({"_id": profile_id}, {"$set": {"status": new_status}})
    
    audio_response_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    msg = "Your application has been submitted successfully." if approved else "Your application needs revision."
    elevenlabs.generate_speech(msg, audio_response_path)
    
    return {"message": "HITL recorded.", "status": new_status}

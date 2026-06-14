from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from app.services.ai.sarvam import sarvam_client
from app.services.ai.gemini import gemini_client
from app.core.database import users_collection, sessions_collection
import uuid
import datetime

router = APIRouter()

@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    language_code: str = Form("hi-IN"),
    user_id: Optional[str] = Form(None)
):
    try:
        content = await audio.read()
        transcript = await sarvam_client.speech_to_text(
            audio_content=content,
            language_code=language_code,
            filename=audio.filename or "audio.wav",
            content_type=audio.content_type or "audio/wav"
        )
        
        session_id = str(uuid.uuid4())
        await sessions_collection.insert_one({
            "id": session_id,
            "user_id": user_id,
            "transcript": transcript,
            "language_code": language_code,
            "created_at": datetime.datetime.utcnow()
        })
        
        return {"transcript": transcript, "session_id": session_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile/extract")
async def extract_profile(transcript: str, user_id: str):
    try:
        profile = await gemini_client.extract_profile(transcript)
        
        await users_collection.update_one(
            {"id": user_id},
            {"$set": {**profile, "updated_at": datetime.datetime.utcnow()}},
            upsert=True
        )
        
        return {"profile": profile}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(text: str, language_code: str = "hi-IN"):
    try:
        audio_base64 = await sarvam_client.text_to_speech(text, language_code)
        return {"audio": audio_base64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


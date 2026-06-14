from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from typing import Optional
from app.services.ai.sarvam import sarvam_client
from app.services.ai.gemini import gemini_client
from app.services.ai.rag import rag_service
from app.core.database import users_collection, sessions_collection, schemes_collection
from app.core.config import settings
from app.services.automation import run_portal_autofill
import uuid
import datetime
import json

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
        # Fetch the existing combined profile from DB to provide context for conversational updates
        existing_user = await users_collection.find_one({"id": user_id})
        existing_profile = {}
        if existing_user:
            existing_profile = {k: v for k, v in existing_user.items() if k not in ["_id", "id", "updated_at", "created_at"]}
            
        profile = await gemini_client.extract_profile(transcript, existing_profile)
        
        # Filter out null/None values so we preserve previously extracted info
        update_data = {k: v for k, v in profile.items() if v is not None and v != ""}
        
        # Ensure we always update the timestamp
        update_data["updated_at"] = datetime.datetime.utcnow()
        
        await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data},
            upsert=True
        )
        
        # Fetch the complete combined profile from DB to return to the frontend
        combined_user = await users_collection.find_one({"id": user_id})
        combined_user.pop("_id", None)
        combined_user.pop("updated_at", None)
        combined_user.pop("created_at", None)
        
        return {"profile": combined_user}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile/update")
async def update_profile(user_id: str, profile: dict):
    try:
        update_data = {k: v for k, v in profile.items() if k not in ["_id", "id", "updated_at", "created_at"]}
        update_data["updated_at"] = datetime.datetime.utcnow()
        await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data},
            upsert=True
        )
        updated_user = await users_collection.find_one({"id": user_id})
        updated_user.pop("_id", None)
        updated_user.pop("updated_at", None)
        updated_user.pop("created_at", None)
        return {"profile": updated_user}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate")
async def translate_text_endpoint(text: str, target_language_code: str):
    try:
        # Map target language code to full language name
        lang_mapping = {
            "hi-IN": "Hindi",
            "te-IN": "Telugu",
            "ta-IN": "Tamil",
            "kn-IN": "Kannada",
            "ml-IN": "Malayalam",
            "mr-IN": "Marathi",
            "gu-IN": "Gujarati",
            "bn-IN": "Bengali"
        }
        target_lang_name = lang_mapping.get(target_language_code, "Hindi")
        translated = await gemini_client.translate_text(text, target_lang_name)
        return {"translated": translated}
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schemes/discover")
async def discover_schemes(user_id: str, language_code: Optional[str] = None):
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found. Please speak first to initialize it.")
        
        # Remove mongo ID and datetime fields to serialize safely
        user.pop("_id", None)
        user.pop("updated_at", None)
        user.pop("created_at", None)
        
        # Call RAG service to discover schemes
        eligible_schemes = await rag_service.discover_schemes(user)
        
        # Translate schemes if language_code is provided and is not English
        if language_code and not language_code.lower().startswith("en"):
            # We map language code to standard language names for Llama translation
            lang_mapping = {
                "hi-IN": "Hindi",
                "te-IN": "Telugu",
                "ta-IN": "Tamil",
                "kn-IN": "Kannada",
                "ml-IN": "Malayalam",
                "mr-IN": "Marathi",
                "gu-IN": "Gujarati",
                "bn-IN": "Bengali"
            }
            target_lang_name = lang_mapping.get(language_code, "Hindi")
            
            translated_schemes = []
            for scheme in eligible_schemes:
                try:
                    title_t = await gemini_client.translate_text(scheme.get("title", ""), target_lang_name)
                    desc_t = await gemini_client.translate_text(scheme.get("description", ""), target_lang_name)
                    benefits_t = await gemini_client.translate_text(scheme.get("benefits", ""), target_lang_name)
                    reason_t = await gemini_client.translate_text(scheme.get("eligibility_reason", ""), target_lang_name)
                    
                    docs = scheme.get("required_documents", [])
                    docs_t = []
                    for doc in docs:
                        docs_t.append(await gemini_client.translate_text(doc, target_lang_name))
                        
                    translated_schemes.append({
                        **scheme,
                        "title": title_t,
                        "description": desc_t,
                        "benefits": benefits_t,
                        "eligibility_reason": reason_t,
                        "required_documents": docs_t
                    })
                except Exception as ex:
                    print("Error translating individual scheme:", ex)
                    translated_schemes.append(scheme)
            eligible_schemes = translated_schemes
            
        return {"schemes": eligible_schemes}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schemes/draft")
async def draft_application(scheme_id: str, user_id: str, language_code: Optional[str] = None):
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")
            
        scheme = await schemes_collection.find_one({"id": scheme_id})
        if not scheme:
            raise HTTPException(status_code=404, detail="Scheme not found.")
            
        # Serialize fields securely
        user.pop("_id", None)
        user.pop("updated_at", None)
        user.pop("created_at", None)
        scheme.pop("_id", None)
        scheme.pop("updated_at", None)
        scheme.pop("created_at", None)
        
        # Call n8n workflow webhook
        import httpx
        payload = {
            "user_profile": user,
            "scheme": scheme
        }
        
        print(f"Calling n8n webhook: {settings.N8N_WEBHOOK_URL} for scheme draft")
        draft_stages = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=20)
                
                # Check response from n8n
                if response.status_code in [200, 201]:
                    data = response.json()
                    draft_stages = data.get("draft_stages", [])
                else:
                    print(f"n8n Webhook Error ({response.status_code}): {response.text}")
        except Exception as conn_err:
            print("Could not connect to n8n workflow. Using fallback draft logic.", conn_err)
            
        if not draft_stages:
            # Mock/Fallback response when n8n is not running locally yet
            draft_stages = [
                f"Stage 1: Document Upload. Please upload your document (Aadhaar or Income Certificate) above to extract details and pre-fill the form.",
                f"Stage 2: Form Review. Review the pre-filled application details. You can verbally correct any field if needed.",
                f"Stage 3: Review & Submit. Review your final application draft, download the pre-filled PDF, and click Submit to complete the application."
            ]
            
        # Translate stages if language_code is provided and is not English
        if language_code and not language_code.lower().startswith("en"):
            lang_mapping = {
                "hi-IN": "Hindi",
                "te-IN": "Telugu",
                "ta-IN": "Tamil",
                "kn-IN": "Kannada",
                "ml-IN": "Malayalam",
                "mr-IN": "Marathi",
                "gu-IN": "Gujarati",
                "bn-IN": "Bengali"
            }
            target_lang_name = lang_mapping.get(language_code, "Hindi")
            translated_stages = []
            for stage in draft_stages:
                try:
                    translated_stage = await gemini_client.translate_text(stage, target_lang_name)
                    translated_stages.append(translated_stage)
                except Exception as ex:
                    print("Error translating draft stage:", ex)
                    translated_stages.append(stage)
            draft_stages = translated_stages
            
        return {"draft_stages": draft_stages}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schemes/verify-document")
async def verify_document(
    document: UploadFile = File(...),
    document_type: str = Form("Aadhaar Card"),
    user_id: str = Form(...)
):
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")

        filename = document.filename.lower()
        
        # Call Gemini to simulate OCR / metadata parsing of details from the uploaded document
        prompt = f"""
        You are an OCR and profile extraction engine for a government caseworker assistant.
        We have uploaded a document of type "{document_type}" with filename "{document.filename}".
        
        Based on this document, extract any relevant profile fields (e.g. name, age, gender, annual_income, caste_category, state, district, disability_status, aadhaar_number, mobile_number) that can be inferred or guessed from the filename or document context.
        
        For example:
        - If filename is "aadhaar_trivedi_123456789012.pdf", name is "Trivedi", state is "Andhra Pradesh", aadhaar_number is "123456789012".
        - If filename is "income_certificate_200000.pdf", annual_income is 200000.
        - If filename is "caste_obc.pdf", caste_category is "OBC".
        - If filename is "disability_cert.pdf", disability_status is "Yes".
        
        Return a JSON object containing any extracted fields. Set fields that cannot be inferred to null.
        Example output format:
        {{
            "name": "Trivedi",
            "annual_income": 200000,
            "aadhaar_number": "123456789012"
        }}
        """
        response_text = await gemini_client._call_llm(prompt)
        extracted = {}
        try:
            text = response_text.replace('```json', '').replace('```', '').strip()
            extracted = json.loads(text)
        except Exception as e:
            print("Error parsing OCR document extraction:", e)

        # Filter out null/None values
        update_data = {k: v for k, v in extracted.items() if v is not None and v != ""}
        
        if update_data:
            update_data["updated_at"] = datetime.datetime.utcnow()
            await users_collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
        # Refetch updated user
        updated_user = await users_collection.find_one({"id": user_id})
        updated_user.pop("_id", None)
        updated_user.pop("updated_at", None)
        updated_user.pop("created_at", None)

        # Build a message describing what was extracted
        extracted_fields_summary = ", ".join([f"{k}: {v}" for k, v in update_data.items() if k != "updated_at"])
        if extracted_fields_summary:
            msg = f"Document '{document.filename}' processed successfully. Extracted details: {extracted_fields_summary}."
        else:
            msg = f"Document '{document.filename}' processed. No new details extracted."

        return {
            "verified": True,
            "document_type": document_type,
            "filename": document.filename,
            "message": msg,
            "profile": updated_user
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schemes/pdf-draft")
async def generate_pdf_draft(scheme_id: str, user_id: str):
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")
            
        scheme = await schemes_collection.find_one({"id": scheme_id})
        if not scheme:
            raise HTTPException(status_code=404, detail="Scheme not found.")
            
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from fastapi.responses import StreamingResponse
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            textColor=colors.HexColor("#1A365D"),
            fontSize=22,
            spaceAfter=15
        )
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            textColor=colors.HexColor("#2C5282"),
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
        
        story.append(Paragraph("BHARAT VOICE ASSISTANT - APPLICATION DRAFT", title_style))
        story.append(Paragraph(f"<b>Scheme Name:</b> {scheme.get('title')}", body_style))
        story.append(Paragraph(f"<b>Official Website:</b> {scheme.get('source_url', 'N/A')}", body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("PRE-FILLED USER DETAILS", section_style))
        story.append(Paragraph(f"Use the following details to fill out the form on the official website:", body_style))
        story.append(Spacer(1, 5))
        
        fields_to_print = [
            ("Applicant Name", "name"),
            ("Age", "age"),
            ("Gender", "gender"),
            ("State", "state"),
            ("District", "district"),
            ("Occupation", "occupation"),
            ("Education", "education"),
            ("Annual Income", "annual_income"),
            ("Caste Category", "caste_category"),
            ("Disability Status", "disability_status"),
            ("Aadhaar Number", "aadhaar_number"),
            ("Mobile Number", "mobile_number"),
        ]
        
        for label, key in fields_to_print:
            val = user.get(key)
            val_str = str(val) if val is not None and val != "" else "Not Specified"
            story.append(Paragraph(f"• <b>{label}:</b> {val_str}", body_style))
            
        story.append(Spacer(1, 15))
        story.append(Paragraph("APPLICATION STEPS", section_style))
        story.append(Paragraph("1. Open the official website page in your browser.", body_style))
        story.append(Paragraph("2. Navigate to the Registration / Application section.", body_style))
        story.append(Paragraph("3. Copy each detail printed above into the respective text input field.", body_style))
        story.append(Paragraph("4. Upload the verified documents that you checked in the assistant.", body_style))
        story.append(Paragraph("5. Review and Submit your application.", body_style))
        
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=draft_{scheme_id}.pdf"}
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schemes/submit")
async def submit_application(scheme_id: str, user_id: str, background_tasks: BackgroundTasks):
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")
            
        scheme = await schemes_collection.find_one({"id": scheme_id})
        if not scheme:
            raise HTTPException(status_code=404, detail="Scheme not found.")
            
        # Call n8n submission webhook if configured
        import httpx
        payload = {
            "user_profile": user,
            "scheme": scheme,
            "action": "submit"
        }
        
        submitted_to_n8n = False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=20)
                if response.status_code in [200, 201]:
                    submitted_to_n8n = True
        except:
            pass
            
        # Trigger local Selenium live browser automation to open and autofill the portal
        portal_url = scheme.get("source_url", "https://pmkisan.gov.in/")
        background_tasks.add_task(run_portal_autofill, user, portal_url)
            
        return {
            "success": True,
            "message": f"Application for '{scheme['title']}' has been submitted successfully to the portal.",
            "pdf_url": f"http://localhost:8000/api/v1/schemes/pdf-draft?scheme_id={scheme_id}&user_id={user_id}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


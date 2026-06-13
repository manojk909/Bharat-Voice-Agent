import os
from google import genai
from google.genai import types
import logging
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = 'gemini-1.5-pro'
            self.vision_model_name = 'gemini-1.5-flash'
            self.embed_model_name = 'text-embedding-004'
        else:
            logger.warning("Gemini API key not found.")

    def extract_intent(self, text: str) -> Dict[str, Any]:
        """Extract structured profile data from text."""
        if not self.api_key:
            return {"occupation": "Farmer", "land_size_acres": 3.0, "location": "Maharashtra", "language": "mr"}

        prompt = f"""
        Extract the following information from the user's statement and return ONLY a JSON object:
        {{
            "name": "...",
            "occupation": "...",
            "land_size_acres": 0.0,
            "income": 0.0,
            "location": "...",
            "language": "..."
        }}
        User Statement: {text}
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            logger.error(f"Gemini Intent Extraction error: {e}")
            return {}

    def extract_document_info(self, image_bytes: bytes) -> str:
        """Perform OCR and data extraction on user documents."""
        if not self.api_key:
            return "Extracted Document Data: Valid Aadhar Card"
        
        try:
            response = self.client.models.generate_content(
                model=self.vision_model_name,
                contents=[
                    "Extract all relevant text and identify the document type.", 
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return "Fallback Document Info"

    def generate_embedding(self, text: str) -> list[float]:
        """Generate vector embedding for the profile data."""
        if not self.api_key:
            return [0.0] * 768
            
        try:
            result = self.client.models.embed_content(
                model=self.embed_model_name,
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Gemini Embedding error: {e}")
            return [0.0] * 768
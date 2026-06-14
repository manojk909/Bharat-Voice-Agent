import google.generativeai as genai
from app.core.config import settings
import json

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash')

class GeminiClient:
    async def extract_profile(self, transcript: str) -> dict:
        prompt = f"""
        Extract the following information from the user's transcript into a JSON object:
        name, age, gender, state, district, occupation, education, annual_income, caste_category, parent_occupation, disability_status
        If a field is not mentioned, set it to null.
        
        Transcript: "{transcript}"
        """
        response = model.generate_content(prompt)
        try:
            # Clean up the markdown JSON block
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print("Error parsing profile:", e)
            return {}

    async def generate_keywords(self, profile: dict) -> list[str]:
        prompt = f"Given this user profile, generate a list of 5-10 keywords to search for relevant government schemes: {json.dumps(profile)}"
        response = model.generate_content(prompt)
        try:
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception:
            # Fallback parsing
            return [word.strip() for word in response.text.split(',') if word.strip()]

    async def evaluate_eligibility(self, profile: dict, scheme_text: str) -> dict:
        prompt = f"""
        Evaluate if the user is eligible for the following scheme.
        User Profile: {json.dumps(profile)}
        Scheme Details: {scheme_text}
        
        Return exactly a JSON object with keys: 'eligible' (boolean), 'confidence' (0-100), and 'reason' (string).
        """
        response = model.generate_content(prompt)
        try:
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception:
            return {"eligible": False, "confidence": 0, "reason": "Failed to evaluate"}

gemini_client = GeminiClient()

import httpx
from app.core.config import settings
import json

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY  # Holds the Groq key
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Using Llama 3.1 8B hosted on Groq for high rate-limit stability
        self.model = "llama-3.1-8b-instant" 

    async def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"} if "json" in prompt.lower() else None
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, headers=self.headers, json=payload, timeout=20)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    print(f"Groq API Error ({response.status_code}): {response.text}")
                    return ""
            except Exception as e:
                print(f"Connection error to Groq: {e}")
                return ""

    async def extract_profile(self, transcript: str, existing_profile: dict = None) -> dict:
        prompt = f"""
        You are an AI caseworker assistant. The user is having a voice conversation with you to build and refine their profile.
        
        Existing Profile:
        {json.dumps(existing_profile or {})}
        
        User statement: "{transcript}"
        
        Extract the following fields in English:
        name, age, gender, state, district, occupation, education, annual_income, caste_category, parent_occupation, disability_status, document_verified, aadhaar_number, mobile_number
        
        Rules:
        1. Contextual Corrections: If the user corrects or updates any info (e.g. "actually my name is Manoj", "no I am 22, not 20", "change my state to Karnataka"), modify that field to the new value.
        2. Document Override: If the user says "the uploaded documents/details are correct", "proceed anyway", "use them as they are", "verify it", or indicates the verification should be accepted/bypassed, set "document_verified" to true. Otherwise, if it is already true in the Existing Profile, preserve it.
        3. Field Preservation: Do not set existing fields to null unless explicitly contradicted or requested. If not mentioned and not in the Existing Profile, set to null.
        4. Standardize key fields in English:
           - "occupation": Standardize as "Farmer" (if kisan/rythu/farming), "Student", "Unemployed", "Professional", etc.
           - "state": Standardize as "Andhra Pradesh", "Telangana", "Uttar Pradesh", "Karnataka", "Maharashtra", etc.
           - "caste_category": Standardize as "SC", "ST", "OBC", "General", etc.
           - "disability_status": Standardize as "Physically Handicapped", "Yes", or "No".
           - "annual_income": Standardize as a clean integer number if possible (e.g. 300000).
           - "aadhaar_number": Extract a 12-digit number if mentioned or in document OCR.
           - "mobile_number": Extract a 10-digit phone number if mentioned.
           
        Return ONLY a raw JSON object containing these keys. Do not include markdown code blocks.
        """
        response_text = await self._call_llm(prompt)
        try:
            # Clean JSON string if LLM returned markdown blocks
            text = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print("Error parsing profile:", e)
            return {}

    async def translate_text(self, text: str, target_language: str) -> str:
        if not target_language or target_language.lower().startswith("en"):
            return text
        prompt = f"""
        Translate the following text into the target language. Keep the original formatting, bullet points, numbers, and styling (like markdown bolding or stars). Do not add any conversational filler, explanations, or quotes. Just return the raw translation.
        
        Target Language Code/Name: {target_language}
        Text to translate:
        {text}
        """
        translated = await self._call_llm(prompt)
        if not translated:
            return text
        return translated.strip()

    async def generate_keywords(self, profile: dict) -> list[str]:
        prompt = f"""
        Given this user profile, generate a list of 5-10 key search terms or short phrases to search for relevant government schemes or scholarships.
        User Profile: {json.dumps(profile)}
        
        Return EXACTLY a JSON object with a single key "keywords" which holds an array of strings. Do not include markdown code blocks.
        Example format:
        {{
            "keywords": ["farmer", "telangana", "subsidy", "agriculture"]
        }}
        """
        response_text = await self._call_llm(prompt)
        try:
            text = response_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text)
            return data.get("keywords", [])
        except Exception:
            return [word.strip() for word in response_text.split(',') if word.strip()]

    async def evaluate_multiple_eligibility(self, profile: dict, schemes: list[dict]) -> list[dict]:
        # Local translation mapping to normalize profile values for Llama eligibility checking
        translation_map = {
            "महाराष्ट्र": "Maharashtra",
            "कर्नाटक": "Karnataka",
            "उत्तर प्रदेश": "Uttar Pradesh",
            "आंध्र प्रदेश": "Andhra Pradesh",
            "तेलंगाना": "Telangana",
            "फार्मर": "Farmer",
            "किसान": "Farmer",
            "कृषि": "Agriculture",
            "विद्यार्थी": "Student",
            "छात्र": "Student",
            "महिला": "Female",
            "पुरुष": "Male",
            "हाँ": "Yes",
            "ना": "No",
            "नहीं": "No"
        }
        
        translated_profile = {}
        for k, v in profile.items():
            if v is not None:
                val_str = str(v).strip()
                translated_profile[k] = translation_map.get(val_str, val_str)
            else:
                translated_profile[k] = v

        schemes_input = []
        for s in schemes:
            schemes_input.append({
                "id": s.get("id"),
                "title": s.get("title"),
                "description": s.get("description"),
                "benefits": s.get("benefits"),
                "eligibility_criteria": s.get("eligibility_criteria")
            })

        prompt = f"""
        Analyze if the user is eligible for each of the following government schemes based on their profile.
        
        User Profile:
        {json.dumps(translated_profile)}
        
        Schemes to evaluate:
        {json.dumps(schemes_input)}
        
        Rules for eligibility evaluation:
        1. If a profile field is null, None, or "Not specified", do NOT reject eligibility based on it. Assume the user is eligible for that specific field unless there is a direct contradiction.
        2. Focus heavily on positive matching fields. For example, if the user's occupation is "किसान" (Kisan) or "फार्मर", it matches "Farmer" or "Agriculture". If the user's state is "उत्तर प्रदेश" (Uttar Pradesh), it matches "Uttar Pradesh" or "UP" or "All".
        3. If the core requirements (like occupation or state or education) align with the explicitly stated profile values, mark 'eligible' as true.
        
        For each scheme, determine:
        1. Whether the user is eligible (true/false)
        2. A confidence score (0-100)
        3. A brief specific reason why they qualify or do not qualify.
        
        Return EXACTLY a JSON object with a single key "evaluations" holding an array of objects.
        Example format:
        {{
            "evaluations": [
                {{
                    "id": "scheme_id_here",
                    "eligible": true,
                    "confidence": 95,
                    "reason": "explanation here"
                }}
            ]
        }}
        
        Do not include markdown, comments, or explanations outside the JSON object.
        """
        response_text = await self._call_llm(prompt)
        print("--- RAW LLM RESPONSE FOR ELIGIBILITY ---")
        print(response_text)
        print("-----------------------------------------")
        try:
            text = response_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text)
            evals = data.get("evaluations", [])
            print(f"Parsed {len(evals)} evaluations successfully.")
            return evals
        except Exception as e:
            print("Error parsing batch eligibility:", e)
            return []

gemini_client = GeminiClient()

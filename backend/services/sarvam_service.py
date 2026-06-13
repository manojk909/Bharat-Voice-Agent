import os
import requests
import logging

logger = logging.getLogger(__name__)

class SarvamAIService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.base_url = "https://api.sarvam.ai/speech-to-text" # Adjust based on actual API
        self.headers = {
            "api-subscription-key": self.api_key,
        }

    def transcribe_audio(self, audio_file_path: str, language_code: str = "hi-IN") -> str:
        """
        Transcribe regional audio into English/regional language via Sarvam AI.
        """
        if not self.api_key:
            logger.warning("Sarvam API key not found. Using mock translation.")
            return "I am a farmer with 3 acres of land in Maharashtra."

        try:
            with open(audio_file_path, "rb") as f:
                files = {"file": f}
                data = {"language_code": language_code}
                response = requests.post(self.base_url, headers=self.headers, files=files, data=data)
                response.raise_for_status()
                return response.json().get("transcript", "")
        except Exception as e:
            logger.error(f"Sarvam AI API error: {e}")
            return "Fallback: Could not transcribe audio."

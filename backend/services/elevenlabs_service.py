import os
import requests
import logging

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"
        self.voice_id = "EXAVITQu4vr4xnSDxMaL" # General neutral voice

    def generate_speech(self, text: str, output_path: str):
        """Generate speech for the given text using ElevenLabs."""
        if not self.api_key:
            logger.warning("ElevenLabs API key missing. Skipping TTS generation.")
            with open(output_path, "wb") as f:
                f.write(b"dummy audio")
            return

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            response = requests.post(f"{self.base_url}/{self.voice_id}", json=data, headers=headers)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            logger.info(f"Audio saved to {output_path}")
        except Exception as e:
            logger.error(f"ElevenLabs API error: {e}")

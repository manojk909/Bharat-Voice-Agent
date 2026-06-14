import httpx
from app.core.config import settings

class SarvamClient:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.headers = {"API-Subscription-Key": self.api_key}

    async def speech_to_text(self, audio_content: bytes, language_code: str = "hi-IN", filename: str = "audio.wav", content_type: str = "audio/wav"):
        # We simulate this since we would typically need the exact file handling.
        # Following Sarvam API structure for STT
        url = "https://api.sarvam.ai/speech-to-text"
        files = {"file": (filename, audio_content, content_type)}
        data = {
            "language_code": language_code,
            "model": "saaras:v3",
            "mode": "transcribe"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, files=files, data=data)
            if response.status_code == 200:
                return response.json().get("transcript", "")
            print("Sarvam STT Error:", response.text)
            return ""

    async def text_to_speech(self, text: str, target_language_code: str = "hi-IN"):
        url = "https://api.sarvam.ai/text-to-speech"
        payload = {
            "inputs": [text],
            "target_language_code": target_language_code,
            "speaker": "anushka", # Default speaker
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v2"
        }
        headers = {**self.headers, "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json().get("audios", [])[0] # base64 string
            print("Sarvam TTS Error:", response.text)
            return ""

sarvam_client = SarvamClient()

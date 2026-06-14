from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SARVAM_API_KEY: str
    GEMINI_API_KEY: str
    MONGODB_URI: str
    QDRANT_PATH: str = "./qdrant_data"
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/draft-application"

    class Config:
        env_file = ".env"

settings = Settings()

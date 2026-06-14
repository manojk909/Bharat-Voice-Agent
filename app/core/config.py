from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SARVAM_API_KEY: str
    GEMINI_API_KEY: str
    MONGODB_URI: str
    QDRANT_PATH: str = "./qdrant_data"

    class Config:
        env_file = ".env"

settings = Settings()

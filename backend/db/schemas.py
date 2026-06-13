from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserProfileBase(BaseModel):
    name: Optional[str] = None
    occupation: Optional[str] = None
    land_size_acres: Optional[float] = None
    income: Optional[float] = None
    location: Optional[str] = None
    language: Optional[str] = "en"
    raw_audio_url: Optional[str] = None
    document_urls: List[str] = Field(default_factory=list)
    extracted_text: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileInDB(UserProfileBase):
    id: str = Field(alias="_id")
    status: str = Field(default="pending") # pending, verified, eligible, submitted
    eligible_schemes: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

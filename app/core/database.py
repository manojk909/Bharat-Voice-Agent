from motor.motor_asyncio import AsyncIOMotorClient
# from qdrant_client import QdrantClient
from .config import settings

# MongoDB Setup
mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
db = mongo_client.get_database("BharatDB")

# Collections
users_collection = db.get_collection("users")
sessions_collection = db.get_collection("sessions")
schemes_collection = db.get_collection("schemes")
applications_collection = db.get_collection("applications")

# Qdrant Local Setup
# qdrant_client = QdrantClient(path=settings.QDRANT_PATH)

def get_db():
    return db

def get_qdrant():
    return None # qdrant_client

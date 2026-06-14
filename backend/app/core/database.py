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

async def init_db():
    try:
        # Create text index on schemes collection for full-text search
        await schemes_collection.create_index([
            ("title", "text"),
            ("description", "text"),
            ("benefits", "text")
        ], name="schemes_text_index")
        print("MongoDB Indexes Initialized Successfully.")
    except Exception as e:
        print("Error initializing database indexes:", e)

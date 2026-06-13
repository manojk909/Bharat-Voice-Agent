import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME", "bharat_voice_agent")
        
        if not self.uri:
            raise ValueError("MONGODB_URI environment variable is required")
            
        self.client = MongoClient(self.uri)
        self.db: Database = self.client[self.db_name]
        self.profiles: Collection = self.db.user_profiles
        
        # Test connection
        try:
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas!")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            raise

    def setup_vector_search_index(self):
        """
        Blueprint for Atlas Vector Search Index.
        Note: The index should ideally be created via Atlas UI or Atlas Admin API.
        This provides the definition.
        """
        vector_index_definition = {
            "name": "profile_vector_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 768, # Assuming Google Gemini embeddings
                        "similarity": "cosine"
                    },
                    {
                        "type": "filter",
                        "path": "status"
                    }
                ]
            }
        }
        logger.info(f"Please create the following Vector Search index in Atlas UI: {vector_index_definition}")

db_client = MongoDBClient()

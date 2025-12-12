from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from config import settings


class DatabaseManager:
    """Singleton class for MongoDB connection management"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection"""
        if self._client is None:
            self._client = MongoClient(settings.MONGODB_URL)
    
    @property
    def client(self) -> MongoClient:
        """Get MongoDB client instance"""
        if self._client is None:
            self._client = MongoClient(settings.MONGODB_URL)
        return self._client
    
    @property
    def master_db(self):
        """Get master database for organization metadata"""
        return self.client[settings.MASTER_DB_NAME]
    
    def get_organization_collection(self, org_name: str):
        """Get organization-specific collection"""
        collection_name = f"org_{org_name.lower().replace(' ', '_')}"
        return self.master_db[collection_name]
    
    def create_organization_collection(self, org_name: str) -> str:
        """
        Create a new collection for an organization
        Returns the collection name
        """
        collection_name = f"org_{org_name.lower().replace(' ', '_')}"
        
        try:
            # Create collection with validation schema (optional)
            self.master_db.create_collection(
                collection_name,
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "properties": {
                            "created_at": {"bsonType": "date"},
                            "updated_at": {"bsonType": "date"}
                        }
                    }
                }
            )
        except CollectionInvalid:
            # Collection already exists
            pass
        
        return collection_name
    
    def delete_organization_collection(self, collection_name: str) -> bool:
        """Delete an organization collection"""
        try:
            self.master_db[collection_name].drop()
            return True
        except Exception:
            return False
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None


# Global database manager instance
db_manager = DatabaseManager()

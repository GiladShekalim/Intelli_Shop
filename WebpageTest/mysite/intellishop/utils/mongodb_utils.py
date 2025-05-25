from pymongo import MongoClient
from django.conf import settings
import os
import logging
import certifi

logger = logging.getLogger(__name__)

# MongoDB client connection
_mongo_client = None

def get_mongo_client():
    """Get or create MongoDB client connection"""
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = settings.MONGODB_URI
        _mongo_client = MongoClient(mongo_uri)
    return _mongo_client

def get_database():
    """Get MongoDB database"""
    client = get_mongo_client()
    db_name = settings.MONGODB_NAME
    return client[db_name]

def get_collection_handle(collection_name):
    """Get MongoDB collection by name"""
    db = get_database()
    if db is not None:
        return db[collection_name]
    return None

def get_db_handle():
    """
    Returns a handle to the MongoDB database and client
    """
    # Get MongoDB connection details from environment variables or settings
    try:
        # Try to import settings for MongoDB URI
        from django.conf import settings
        
        # Get the connection string - first from env, then from settings, then default
        mongodb_uri = os.environ.get('MONGODB_URI', getattr(settings, 'MONGODB_URI', None))
        db_name = os.environ.get('MONGODB_NAME', getattr(settings, 'MONGODB_NAME', 'intellishop_db'))
        
        # Check if mongodb_uri is still None or contains placeholders
        if mongodb_uri is None or '<' in mongodb_uri:
            logger.warning("MongoDB URI not properly configured. Using local fallback.")
            mongodb_uri = 'mongodb+srv://giladshkalim:Gilad1212@intellidb.yuauj7i.mongodb.net/IntelliDB?retryWrites=true&w=majority'
            
        # Updated client creation with SSL configuration
        client = MongoClient(
            mongodb_uri,
            ssl=True,
            ssl_ca_certs=certifi.where()
        )
        
        db_handle = client[db_name]
        
        # Test connection
        client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB: {db_name}")
        
        return db_handle, client
        
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        # Return None values to indicate connection failure
        return None, None 
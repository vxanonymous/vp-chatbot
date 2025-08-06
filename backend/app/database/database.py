from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
import logging
import ssl
import certifi
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager for the application."""
    
    def __init__(self):
        self.client: Any = None
        self.database: Any = None


db = MongoDB()


async def connect_to_mongo():
    """Establish connection to MongoDB database for vacation chatbot data."""
    try:
        # Determine connection type (Atlas cloud or local)
        if "mongodb+srv://" in settings.mongodb_url or "mongodb.net" in settings.mongodb_url:
            # Connect to MongoDB Atlas with SSL for production deployment
            db.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=20000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                retryWrites=True,
                w="majority",
                tls=True,
                tlsAllowInvalidCertificates=False,
                tlsCAFile=certifi.where()
            )
        else:
            # Connect to local MongoDB instance for development
            db.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=20000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000
            )
        
        if db.client:
            # Set up database reference for vacation chatbot collections
            db.database = db.client[settings.mongodb_db_name]
            
            # Test the connection to ensure database is accessible
            await db.client.server_info()
            logger.info("Great! Successfully connected to the MongoDB database")
            
            # Set up database indexes for optimal query performance
            await create_indexes()
        else:
            raise Exception("Failed to create MongoDB client")
        
    except ServerSelectionTimeoutError as e:
        logger.error(f"Couldn't connect to the MongoDB database: {e}")
        raise
    except Exception as e:
        logger.error(f"Something went wrong with the MongoDB connection: {e}")
        raise


async def close_mongo_connection():
    """Close the MongoDB database connection."""
    if db.client:
        db.client.close()
        logger.info("Successfully closed the MongoDB connection")


async def create_indexes():
    """Create database indexes for optimal vacation chatbot query performance."""
    try:
        if not db.database:
            logger.warning("Database isn't ready yet, so we can't create indexes")
            return
            
        # Create user collection indexes for authentication
        await db.database.users.create_index("email", unique=True)
        
        # Create conversation collection indexes for chat history
        await db.database.conversations.create_index("user_id")
        await db.database.conversations.create_index("created_at")
        await db.database.conversations.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("Successfully set up all the database indexes")
    except Exception as e:
        logger.warning(f"Had some trouble setting up the database indexes: {e}")


def get_database():
    return db.database


def is_database_available():
    """Check if database is available."""
    try:
        return db.client is not None and db.database is not None
    except Exception:
        return False
# Will utilize later

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import logging
import ssl
import certifi
from typing import Optional
from app.config import settings
import asyncio

logger = logging.getLogger(__name__)


class OptimizedMongoDB:
    """Optimized MongoDB connection with enhanced connection pooling and performance."""
    
    def __init__(self):
        self.client: "Optional[AsyncIOMotorClient]" = None
        self.database: "Optional[AsyncIOMotorDatabase]" = None
        self._connection_pool_size = 50  # Increased from default
        self._min_pool_size = 10
        self._max_idle_time_ms = 30000
        self._wait_queue_timeout_ms = 5000
        self._server_selection_timeout_ms = 10000  # Reduced from 20000
        self._connect_timeout_ms = 10000  # Reduced from 20000
        self._socket_timeout_ms = 15000  # Reduced from 20000

    async def connect(self):
        """Create optimized database connection with enhanced pooling."""
        try:
            # Enhanced connection configuration
            connection_kwargs = {
                "serverSelectionTimeoutMS": self._server_selection_timeout_ms,
                "connectTimeoutMS": self._connect_timeout_ms,
                "socketTimeoutMS": self._socket_timeout_ms,
                "maxPoolSize": self._connection_pool_size,
                "minPoolSize": self._min_pool_size,
                "maxIdleTimeMS": self._max_idle_time_ms,
                "waitQueueTimeoutMS": self._wait_queue_timeout_ms,
                "retryWrites": True,
                "retryReads": True,
                "w": "majority",
                "journal": True,
                "readPreference": "primaryPreferred",
                "readConcernLevel": "majority"
            }
            
            # Check if using MongoDB Atlas (cloud) or local
            if "mongodb+srv://" in settings.mongodb_url or "mongodb.net" in settings.mongodb_url:
                # MongoDB Atlas connection with enhanced SSL
                connection_kwargs.update({
                    "tls": True,
                    "tlsAllowInvalidCertificates": False,
                    "tlsCAFile": certifi.where(),
                    "tlsInsecure": False
                })
            else:
                # Local MongoDB connection with optimized settings
                connection_kwargs.update({
                    "tls": False
                })
            
            # Create client with optimized settings
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                **connection_kwargs
            )
            
            if self.client:
                self.database = self.client[settings.mongodb_db_name]
                
                # Verify connection with timeout
                await asyncio.wait_for(self.client.server_info(), timeout=10.0)
                logger.info("✅ Connected to MongoDB with optimized settings")
                
                # Create optimized indexes
                await self._create_optimized_indexes()
                
                # Log connection pool status
                await self._log_connection_pool_status()
            else:
                raise Exception("Failed to create MongoDB client")
                
        except asyncio.TimeoutError:
            logger.error("❌ MongoDB connection timeout")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ Unable to connect to MongoDB: {e}")
            raise
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failure: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            raise

    async def disconnect(self):
        """Close database connection gracefully."""
        if self.client:
            try:
                self.client.close()
                logger.info("✅ Disconnected from MongoDB")
            except Exception as e:
                logger.error(f"❌ Error closing MongoDB connection: {e}")

    async def _create_optimized_indexes(self):
        """Create optimized database indexes for better performance."""
        try:
            if not self.database:
                logger.warning("⚠️  Database not available for index creation")
                return
                
            # User indexes with optimized settings
            await self.database.users.create_index(
                "email", 
                unique=True, 
                background=True,
                sparse=True
            )
            await self.database.users.create_index(
                "username", 
                background=True,
                sparse=True
            )
            
            # Conversation indexes with compound optimization
            await self.database.conversations.create_index(
                "user_id", 
                background=True
            )
            await self.database.conversations.create_index(
                "created_at", 
                background=True
            )
            await self.database.conversations.create_index(
                [("user_id", 1), ("created_at", -1)], 
                background=True
            )
            await self.database.conversations.create_index(
                [("user_id", 1), ("is_active", 1)], 
                background=True
            )
            
            # Message indexes for fast retrieval
            await self.database.messages.create_index(
                "conversation_id", 
                background=True
            )
            await self.database.messages.create_index(
                [("conversation_id", 1), ("created_at", -1)], 
                background=True
            )
            await self.database.messages.create_index(
                "created_at", 
                background=True
            )
            
            logger.info("✅ Optimized database indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️  Index creation warning: {e}")

    async def _log_connection_pool_status(self):
        """Log connection pool status for monitoring."""
        try:
            if self.client:
                # Get server status to check connection
                server_info = await self.client.server_info()
                logger.info(f"📊 MongoDB Server Version: {server_info.get('version', 'Unknown')}")
                logger.info(f"📊 Connection Pool Size: {self._connection_pool_size}")
                logger.info(f"📊 Min Pool Size: {self._min_pool_size}")
        except Exception as e:
            logger.warning(f"⚠️  Could not log connection pool status: {e}")

    def get_database(self):
        """Get database instance."""
        return self.database

    def is_available(self):
        """Check if database is available."""
        try:
            return self.client is not None and self.database is not None
        except Exception:
            return False

    async def health_check(self):
        """Perform database health check."""
        try:
            if not self.client:
                return False
            
            # Quick ping to check connectivity
            await asyncio.wait_for(self.client.admin.command('ping'), timeout=5.0)
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False


# Global optimized database instance
optimized_db = OptimizedMongoDB()


async def connect_to_optimized_mongo():
    """Connect to MongoDB with optimized settings."""
    await optimized_db.connect()


async def close_optimized_mongo_connection():
    """Close optimized MongoDB connection."""
    await optimized_db.disconnect()


def get_optimized_database():
    """Get optimized database instance."""
    return optimized_db.get_database()


def is_optimized_database_available():
    """Check if optimized database is available."""
    return optimized_db.is_available()


async def optimized_database_health_check():
    """Perform optimized database health check."""
    return await optimized_db.health_check() 
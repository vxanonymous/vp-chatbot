from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Verifies database connectivity and returns detailed service status
    for monitoring and debugging purposes.
    """
    try:
        # Verify database connection for vacation chatbot data
        db = get_database()
        if db is None:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "vacation-planning-chatbot",
                "database": "disconnected",
                "error": "Database connection failed - unable to access conversation data"
            }
        
        # Test database connectivity to ensure vacation chatbot can store conversations
        try:
            await db.client.server_info()
            db_status = "connected"
        except Exception as e:
            logger.error(f"Couldn't check if the database is healthy: {e}")
            db_status = "error"
        
        return {
            "status": "healthy" if db_status == "connected" else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "vacation-planning-chatbot",
            "database": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Something went wrong during the health check: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "vacation-planning-chatbot",
            "error": str(e)
        }


@router.get("/")
async def root():
    """API root endpoint with service information."""
    return {
        "message": "Vacation Planning Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/health"
        }
    }
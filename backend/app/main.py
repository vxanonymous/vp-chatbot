from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.api import chat, health, auth, conversations

"""
FastAPI Main Application for Vacation Planning Chatbot

This is the main entry point for the backend API. It sets up the FastAPI application,
configures middleware, database connections, and registers all API routes.
"""

# Set up logging configuration for vacation chatbot operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events for vacation chatbot."""
    # Connect to MongoDB for storing conversations and user data
    if not settings.skip_mongodb_connection:
        await connect_to_mongo()
    
    yield
    
    # Clean up MongoDB connection to prevent resource leaks
    if not settings.skip_mongodb_connection:
        await close_mongo_connection()


# Initialize FastAPI application for vacation planning chatbot API
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware to allow React frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API route modules for vacation planning chatbot functionality
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
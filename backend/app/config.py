import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache

"""
Application Configuration for Vacation Planning Chatbot

This module manages all application settings, environment variables, and configuration
for the backend API. It provides validation and caching for optimal performance.
"""


class Settings(BaseSettings):
    """
    Application settings and configuration management.
    
    Handles environment variables, database settings, API keys, and security
    configurations with validation for production environments.
    """
    
    # Environment settings for deployment configuration
    environment: str = "development"
    
    # Application metadata for vacation planning chatbot
    app_name: str = "Vacation Planning Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Security and authentication for user sessions
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database configuration for storing conversations and user data
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "vacation_chatbot"
    mongodb_ssl_verify: bool = True
    mongodb_ssl: bool = False
    
    # OpenAI API settings for AI-powered vacation planning responses
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000
    openai_timeout: int = 30
    
    # CORS and security
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Rate limiting configuration
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance and limits for chat conversations
    max_conversation_messages: int = 100
    max_message_length: int = 10000
    request_timeout: int = 30
    response_timeout: int = 25
    
    # Development settings
    development_mode: bool = False
    skip_mongodb_connection: bool = False
    
    # Redis cache configuration
    redis_url: str = "redis://localhost:6379"
    
    # MongoDB Configuration
    mongodb_db_name: str = "vacation_chatbot"
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 43200  # 30 days
    
    # API Configuration
    api_version: str = "v1"
    api_title: str = "Vacation Planning Chatbot API"
    
    # Conversation Configuration for chat history management
    max_conversation_length: int = 50
    conversation_ttl: int = 3600  # 1 hour in seconds
    
    # New field
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        # Only validate in production environment
        if (v == "your-secret-key-change-in-production" and 
            os.getenv("ENVIRONMENT", "development").lower() == "production"):
            raise ValueError("SECRET_KEY must be set in production")
        return v
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v):
        # Allow empty API key in development for testing
        if not v and os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise ValueError("OPENAI_API_KEY must be set in production")
        return v
    
    @field_validator("mongodb_url")
    @classmethod
    def validate_mongodb_url(cls, v):
        if not v:
            raise ValueError("MONGODB_URL must be set")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


# Environment-specific configurations
def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def get_cors_origins() -> list:
    """Get CORS origins based on environment."""
    if is_production():
        # Add your production domain here
        return ["https://yourdomain.com"]
    return settings.cors_origins


def get_log_level() -> str:
    """Get log level based on environment."""
    if is_development():
        return "DEBUG"
    return settings.log_level


def get_mongodb_config() -> dict:
    """Get MongoDB configuration based on environment."""
    config = {
        "url": settings.mongodb_url,
        "database": settings.mongodb_database,
        "ssl_verify": settings.mongodb_ssl_verify
    }
    
    if is_production():
        # Production-specific MongoDB settings
        config.update({
            "ssl_verify": True,
            "retry_writes": True,
            "w": "majority"
        })
    
    return config
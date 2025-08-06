try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback for environments without pydantic
    class BaseModel(object):
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    def Field(*args, **kwargs):
        if len(args) > 0:
            return args[0]
        return kwargs.get('default', None)
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role types for chat conversations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Individual chat message model."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None


class ChatRequest(BaseModel):
    """Request model for chat API endpoints."""
    message: str = Field(..., min_length=1, max_length=9999, description="Chat message")
    conversation_id: Optional[str] = None
    user_preferences: Optional[Dict] = None


class ChatResponse(BaseModel):
    """Response model for chat API endpoints."""
    response: str
    conversation_id: str
    suggestions: Optional[List[str]] = None
    vacation_summary: Optional[Dict] = None


class ConversationHistory(BaseModel):
    """Complete conversation history model."""
    conversation_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    user_preferences: Optional[Dict] = None
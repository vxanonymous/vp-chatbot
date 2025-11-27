from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
from bson import ObjectId
from .object_id import PyObjectId

class ConversationCreate(BaseModel):
    # Model for creating new conversations.
    title: str = Field(..., min_length=1, max_length=200, description="Conversation title")

class ConversationInDB(BaseModel):
    # Internal conversation model for database operations.
    id: PyObjectId = Field(alias="_id")
    user_id: str
    title: str = "New Conversation"
    messages: List[Dict] = []
    vacation_preferences: Optional[Dict] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str} # Add for robust serialization
    )

class ConversationSummary(BaseModel):
    # Summary model for conversation listings.
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
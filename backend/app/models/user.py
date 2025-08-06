from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from .object_id import PyObjectId

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")

class UserCreate(UserBase):
    """Model for user registration requests."""
    password: str = Field(..., min_length=8, max_length=100, description="User password")

class UserLogin(BaseModel):
    """Model for user login requests."""
    email: EmailStr
    password: str = Field(..., min_length=1, description="User password")

class UserInDB(UserBase):
    """Internal user model for database operations."""
    id: PyObjectId = Field(alias="_id")
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class UserResponse(UserBase):
    """User model for API responses (excludes sensitive data)."""
    id: str = Field(alias="_id")
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(
        populate_by_name=True,
    )

class Token(BaseModel):
    """Authentication token model for API responses."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    """Token payload data for authentication."""
    user_id: Optional[str] = None
    email: Optional[str] = None
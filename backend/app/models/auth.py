"""
Authentication and token models for user sessions.
"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Authentication token response model."""
    access_token: str
    token_type: str
    user_id: str
    email: str
    full_name: str


class TokenData(BaseModel):
    """Token data model for JWT payload."""
    user_id: Optional[str] = None
    email: Optional[str] = None 
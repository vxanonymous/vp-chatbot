from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None):
    # Create a JWT access token for user authentication.
    # Generates a secure token with optional custom expiration time,
    # defaulting to the configured token lifetime.
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict]:
    # Decode and verify a JWT access token
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
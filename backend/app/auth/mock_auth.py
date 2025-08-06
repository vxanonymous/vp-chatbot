"""
Mock authentication for testing environments.

Provides simplified authentication for development and testing
without requiring real JWT tokens.
"""
import app.api.chat
import app.api.conversations
from app.models.user import TokenData

try:
    from fastapi import Request
    from fastapi.security import HTTPBearer
except ImportError:
    # Fallbacks for environments without fastapi
    Request = object
    class HTTPBearer:
        def __init__(self, auto_error=False):
            pass

security = HTTPBearer(auto_error=False)

async def get_mock_current_user(request: Request) -> TokenData:
    """
    Mock current user for testing environments.
    
    Returns a test user when in test mode, otherwise delegates to real authentication.
    """
    # Check if we're in test mode
    if "test" in request.headers.get("user-agent", ""):
        return TokenData(user_id="user123", email="test@example.com")
    
    # Otherwise, use real authentication
    from app.auth.dependencies import get_current_user
    return await get_current_user(request)

def setup_mock_auth():
    """
    Setup mock authentication for testing.
    
    Replaces authentication dependencies with mock versions for testing.
    """
    # Replace the dependency
    app.api.chat.get_current_user = get_mock_current_user
    app.api.conversations.get_current_user = get_mock_current_user

"""
Authentication API endpoints.

Handles user registration, login, and token management for the vacation
planning chatbot backend.
"""
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserCreate, UserResponse
from app.models.auth import Token, TokenData
from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import create_access_token
from app.core.container import get_container, ServiceContainer
from app.config import settings
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

# Service dependency functions for backward compatibility
def get_user_service() -> UserService:
    """Get user service from dependency injection container for authentication."""
    return get_container().user_service


@router.post("/signup", response_model=Token, status_code=201)
async def signup(
    user_data: UserCreate,
    container: ServiceContainer = Depends(get_container)
):
    """
    Register a new user account.
    
    Creates a new user with the provided information and returns
    an authentication token for immediate login.
    """
    try:
        # Check if someone is already using this email address
        existing_user = await container.user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered. Please try logging in instead."
            )
        
        # Create the new user account in our system
        user = await container.user_service.create_user(user_data)
        
        # Generate a secure authentication token for immediate access
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Something went wrong during user signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we couldn't create your account right now. Please try again."
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    container: ServiceContainer = Depends(get_container)
):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT token for authenticated access.
    """
    try:
        # Check if the email and password match our records
        user = await container.user_service.authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The email or password you entered is incorrect. Please check and try again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your account has been deactivated. Please contact support for assistance."
            )
        
        # Create a secure access token for the authenticated user
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Something went wrong during user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We're having trouble signing you in right now. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Get current user information."""
    if not current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again."
        )
    
    user = await container.user_service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="We couldn't find your account. Please contact support."
        )
    
    return UserResponse(
        _id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Refresh access token."""
    try:
        if not current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please log in again."
            )
        
        user = await container.user_service.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="We couldn't find your account. Please contact support."
            )
        
        # Create a fresh access token to extend the user's session
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Couldn't refresh the user's token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We're having trouble refreshing your session. Please log in again."
        )
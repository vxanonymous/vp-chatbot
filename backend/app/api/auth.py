# Authentication API endpoints
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import create_access_token
from app.config import get_settings
settings = get_settings()
from app.core.container import ServiceContainer, get_container
from app.models.auth import Token, TokenData
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

# Service dependency functions for backward compatibility

@router.post("/signup", response_model=Token, status_code=201)
async def signup(
    user_data: UserCreate,
    container: ServiceContainer = Depends(get_container)
):

    try:
        existing_user = await container.user_service.get_user_by_email(user_data.email)
        logger.debug("Signup lookup for %s found=%s", user_data.email, bool(existing_user))
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered. Please try logging in instead."
            )
        
        user = await container.user_service.create_user(user_data)
        
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

    try:
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
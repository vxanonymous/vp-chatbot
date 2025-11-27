from app.auth.jwt_handler import create_access_token
from datetime import timedelta
from app.api.auth import signup, login, get_current_user_info, refresh_token
from app.auth.dependencies import get_current_user
from app.core.container import ServiceContainer
from app.core.exceptions import ValidationError
from app.models.auth import TokenData
from app.models.user import TokenData
from app.models.user import UserCreate, UserResponse
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordRequestForm
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import patch, MagicMock
import pytest

class TestAuthAPIEndpoints:
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.user_service = MagicMock()
        return container
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user.
        user = MagicMock()
        user.id = "user_123"
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_token_data(self):
    # Create a mock token data.
        return TokenData(user_id="user_123", email="test@example.com")
    
    @pytest.mark.asyncio
    async def test_signup_success(self, mock_container, mock_user):
        mock_container.user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_container.user_service.create_user = AsyncMock(return_value=mock_user)
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        result = await signup(user_data=user_data, container=mock_container)
        
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user_id == "user_123"
        assert result.email == "test@example.com"
        mock_container.user_service.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_signup_existing_user(self, mock_container, mock_user):
        mock_container.user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await signup(user_data=user_data, container=mock_container)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_signup_service_error(self, mock_container):
        mock_container.user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_container.user_service.create_user = AsyncMock(side_effect=Exception("Database error"))
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await signup(user_data=user_data, container=mock_container)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_container, mock_user):
        mock_container.user_service.authenticate_user = AsyncMock(return_value=mock_user)
        
        form_data = MagicMock(spec=OAuth2PasswordRequestForm)
        form_data.username = "test@example.com"
        form_data.password = "SecurePass123!"
        
        result = await login(form_data=form_data, container=mock_container)
        
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user_id == "user_123"
        mock_container.user_service.authenticate_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_container):
        mock_container.user_service.authenticate_user = AsyncMock(return_value=None)
        
        form_data = MagicMock(spec=OAuth2PasswordRequestForm)
        form_data.username = "test@example.com"
        form_data.password = "WrongPassword"
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form_data=form_data, container=mock_container)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_container):
        inactive_user = MagicMock()
        inactive_user.is_active = False
        mock_container.user_service.authenticate_user = AsyncMock(return_value=inactive_user)
        
        form_data = MagicMock(spec=OAuth2PasswordRequestForm)
        form_data.username = "test@example.com"
        form_data.password = "SecurePass123!"
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form_data=form_data, container=mock_container)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "deactivated" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_login_service_error(self, mock_container):
        mock_container.user_service.authenticate_user = AsyncMock(side_effect=Exception("Database error"))
        
        form_data = MagicMock(spec=OAuth2PasswordRequestForm)
        form_data.username = "test@example.com"
        form_data.password = "SecurePass123!"
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form_data=form_data, container=mock_container)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_success(self, mock_container, mock_user, mock_token_data):
        mock_container.user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        
        result = await get_current_user_info(
            current_user=mock_token_data,
            container=mock_container
        )
        
        assert isinstance(result, UserResponse)
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        mock_container.user_service.get_user_by_id.assert_called_once_with("user_123")
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_no_user_id(self, mock_container):
        token_data = TokenData(user_id=None, email="test@example.com")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_info(
                current_user=token_data,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_not_found(self, mock_container, mock_token_data):
        mock_container.user_service.get_user_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_info(
                current_user=mock_token_data,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, mock_container, mock_user, mock_token_data):
        mock_container.user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        
        result = await refresh_token(
            current_user=mock_token_data,
            container=mock_container
        )
        
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_refresh_token_no_user_id(self, mock_container):
        token_data = TokenData(user_id=None, email="test@example.com")
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(
                current_user=token_data,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, mock_container, mock_token_data):
        mock_container.user_service.get_user_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(
                current_user=mock_token_data,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_refresh_token_service_error(self, mock_container, mock_token_data):
        mock_container.user_service.get_user_by_id = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(
                current_user=mock_token_data,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR




class TestAuthDependencies:
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        from app.auth.jwt_handler import create_access_token
        from datetime import timedelta
        
        token = create_access_token(data={"sub": "user_123", "email": "test@example.com"})
        credentials = HTTPAuthorizationCredentials(credentials=token, scheme="Bearer")
        
        result = await get_current_user(credentials)
        
        assert isinstance(result, TokenData)
        assert result.user_id == "user_123"
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        credentials = HTTPAuthorizationCredentials(credentials="invalid_token", scheme="Bearer")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id(self):
        from app.auth.jwt_handler import create_access_token
        
        token = create_access_token(data={"email": "test@example.com"})
        credentials = HTTPAuthorizationCredentials(credentials=token, scheme="Bearer")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED




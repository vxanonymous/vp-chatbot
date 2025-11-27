# Additional tests for chat.py error paths to improve coverage.
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.chat import router, send_message, stream_message
from app.core.exceptions import NotFoundError, ValidationError
from app.models.chat import ChatRequest, ChatResponse
from app.models.user import TokenData
from unittest.mock import patch


class TestChatAPIErrorPaths:
# Test error handling paths in chat API.
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock container.
        container = MagicMock()
        container.conversation_handler = MagicMock()
        container.conversation_service = MagicMock()
        container.proactive_assistant = MagicMock()
        container.vacation_planner = MagicMock()
        container.openai_service = MagicMock()
        return container
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user.
        return TokenData(user_id="user_123", email="test@example.com")
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_rate_limit_exceeded(self, mock_rate_limiter, mock_container, mock_user):
        # Test send_message when rate limit is exceeded
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(False, 0))
        mock_rate_limiter.max_requests = 20
        mock_rate_limiter.window_seconds = 60
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_invalid_validation(self, mock_rate_limiter, mock_container, mock_user):
        # Test send_message when validation fails
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        mock_container.error_recovery = MagicMock()
        mock_container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": False, "issues": ["possibly_off_topic"]})
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Please stay on topic")
        mock_container.conversation_service = MagicMock()
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        
        request = ChatRequest(message="Hello")
        
        result = await send_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(result, ChatResponse)
        assert result.response == "Please stay on topic"
        assert result.suggestions is None
        assert result.vacation_summary is None
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_app_exception(self, mock_rate_limiter, mock_container, mock_user):
        # Test send_message when AppException is raised
        from app.core.exceptions import AppException
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        mock_container.error_recovery = MagicMock()
        mock_container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
        mock_container.conversation_service = MagicMock()
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=AppException("Service error", status_code=500)
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException):
            await send_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_value_error_conversation_not_found(self, mock_rate_limiter, mock_container, mock_user):
        # Test send_message when conversation not found
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        mock_container.conversation_service = MagicMock()
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        mock_container.error_recovery = MagicMock()
        mock_container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=ValueError("Conversation not found")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id="invalid_id",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_value_error_failed_to_save(self, mock_rate_limiter, mock_container, mock_user):
    # Test send_message when failed to save.
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        mock_container.error_recovery = MagicMock()
        mock_container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=ValueError("Failed to save message")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_value_error_generic(self, mock_rate_limiter, mock_container, mock_user):
    # Test send_message with generic ValueError.
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        mock_container.error_recovery = MagicMock()
        mock_container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=ValueError("Some other error")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_send_message_generic_exception(self, mock_container, mock_user):
    # Test send_message with generic exception.
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_stream_message_timeout_error(self, mock_container, mock_user):
        # Test stream_message when timeout occurs in stream
        import asyncio
        from datetime import datetime, timezone
        from app.models.conversation_db import ConversationInDB
        from app.models.object_id import PyObjectId
        
        mock_conversation = ConversationInDB(
            id=PyObjectId(),
            user_id="user_123",
            title="Test",
            messages=[{"role": "user", "content": "Hello"}],
            vacation_preferences={},
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_container.conversation_service.get_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_container.conversation_service.add_message = AsyncMock(
            return_value=mock_conversation
        )
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(
            return_value={}
        )
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(
            return_value={}
        )
        mock_container.error_recovery = MagicMock()
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Timeout error")
        # Simulate timeout by raising asyncio.TimeoutError
        mock_container.openai_service.generate_response_async = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id="test_id",
            current_user=mock_user,
            container=mock_container
        )
        
        assert response is not None
        # Consume the generator to trigger timeout handling
        async for chunk in response.body_iterator:
            pass
        # Verify timeout error recovery was called
        mock_container.error_recovery.get_recovery_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_stream_message_app_exception_in_add_message(self, mock_container, mock_user):
    # Test stream_message when AppException occurs in add_message.
        from app.core.exceptions import DatabaseError
        
        mock_container.conversation_service.get_conversation = AsyncMock(
            return_value=None
        )
        mock_container.conversation_service.add_message = AsyncMock(
            side_effect=DatabaseError("Database error")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException):
            await stream_message(
                request=request,
                conversation_id="test_id",
                current_user=mock_user,
                container=mock_container
            )
    
    @pytest.mark.asyncio
    async def test_stream_message_generic_exception(self, mock_container, mock_user):
    # Test stream_message with generic exception.
        mock_container.conversation_service.get_conversation = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id="test_id",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


from app.core.exceptions import AppException
from app.core.exceptions import DatabaseError
from app.core.exceptions import ServiceError
from app.core.exceptions import ValidationError
from app.models.conversation_db import ConversationInDB
from app.models.object_id import PyObjectId
from bson import ObjectId
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from app.api.chat import get_conversation_analysis, submit_feedback
from app.api.chat import router, send_message, stream_message
from app.api.chat import send_message, stream_message, get_conversation_analysis, submit_feedback
from app.api.chat import stream_message
from app.core.container import ServiceContainer
from app.core.exceptions import AppException
from app.core.exceptions import AppException, DatabaseError
from app.core.exceptions import NotFoundError, ValidationError
from app.models.chat import ChatRequest
from app.models.chat import ChatRequest, ChatResponse
from app.models.chat import ChatRequest, ChatResponse, Message, MessageRole
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB
from app.models.user import TokenData
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import patch
import asyncio
import json
import pytest

class TestChatAPIEndpoints:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        
        container.conversation_handler = MagicMock()
        container.conversation_service = MagicMock()
        container.conversation_service.get_conversation = AsyncMock(return_value=None)
        container.proactive_assistant = MagicMock()
        container.vacation_planner = MagicMock()
        container.error_recovery = MagicMock()
        container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
        container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
        
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_handler.process_message = AsyncMock(return_value={
            "conversation_id": "conv_123",
            "response": "Test response"
        })
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "exploring",
            "destinations": ["Paris"]
        })
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[
            {"content": "Suggestion 1"},
            {"content": "Suggestion 2"}
        ])
        mock_container.vacation_planner.create_vacation_summary = MagicMock(return_value={
            "destination": "Paris",
            "summary": "Test summary"
        })
        
        request = ChatRequest(message="I want to go to Paris")
        
        result = await send_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(result, ChatResponse)
        assert result.response == "Test response"
        assert result.conversation_id is not None
        assert result.suggestions == ["Suggestion 1", "Suggestion 2"]
        assert result.vacation_summary is not None
        mock_container.conversation_handler.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_with_existing_conversation(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_handler.process_message = AsyncMock(return_value={
            "conversation_id": "conv_123",
            "response": "Test response"
        })
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        
        request = ChatRequest(message="Tell me more")
        
        result = await send_message(
            request=request,
            conversation_id="conv_123",
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.conversation_id is not None
        mock_container.conversation_handler.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_conversation_not_found(self, mock_rate_limiter, mock_user, mock_container):
        from fastapi import HTTPException
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        mock_container.conversation_handler.process_message = AsyncMock(side_effect=ValueError("Conversation not found"))
        mock_container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response for not found")
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id="nonexistent",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == 404
        mock_container.error_recovery.get_recovery_response.assert_called_once()
        assert "Recovery response" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_send_message_no_suggestions(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_handler.process_message = AsyncMock(return_value={
            "conversation_id": "conv_123",
            "response": "Test response"
        })
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=None)
        
        request = ChatRequest(message="Hello")
        
        result = await send_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.suggestions is None
        assert result.vacation_summary is None
    
    @pytest.mark.asyncio
    async def test_send_message_no_vacation_summary(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_handler.process_message = AsyncMock(return_value={
            "conversation_id": "conv_123",
            "response": "Test response"
        })
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "exploring"
        })
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[])
        
        request = ChatRequest(message="Hello")
        
        result = await send_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.vacation_summary is None
    
    @pytest.mark.asyncio
    async def test_stream_message_success(self, mock_user, mock_container, mock_conversation):
        from fastapi.responses import StreamingResponse
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "exploring",
            "destinations": ["Paris"]
        })
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={
            "conversation_id": "conv_123",
            "message_count": 2,
            "user_id": "test_user_123"
        })
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[
            {"content": "Suggestion 1"}
        ])
        mock_container.vacation_planner.create_vacation_summary = MagicMock(return_value={
            "destination": "Paris"
        })
        
        request = ChatRequest(message="I want to go to Paris")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
    
    @pytest.mark.asyncio
    async def test_stream_message_error_handling(self, mock_user, mock_container):
        from fastapi import HTTPException
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(side_effect=Exception("Test error"))
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == 500

class TestChatAPIAdditional:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_service = MagicMock()
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_get_conversation_analysis_success(self, mock_user, mock_container, mock_conversation):
        from app.models.object_id import PyObjectId
        mock_conversation.id = PyObjectId()
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.analyze_conversation = AsyncMock(return_value={
            "message_count": 2,
            "topics": ["travel", "vacation"]
        })
        
        result = await get_conversation_analysis(
            conversation_id=str(mock_conversation.id),
            current_user=mock_user,
            container=mock_container
        )
        
        assert "conversation_id" in result
        assert "analysis" in result
        assert result["analysis"]["message_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_conversation_analysis_not_found(self, mock_user, mock_container):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation_analysis(
                conversation_id="nonexistent",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_get_conversation_analysis_error(self, mock_user, mock_container, mock_conversation):
        from app.core.exceptions import DatabaseError
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.analyze_conversation = AsyncMock(side_effect=DatabaseError("DB error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation_analysis(
                conversation_id="conv_123",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_submit_feedback_success(self, mock_user, mock_container, mock_conversation):
        from app.models.object_id import PyObjectId
        mock_conversation.id = PyObjectId()
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_feedback = AsyncMock(return_value=True)
        
        result = await submit_feedback(
            conversation_id=str(mock_conversation.id),
            feedback="Great service!",
            rating=5,
            current_user=mock_user,
            container=mock_container
        )
        
        assert "message" in result
        assert "successfully" in result["message"]
        mock_container.conversation_service.add_feedback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_feedback_conversation_not_found(self, mock_user, mock_container):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await submit_feedback(
                conversation_id="nonexistent",
                feedback="Great!",
                rating=5,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_submit_feedback_save_failed(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_feedback = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await submit_feedback(
                conversation_id="conv_123",
                feedback="Great!",
                rating=5,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to save feedback" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_submit_feedback_error(self, mock_user, mock_container, mock_conversation):
        from app.core.exceptions import DatabaseError
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_feedback = AsyncMock(side_effect=DatabaseError("DB error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await submit_feedback(
                conversation_id="conv_123",
                feedback="Great!",
                rating=5,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

class TestChatAPIErrorHandling:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_handler = MagicMock()
        container.conversation_service = MagicMock()
        container.proactive_assistant = MagicMock()
        container.vacation_planner = MagicMock()
        container.openai_service = MagicMock()
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_send_message_http_exception_re_raise(self, mock_user, mock_container):
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Not found")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_send_message_generic_exception(self, mock_user, mock_container):
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
    async def test_stream_message_app_exception_inner(self, mock_user, mock_container, mock_conversation):
        from app.core.exceptions import DatabaseError
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(side_effect=DatabaseError("DB error"))
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_stream_message_timeout_in_generate_stream(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.openai_service.generate_response_async = AsyncMock(side_effect=asyncio.TimeoutError())
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_stream_message_app_exception_in_generate_stream(self, mock_user, mock_container, mock_conversation):
        from app.core.exceptions import ServiceError
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.openai_service.generate_response_async = AsyncMock(side_effect=ServiceError("Service error"))
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_stream_message_generic_exception_in_generate_stream(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.openai_service.generate_response_async = AsyncMock(side_effect=Exception("Unexpected error"))
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_stream_message_app_exception_outer(self, mock_user, mock_container):
        from app.core.exceptions import ValidationError
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(
            side_effect=ValidationError("Invalid input")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_stream_message_generic_exception_outer(self, mock_user, mock_container):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_get_conversation_analysis_generic_exception(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.analyze_conversation = AsyncMock(side_effect=Exception("Unexpected error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation_analysis(
                conversation_id="conv_123",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_submit_feedback_generic_exception(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_feedback = AsyncMock(side_effect=Exception("Unexpected error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await submit_feedback(
                conversation_id="conv_123",
                feedback="Great!",
                rating=5,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

class TestChatAPIErrorPaths:
    
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

class TestChatAPIStreaming:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_service = MagicMock()
        container.conversation_handler = MagicMock()
        container.openai_service = MagicMock()
        container.proactive_assistant = MagicMock()
        container.vacation_planner = MagicMock()
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_stream_message_new_conversation(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        
        request = ChatRequest(message="I want to go to Paris")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
        mock_container.conversation_service.create_conversation_with_auto_title.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_message_existing_conversation(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        
        request = ChatRequest(message="Tell me more")
        
        response = await stream_message(
            request=request,
            conversation_id=str(mock_conversation.id),
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
        mock_container.conversation_service.get_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_message_conversation_not_found(self, mock_user, mock_container):
        from fastapi import HTTPException
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id="nonexistent",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_stream_message_save_failed(self, mock_user, mock_container, mock_conversation):
        from fastapi import HTTPException
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=None)
        
        request = ChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await stream_message(
                request=request,
                conversation_id=None,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_stream_message_with_suggestions(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "exploring"
        })
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[
            {"content": "Suggestion 1"}
        ])
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
    
    @pytest.mark.asyncio
    async def test_stream_message_timeout(self, mock_user, mock_container, mock_conversation):
        import asyncio
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)

class TestChatAPIStreamingAdditional:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_service = MagicMock()
        container.conversation_handler = MagicMock()
        container.openai_service = MagicMock()
        container.proactive_assistant = MagicMock()
        container.vacation_planner = MagicMock()
        container.error_recovery = MagicMock()
        container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_stream_message_with_extracted_preferences(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": {"destinations": ["Paris"]},
            "confidence_score": 0.9
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "planning",
            "destinations": ["Paris"]
        })
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[
            {"content": "Suggestion 1"}
        ])
        mock_container.vacation_planner.create_vacation_summary = MagicMock(return_value={
            "destination": "Paris"
        })
        
        request = ChatRequest(message="I want to go to Paris")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
        
        # Consume the stream to verify it works
        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                chunks.append(chunk.decode())
            else:
                chunks.append(chunk)
        
        # Verify we got content chunks
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_stream_message_with_vacation_summary(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "planning",
            "destinations": ["Paris"]
        })
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=None)
        mock_container.vacation_planner.create_vacation_summary = MagicMock(return_value={
            "destination": "Paris",
            "summary": "Great choice!"
        })
        
        request = ChatRequest(message="I want to go to Paris")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
    
    @pytest.mark.asyncio
    async def test_stream_message_without_final_conversation(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
    
    @pytest.mark.asyncio
    async def test_stream_message_app_exception(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(side_effect=AppException("Test error"))
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
        
        # Consume the stream to verify error response
        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                chunks.append(chunk.decode())
            else:
                chunks.append(chunk)
        
        # Should have error response and done
        assert len(chunks) >= 2
    
    @pytest.mark.asyncio
    async def test_stream_message_generic_exception(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(side_effect=Exception("Generic error"))
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value=None)
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
        
        # Consume the stream to verify error response
        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                chunks.append(chunk.decode())
            else:
                chunks.append(chunk)
        
        # Should have error response and done
        assert len(chunks) >= 2
    
    @pytest.mark.asyncio
    async def test_stream_message_without_suggestions(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "exploring"
        })
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=None)
        mock_container.vacation_planner.create_vacation_summary = MagicMock(return_value=None)
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
    
    @pytest.mark.asyncio
    async def test_stream_message_without_destinations(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={
            "decision_stage": "exploring"
        })
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[
            {"content": "Suggestion 1"}
        ])
        
        request = ChatRequest(message="Hello")
        
        response = await stream_message(
            request=request,
            conversation_id=None,
            current_user=mock_user,
            container=mock_container
        )
        
        assert isinstance(response, StreamingResponse)
        
        # Vacation planner should not be called since no destinations
        mock_container.vacation_planner.create_vacation_summary.assert_not_called()


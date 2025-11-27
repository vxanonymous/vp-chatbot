from app.models.object_id import PyObjectId
from app.services.openai_service import OpenAIService
from bson import ObjectId
from datetime import datetime, timezone
import asyncio
from app.core.exceptions import NotFoundError, ValidationError
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB
from app.services.conversation_handler import ConversationHandler
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

class TestConversationHandler:
    
    @pytest.fixture
    def mock_conversation_service(self):
    # Create a mock conversation service.
        service = MagicMock()
        service.create_conversation = AsyncMock()
        service.create_conversation_with_auto_title = AsyncMock()
        service.get_conversation = AsyncMock()
        service.add_message = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_openai_service(self):
    # Create a mock OpenAI service.
        service = MagicMock()
        service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        return service
    
    @pytest.fixture
    def mock_intelligence_service(self):
    # Create a mock intelligence service.
        service = MagicMock()
        service.analyze_conversation = MagicMock(return_value={
            "decision_stage": "exploring",
            "stage_confidence": 0.8
        })
        return service
    
    @pytest.fixture
    def handler(self, mock_conversation_service, mock_openai_service, mock_intelligence_service):
    # Create a ConversationHandler instance.
        return ConversationHandler(
            conversation_service=mock_conversation_service,
            openai_service=mock_openai_service,
            intelligence_service=mock_intelligence_service
        )
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_ensure_conversation_exists_new(self, handler, mock_conversation_service, mock_conversation):
        from app.services.openai_service import OpenAIService
        handler.openai_service = MagicMock(spec=OpenAIService)
        mock_conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        
        result = await handler.ensure_conversation_exists(
            conversation_id=None,
            user_id="user_123",
            initial_message="Hello"
        )
        
        assert result == mock_conversation
        mock_conversation_service.create_conversation_with_auto_title.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_conversation_exists_existing(self, handler, mock_conversation_service, mock_conversation):
        mock_conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        
        result = await handler.ensure_conversation_exists(
            conversation_id="conv_123",
            user_id="user_123",
            initial_message="Hello"
        )
        
        assert result == mock_conversation
        mock_conversation_service.get_conversation.assert_called_once_with(
            conversation_id="conv_123",
            user_id="user_123"
        )
    
    @pytest.mark.asyncio
    async def test_ensure_conversation_exists_not_found(self, handler, mock_conversation_service):
        mock_conversation_service.get_conversation = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Conversation not found"):
            await handler.ensure_conversation_exists(
                conversation_id="nonexistent",
                user_id="user_123",
                initial_message="Hello"
            )
    
    @pytest.mark.asyncio
    async def test_add_user_message_success(self, handler, mock_conversation_service, mock_conversation):
        mock_conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        
        result = await handler.add_user_message(
            conversation_id="conv_123",
            user_id="user_123",
            message_content="Hello"
        )
        
        assert result == mock_conversation
        mock_conversation_service.add_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_user_message_failure(self, handler, mock_conversation_service):
        mock_conversation_service.add_message = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Failed to save message"):
            await handler.add_user_message(
                conversation_id="conv_123",
                user_id="user_123",
                message_content="Hello"
            )
    
    @pytest.mark.asyncio
    async def test_extract_user_preferences_with_intelligence(self, handler, mock_intelligence_service, mock_conversation):
        mock_intelligence_service.analyze_preferences = AsyncMock(return_value={
            "decision_stage": "planning",
            "stage_confidence": 0.9,
            "detected_interests": ["adventure", "culture"],
            "mentioned_destinations": ["Paris"]
        })
        
        result = await handler.extract_user_preferences(mock_conversation)
        
        assert result is not None
        assert result["decision_stage"] == "planning"
        assert "destinations" in result
        mock_intelligence_service.analyze_preferences.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_user_preferences_no_intelligence(self, handler, mock_conversation):
        handler.intelligence_service = None
        
        result = await handler.extract_user_preferences(mock_conversation)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, handler, mock_conversation_service, mock_openai_service, mock_conversation):
        from app.services.openai_service import OpenAIService
        handler.openai_service = mock_openai_service
        handler.openai_service = MagicMock(spec=OpenAIService)
        handler.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        
        result = await handler.process_message(
            message_content="Hello",
            conversation_id=None,
            user_id="user_123"
        )
        
        assert "conversation_id" in result
        assert "response" in result
        assert result["response"] == "Test response"
    
    @pytest.mark.asyncio
    async def test_process_message_with_existing_conversation(self, handler, mock_conversation_service, mock_openai_service, mock_conversation):
        from app.services.openai_service import OpenAIService
        handler.openai_service = MagicMock(spec=OpenAIService)
        handler.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        mock_conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        
        result = await handler.process_message(
            message_content="Hello",
            conversation_id="conv_123",
            user_id="user_123"
        )
        
        assert result["conversation_id"] is not None
        mock_conversation_service.get_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_timeout(self, handler, mock_conversation_service, mock_openai_service, mock_conversation):
        import asyncio
        from app.services.openai_service import OpenAIService
        handler.openai_service = MagicMock(spec=OpenAIService)
        handler.openai_service.generate_response_async = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        
        result = await handler.process_message(
            message_content="Hello",
            conversation_id=None,
            user_id="user_123"
        )
        
        assert result["response"] == handler.FALLBACK_RESPONSE
    
    @pytest.mark.asyncio
    async def test_process_message_error(self, handler, mock_conversation_service, mock_openai_service, mock_conversation):
        from app.services.openai_service import OpenAIService
        handler.openai_service = MagicMock(spec=OpenAIService)
        handler.openai_service.generate_response_async = AsyncMock(side_effect=Exception("Test error"))
        mock_conversation_service.create_conversation_with_auto_title = AsyncMock(return_value=mock_conversation)
        mock_conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        
        result = await handler.process_message(
            message_content="Hello",
            conversation_id=None,
            user_id="user_123"
        )
        
        assert result["response"] == handler.ERROR_RESPONSE



class TestConversationHandlerAdditional:
# Additional tests for ConversationHandler.
    
    @pytest.fixture
    def mock_conversation_service(self):
    # Create a mock conversation service.
        service = MagicMock()
        service.create_conversation = AsyncMock()
        service.create_conversation_with_auto_title = AsyncMock()
        service.get_conversation = AsyncMock()
        service.add_message = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_openai_service(self):
    # Create a mock OpenAI service.
        service = MagicMock()
        service.generate_response_async = AsyncMock(return_value={
            "content": "Test response",
            "extracted_preferences": None,
            "confidence_score": 0.8
        })
        return service
    
    @pytest.fixture
    def handler(self, mock_conversation_service, mock_openai_service):
    # Create a ConversationHandler instance.
        return ConversationHandler(
            conversation_service=mock_conversation_service,
            openai_service=mock_openai_service,
            intelligence_service=None
        )
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_build_conversation_metadata(self, handler):
        result = handler.build_conversation_metadata(
            conversation_id="conv_123",
            user_id="user_123",
            message_count=5
        )
        
        assert result["conversation_id"] == "conv_123"
        assert result["user_id"] == "user_123"
        assert result["message_count"] == 5
    
    @pytest.mark.asyncio
    async def test_prepare_messages_for_ai(self, handler, mock_conversation):
        mock_conversation.messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
        result = handler.prepare_messages_for_ai(mock_conversation)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "Hi!"
    
    @pytest.mark.asyncio
    async def test_generate_ai_response_success(self, handler, mock_openai_service):
        handler.openai_service = mock_openai_service
        messages = [{"role": "user", "content": "Hello"}]
        user_preferences = {"decision_stage": "exploring"}
        conversation_metadata = {"conversation_id": "conv_123"}
        
        result = await handler.generate_ai_response(
            messages=messages,
            user_preferences=user_preferences,
            conversation_metadata=conversation_metadata
        )
        
        assert "content" in result
        assert result["content"] == "Test response"
        mock_openai_service.generate_response_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ai_response_timeout(self, handler, mock_openai_service):
        import asyncio
        handler.openai_service = mock_openai_service
        mock_openai_service.generate_response_async = AsyncMock(side_effect=asyncio.TimeoutError())
        
        result = await handler.generate_ai_response(
            messages=[],
            user_preferences=None,
            conversation_metadata={}
        )
        
        assert result["content"] == handler.FALLBACK_RESPONSE
    
    @pytest.mark.asyncio
    async def test_generate_ai_response_error(self, handler, mock_openai_service):
        handler.openai_service = mock_openai_service
        mock_openai_service.generate_response_async = AsyncMock(side_effect=Exception("Test error"))
        
        result = await handler.generate_ai_response(
            messages=[],
            user_preferences=None,
            conversation_metadata={}
        )
        
        assert result["content"] == handler.ERROR_RESPONSE
    
    @pytest.mark.asyncio
    async def test_save_assistant_message_success(self, handler, mock_conversation_service, mock_conversation):
        mock_conversation_service.add_message = AsyncMock(return_value=mock_conversation)
        
        result = await handler.save_assistant_message(
            conversation_id="conv_123",
            user_id="user_123",
            content="Test response",
            extracted_preferences={"destinations": ["Paris"]},
            confidence_score=0.9
        )
        
        assert result == mock_conversation
        mock_conversation_service.add_message.assert_called_once()
        call_args = mock_conversation_service.add_message.call_args
        message = call_args[1]["message"]
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Test response"
        assert message.metadata["extracted_preferences"]["destinations"] == ["Paris"]
    
    @pytest.mark.asyncio
    async def test_save_assistant_message_failure(self, handler, mock_conversation_service):
        mock_conversation_service.add_message = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Failed to save AI response"):
            await handler.save_assistant_message(
                conversation_id="conv_123",
                user_id="user_123",
                content="Test response"
            )
    
    @pytest.mark.asyncio
    async def test_extract_user_preferences_from_metadata(self, handler, mock_conversation):
        class MockMessage:
            def __init__(self, role, content, metadata=None):
                self.role = role
                self.content = content
                self.metadata = metadata or {}
        
        mock_conversation.messages = [
            MockMessage("user", "Hello"),
            MockMessage("assistant", "Hi!", {
                "extracted_preferences": {
                    "destinations": ["Paris"],
                    "budget_range": "moderate"
                }
            }),
            MockMessage("user", "Tell me more")
        ]
        
        result = await handler.extract_user_preferences(mock_conversation)
        
        assert result is not None
        assert result["destinations"] == ["Paris"]
        assert result["budget_range"] == "moderate"




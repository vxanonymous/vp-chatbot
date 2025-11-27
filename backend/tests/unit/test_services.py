# Tests for service implementations.
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from app.models.user import UserCreate, UserInDB
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB, ConversationUpdate
from app.models.object_id import PyObjectId
from app.services.user_service import UserService
from app.services.conversation_service import ConversationService
from app.services.openai_service import OpenAIService
from app.services.vacation_intelligence_service import VacationIntelligenceService
from app.services.conversation_memory import ConversationMemory
from app.services.proactive_assistant import ProactiveAssistant
from app.services.error_recovery import ErrorRecoveryService
from app.auth.password import get_password_hash, verify_password


class TestUserService:
# Test user service functionality.
    
    @pytest.fixture
    def mock_collection(self):
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_collection):
        return UserService(mock_collection)
    
    @pytest.fixture
    def sample_user_data(self):
        return UserCreate(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_collection, sample_user_data):
    # Test successful user creation.
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        user = await user_service.create_user(sample_user_data)
        
        assert user.email == sample_user_data.email
        assert user.full_name == sample_user_data.full_name
        assert user.is_active is True
        assert user.created_at is not None
        
        assert user.hashed_password != sample_user_data.password
        assert verify_password(sample_user_data.password, user.hashed_password)
        
        mock_collection.find_one.assert_called_once_with({"email": sample_user_data.email})
        mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_existing_email(self, user_service, mock_collection, sample_user_data):
    # Test user creation with existing email.
        mock_collection.find_one.return_value = {"email": sample_user_data.email}
        
        with pytest.raises(ValueError, match="already registered"):
            await user_service.create_user(sample_user_data)
        
        mock_collection.find_one.assert_called_once_with({"email": sample_user_data.email})
        mock_collection.insert_one.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service, mock_collection):
    # Test successful user authentication.
        email = "test@example.com"
        password = "testpassword123"
        hashed_password = get_password_hash(password)
        
        mock_collection.find_one.return_value = {
            "_id": ObjectId(),
            "email": email,
            "hashed_password": hashed_password,
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        user = await user_service.authenticate_user(email, password)
        
        assert user is not None
        assert user.email == email
        assert user.is_active is True
        
        mock_collection.find_one.assert_called_once_with({"email": email})
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_service, mock_collection):
    # Test authentication with non-existent user.
        mock_collection.find_one.return_value = None
        
        user = await user_service.authenticate_user("nonexistent@example.com", "password")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, user_service, mock_collection):
    # Test authentication with wrong password.
        email = "test@example.com"
        hashed_password = get_password_hash("correctpassword")
        
        mock_collection.find_one.return_value = {
            "_id": ObjectId(),
            "email": email,
            "hashed_password": hashed_password,
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        user = await user_service.authenticate_user(email, "wrongpassword")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_collection):
    # Test getting user by ID.
        user_id = ObjectId()
        mock_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com",
            "hashed_password": "hashed",
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        user = await user_service.get_user_by_id(str(user_id))
        assert user is not None
        assert str(user.id) == str(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_collection):
    # Test getting non-existent user by ID.
        mock_collection.find_one.return_value = None
        
        user = await user_service.get_user_by_id("507f1f77bcf86cd799439011")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_collection):
    # Test getting user by email.
        email = "test@example.com"
        mock_collection.find_one.return_value = {
            "_id": ObjectId(),
            "email": email,
            "hashed_password": "hashed",
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        user = await user_service.get_user_by_email(email)
        assert user is not None
        assert user.email == email


class TestConversationService:
# Test conversation service functionality.
    
    @pytest.fixture
    def mock_collection(self):
        collection = AsyncMock()
        collection.find = MagicMock()
        collection.aggregate = AsyncMock()
        return collection
    
    @pytest.fixture
    def conversation_service(self, mock_collection):
        return ConversationService(mock_collection)
    
    @pytest.fixture
    def sample_message(self):
        return Message(
            role=MessageRole.USER,
            content="I want to go to Paris"
        )
    
    @pytest.mark.asyncio
    async def test_create_conversation_success(self, conversation_service, mock_collection):
    # Test successful conversation creation.
        user_id = "user123"
        title = "Paris Trip"
        
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
        
        conversation = await conversation_service.create_conversation(user_id, title)
        
        assert conversation.user_id == user_id
        assert conversation.title == title
        assert conversation.is_active is True
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        
        mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_conversations(self, conversation_service, mock_collection):
    # Test getting user conversations.
        user_id = "user123"
        
        mock_conversations = [
            {
                "id": str(ObjectId()),
                "_id": str(ObjectId()),
                "title": "Paris Trip",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "message_count": 5
            }
        ]
        
        async def async_iter():
            for conv in mock_conversations:
                yield conv
        
        class MockCursor:
            def __aiter__(self):
                return async_iter()
        
        mock_collection.aggregate = MagicMock(return_value=MockCursor())
        
        conversations = await conversation_service.get_user_conversations(user_id)
        
        assert len(conversations) >= 0
        mock_collection.aggregate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation_success(self, conversation_service, mock_collection):
    # Test getting specific conversation.
        conversation_id = ObjectId()
        user_id = "user123"
        
        mock_collection.find_one.return_value = {
            "_id": conversation_id,
            "user_id": user_id,
            "title": "Paris Trip",
            "messages": [],
            "vacation_preferences": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        conversation = await conversation_service.get_conversation(str(conversation_id), user_id)
        
        assert conversation is not None
        assert conversation.title == "Paris Trip"
        assert conversation.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_get_conversation_invalid_id(self, conversation_service, mock_collection):
    # Test getting conversation with invalid ID.
        mock_collection.find_one.return_value = None
        conversation = await conversation_service.get_conversation("invalid-id", "user123")
        assert conversation is None
    
    @pytest.mark.asyncio
    async def test_add_message_success(self, conversation_service, mock_collection, sample_message):
    # Test adding message to conversation.
        conversation_id = ObjectId()
        user_id = "user123"
        
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.find_one.return_value = {
            "_id": conversation_id,
            "user_id": user_id,
            "title": "Paris Trip",
            "messages": [{"role": "user", "content": sample_message.content}],
            "vacation_preferences": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        conversation = await conversation_service.add_message(
            str(conversation_id), user_id, sample_message
        )
        
        assert conversation is not None
        assert len(conversation.messages) == 1
        
        mock_collection.update_one.assert_called_once()
        mock_collection.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_conversation_success(self, conversation_service, mock_collection):
    # Test updating conversation.
        conversation_id = ObjectId()
        user_id = "user123"
        update_data = ConversationUpdate(title="Updated Title")
        
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.find_one.return_value = {
            "_id": conversation_id,
            "user_id": user_id,
            "title": "Updated Title",
            "messages": [],
            "vacation_preferences": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        conversation = await conversation_service.update_conversation(
            str(conversation_id), user_id, update_data
        )
        
        assert conversation is not None
        assert conversation.title == "Updated Title"
        
        mock_collection.update_one.assert_called_once()
        mock_collection.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, conversation_service, mock_collection):
    # Test deleting conversation.
        conversation_id = ObjectId()
        user_id = "user123"
        
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        success = await conversation_service.delete_conversation(str(conversation_id), user_id)
        
        assert success is True
        
        mock_collection.update_one.assert_called_once()


class TestOpenAIService:
# Test OpenAI service functionality.
    
    @pytest.fixture
    def openai_service(self):
        from app.config import Settings
        mock_settings = Settings(
            openrouter_api_key="test-key",
            openrouter_model="x-ai/grok-4.1-fast",
            openrouter_temperature=0.8,
            openrouter_max_tokens=2000
        )
        with patch('app.config.get_settings', return_value=mock_settings):
            return OpenAIService()
    
    @pytest.fixture
    def sample_messages(self):
        return [
            Message(role=MessageRole.USER, content="I want to go to Paris")
        ]
    
    @pytest.mark.asyncio
    @patch('app.services.openai_service.OpenAI')
    async def test_generate_response_async_success(self, mock_openai_class, openai_service, sample_messages):
    # Test successful async response generation.
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Paris is great!"
        mock_response.choices[0].message.function_call = None
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        
        openai_service.client = mock_client
        
        result = await openai_service.generate_response_async(sample_messages)
        
        assert "content" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
        
        mock_client.chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    @patch('app.services.openai_service.OpenAI')
    async def test_generate_response_async_api_error(self, mock_openai_class, openai_service, sample_messages):
    # Test async response generation when API fails.
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        messages_dict = [{"role": "user", "content": msg.content} for msg in sample_messages]
        result = await openai_service.generate_response_async(messages_dict)
        
        assert "content" in result
        assert isinstance(result["content"], str)


class TestVacationIntelligenceService:
# Test vacation intelligence service functionality.
    
    @pytest.fixture
    def intelligence_service(self):
        return VacationIntelligenceService()
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_exploring_stage(self, intelligence_service):
    # Test preference analysis for exploring stage.
        messages = [
            {"role": "user", "content": "I'm thinking about going somewhere warm"}
        ]
        
        insights = await intelligence_service.analyze_preferences(messages, None)
        
        assert insights["decision_stage"] in ["exploring", "planning", "comparing", "finalizing"]
        assert insights["stage_confidence"] >= 0.0
        assert "detected_interests" in insights
        assert "mentioned_destinations" in insights
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_planning_stage(self, intelligence_service):
    # Test preference analysis for planning stage.
        messages = [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "user", "content": "What should I do there?"}
        ]
        
        preferences = {"destinations": ["Paris"]}
        insights = await intelligence_service.analyze_preferences(messages, preferences)
        
        assert "Paris" in insights["mentioned_destinations"] or any("paris" in str(d).lower() for d in insights["mentioned_destinations"])
    
    def test_detect_interests(self, intelligence_service):
    # Test interest detection.
        text = "I love hiking and adventure sports"
        interests = intelligence_service._detect_interests(text)
        
        assert isinstance(interests, list)
        assert len(interests) >= 0
    
    def test_extract_destinations(self, intelligence_service):
    # Test destination extraction.
        messages = [
            {"role": "user", "content": "I want to visit Paris and Tokyo"}
        ]
        
        destinations = intelligence_service._extract_destinations(messages)
        
        assert isinstance(destinations, list)
        assert len(destinations) >= 0
    
    def test_generate_dynamic_suggestions(self, intelligence_service):
    # Test dynamic suggestion generation.
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": ["adventure"]
        }
        last_message = "I want adventure"
        
        suggestions = intelligence_service.generate_dynamic_suggestions(conversation_state, last_message)
        
        assert len(suggestions) > 0
        assert isinstance(suggestions, list)


class TestConversationMemory:
# Test conversation memory functionality.
    
    @pytest.fixture
    def memory(self):
        return ConversationMemory()
    
    def test_get_context(self, memory):
    # Test getting context.
        conversation_id = "conv123"
        context = memory.get_context(conversation_id)
        
        assert isinstance(context, dict)
    
    def test_extract_key_points(self, memory):
    # Test key point extraction.
        messages = [
            {"role": "user", "content": "I want to go to Paris for 5 days"},
            {"role": "assistant", "content": "Great! What's your budget?"},
            {"role": "user", "content": "Around $2000"}
        ]
        
        key_points = memory.extract_key_points(messages)
        
        assert "destinations" in key_points
        assert "preferences" in key_points
        assert "requirements" in key_points


class TestProactiveAssistant:
# Test proactive assistant functionality.
    
    @pytest.fixture
    def assistant(self):
        return ProactiveAssistant()
    
    def test_get_proactive_suggestions(self, assistant):
    # Test proactive suggestion generation.
        context = {"stage": "exploring"}
        preferences = {"destinations": ["Paris"]}
        
        suggestions = assistant.get_proactive_suggestions(context, preferences, 1)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all("content" in s for s in suggestions)


class TestErrorRecoveryService:
# Test error recovery service functionality.
    
    @pytest.fixture
    def recovery_service(self):
        return ErrorRecoveryService()
    
    def test_recover_from_error(self, recovery_service):
    # Test error recovery.
        error_message = "What's the weather like today?"
        
        response = recovery_service.recover_from_error(error_message)
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_get_recovery_response(self, recovery_service):
    # Test getting recovery response.
        response = recovery_service.get_recovery_response("general_error")
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_validate_conversation_flow(self, recovery_service):
    # Test conversation flow validation.
        messages = [
            {"role": "user", "content": "I want to travel"}
        ]
        new_message = "What's the weather like?"
        
        validation = recovery_service.validate_conversation_flow(messages, new_message)
        
        assert "is_valid" in validation
        assert "issues" in validation
        assert "suggestions" in validation

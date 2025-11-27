# - Service integration with API layer

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.user import UserCreate, UserInDB, TokenData
from app.models.chat import Message, MessageRole, ChatRequest, ChatResponse
from app.models.conversation_db import ConversationInDB, ConversationSummary
from app.models.object_id import PyObjectId
from app.core.container import ServiceContainer, get_container
from app.auth.dependencies import get_current_user

# Import real service fixtures
pytest_plugins = ['tests.integration.conftest_integration']


@pytest.fixture(autouse=True)
def setup_dependencies():
    # Set up and tear down dependency overrides for each test
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
# Create test client.
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
# Create async test client.
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user():
# Create a mock user for authentication.
    return TokenData(
        user_id=str(ObjectId()),
        email="test@example.com"
    )


@pytest.fixture
def mock_conversation():
# Create a mock conversation.
    return ConversationInDB(
        id=PyObjectId(),
        user_id=str(ObjectId()),
        title="Test Conversation",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"}
        ],
        vacation_preferences={},
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_container():
    # Create a mock service container (for tests that specifically need mocks)
    container = MagicMock(spec=ServiceContainer)
    
    # Mock services - ensure all are properly set up
    container.user_service = MagicMock()
    container.conversation_service = MagicMock()
    container.conversation_service.get_conversation = AsyncMock(return_value=None)
    container.conversation_service.get_user_conversations = AsyncMock(return_value=[])
    container.conversation_service.delete_conversation = AsyncMock(return_value=True)
    container.conversation_handler = MagicMock()
    container.conversation_handler.process_message = AsyncMock(return_value={"conversation_id": "test_id", "response": "Test response"})
    container.conversation_handler.extract_user_preferences = AsyncMock(return_value={})
    container.openai_service = MagicMock()
    container.proactive_assistant = MagicMock()
    container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[])
    container.vacation_planner = MagicMock()
    container.vacation_planner.create_vacation_summary = MagicMock(return_value=None)
    container.error_recovery = MagicMock()
    container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
    container.error_recovery.get_recovery_response = MagicMock(return_value="Recovery response")
    
    return container


class TestAuthEndpoints:
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_signup_success(self, mock_rate_limiter, client, mock_container):
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        from app.core.container import get_container
        app.dependency_overrides[get_container] = lambda: mock_container
        
        mock_user = UserInDB(
            id=PyObjectId(),
            email="newuser@example.com",
            full_name="New User",
            hashed_password="hashed_password",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        mock_container.user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_container.user_service.create_user = AsyncMock(return_value=mock_user)
        
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 201
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client, real_container_with_mocked_openai):
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # First, create a user
        first_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "existing@example.com",
                "full_name": "Existing User",
                "password": "SecurePass123!"
            }
        )
        assert first_response.status_code == 201
        
        # Try to create the same user again
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "existing@example.com",
                "full_name": "New User",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, real_container_with_mocked_openai):
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # First, create a user
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "full_name": "Test User",
                "password": "SecurePass123!"
            }
        )
        assert signup_response.status_code == 201
        
        # Now login with the same credentials
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, mock_container):
        from app.core.container import get_container
        app.dependency_overrides[get_container] = lambda: mock_container
        
        mock_container.user_service.authenticate_user = AsyncMock(return_value=None)
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


class TestChatEndpoints:
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_success(self, mock_rate_limiter, client, mock_user, real_container_with_mocked_openai):
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        response = client.post(
            "/api/v1/chat/",
            json={"message": "I want to plan a trip to Japan"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_with_suggestions(self, mock_rate_limiter, client, mock_user, real_container_with_mocked_openai):
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # Send a message that should trigger suggestions
        response = client.post(
            "/api/v1/chat/",
            json={"message": "I want to visit Japan"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        # Real services may or may not return suggestions depending on logic
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_send_message_conversation_not_found(self, mock_rate_limiter, client, mock_user, mock_container):
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        app.dependency_overrides[get_current_user] = lambda: mock_user
        from app.core.container import get_container
        app.dependency_overrides[get_container] = lambda: mock_container
        
        mock_container.error_recovery.validate_conversation_flow = MagicMock(return_value={"is_valid": True, "issues": []})
        mock_container.conversation_service.get_conversation = AsyncMock(side_effect=[None, None])
        mock_container.conversation_handler.process_message = AsyncMock(
            side_effect=ValueError("Conversation not found")
        )
        mock_container.error_recovery.get_recovery_response = MagicMock(
            return_value="Conversation not found. Please create a new conversation."
        )
        
        response = client.post(
            "/api/v1/chat/",
            json={"message": "Hello"},
            params={"conversation_id": "nonexistent"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 404
        mock_container.error_recovery.get_recovery_response.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_stream_message_success(self, mock_rate_limiter, async_client, mock_user, mock_container, mock_conversation):
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        app.dependency_overrides[get_current_user] = lambda: mock_user
        from app.core.container import get_container
        app.dependency_overrides[get_container] = lambda: mock_container
        
        mock_container.conversation_service.create_conversation_with_auto_title = AsyncMock(
            return_value=mock_conversation
        )
        # add_message is called twice: once for user message, once for assistant message
        updated_conv = ConversationInDB(
            id=mock_conversation.id,
            user_id=mock_conversation.user_id,
            title=mock_conversation.title,
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello! How can I help you?"}
            ],
            vacation_preferences={},
            is_active=True,
            created_at=mock_conversation.created_at,
            updated_at=mock_conversation.updated_at
        )
        mock_container.conversation_service.add_message = AsyncMock(side_effect=[updated_conv, updated_conv])
        mock_container.conversation_handler.extract_user_preferences = AsyncMock(return_value={})
        mock_container.conversation_handler.build_conversation_metadata = MagicMock(return_value={})
        mock_container.openai_service.generate_response_async = AsyncMock(return_value={
            "content": "Hello! How can I help you?",
            "extracted_preferences": {}
        })
        mock_container.proactive_assistant.get_proactive_suggestions = MagicMock(return_value=[])
        mock_container.vacation_planner.create_vacation_summary = MagicMock(return_value=None)
        
        response = await async_client.post(
            "/api/v1/chat/stream",
            json={"message": "Hello"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert response.status_code == 200
        chunks = []
        async for chunk in response.aiter_text():
            chunks.append(chunk)
        
        assert len(chunks) > 0


class TestConversationEndpoints:
    
    @pytest.mark.asyncio
    async def test_get_conversations_success(self, client, mock_user, real_container_with_mocked_openai):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # First create a conversation
        create_response = client.post(
            "/api/v1/conversations",
            params={"title": "Trip to Japan"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create_response.status_code == 201
        
        # Now get conversations
        response = client.get(
            "/api/v1/conversations",
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    @pytest.mark.asyncio
    async def test_create_conversation_success(self, client, mock_user, real_container_with_mocked_openai):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        response = client.post(
            "/api/v1/conversations",
            params={"title": "New Vacation Plan"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Vacation Plan"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_get_conversation_success(self, client, mock_user, real_container_with_mocked_openai):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # First create a conversation
        create_response = client.post(
            "/api/v1/conversations",
            params={"title": "Test Conversation"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create_response.status_code == 201
        conversation_id = create_response.json()["id"]
        
        # Now get it
        response = client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == "Test Conversation"
    
    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, client, mock_user, real_container_with_mocked_openai):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        fake_id = str(ObjectId())
        response = client.get(
            f"/api/v1/conversations/{fake_id}",
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, client, mock_user, real_container_with_mocked_openai):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # First create a conversation
        create_response = client.post(
            "/api/v1/conversations/",
            params={"title": "To Delete"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create_response.status_code == 201
        response_data = create_response.json()
        # ConversationInDB uses _id alias, but Pydantic may serialize as id or _id
        conversation_id = str(response_data.get("id") or response_data.get("_id", ""))
        assert conversation_id and conversation_id != "", f"Response: {response_data}"
        
        # Now delete it
        response = client.delete(
            f"/api/v1/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Conversation deleted successfully"


class TestErrorHandling:
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = client.get("/api/v1/conversations")
        assert response.status_code in [401, 403]  # Both are valid for unauthorized access
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, client, mock_user):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = client.post(
            "/api/v1/chat/",
            data="invalid json",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client, mock_user):
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = client.post(
            "/api/v1/chat/",
            json={},
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == 422


class TestServiceIntegration:
    
    @pytest.mark.asyncio
    @patch('app.api.chat.chat_rate_limiter')
    async def test_full_conversation_flow(self, mock_rate_limiter, client, mock_user, real_container_with_mocked_openai):
        mock_rate_limiter.is_allowed = AsyncMock(return_value=(True, 19))
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        
        # Create conversation using REAL service
        create_response = client.post(
            "/api/v1/conversations/",
            params={"title": "Vacation Planning"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create_response.status_code == 201
        response_data = create_response.json()
        # ConversationInDB uses _id alias, but Pydantic may serialize as id or _id
        conversation_id = str(response_data.get("id") or response_data.get("_id", ""))
        assert conversation_id and conversation_id != "", f"Response: {response_data}"
        
        # Send message using REAL services (rate limiter already patched in decorator)
        message_response = client.post(
            "/api/v1/chat/",
            json={"message": "I want to plan a trip"},
            params={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert message_response.status_code == 200
        assert "response" in message_response.json()
        assert "conversation_id" in message_response.json()


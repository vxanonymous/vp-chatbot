import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId
from fastapi.testclient import TestClient
from app.main import app
from app.models.conversation_db import ConversationInDB, ConversationSummary
from app.auth.dependencies import get_current_user
from app.core.container import get_container

# Use real services for integration tests
pytest_plugins = ['tests.integration.conftest_integration']

pytestmark = pytest.mark.asyncio


class TestAPISoftDeleteIntegration:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, mock_user, real_container_with_mocked_openai):
        # Set up and tear down dependency overrides for each test
        # Use real services instead of mocks
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: real_container_with_mocked_openai
        yield
        # Clean up dependency overrides after each test
        app.dependency_overrides.clear()
    
    # Override mock_user to use real user from database
    @pytest.fixture
    def real_user(self, real_container_with_mocked_openai):
        # Create a real user in the test database
        from app.models.user import UserCreate
        import asyncio
        
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="SecurePass123!"
        )
        
        user = asyncio.run(real_container_with_mocked_openai.user_service.create_user(user_data))
        
        from app.models.user import TokenData
        return TokenData(
            user_id=str(user.id),
            email=user.email
        )
    
    @pytest.fixture
    def client(self):
    # Create test client.
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user.
        from app.models.user import TokenData
        return TokenData(
            user_id=str(ObjectId()),
            email="test@example.com"
        )
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        return ConversationInDB(
            id=ObjectId(),
            user_id="user123",
            title="Test Conversation",
            messages=[],
            vacation_preferences={},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_conversation_service(self):
        # Provide a basic mock service for API endpoint tests that expect mocked services
        service = MagicMock()
        service.delete_conversation = AsyncMock(return_value=True)
        from datetime import datetime, timezone
        service.get_user_conversations = AsyncMock(return_value=[
            {
                "id": "conv_active",
                "title": "Active Conversation",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "message_count": 0
            }
        ])
        return service
    
    @pytest.fixture
    def mock_container(self, mock_conversation_service):
    # Create a mock service container.
        container = MagicMock()
        container.conversation_service = mock_conversation_service
        return container
    
    async def test_delete_conversation_endpoint_soft_delete(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        valid_conv_id = "507f1f77bcf86cd799439011"
        
        # Make DELETE request
        app.dependency_overrides[get_container] = lambda: mock_container
        response = client.delete(f"/api/v1/conversations/{valid_conv_id}")
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["message"] == "Conversation deleted successfully"
        
        # Verify service method was called
        call_args = mock_container.conversation_service.delete_conversation.call_args
        assert call_args is not None
        assert call_args[1]["conversation_id"] == valid_conv_id
        assert call_args[1]["user_id"] == str(mock_user.user_id)
    
    async def test_get_conversations_filters_active_only(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        # Make GET request
        app.dependency_overrides[get_container] = lambda: mock_container
        response = client.get("/api/v1/conversations/")
        
        # Verify response
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 1
        assert conversations[0]["title"] == "Active Conversation"
        
        # Verify service method was called
        call_args = mock_container.conversation_service.get_user_conversations.call_args
        assert call_args is not None
        # Should be called with user_id as a string
        assert str(mock_user.user_id) in call_args[0] or str(mock_user.user_id) in call_args[1].values()
    
    async def test_delete_conversation_not_found(
        self, 
        client, 
        real_user, 
        real_container_with_mocked_openai
    ):
        fake_id = str(ObjectId())
        
        # Make DELETE request
        response = client.delete(f"/api/v1/conversations/{fake_id}")
        
        # Verify response
        assert response.status_code == 404
        # Our new human-like error message
        assert "We couldn't find that conversation" in response.json()["detail"]
    
    async def test_get_conversation_after_soft_delete(
        self, 
        client, 
        real_user, 
        real_container_with_mocked_openai
    ):
        # Create a conversation
        create_response = client.post(
            "/api/v1/conversations",
            params={"title": "To Soft Delete"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create_response.status_code == 201
        conversation_id = create_response.json()["id"]
        
        # Delete it (soft delete)
        delete_response = client.delete(f"/api/v1/conversations/{conversation_id}")
        assert delete_response.status_code == 200
        
        # Try to get it - should return 404 because soft-deleted conversations are filtered
        response = client.get(f"/api/v1/conversations/{conversation_id}")
        
        # The API filters out soft-deleted conversations, so it returns 404
        assert response.status_code == 404
    
    async def test_create_conversation_sets_active_true(
        self, 
        client, 
        real_user, 
        real_container_with_mocked_openai
    ):
        # Make POST request
        response = client.post(
            "/api/v1/conversations/",
            params={"title": "New Test Conversation"}
        )
        
        # Verify response
        assert response.status_code == 201
        conversation = response.json()
        assert conversation["title"] == "New Test Conversation"
        assert conversation["is_active"] is True
    
    async def test_update_conversation_preserves_active_status(
        self, 
        client, 
        real_user, 
        real_container_with_mocked_openai
    ):
        # First create a conversation
        create_response = client.post(
            "/api/v1/conversations",
            params={"title": "Original Title"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create_response.status_code == 201
        conversation_id = create_response.json()["id"]
        assert create_response.json()["is_active"] is True
        
        # Update it
        response = client.put(
            f"/api/v1/conversations/{conversation_id}",
            json={"title": "Updated Conversation"}
        )
        
        # Verify response
        assert response.status_code == 200
        conversation = response.json()
        assert conversation["title"] == "Updated Conversation"
        assert conversation["is_active"] is True
    
    async def test_conversation_list_excludes_inactive(
        self, 
        client, 
        real_user, 
        real_container_with_mocked_openai
    ):
        # Create two active conversations
        create1 = client.post(
            "/api/v1/conversations",
            params={"title": "Active Conversation 1"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create1.status_code == 201
        
        create2 = client.post(
            "/api/v1/conversations",
            params={"title": "Active Conversation 2"},
            headers={"Authorization": f"Bearer fake_token"}
        )
        assert create2.status_code == 201
        
        # Delete one (soft delete) - remove the second conversation
        conv2_id = create2.json()["id"]
        delete_response = client.delete(f"/api/v1/conversations/{conv2_id}")
        assert delete_response.status_code == 200
        
        # Get conversations - should only return active ones
        response = client.get("/api/v1/conversations/")
        
        # Verify response
        assert response.status_code == 200
        conversations = response.json()
        # Should have at least 1 active conversation (the one we didn't delete)
        assert len(conversations) == 1
        assert conversations[0]["title"] == "Active Conversation 1"
    
    async def test_unauthorized_delete_conversation(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        mock_container.conversation_service.delete_conversation.return_value = False
        
        # Make DELETE request for conversation owned by different user
        app.dependency_overrides[get_container] = lambda: mock_container
        response = client.delete("/api/v1/conversations/other_user_conv")
        
        # Verify response
        assert response.status_code == 404
        # Our new human-like error message
        assert "We couldn't find that conversation" in response.json()["detail"]
    
    async def test_delete_conversation_service_error(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        mock_container.conversation_service.delete_conversation.side_effect = Exception("Database error")
        
        # Make DELETE request
        app.dependency_overrides[get_container] = lambda: mock_container
        response = client.delete("/api/v1/conversations/conv1")
        
        # Verify response
        assert response.status_code == 500
        # Our new human-like error message
        assert "Sorry, we couldn't delete that conversation" in response.json()["detail"] 
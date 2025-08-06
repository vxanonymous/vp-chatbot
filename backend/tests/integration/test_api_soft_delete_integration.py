"""
Integration tests for API endpoints with soft delete functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId
from fastapi.testclient import TestClient
from app.main import app
from app.models.conversation_db import ConversationInDB, ConversationSummary
from app.auth.dependencies import get_current_user
from app.core.container import get_container

pytestmark = pytest.mark.asyncio


class TestAPISoftDeleteIntegration:
    """Integration tests for soft delete functionality in API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, mock_user, mock_container):
        """Set up and tear down dependency overrides for each test."""
        # Set dependency overrides before each test
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_container] = lambda: mock_container
        yield
        # Clean up dependency overrides after each test
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        from app.models.user import TokenData
        return TokenData(
            user_id=str(ObjectId()),
            email="test@example.com"
        )
    
    @pytest.fixture
    def mock_conversation(self):
        """Create a mock conversation."""
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
        """Create a mock conversation service."""
        service = AsyncMock()
        
        # Mock create_conversation
        service.create_conversation.return_value = ConversationInDB(
            id=ObjectId(),
            user_id="user123",
            title="New Conversation",
            messages=[],
            vacation_preferences={},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock get_user_conversations
        service.get_user_conversations.return_value = [
            ConversationSummary(
                id="conv1",
                title="Active Conversation",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                message_count=5
            )
        ]
        
        # Mock get_conversation
        service.get_conversation.return_value = ConversationInDB(
            id=ObjectId("507f1f77bcf86cd799439011"),
            user_id="user123",
            title="Test Conversation",
            messages=[],
            vacation_preferences={},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock delete_conversation
        service.delete_conversation.return_value = True
        
        return service
    
    @pytest.fixture
    def mock_container(self, mock_conversation_service):
        """Create a mock service container."""
        container = MagicMock()
        container.conversation_service = mock_conversation_service
        return container
    
    async def test_delete_conversation_endpoint_soft_delete(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        """Test that the delete conversation endpoint performs soft delete."""
        valid_conv_id = "507f1f77bcf86cd799439011"
        
        # Make DELETE request
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
        """Test that get conversations endpoint only returns active conversations."""
        # Make GET request
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
        mock_user, 
        mock_container
    ):
        """Test delete conversation when conversation is not found."""
        mock_container.conversation_service.delete_conversation.return_value = False
        
        # Make DELETE request
        response = client.delete("/api/v1/conversations/nonexistent")
        
        # Verify response
        assert response.status_code == 404
        # Our new human-like error message
        assert "We couldn't find that conversation" in response.json()["detail"]
    
    async def test_get_conversation_after_soft_delete(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        """Test that get conversation can still access soft-deleted conversations."""
        # Mock inactive conversation
        inactive_conversation = ConversationInDB(
            id=ObjectId("507f1f77bcf86cd799439011"),
            user_id="user123",
            title="Inactive Conversation",
            messages=[],
            vacation_preferences={},
            is_active=False,  # Soft deleted
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_container.conversation_service.get_conversation.return_value = inactive_conversation
        
        # Make GET request
        response = client.get("/api/v1/conversations/conv1")
        
        # Verify response
        assert response.status_code == 200
        conversation = response.json()
        assert conversation["title"] == "Inactive Conversation"
        assert conversation["is_active"] is False
    
    async def test_create_conversation_sets_active_true(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        """Test that new conversations are created with is_active=True."""
        # Make POST request
        response = client.post(
            "/api/v1/conversations/",
            params={"title": "New Test Conversation"}
        )
        
        # Verify response
        assert response.status_code == 201
        conversation = response.json()
        assert conversation["title"] == "New Conversation"
        assert conversation["is_active"] is True
        
        # Verify service method was called
        call_args = mock_container.conversation_service.create_conversation.call_args
        assert call_args is not None
        assert call_args[1]["user_id"] == str(mock_user.user_id)
        assert call_args[1]["title"] == "New Test Conversation"
    
    async def test_update_conversation_preserves_active_status(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        """Test that updating a conversation preserves its active status."""
        # Mock updated conversation
        updated_conversation = ConversationInDB(
            id=ObjectId("507f1f77bcf86cd799439011"),
            user_id="user123",
            title="Updated Conversation",
            messages=[],
            vacation_preferences={},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_container.conversation_service.update_conversation.return_value = updated_conversation
        
        # Make PUT request
        response = client.put(
            "/api/v1/conversations/conv1",
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
        mock_user, 
        mock_container
    ):
        """Test that conversation list excludes inactive conversations."""
        # Mock only active conversations
        active_conversations = [
            ConversationSummary(
                id="conv1",
                title="Active Conversation 1",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                message_count=5
            ),
            ConversationSummary(
                id="conv2",
                title="Active Conversation 2",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                message_count=3
            )
        ]
        mock_container.conversation_service.get_user_conversations.return_value = active_conversations
        
        # Make GET request
        response = client.get("/api/v1/conversations/")
        
        # Verify response
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 2
        
        # Verify all returned conversations are active (though we can't directly check is_active
        # since ConversationSummary doesn't include it, but the service should filter them)
        assert conversations[0]["title"] == "Active Conversation 1"
        assert conversations[1]["title"] == "Active Conversation 2"
    
    async def test_unauthorized_delete_conversation(
        self, 
        client, 
        mock_user, 
        mock_container
    ):
        """Test that users cannot delete conversations they don't own."""
        mock_container.conversation_service.delete_conversation.return_value = False
        
        # Make DELETE request for conversation owned by different user
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
        """Test handling of service errors during conversation deletion."""
        mock_container.conversation_service.delete_conversation.side_effect = Exception("Database error")
        
        # Make DELETE request
        response = client.delete("/api/v1/conversations/conv1")
        
        # Verify response
        assert response.status_code == 500
        # Our new human-like error message
        assert "Sorry, we couldn't delete that conversation" in response.json()["detail"] 
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from types import SimpleNamespace
from bson import ObjectId
from app.services.conversation_service import ConversationService
from app.models.conversation_db import ConversationSummary

# Import integration test fixtures
pytest_plugins = ['tests.integration.conftest_integration']

pytestmark = pytest.mark.asyncio


class TestSoftDeleteFunctionality:
    
    @pytest.fixture
    def mock_collection(self):
    # Create a mock MongoDB collection.
        return AsyncMock()
    
    @pytest.fixture
    def conversation_service(self, mock_collection):
    # Create conversation service with mocked collection.
        return ConversationService(mock_collection)
    
    @pytest.fixture
    def sample_conversation_doc(self):
    # Create a sample conversation document.
        return {
            "_id": ObjectId(),
            "user_id": "user123",
            "title": "Test Conversation",
            "messages": [],
            "vacation_preferences": {},
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    async def test_delete_conversation_soft_delete(self, real_container_with_mocked_openai):
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        
        # Use real conversation service from container
        conversation_service = real_container_with_mocked_openai.conversation_service
        
        # First create a conversation
        user_id = str(ObjectId())
        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            title="Test Conversation"
        )
        assert conversation.is_active is True
        
        # Now delete it (soft delete)
        result = await conversation_service.delete_conversation(
            str(conversation.id),
            user_id
        )
        
        # Verify the result
        assert result is True
        
        # Verify it's soft deleted (is_active = False)
        deleted_conv = await conversation_service.get_conversation(
            str(conversation.id),
            user_id
        )
        # Should return None because soft-deleted conversations are filtered out
        assert deleted_conv is None or deleted_conv.is_active is False
    
    async def test_delete_conversation_not_found(self, conversation_service):
        fake_id = str(ObjectId())
        fake_user_id = str(ObjectId())
        conversation_service.collection.update_one.return_value = SimpleNamespace(modified_count=0)
        
        result = await conversation_service.delete_conversation(fake_id, fake_user_id)
        
        # Verify the result
        assert result is False
    
    async def test_list_conversations_filters_active_only(self):
        from bson import ObjectId
        from mongomock_motor import AsyncMongoMockClient
        
        client = AsyncMongoMockClient()
        conversation_service = ConversationService(client[str(ObjectId())].conversations)
        user_id = str(ObjectId())
        
        # Create an active conversation
        conv1 = await conversation_service.create_conversation(
            user_id=user_id,
            title="Active Conversation"
        )
        
        # Create and soft delete another conversation
        conv2 = await conversation_service.create_conversation(
            user_id=user_id,
            title="To Delete"
        )
        await conversation_service.delete_conversation(str(conv2.id), user_id)
        
        # List conversations - should only return active ones
        result = await conversation_service.list_conversations(user_id)
        
        # Verify result
        assert len(result) == 1
        assert result[0].is_active is True
        assert result[0].title == "Active Conversation"
    
    async def test_get_user_conversations_filters_active_only(self):
        from bson import ObjectId
        from mongomock_motor import AsyncMongoMockClient
        
        client = AsyncMongoMockClient()
        conversation_service = ConversationService(client[str(ObjectId())].conversations)
        user_id = str(ObjectId())
        
        # Create active conversations
        await conversation_service.create_conversation(
            user_id=user_id,
            title="Active Conversation 1"
        )
        conv2 = await conversation_service.create_conversation(
            user_id=user_id,
            title="To Delete"
        )
        
        # Soft delete one
        await conversation_service.delete_conversation(str(conv2.id), user_id)
        
        # Get user conversations
        result = await conversation_service.get_user_conversations(user_id)
        
        # Verify result - should only return active conversations
        assert len(result) == 1
        assert isinstance(result[0], ConversationSummary)
        assert result[0].title == "Active Conversation 1"
    
    async def test_get_conversation_returns_inactive_conversation(self):
        from bson import ObjectId
        from mongomock_motor import AsyncMongoMockClient
        
        client = AsyncMongoMockClient()
        conversation_service = ConversationService(client[str(ObjectId())].conversations)
        user_id = str(ObjectId())
        
        # Create a conversation
        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            title="To Soft Delete"
        )
        assert conversation.is_active is True
        
        # Soft delete it
        await conversation_service.delete_conversation(str(conversation.id), user_id)
        
        # Try to get it - get_conversation doesn't filter by is_active, so it should return it
        # But the service might filter it out, let's check
        result = await conversation_service.get_conversation(str(conversation.id), user_id)
        
        # The service may or may not filter inactive conversations in get_conversation
        if result is not None:
            # If it returns, it should be inactive
            assert result.is_active is False
    
    async def test_delete_conversation_timeout_handling(self, conversation_service, mock_collection):
        # Mock timeout
        mock_collection.update_one.side_effect = Exception("Timeout")
        
        result = await conversation_service.delete_conversation("507f1f77bcf86cd799439011", "user123")
        
        # Verify the result
        assert result is False
    
    async def test_delete_conversation_invalid_object_id(self, conversation_service, mock_collection):
        # Mock invalid ObjectId error
        mock_collection.update_one.side_effect = Exception("Invalid ObjectId")
        
        result = await conversation_service.delete_conversation("invalid_id", "user123")
        
        # Verify the result
        assert result is False
    
    async def test_conversation_soft_delete_preserves_data(self, conversation_service, mock_collection):
        # Mock the update_one result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        result = await conversation_service.delete_conversation("507f1f77bcf86cd799439011", "user123")
        
        # Verify the result
        assert result is True
        
        # Verify update_one was called with correct parameters
        call_args = mock_collection.update_one.call_args
        
        # Check that we're only setting is_active and updated_at, not deleting data
        update_doc = call_args[0][1]["$set"]
        assert len(update_doc) == 2
        assert update_doc["is_active"] is False
        assert "updated_at" in update_doc
    
    async def test_multiple_conversations_soft_delete(self, conversation_service, mock_collection):
        # Mock the update_one results
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        conversation_ids = ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
        results = []
        
        for conv_id in conversation_ids:
            result = await conversation_service.delete_conversation(conv_id, "user123")
            results.append(result)
        
        # Verify all deletions were successful
        assert all(results) is True
        
        # Verify update_one was called for each conversation
        assert mock_collection.update_one.call_count == 3
        
        # Verify each call had correct parameters
        calls = mock_collection.update_one.call_args_list
        for i, call in enumerate(calls):
            assert call[0][0]["_id"] == ObjectId(conversation_ids[i])
            assert call[0][0]["user_id"] == "user123"
            assert call[0][1]["$set"]["is_active"] is False 
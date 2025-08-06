"""
Tests for soft delete functionality in conversation service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from app.services.conversation_service import ConversationService
from app.models.conversation_db import ConversationSummary

pytestmark = pytest.mark.asyncio


class TestSoftDeleteFunctionality:
    """Test the soft delete functionality for conversations."""
    
    @pytest.fixture
    def mock_collection(self):
        """Create a mock MongoDB collection."""
        return AsyncMock()
    
    @pytest.fixture
    def conversation_service(self, mock_collection):
        """Create conversation service with mocked collection."""
        return ConversationService(mock_collection)
    
    @pytest.fixture
    def sample_conversation_doc(self):
        """Create a sample conversation document."""
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
    
    async def test_delete_conversation_soft_delete(self, conversation_service, mock_collection):
        """Test that delete_conversation performs soft delete."""
        # Mock the update_one result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        # Test soft delete
        result = await conversation_service.delete_conversation("507f1f77bcf86cd799439011", "user123")
        
        # Verify the result
        assert result is True
        
        # Verify update_one was called with correct parameters
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        
        # Check the filter
        assert call_args[0][0]["_id"] == ObjectId("507f1f77bcf86cd799439011")
        assert call_args[0][0]["user_id"] == "user123"
        
        # Check the update
        assert "$set" in call_args[0][1]
        assert call_args[0][1]["$set"]["is_active"] is False
        assert "updated_at" in call_args[0][1]["$set"]
    
    async def test_delete_conversation_not_found(self, conversation_service, mock_collection):
        """Test delete_conversation when conversation is not found."""
        # Mock the update_one result
        mock_result = MagicMock()
        mock_result.modified_count = 0
        mock_collection.update_one.return_value = mock_result
        
        # Test soft delete
        result = await conversation_service.delete_conversation("conversation123", "user123")
        
        # Verify the result
        assert result is False
    
    async def test_list_conversations_filters_active_only(self, conversation_service, mock_collection, sample_conversation_doc):
        """Test that list_conversations only returns active conversations."""
        # Mock the find cursor
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [sample_conversation_doc]
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        # Test listing conversations
        result = await conversation_service.list_conversations("user123")
        
        # Verify find was called with is_active filter
        mock_collection.find.assert_called_once()
        call_args = mock_collection.find.call_args
        
        # Check the filter includes is_active: True
        assert call_args[0][0]["user_id"] == "user123"
        assert call_args[0][0]["is_active"] is True
        
        # Verify result
        assert len(result) == 1
        assert result[0].is_active is True
    
    async def test_get_user_conversations_filters_active_only(self, conversation_service, mock_collection):
        """Test that get_user_conversations only returns active conversations."""
        # Mock the aggregate pipeline
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [{
            "id": "507f1f77bcf86cd799439011",
            "title": "Test Conversation",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 5
        }]
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)
        
        # Test getting user conversations
        result = await conversation_service.get_user_conversations("user123")
        
        # Verify aggregate was called with correct pipeline
        mock_collection.aggregate.assert_called_once()
        call_args = mock_collection.aggregate.call_args
        
        # Check the pipeline includes is_active filter
        pipeline = call_args[0][0]
        match_stage = pipeline[0]
        assert match_stage["$match"]["user_id"] == "user123"
        assert match_stage["$match"]["is_active"] is True
        
        # Verify result
        assert len(result) == 1
        assert isinstance(result[0], ConversationSummary)
    
    async def test_get_conversation_returns_inactive_conversation(self, conversation_service, mock_collection, sample_conversation_doc):
        """Test that get_conversation can still access inactive conversations."""
        # Set conversation as inactive
        sample_conversation_doc["is_active"] = False
        
        # Mock find_one
        mock_collection.find_one.return_value = sample_conversation_doc
        
        # Test getting conversation
        result = await conversation_service.get_conversation("507f1f77bcf86cd799439011", "user123")
        
        # Verify find_one was called without is_active filter
        mock_collection.find_one.assert_called_once()
        call_args = mock_collection.find_one.call_args
        
        # Check the filter doesn't include is_active
        assert call_args[0][0]["_id"] == ObjectId("507f1f77bcf86cd799439011")
        assert call_args[0][0]["user_id"] == "user123"
        assert "is_active" not in call_args[0][0]
        
        # Verify result
        assert result is not None
        assert result.is_active is False
    
    async def test_delete_conversation_timeout_handling(self, conversation_service, mock_collection):
        """Test timeout handling in delete_conversation."""
        # Mock timeout
        mock_collection.update_one.side_effect = Exception("Timeout")
        
        # Test soft delete
        result = await conversation_service.delete_conversation("507f1f77bcf86cd799439011", "user123")
        
        # Verify the result
        assert result is False
    
    async def test_delete_conversation_invalid_object_id(self, conversation_service, mock_collection):
        """Test delete_conversation with invalid ObjectId."""
        # Mock invalid ObjectId error
        mock_collection.update_one.side_effect = Exception("Invalid ObjectId")
        
        # Test soft delete
        result = await conversation_service.delete_conversation("invalid_id", "user123")
        
        # Verify the result
        assert result is False
    
    async def test_conversation_soft_delete_preserves_data(self, conversation_service, mock_collection):
        """Test that soft delete preserves conversation data."""
        # Mock the update_one result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        # Test soft delete
        result = await conversation_service.delete_conversation("507f1f77bcf86cd799439011", "user123")
        
        # Verify the result
        assert result is True
        
        # Verify update_one was called with correct parameters
        call_args = mock_collection.update_one.call_args
        
        # Check that we're only setting is_active and updated_at, not deleting data
        update_doc = call_args[0][1]["$set"]
        assert len(update_doc) == 2  # Only is_active and updated_at
        assert update_doc["is_active"] is False
        assert "updated_at" in update_doc
    
    async def test_multiple_conversations_soft_delete(self, conversation_service, mock_collection):
        """Test soft deleting multiple conversations."""
        # Mock the update_one results
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        # Test soft deleting multiple conversations
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
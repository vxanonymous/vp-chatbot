"""
Comprehensive unit tests for ConversationManager service.

This module tests the ConversationManager service which handles:
- Conversation lifecycle management (create, read, update, delete)
- Message handling and storage
- Redis caching and persistence
- User preferences management
- Error handling and edge cases
- Performance and memory efficiency

The tests use mocked Redis and MongoDB to ensure isolated testing
without external dependencies.

FILE DEPENDENCIES:
==================
UTILIZES (Dependencies):
- app/services/conversation_manager.py - Main service being tested
- app/models/conversation_db.py - Conversation data models
- app/models/chat.py - Message and chat models
- app/models/object_id.py - Object ID handling
- redis - Redis client for caching
- unittest.mock - Mocking utilities
- conftest.py - Test fixtures and configuration

USED BY (Dependents):
- pytest.ini - Test configuration
- run-tests.sh - Test execution scripts
- TEST_SUMMARY.md - Test documentation
- test_integration_comprehensive.py - Integration tests
- CI/CD pipelines - Automated testing
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.conversation_manager import ConversationManager
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB


class TestConversationManager:
    """
    Test suite for ConversationManager service functionality.
    
    This class provides comprehensive testing of the conversation management
    system, including Redis caching, MongoDB persistence, and error handling.
    All external dependencies are mocked to ensure reliable, fast test execution.
    """
    
    @pytest.fixture
    def mock_redis(self):
        """
        Mock Redis client for testing.
        
        Provides a mock Redis instance that simulates Redis operations
        without requiring an actual Redis server during testing.
        """
        mock_redis = Mock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        mock_redis.delete.return_value = 1
        return mock_redis
    
    @pytest.fixture
    def conversation_manager(self, mock_redis):
        """
        Create ConversationManager with mocked Redis.
        
        Sets up a ConversationManager instance with mocked Redis dependencies
        for isolated testing without external service requirements.
        """
        with patch('app.services.conversation_manager.redis') as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            manager = ConversationManager()
            return manager, mock_redis
    
    def test_initialization(self, conversation_manager):
        """
        Test ConversationManager initialization.
        
        Verifies that:
        - Default TTL is set to 3600 seconds (1 hour)
        - Default max conversation length is 50 messages
        - Redis connection is properly established
        
        This test ensures the manager is configured with correct defaults.
        """
        manager, mock_redis = conversation_manager
        
        assert manager.ttl == 3600  # 1 hour default
        assert manager.max_length == 50  # Default max length
        assert mock_redis is not None
    
    def test_create_conversation(self, conversation_manager):
        """
        Test creating a new conversation.
        
        Verifies that:
        - A unique conversation ID is generated
        - Conversation data is properly structured in Redis
        - Default values are set correctly (empty messages, preferences)
        - Timestamps are included in the conversation data
        
        This test ensures new conversations are created with proper structure.
        """
        manager, mock_redis = conversation_manager
        
        conversation_id = manager.create_conversation()
        
        assert conversation_id is not None
        assert isinstance(conversation_id, str)
        assert len(conversation_id) > 0
        
        # Verify Redis was called with our new vacation-specific key format
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("vacation_chat:")
        assert call_args[0][1] == 3600  # TTL
        
        # Verify conversation data structure
        stored_data = json.loads(call_args[0][2])
        assert stored_data["id"] == conversation_id
        assert stored_data["messages"] == []
        assert "created_at" in stored_data
        assert "updated_at" in stored_data
        # Our new implementation provides meaningful default preferences
        assert "budget_range" in stored_data["user_preferences"]
        assert "travel_style" in stored_data["user_preferences"]
        assert "group_size" in stored_data["user_preferences"]
        assert stored_data["user_preferences"]["budget_range"] == "not_set"
        assert stored_data["user_preferences"]["travel_style"] == "not_set"
        assert stored_data["user_preferences"]["group_size"] == 1
    
    def test_create_conversation_with_id(self, conversation_manager):
        """
        Test creating a conversation with specific ID.
        
        Verifies that:
        - Conversation can be created with a predefined ID
        - The specified ID is used instead of auto-generation
        - Redis key follows the expected naming convention
        
        This test ensures conversations can be created with custom IDs when needed.
        """
        manager, mock_redis = conversation_manager
        
        specific_id = "test-conversation-123"
        conversation_id = manager.create_conversation_with_id(specific_id)
        
        assert conversation_id == specific_id
        
        # Verify Redis was called with our new vacation-specific key format
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"vacation_chat:{specific_id}"
    
    def test_load_from_mongodb(self, conversation_manager):
        """
        Test loading conversation from MongoDB into Redis.
        
        Verifies that:
        - MongoDB conversation data is properly loaded into Redis
        - All conversation fields are preserved (messages, preferences, timestamps)
        - Redis key follows the correct naming convention
        - Data structure remains consistent between MongoDB and Redis
        
        This test ensures seamless data migration from MongoDB to Redis cache.
        """
        manager, mock_redis = conversation_manager
        
        # Create mock MongoDB conversation
        mock_conversation = Mock(spec=ConversationInDB)
        mock_conversation.id = "test-id-123"
        mock_conversation.messages = [
            {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:01:00"}
        ]
        mock_conversation.created_at = datetime(2023, 1, 1)
        mock_conversation.updated_at = datetime(2023, 1, 1)
        mock_conversation.vacation_preferences = {"destination": "Paris"}
        
        manager.load_from_mongodb(mock_conversation)
        
        # Verify Redis was called with our new vacation-specific key format
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"vacation_chat:{mock_conversation.id}"
        
        # Verify data structure
        stored_data = json.loads(call_args[0][2])
        assert stored_data["id"] == mock_conversation.id
        assert len(stored_data["messages"]) == 2
        # Our new implementation merges preferences with defaults
        assert "destination" in stored_data["user_preferences"]
        assert stored_data["user_preferences"]["destination"] == "Paris"
        assert "budget_range" in stored_data["user_preferences"]
        assert "travel_style" in stored_data["user_preferences"]
    
    def test_get_conversation_not_found(self, conversation_manager):
        """
        Test getting non-existent conversation.
        
        Verifies that:
        - Attempting to retrieve a non-existent conversation returns None
        - Redis is queried with the correct key format
        - System handles missing data gracefully without errors
        
        This test ensures proper handling of missing conversation data.
        """
        manager, mock_redis = conversation_manager
        
        # Mock Redis returning None
        mock_redis.get.return_value = None
        
        result = manager.get_conversation("non-existent-id")
        
        assert result is None
        # Our new implementation tries multiple key formats, so it will be called multiple times
        assert mock_redis.get.call_count >= 1
    
    def test_get_conversation_success(self, conversation_manager):
        """
        Test getting existing conversation.
        
        Verifies that:
        - Existing conversation data is retrieved correctly from Redis
        - Message structure is preserved with all required fields
        - Timestamps and metadata are handled properly
        - Conversation data is returned in the expected format
        
        This test ensures successful retrieval of conversation data from cache.
        """
        manager, mock_redis = conversation_manager
        
        # Mock Redis returning conversation data
        conversation_data = {
            "id": "test-id-123",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2023-01-01T00:00:00",
                    "metadata": None
                },
                {
                    "role": "assistant", 
                    "content": "Hi there!",
                    "timestamp": "2023-01-01T00:01:00",
                    "metadata": None
                }
            ],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:01:00",
            "user_preferences": {"destination": "Paris"}
        }
        
        mock_redis.get.return_value = json.dumps(conversation_data)
        
        result = manager.get_conversation("test-id-123")
        
        assert result is not None
        assert result.conversation_id == "test-id-123"
        assert len(result.messages) == 2
        assert result.messages[0].role == MessageRole.USER
        assert result.messages[0].content == "Hello"
        assert result.messages[1].role == MessageRole.ASSISTANT
        assert result.messages[1].content == "Hi there!"
        assert result.user_preferences == {"destination": "Paris"}
    
    def test_get_conversation_with_metadata(self, conversation_manager):
        """Test getting conversation with message metadata."""
        manager, mock_redis = conversation_manager
        
        conversation_data = {
            "id": "test-id-123",
            "messages": [
                {
                    "role": "assistant",
                    "content": "I can help you plan your trip!",
                    "timestamp": "2023-01-01T00:00:00",
                    "metadata": {
                        "extracted_preferences": {"destination": "Paris"},
                        "confidence_score": 0.85
                    }
                }
            ],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "user_preferences": {}
        }
        
        mock_redis.get.return_value = json.dumps(conversation_data)
        
        result = manager.get_conversation("test-id-123")
        
        assert result is not None
        assert len(result.messages) == 1
        assert result.messages[0].metadata == {
            "extracted_preferences": {"destination": "Paris"},
            "confidence_score": 0.85
        }
    
    def test_add_message_success(self, conversation_manager):
        """Test adding message to conversation."""
        manager, mock_redis = conversation_manager
        
        # Mock existing conversation
        existing_data = {
            "id": "test-id-123",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2023-01-01T00:00:00",
                    "metadata": None
                }
            ],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "user_preferences": {}
        }
        
        mock_redis.get.return_value = json.dumps(existing_data)
        
        # Create message to add
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Hi there! How can I help you plan your vacation?",
            metadata={"confidence": 0.9}
        )
        
        result = manager.add_message("test-id-123", message)
        
        assert result is True
        
        # Verify Redis was called to update
        assert mock_redis.setex.call_count == 1
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert len(updated_data["messages"]) == 2
        assert updated_data["messages"][1]["role"] == "assistant"
        assert updated_data["messages"][1]["content"] == "Hi there! How can I help you plan your vacation?"
        assert updated_data["messages"][1]["metadata"] == {"confidence": 0.9}
    
    def test_add_message_conversation_not_found(self, conversation_manager):
        """Test adding message to non-existent conversation."""
        manager, mock_redis = conversation_manager
        
        # Mock Redis returning None
        mock_redis.get.return_value = None
        
        message = Message(role=MessageRole.USER, content="Hello")
        
        result = manager.add_message("non-existent-id", message)
        
        assert result is False
        # Should not call setex
        mock_redis.setex.assert_not_called()
    
    def test_add_message_respects_max_length(self, conversation_manager):
        """Test that adding messages respects max length limit."""
        manager, mock_redis = conversation_manager
        manager.max_length = 3  # Set small max length for testing
        
        # Mock conversation with max messages
        existing_data = {
            "id": "test-id-123",
            "messages": [
                {"role": "user", "content": f"Message {i}", "timestamp": "2023-01-01T00:00:00", "metadata": None}
                for i in range(3)
            ],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "user_preferences": {}
        }
        
        mock_redis.get.return_value = json.dumps(existing_data)
        
        # Add new message
        message = Message(role=MessageRole.ASSISTANT, content="New message")
        result = manager.add_message("test-id-123", message)
        
        assert result is True
        
        # Verify only the last 3 messages are kept
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        assert len(updated_data["messages"]) == 3
        assert updated_data["messages"][-1]["content"] == "New message"
    
    def test_update_user_preferences_success(self, conversation_manager):
        """Test updating user preferences."""
        manager, mock_redis = conversation_manager
        
        existing_data = {
            "id": "test-id-123",
            "messages": [],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "user_preferences": {"existing": "value"}
        }
        
        mock_redis.get.return_value = json.dumps(existing_data)
        
        new_preferences = {"destination": "Paris", "budget": "moderate"}
        result = manager.update_user_preferences("test-id-123", new_preferences)
        
        assert result is True
        
        # Verify preferences were merged
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        assert updated_data["user_preferences"]["existing"] == "value"
        assert updated_data["user_preferences"]["destination"] == "Paris"
        assert updated_data["user_preferences"]["budget"] == "moderate"
    
    def test_update_user_preferences_conversation_not_found(self, conversation_manager):
        """Test updating preferences for non-existent conversation."""
        manager, mock_redis = conversation_manager
        
        mock_redis.get.return_value = None
        
        result = manager.update_user_preferences("non-existent-id", {"test": "value"})
        
        assert result is False
        mock_redis.setex.assert_not_called()
    
    def test_delete_conversation_success(self, conversation_manager):
        """Test deleting conversation."""
        manager, mock_redis = conversation_manager
        
        result = manager.delete_conversation("test-id-123")
        
        assert result is True
        # Our new implementation tries multiple key formats, so it will be called multiple times
        assert mock_redis.delete.call_count >= 1
    
    def test_delete_conversation_not_found(self, conversation_manager):
        """Test deleting non-existent conversation."""
        manager, mock_redis = conversation_manager
        
        # Mock Redis returning 0 (not found)
        mock_redis.delete.return_value = 0
        
        result = manager.delete_conversation("non-existent-id")
        
        assert result is False
        # Our new implementation tries multiple key formats, so it will be called multiple times
        assert mock_redis.delete.call_count >= 1
    
    def test_conversation_data_persistence(self, conversation_manager):
        """Test that conversation data persists correctly."""
        manager, mock_redis = conversation_manager
        
        # Create conversation
        conversation_id = manager.create_conversation()
        
        # Verify initial data
        call_args = mock_redis.setex.call_args
        initial_data = json.loads(call_args[0][2])
        
        assert initial_data["messages"] == []
        # Check for our new human-like user preferences structure
        assert "budget_range" in initial_data["user_preferences"]
        assert "travel_style" in initial_data["user_preferences"]
        assert "group_size" in initial_data["user_preferences"]
        assert initial_data["user_preferences"]["budget_range"] == "not_set"
        assert initial_data["user_preferences"]["travel_style"] == "not_set"
        assert initial_data["user_preferences"]["group_size"] == 1
        
        # Mock getting the conversation back
        mock_redis.get.return_value = json.dumps(initial_data)
        
        # Add a message
        message = Message(role=MessageRole.USER, content="Test message")
        manager.add_message(conversation_id, message)
        
        # Verify data was updated
        assert mock_redis.setex.call_count == 2
        update_call_args = mock_redis.setex.call_args_list[1]
        updated_data = json.loads(update_call_args[0][2])
        
        assert len(updated_data["messages"]) == 1
        assert updated_data["messages"][0]["content"] == "Test message"
    
    def test_conversation_isolation(self, conversation_manager):
        """Test that conversations are isolated from each other."""
        manager, mock_redis = conversation_manager
        
        # Create two conversations
        conv1_id = manager.create_conversation()
        conv2_id = manager.create_conversation()
        
        assert conv1_id != conv2_id
        
        # Verify different Redis keys with our new vacation-specific format
        call_args = mock_redis.setex.call_args_list
        assert call_args[0][0][0] == f"vacation_chat:{conv1_id}"
        assert call_args[1][0][0] == f"vacation_chat:{conv2_id}"
    
    def test_error_handling_json_parse_error(self, conversation_manager):
        """Test handling of JSON parse errors."""
        manager, mock_redis = conversation_manager
        
        # Mock Redis returning invalid JSON
        mock_redis.get.return_value = "invalid json"
        
        result = manager.get_conversation("test-id")
        
        assert result is None
    
    def test_error_handling_missing_fields(self, conversation_manager):
        """Test handling of conversations with missing fields."""
        manager, mock_redis = conversation_manager
        
        # Mock conversation with missing fields
        incomplete_data = {
            "id": "test-id-123",
            "messages": []
            # Missing created_at, updated_at, user_preferences, vacation_session
        }
        
        mock_redis.get.return_value = json.dumps(incomplete_data)
        
        result = manager.get_conversation("test-id-123")
        
        # Should handle gracefully - the actual implementation returns None for missing fields
        assert result is None  # The service correctly handles missing required fields
    
    def test_message_metadata_handling(self, conversation_manager):
        """Test handling of message metadata."""
        manager, mock_redis = conversation_manager
        
        existing_data = {
            "id": "test-id-123",
            "messages": [],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "user_preferences": {
                "budget_range": "not_set",
                "travel_style": "not_set",
                "group_size": 1,
                "preferred_destinations": [],
                "accessibility_needs": False,
                "has_pets": False,
                "preferred_weather": "not_set"
            }
        }
        
        mock_redis.get.return_value = json.dumps(existing_data)
        
        # Add message with complex metadata
        complex_metadata = {
            "extracted_preferences": {
                "destinations": ["Paris", "London"],
                "budget": "moderate"
            },
            "confidence_score": 0.95,
            "processing_time": 1.23
        }
        
        message = Message(
            role=MessageRole.ASSISTANT,
            content="I found some great destinations for you!",
            metadata=complex_metadata
        )
        
        result = manager.add_message("test-id-123", message)
        
        assert result is True
        
        # Verify metadata was preserved
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        stored_metadata = updated_data["messages"][0]["metadata"]
        
        assert stored_metadata["extracted_preferences"]["destinations"] == ["Paris", "London"]
        assert stored_metadata["confidence_score"] == 0.95
        assert stored_metadata["processing_time"] == 1.23
    
    def test_timestamp_handling(self, conversation_manager):
        """Test timestamp handling in conversations."""
        manager, mock_redis = conversation_manager
        
        # Create conversation
        conversation_id = manager.create_conversation()
        
        # Verify timestamps are present
        call_args = mock_redis.setex.call_args
        data = json.loads(call_args[0][2])
        
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify timestamps are valid ISO format
        datetime.fromisoformat(data["created_at"])
        datetime.fromisoformat(data["updated_at"])
    
    def test_redis_connection_error_handling(self, conversation_manager):
        """Test handling of Redis connection errors."""
        manager, mock_redis = conversation_manager
        
        # Mock Redis operations raising exceptions
        mock_redis.setex.side_effect = Exception("Redis connection error")
        
        # Should handle gracefully
        with pytest.raises(Exception):
            manager.create_conversation()
    
    def test_conversation_manager_performance(self, conversation_manager):
        """Test ConversationManager performance characteristics."""
        manager, mock_redis = conversation_manager
        
        # Test creating multiple conversations quickly
        start_time = datetime.now()
        
        for i in range(10):
            manager.create_conversation()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete quickly (less than 1 second for 10 operations)
        assert duration < 1.0
        assert mock_redis.setex.call_count == 10
    
    def test_conversation_manager_memory_efficiency(self, conversation_manager):
        """Test ConversationManager memory efficiency."""
        manager, mock_redis = conversation_manager
        
        # Create conversation with many messages
        existing_data = {
            "id": "test-id-123",
            "messages": [
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Message {i} with some content",
                    "timestamp": "2023-01-01T00:00:00",
                    "metadata": None
                }
                for i in range(100)
            ],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "user_preferences": {}
        }
        
        mock_redis.get.return_value = json.dumps(existing_data)
        
        # Add message (should trigger max length enforcement)
        message = Message(role=MessageRole.USER, content="New message")
        result = manager.add_message("test-id-123", message)
        
        assert result is True
        
        # Verify max length was enforced
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        assert len(updated_data["messages"]) <= manager.max_length 
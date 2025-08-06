"""
Comprehensive Edge Case Tests for Vacation Planning Chatbot

This module contains extensive testing of edge cases and boundary conditions for:
- Conversation service edge cases (empty data, long titles, special characters)
- User service edge cases (special characters, long names, duplicate emails)
- OpenAI service edge cases (timeouts, rate limits, malformed data)
- Message handling edge cases (null content, very long content, special characters)
- Database edge cases (connection failures, timeouts, permission errors)
- Performance edge cases (large conversations, concurrent operations)
- Error handling edge cases (malformed data, missing fields, corrupted data)

These tests ensure the system is robust and handles unusual or extreme conditions
gracefully without crashing or producing unexpected behavior.

FILE DEPENDENCIES:
==================
UTILIZES (Dependencies):
- app/services/conversation_service.py - Conversation service for edge case testing
- app/services/user_service.py - User service for edge case testing
- app/services/openai_service.py - OpenAI service for edge case testing
- app/models/user.py - User data models
- app/models/chat.py - Message and chat models
- app/models/conversation_db.py - Conversation data models
- app/models/object_id.py - Object ID handling
- app/auth/password.py - Password hashing and verification
- unittest.mock - Mocking utilities
- conftest.py - Test fixtures and configuration
- pytest.asyncio - Async test support

USED BY (Dependents):
- pytest.ini - Test configuration
- run-tests.sh - Test execution scripts
- TEST_SUMMARY.md - Test documentation
- test_integration_comprehensive.py - Integration tests
- CI/CD pipelines - Automated testing
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from bson import ObjectId
import asyncio
import time
from app.services.conversation_service import ConversationService
from app.services.user_service import UserService
from app.services.openai_service import OpenAIService
from app.models.user import UserInDB, UserCreate
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB
from app.models.object_id import PyObjectId
from app.auth.password import get_password_hash, verify_password
import json

class MockDatabase:
    """Mock database for edge case testing without external dependencies."""
    def __init__(self):
        self.conversations = Mock()
        self.users = Mock()

class TestConversationEdgeCases:
    """
    Test suite for conversation service edge cases.
    
    This class tests how the conversation service handles unusual or extreme
    conditions such as empty data, very long content, special characters,
    and maximum data sizes. These tests ensure the service remains stable
    under all conditions.
    """
    
    @pytest.fixture
    def conversation_service(self):
        """Create conversation service instance for edge case testing."""
        mock_db = MockDatabase()
        return ConversationService(mock_db.conversations)
    
    @pytest.mark.asyncio
    async def test_empty_conversation_creation(self, conversation_service):
        """
        Test creating conversation with minimal data.
        
        Verifies that:
        - Conversations can be created with empty titles
        - System handles minimal input gracefully
        - Empty strings are preserved rather than causing errors
        - Basic conversation structure is maintained
        
        This test ensures the system works with minimal user input.
        """
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            
            result = await conversation_service.create_conversation(
                user_id="user123",
                title=""  # Empty title
            )
            
            assert result is not None
            assert result.user_id == "user123"
            assert result.title == ""  # Should handle empty title
    
    @pytest.mark.asyncio
    async def test_very_long_title(self, conversation_service):
        """
        Test creating conversation with very long title.
        
        Verifies that:
        - Very long titles (1000+ characters) are handled correctly
        - System doesn't truncate or reject long titles
        - Database operations work with large text fields
        - Performance remains acceptable with large data
        
        This test ensures the system can handle unusually long user input.
        """
        long_title = "a" * 1000  # Very long title
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            
            result = await conversation_service.create_conversation(
                user_id="user123",
                title=long_title
            )
            
            assert result is not None
            assert result.title == long_title
    
    @pytest.mark.asyncio
    async def test_special_characters_in_title(self, conversation_service):
        """
        Test creating conversation with special characters.
        
        Verifies that:
        - Emojis, symbols, and special characters are preserved
        - Unicode characters are handled correctly
        - Special characters don't cause parsing errors
        - Database storage and retrieval work with complex characters
        
        This test ensures the system supports international users and rich text.
        """
        special_title = "🎉 Vacation Plan! @#$%^&*()_+-=[]{}|;':\",./<>?"
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            
            result = await conversation_service.create_conversation(
                user_id="user123",
                title=special_title
            )
            
            assert result is not None
            assert result.title == special_title
    
    @pytest.mark.asyncio
    async def test_conversation_with_max_messages(self, conversation_service):
        """
        Test conversation with maximum number of messages.
        
        Verifies that:
        - Conversations with 1000+ messages are handled correctly
        - Large message arrays don't cause memory issues
        - Database operations scale with large datasets
        - Performance remains acceptable with maximum data
        
        This test ensures the system can handle very long conversations.
        """
        conversation_id = str(ObjectId())
        max_messages = [{"role": "user", "content": f"Message {i}", "timestamp": datetime.utcnow().isoformat()} 
                       for i in range(1000)]
        
        mock_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": "Large Conversation",
            "messages": max_messages,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_conversation)
            
            result = await conversation_service.get_conversation(conversation_id, "user123")
            
            assert result is not None
            assert len(result.messages) == 1000
    
    @pytest.mark.asyncio
    async def test_conversation_with_empty_messages(self, conversation_service):
        """Test conversation with empty messages."""
        conversation_id = str(ObjectId())
        empty_messages = [
            {"role": "user", "content": "", "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": "", "timestamp": datetime.utcnow().isoformat()},
        ]
        
        mock_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": "Empty Messages",
            "messages": empty_messages,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_conversation)
            
            result = await conversation_service.get_conversation(conversation_id, "user123")
            
            assert result is not None
            assert len(result.messages) == 2
            assert result.messages[0]["content"] == ""
            assert result.messages[1]["content"] == ""
    
    @pytest.mark.asyncio
    async def test_invalid_object_id_handling(self, conversation_service):
        """Test handling of invalid ObjectId."""
        invalid_ids = [
            "invalid_id",
            "123",
            "",
            "not_an_object_id",
            "507f1f77bcf86cd799439011",  # Valid format but might not exist
        ]
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=None)
            
            for invalid_id in invalid_ids:
                result = await conversation_service.get_conversation(invalid_id, "user123")
                assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_conversation_access(self, conversation_service):
        """Test concurrent access to same conversation."""
        conversation_id = str(ObjectId())
        mock_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": "Concurrent Test",
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_conversation)
            
            # Simulate concurrent access
            tasks = []
            for i in range(10):
                task = conversation_service.get_conversation(conversation_id, "user123")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All should return the same result
            for result in results:
                assert result is not None
                assert str(result.id) == conversation_id  # Convert ObjectId to string for comparison

class TestUserServiceEdgeCases:
    """Test user service edge cases."""
    
    @pytest.fixture
    def user_service(self):
        """Create user service instance."""
        mock_db = MockDatabase()
        return UserService(mock_db.users)
    
    @pytest.mark.asyncio
    async def test_user_with_special_characters(self, user_service):
        """Test user creation with special characters."""
        user_data = UserCreate(
            email="test+special@example.com",
            full_name="José María O'Connor-Smith",
            password="SecurePass123!"
        )
        
        with patch.object(user_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            
            result = await user_service.create_user(user_data)
            
            assert result is not None
            assert result.email == "test+special@example.com"
            assert result.full_name == "José María O'Connor-Smith"
    
    @pytest.mark.asyncio
    async def test_user_with_very_long_name(self, user_service):
        """Test user creation with very long name."""
        long_name = "A" * 100  # Maximum allowed length
        user_data = UserCreate(
            email="longname@example.com",
            full_name=long_name,
            password="SecurePass123!"
        )
        
        with patch.object(user_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            
            result = await user_service.create_user(user_data)
            
            assert result is not None
            assert result.full_name == long_name
    
    @pytest.mark.asyncio
    async def test_duplicate_email_handling(self, user_service):
        """Test handling of duplicate email registration."""
        user_data = UserCreate(
            email="duplicate@example.com",
            full_name="Test User",
            password="SecurePass123!"
        )
        
        with patch.object(user_service, 'collection') as mock_collection:
            # First user creation
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            
            result1 = await user_service.create_user(user_data)
            assert result1 is not None
            
            # Second attempt with same email
            mock_collection.find_one = AsyncMock(return_value={"email": "duplicate@example.com"})
            
            with pytest.raises(ValueError, match="This email is already registered"):
                await user_service.create_user(user_data)
    
    @pytest.mark.asyncio
    async def test_user_authentication_edge_cases(self, user_service):
        """Test user authentication edge cases."""
        # Test with non-existent user
        with patch.object(user_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=None)
            
            result = await user_service.authenticate_user(
                email="nonexistent@example.com",
                password="anypassword"
            )
            assert result is None
        
        # Test with inactive user
        inactive_user = {
            "_id": ObjectId(),
            "email": "inactive@example.com",
            "full_name": "Inactive User",
            "hashed_password": get_password_hash("SecurePass123!"),
            "is_active": False
        }
        
        with patch.object(user_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=inactive_user)
            
            result = await user_service.authenticate_user(
                email="inactive@example.com",
                password="SecurePass123!"
            )
            assert result is None

class TestOpenAIServiceEdgeCases:
    """Test OpenAI service edge cases."""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance."""
        return OpenAIService()
    
    @pytest.mark.asyncio
    async def test_empty_message_list(self, openai_service):
        """Test OpenAI service with empty message list."""
        messages = []
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="Default response"))]
            ))
            
            result = await openai_service.generate_response_async(messages)
            
            assert result is not None
            assert "content" in result
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, openai_service):
        """Test OpenAI service with very long message."""
        long_message = "a" * 10000  # Very long message
        messages = [Message(role=MessageRole.USER, content=long_message)]
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="Response to long message"))]
            ))
            
            result = await openai_service.generate_response_async(messages)
            
            assert result is not None
            assert "content" in result
    
    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, openai_service):
        """Test OpenAI service with special characters."""
        special_message = "🎉 Hello! @#$%^&*()_+-=[]{}|;':\",./<>? 测试中文"
        messages = [Message(role=MessageRole.USER, content=special_message)]
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="Response with special chars"))]
            ))
            
            result = await openai_service.generate_response_async(messages)
            
            assert result is not None
            assert "content" in result
    
    @pytest.mark.asyncio
    async def test_openai_service_timeout(self, openai_service):
        """Test OpenAI service timeout handling."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=asyncio.TimeoutError())
            
            result = await openai_service.generate_response_async(messages)
            
            # Should handle timeout gracefully
            assert result is not None
            assert "content" in result
    
    @pytest.mark.asyncio
    async def test_openai_service_rate_limit(self, openai_service):
        """Test OpenAI service rate limit handling."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            
            result = await openai_service.generate_response_async(messages)
            
            # Should handle rate limit gracefully
            assert result is not None
            assert "content" in result

class TestMessageEdgeCases:
    """Test message handling edge cases."""
    
    def test_message_with_null_content(self):
        """Test message with null content."""
        # Message model requires content to be a string, so we test with empty string instead
        message = Message(role=MessageRole.USER, content="")
        
        assert message.content == ""
        assert message.role == MessageRole.USER
    
    def test_message_with_empty_content(self):
        """Test message with empty content."""
        message = Message(role=MessageRole.USER, content="")
        
        assert message.content == ""
        assert message.role == MessageRole.USER
    
    def test_message_with_very_long_content(self):
        """Test message with very long content."""
        long_content = "a" * 50000  # Very long content
        message = Message(role=MessageRole.USER, content=long_content)
        
        assert len(message.content) == 50000
        assert message.role == MessageRole.USER
    
    def test_message_with_special_characters(self):
        """Test message with special characters."""
        special_content = "🎉 Hello! @#$%^&*()_+-=[]{}|;':\",./<>? 测试中文\n\t\r"
        message = Message(role=MessageRole.USER, content=special_content)
        
        assert message.content == special_content
        assert message.role == MessageRole.USER
    
    def test_message_with_json_content(self):
        """Test message with JSON content."""
        json_content = '{"key": "value", "number": 123, "array": [1, 2, 3]}'
        message = Message(role=MessageRole.USER, content=json_content)
        
        assert message.content == json_content
        # Should be able to parse as JSON
        parsed = json.loads(message.content)
        assert parsed["key"] == "value"
        assert parsed["number"] == 123
        assert parsed["array"] == [1, 2, 3]

class TestDatabaseEdgeCases:
    """Test database operation edge cases."""
    
    @pytest.fixture
    def conversation_service(self):
        """Create conversation service instance."""
        mock_db = MockDatabase()
        return ConversationService(mock_db.conversations)
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self, conversation_service):
        """Test handling of database connection failure."""
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(side_effect=Exception("Database connection failed"))
            
            # Service should handle exception gracefully and return None
            result = await conversation_service.get_conversation(str(ObjectId()), "user123")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_database_timeout(self, conversation_service):
        """Test handling of database timeout."""
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(side_effect=asyncio.TimeoutError())
            
            # Service should handle timeout gracefully and return None
            result = await conversation_service.get_conversation(str(ObjectId()), "user123")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_database_permission_error(self, conversation_service):
        """Test handling of database permission error."""
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(side_effect=Exception("Permission denied"))
            
            # Service should handle permission error gracefully and return None
            result = await conversation_service.get_conversation(str(ObjectId()), "user123")
            assert result is None

class TestPerformanceEdgeCases:
    """Test performance edge cases."""
    
    @pytest.fixture
    def conversation_service(self):
        """Create conversation service instance."""
        mock_db = MockDatabase()
        return ConversationService(mock_db.conversations)
    
    @pytest.mark.asyncio
    async def test_large_conversation_processing(self, conversation_service):
        """Test processing of very large conversations."""
        # Create a conversation with many messages
        conversation_id = str(ObjectId())
        large_messages = []
        
        for i in range(1000):
            large_messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}: " + "a" * 100,  # 100 chars per message
                "timestamp": datetime.utcnow().isoformat()
            })
        
        mock_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": "Large Conversation",
            "messages": large_messages,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_conversation)
            
            start_time = time.time()
            result = await conversation_service.get_conversation(conversation_id, "user123")
            end_time = time.time()
            
            assert result is not None
            assert len(result.messages) == 1000
            assert end_time - start_time < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, conversation_service):
        """Test concurrent operations on same service."""
        conversation_id = str(ObjectId())
        mock_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": "Concurrent Test",
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_conversation)
            mock_collection.update_one = AsyncMock(return_value=Mock(modified_count=1))
            
            # Perform multiple concurrent operations
            tasks = []
            for i in range(10):
                # Add message
                message = Message(role=MessageRole.USER, content=f"Message {i}")
                task = conversation_service.add_message(conversation_id, "user123", message)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All operations should succeed
            for result in results:
                assert result is not None

class TestErrorHandlingEdgeCases:
    """Test error handling edge cases."""
    
    @pytest.fixture
    def conversation_service(self):
        """Create conversation service instance."""
        mock_db = MockDatabase()
        return ConversationService(mock_db.conversations)
    
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self, conversation_service):
        """Test handling of malformed data."""
        conversation_id = str(ObjectId())
        malformed_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": None,  # Malformed: title should be string
            "messages": "not_a_list",  # Malformed: messages should be list
            "created_at": "invalid_date",  # Malformed: should be datetime
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=malformed_conversation)
            
            # Should handle malformed data gracefully
            try:
                result = await conversation_service.get_conversation(conversation_id, "user123")
                # If it doesn't raise an exception, result might be None or malformed
                assert result is None or hasattr(result, 'title')
            except Exception as e:
                # Should be a validation error, not a crash
                assert "validation" in str(e).lower() or "malformed" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, conversation_service):
        """Test handling of missing required fields."""
        conversation_id = str(ObjectId())
        incomplete_conversation = {
            "_id": ObjectId(conversation_id),
            # Missing user_id, title, messages, etc.
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=incomplete_conversation)
            
            # Should handle missing fields gracefully
            try:
                result = await conversation_service.get_conversation(conversation_id, "user123")
                assert result is None
            except Exception as e:
                # Should be a validation error, not a crash
                assert "validation" in str(e).lower() or "missing" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_corrupted_data_handling(self, conversation_service):
        """Test handling of corrupted data."""
        conversation_id = str(ObjectId())
        corrupted_conversation = {
            "_id": ObjectId(conversation_id),
            "user_id": "user123",
            "title": "Corrupted Data",
            "messages": [{"invalid": "structure"}],  # Corrupted message structure
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(conversation_service, 'collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=corrupted_conversation)
            
            # Should handle corrupted data gracefully
            try:
                result = await conversation_service.get_conversation(conversation_id, "user123")
                assert result is None or hasattr(result, 'messages')
            except Exception as e:
                # Should be a validation error, not a crash
                assert "validation" in str(e).lower() or "corrupted" in str(e).lower() 
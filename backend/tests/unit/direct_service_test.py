import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime
from types import SimpleNamespace

class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class UpdateOneResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count

@pytest.mark.asyncio
async def test_create_conversation_direct():
    # Test creating a conversation directly using the service without global mocking.
    # Import here to avoid any global mocking
    from app.services.conversation_service import ConversationService
    
    # Create a mock collection with proper AsyncMock methods
    collection = SimpleNamespace()
    collection.create_index = AsyncMock()
    collection.insert_one = AsyncMock(return_value=InsertOneResult(ObjectId()))
    collection.find_one = AsyncMock()
    collection.find_one_and_update = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    
    # Create the service with our mock collection
    service = ConversationService(collection)
    
    # Test the service directly
    res = service.create_conversation("user123", "Test Conversation")
    print(f"DEBUG: type(res) = {type(res)}")
    result = await res
    
    # Verify the result
    assert result is not None
    assert hasattr(result, 'id')
    assert hasattr(result, 'user_id')
    assert hasattr(result, 'title')
    assert result.user_id == "user123"
    assert result.title == "Test Conversation"
    
    # Verify the mock was called
    collection.insert_one.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_conversation_direct():
    # Test getting a conversation directly using the service.
    from app.services.conversation_service import ConversationService
    
    # Create a mock collection with proper AsyncMock methods
    collection = SimpleNamespace()
    collection.create_index = AsyncMock()
    mock_conversation_doc = {
        "_id": ObjectId(),
        "user_id": "user123",
        "title": "Test Conversation",
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    # Ensure find_one is an AsyncMock
    collection.find_one = AsyncMock(return_value=mock_conversation_doc)
    collection.insert_one = AsyncMock()
    collection.find_one_and_update = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    
    # Create the service with our mock collection
    service = ConversationService(collection)
    
    # Test the service directly
    result = await service.get_conversation(str(mock_conversation_doc["_id"]), "user123")
    
    # Verify the result
    assert result is not None
    assert hasattr(result, 'id')
    assert hasattr(result, 'user_id')
    assert hasattr(result, 'title')
    
    # Verify the mock was called
    collection.find_one.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_message_direct():
    # Test adding a message directly using the service.
    from app.services.conversation_service import ConversationService
    
    # Create a mock collection with proper AsyncMock methods
    collection = SimpleNamespace()
    collection.create_index = AsyncMock()
    mock_updated_doc = {
        "_id": ObjectId(),
        "user_id": "user123",
        "title": "Test Conversation",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    # update_one returns an object with modified_count=1
    collection.update_one = AsyncMock(return_value=UpdateOneResult(1))
    collection.find_one = AsyncMock(return_value=mock_updated_doc)
    collection.insert_one = AsyncMock()
    collection.find_one_and_update = AsyncMock()
    collection.delete_one = AsyncMock()
    
    # Create the service with our mock collection
    service = ConversationService(collection)
    
    # Test the service directly
    message = MagicMock()
    message.dict.return_value = {"role": "assistant", "content": "Hi there!"}
    result = await service.add_message(str(mock_updated_doc["_id"]), "user123", message)
    
    # Verify the result
    assert result is not None
    assert hasattr(result, 'id')
    assert hasattr(result, 'user_id')
    assert hasattr(result, 'title')
    
    # Verify the mock was called
    collection.update_one.assert_awaited_once() 
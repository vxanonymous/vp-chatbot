from app.core.exceptions import DatabaseError
from app.core.exceptions import NotFoundError
from app.models.conversation_db import ConversationUpdate
from app.models.object_id import PyObjectId
from bson import ObjectId
from datetime import datetime, timezone
from app.api.conversations import (
    create_conversation,
    update_conversation,
    patch_conversation,
    get_conversations,
    get_conversation,
    delete_conversation
)
from app.core.container import ServiceContainer
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB, ConversationSummary
from app.models.conversation_db import ConversationInDB, ConversationUpdate
from app.models.user import TokenData
from fastapi import HTTPException, status
from unittest.mock import AsyncMock, MagicMock
import pytest

class TestConversationsAPI:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_service = MagicMock()
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.fixture
    def mock_conversation_summaries(self):
    # Create mock conversation summaries.
        from datetime import datetime, timezone
        return [
            ConversationSummary(
                id="conv_1",
                title="Conversation 1",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                message_count=5
            ),
            ConversationSummary(
                id="conv_2",
                title="Conversation 2",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                message_count=3
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_conversations_success(self, mock_user, mock_container, mock_conversation_summaries):
        mock_container.conversation_service.get_user_conversations = AsyncMock(return_value=mock_conversation_summaries)
        
        result = await get_conversations(
            current_user=mock_user,
            container=mock_container
        )
        
        assert len(result) == 2
        assert result[0].title == "Conversation 1"
        mock_container.conversation_service.get_user_conversations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversations_empty(self, mock_user, mock_container):
        mock_container.conversation_service.get_user_conversations = AsyncMock(return_value=[])
        
        result = await get_conversations(
            current_user=mock_user,
            container=mock_container
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_conversations_pagination(self, mock_user, mock_container, mock_conversation_summaries):
        mock_container.conversation_service.get_user_conversations = AsyncMock(return_value=mock_conversation_summaries[:1])
        
        result = await get_conversations(
            current_user=mock_user,
            container=mock_container
        )
        
        assert len(result) == 1
        mock_container.conversation_service.get_user_conversations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation_success(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=mock_conversation)
        
        result = await get_conversation(
            conversation_id=str(mock_conversation.id),
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.title == "Test Conversation"
        assert result.user_id == "test_user_123"
        mock_container.conversation_service.get_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_user, mock_container):
        from app.core.exceptions import NotFoundError
        mock_container.conversation_service.get_conversation = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation(
                conversation_id="nonexistent",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, mock_user, mock_container):
        mock_container.conversation_service.delete_conversation = AsyncMock(return_value=True)
        
        result = await delete_conversation(
            conversation_id="conv_123",
            current_user=mock_user,
            container=mock_container
        )
        
        assert result["message"] == "Conversation deleted successfully"
        mock_container.conversation_service.delete_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, mock_user, mock_container):
        from app.core.exceptions import NotFoundError
        mock_container.conversation_service.delete_conversation = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_conversation(
                conversation_id="nonexistent",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_delete_conversation_error(self, mock_user, mock_container):
        from app.core.exceptions import DatabaseError
        mock_container.conversation_service.delete_conversation = AsyncMock(side_effect=DatabaseError("DB error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_conversation(
                conversation_id="conv_123",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

class TestConversationsAPIAdditional:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_service = MagicMock()
        return container
    
    @pytest.fixture
    def mock_conversation(self):
    # Create a mock conversation.
        from datetime import datetime, timezone
        from app.models.object_id import PyObjectId
        from bson import ObjectId
        return ConversationInDB(
            id=PyObjectId(ObjectId()),
            user_id="test_user_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_create_conversation_success(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation = AsyncMock(return_value=mock_conversation)
        
        result = await create_conversation(
            title="New Conversation",
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.title == "Test Conversation"
        mock_container.conversation_service.create_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_conversation_default_title(self, mock_user, mock_container, mock_conversation):
        mock_container.conversation_service.create_conversation = AsyncMock(return_value=mock_conversation)
        
        result = await create_conversation(
            current_user=mock_user,
            container=mock_container
        )
        
        assert result is not None
        mock_container.conversation_service.create_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_conversation_error(self, mock_user, mock_container):
        mock_container.conversation_service.create_conversation = AsyncMock(side_effect=Exception("DB error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await create_conversation(
                title="New Conversation",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_update_conversation_success(self, mock_user, mock_container, mock_conversation):
        updated_conversation = mock_conversation
        updated_conversation.title = "Updated Title"
        mock_container.conversation_service.update_conversation = AsyncMock(return_value=updated_conversation)
        
        update_data = ConversationUpdate(title="Updated Title")
        result = await update_conversation(
            conversation_id=str(mock_conversation.id),
            update_data=update_data,
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.title == "Updated Title"
        mock_container.conversation_service.update_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, mock_user, mock_container):
        mock_container.conversation_service.update_conversation = AsyncMock(return_value=None)
        
        update_data = ConversationUpdate(title="New Title")
        with pytest.raises(HTTPException) as exc_info:
            await update_conversation(
                conversation_id="nonexistent",
                update_data=update_data,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_update_conversation_error(self, mock_user, mock_container):
        mock_container.conversation_service.update_conversation = AsyncMock(side_effect=Exception("DB error"))
        
        update_data = ConversationUpdate(title="New Title")
        with pytest.raises(HTTPException) as exc_info:
            await update_conversation(
                conversation_id="conv_123",
                update_data=update_data,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_patch_conversation_success(self, mock_user, mock_container, mock_conversation):
        updated_conversation = mock_conversation
        updated_conversation.title = "Patched Title"
        mock_container.conversation_service.update_conversation = AsyncMock(return_value=updated_conversation)
        
        update_data = ConversationUpdate(title="Patched Title")
        result = await patch_conversation(
            conversation_id=str(mock_conversation.id),
            update_data=update_data,
            current_user=mock_user,
            container=mock_container
        )
        
        assert result.title == "Patched Title"
        mock_container.conversation_service.update_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_patch_conversation_not_found(self, mock_user, mock_container):
        mock_container.conversation_service.update_conversation = AsyncMock(return_value=None)
        
        update_data = ConversationUpdate(title="New Title")
        with pytest.raises(HTTPException) as exc_info:
            await patch_conversation(
                conversation_id="nonexistent",
                update_data=update_data,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

class TestConversationsAPIErrorHandling:
    
    @pytest.fixture
    def mock_user(self):
    # Create a mock user token.
        return TokenData(user_id="test_user_123", email="test@example.com")
    
    @pytest.fixture
    def mock_container(self):
    # Create a mock service container.
        container = MagicMock(spec=ServiceContainer)
        container.conversation_service = MagicMock()
        return container
    
    @pytest.mark.asyncio
    async def test_get_conversations_generic_exception(self, mock_user, mock_container):
        mock_container.conversation_service.get_user_conversations = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversations(
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_get_conversation_generic_exception(self, mock_user, mock_container):
        mock_container.conversation_service.get_conversation = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation(
                conversation_id="conv_123",
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_patch_conversation_generic_exception(self, mock_user, mock_container):
        from app.models.conversation_db import ConversationUpdate
        mock_container.conversation_service.update_conversation = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        update_data = ConversationUpdate(title="Updated Title")
        
        with pytest.raises(HTTPException) as exc_info:
            await patch_conversation(
                conversation_id="conv_123",
                update_data=update_data,
                current_user=mock_user,
                container=mock_container
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


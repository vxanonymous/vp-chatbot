from app.auth.password import get_password_hash
from app.core.exceptions import ValidationError, DatabaseError
from app.models.user import UserCreate
from app.models.user import UserCreate, UserInDB
from app.models.user import UserInDB, UserCreate
from app.services.user_service import UserService
from bson import ObjectId
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

class TestUserServiceComprehensive:
# Comprehensive tests for UserService.
    
    @pytest.fixture
    def mock_collection(self):
    # Create a mock MongoDB collection.
        collection = AsyncMock()
        return collection
    
    @pytest.fixture
    def user_service(self, mock_collection):
    # Create a UserService instance.
        return UserService(mock_collection)
    
    @pytest.fixture
    def sample_user_doc(self):
    # Create a sample user document.
        user_id = ObjectId()
        return {
            "_id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "hashed_password": "hashed_password",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_collection, sample_user_doc):
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=sample_user_doc["_id"]))
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        result = await user_service.create_user(user_data)
        
        assert result is not None
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_collection, sample_user_doc):
        mock_collection.find_one = AsyncMock(return_value=sample_user_doc)
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        with pytest.raises(ValueError, match="already registered"):
            await user_service.create_user(user_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service, mock_collection, sample_user_doc):
        from app.auth.password import get_password_hash
        sample_user_doc["hashed_password"] = get_password_hash("SecurePass123!")
        mock_collection.find_one = AsyncMock(return_value=sample_user_doc)
        
        result = await user_service.authenticate_user(
            email="test@example.com",
            password="SecurePass123!"
        )
        
        assert result is not None
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, user_service, mock_collection, sample_user_doc):
        from app.auth.password import get_password_hash
        sample_user_doc["hashed_password"] = get_password_hash("CorrectPassword")
        mock_collection.find_one = AsyncMock(return_value=sample_user_doc)
        
        result = await user_service.authenticate_user(
            email="test@example.com",
            password="WrongPassword"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(return_value=None)
        
        result = await user_service.authenticate_user(
            email="nonexistent@example.com",
            password="password"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_collection, sample_user_doc):
        mock_collection.find_one = AsyncMock(return_value=sample_user_doc)
        
        result = await user_service.get_user_by_id(str(sample_user_doc["_id"]))
        
        assert result is not None
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(return_value=None)
        
        result = await user_service.get_user_by_id(str(ObjectId()))
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid(self, user_service, mock_collection):
        result = await user_service.get_user_by_id("invalid_id")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_collection, sample_user_doc):
        mock_collection.find_one = AsyncMock(return_value=sample_user_doc)
        
        result = await user_service.get_user_by_email("test@example.com")
        
        assert result is not None
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(return_value=None)
        
        result = await user_service.get_user_by_email("nonexistent@example.com")
        
        assert result is None



class TestUserServiceAdditional:
    
    @pytest.fixture
    def mock_collection(self):
    # Create a mock MongoDB collection.
        collection = MagicMock()
        return collection
    
    @pytest.fixture
    def user_service(self, mock_collection):
    # Create a UserService instance with mocked collection.
        service = UserService(mock_collection)
        return service
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_collection):
        user_id = str(ObjectId())
        update_data = {"full_name": "Updated Name"}
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "full_name": "Updated Name",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        result = await user_service.update_user(user_id, update_data)
        
        assert result is not None
        assert result.full_name == "Updated Name"
        mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service, mock_collection):
        user_id = str(ObjectId())
        update_data = {"full_name": "Updated Name"}
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
        
        result = await user_service.update_user(user_id, update_data)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_removes_password(self, user_service, mock_collection):
        user_id = str(ObjectId())
        update_data = {"full_name": "Updated Name", "hashed_password": "should_be_removed"}
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "full_name": "Updated Name",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        await user_service.update_user(user_id, update_data.copy())
        
        call_args = mock_collection.update_one.call_args
        update_dict = call_args[0][1]["$set"]
        assert "hashed_password" not in update_dict
        assert "full_name" in update_dict
    
    @pytest.mark.asyncio
    async def test_update_user_removes_email(self, user_service, mock_collection):
        user_id = str(ObjectId())
        update_data = {"full_name": "Updated Name", "email": "should_be_removed@example.com"}
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "full_name": "Updated Name",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        await user_service.update_user(user_id, update_data.copy())
        
        call_args = mock_collection.update_one.call_args
        update_dict = call_args[0][1]["$set"]
        assert "email" not in update_dict
        assert "full_name" in update_dict
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_collection):
        user_id = str(ObjectId())
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        result = await user_service.delete_user(user_id)
        
        assert result is True
        mock_collection.delete_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_collection):
        user_id = str(ObjectId())
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        result = await user_service.delete_user(user_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, user_service, mock_collection):
        async def async_iter():
            yield {
                "_id": ObjectId(),
                "email": "user1@example.com",
                "full_name": "User 1",
                "hashed_password": "hashed1",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            yield {
                "_id": ObjectId(),
                "email": "user2@example.com",
                "full_name": "User 2",
                "hashed_password": "hashed2",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter()
        mock_collection.find.return_value.skip.return_value.limit.return_value = mock_cursor
        
        result = await user_service.list_users(skip=0, limit=10)
        
        assert len(result) == 2
        assert result[0].email == "user1@example.com"
        assert result[1].email == "user2@example.com"
    
    @pytest.mark.asyncio
    async def test_list_users_empty(self, user_service, mock_collection):
        async def async_iter():
            if False:
                yield
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter()
        mock_collection.find.return_value.skip.return_value.limit.return_value = mock_cursor
        
        result = await user_service.list_users(skip=0, limit=10)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_list_users_pagination(self, user_service, mock_collection):
        async def async_iter():
            yield {
                "_id": ObjectId(),
                "email": "user1@example.com",
                "full_name": "User 1",
                "hashed_password": "hashed1",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter()
        mock_collection.find.return_value.skip.return_value.limit.return_value = mock_cursor
        
        result = await user_service.list_users(skip=10, limit=5)
        
        assert len(result) == 1
        mock_collection.find.assert_called_once()



class TestUserServiceEdgeCases:
    
    @pytest.fixture
    def mock_collection(self):
    # Create a mock MongoDB collection.
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_collection):
    # Create UserService instance.
        return UserService(mock_collection)
    
    @pytest.mark.asyncio
    async def test_create_user_with_exception(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(side_effect=Exception("DB error"))
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        with pytest.raises(Exception, match="DB error"):
            await user_service.create_user(user_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_exception(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(side_effect=Exception("DB error"))
        
        result = await user_service.authenticate_user(
            email="test@example.com",
            password="password"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_with_exception(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(side_effect=Exception("DB error"))
        
        result = await user_service.get_user_by_id(str(ObjectId()))
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_with_exception(self, user_service, mock_collection):
        mock_collection.find_one = AsyncMock(side_effect=Exception("DB error"))
        
        result = await user_service.get_user_by_email("test@example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_with_exception(self, user_service, mock_collection):
        mock_collection.update_one = AsyncMock(side_effect=Exception("DB error"))
        
        result = await user_service.update_user(
            user_id=str(ObjectId()),
            update_data={"full_name": "New Name"}
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_user_with_exception(self, user_service, mock_collection):
        mock_collection.delete_one = AsyncMock(side_effect=Exception("DB error"))
        
        result = await user_service.delete_user(str(ObjectId()))
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_users_with_exception(self, user_service, mock_collection):
        mock_collection.find = MagicMock()
        mock_collection.find.return_value.skip.return_value.limit.return_value = AsyncMock()
        
        async def async_iter():
            raise Exception("DB error")
            yield
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter()
        mock_collection.find.return_value.skip.return_value.limit.return_value = mock_cursor
        
        result = await user_service.list_users(skip=0, limit=10)
        
        assert result == []




import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pymongo.errors import ServerSelectionTimeoutError

from app.database.database import (
    MongoDB,
    connect_to_mongo,
    close_mongo_connection,
    create_indexes,
    get_database,
    is_database_available,
    db
)


class TestMongoDB:
    
    def test_mongodb_init(self):
        mongo = MongoDB()
        assert mongo.client is None
        assert mongo.database is None
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_atlas(self):
        with patch('app.database.database.settings') as mock_settings:
            mock_settings.mongodb_url = "mongodb+srv://test:test@cluster.mongodb.net/test"
            mock_settings.mongodb_db_name = "test_db"
            
            mock_client = MagicMock()
            mock_client.server_info = AsyncMock()
            mock_database = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_database)
            
            with patch('app.database.database.AsyncIOMotorClient', return_value=mock_client):
                with patch('app.database.database.create_indexes', new_callable=AsyncMock) as mock_create_indexes:
                    await connect_to_mongo()
                    
                    assert db.client is not None
                    assert db.database is not None
                    mock_create_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_local(self):
        with patch('app.database.database.settings') as mock_settings:
            mock_settings.mongodb_url = "mongodb://localhost:27017/test"
            mock_settings.mongodb_db_name = "test_db"
            
            mock_client = MagicMock()
            mock_client.server_info = AsyncMock()
            mock_database = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_database)
            
            with patch('app.database.database.AsyncIOMotorClient', return_value=mock_client):
                with patch('app.database.database.create_indexes', new_callable=AsyncMock) as mock_create_indexes:
                    await connect_to_mongo()
                    
                    assert db.client is not None
                    assert db.database is not None
                    mock_create_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_timeout_error(self):
        with patch('app.database.database.settings') as mock_settings:
            mock_settings.mongodb_url = "mongodb://localhost:27017/test"
            mock_settings.mongodb_db_name = "test_db"
            
            mock_client = MagicMock()
            mock_client.server_info = AsyncMock(side_effect=ServerSelectionTimeoutError("Connection timeout"))
            
            with patch('app.database.database.AsyncIOMotorClient', return_value=mock_client):
                with pytest.raises(ServerSelectionTimeoutError):
                    await connect_to_mongo()
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_general_exception(self):
        with patch('app.database.database.settings') as mock_settings:
            mock_settings.mongodb_url = "mongodb://localhost:27017/test"
            mock_settings.mongodb_db_name = "test_db"
            
            with patch('app.database.database.AsyncIOMotorClient', side_effect=Exception("Connection failed")):
                with pytest.raises(Exception, match="Connection failed"):
                    await connect_to_mongo()
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_no_client(self):
        with patch('app.database.database.settings') as mock_settings:
            mock_settings.mongodb_url = "mongodb://localhost:27017/test"
            mock_settings.mongodb_db_name = "test_db"
            
            with patch('app.database.database.AsyncIOMotorClient', return_value=None):
                with pytest.raises(Exception, match="Failed to create MongoDB client"):
                    await connect_to_mongo()
    
    @pytest.mark.asyncio
    async def test_close_mongo_connection(self):
        db.client = MagicMock()
        db.client.close = MagicMock()
        
        await close_mongo_connection()
        
        db.client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_mongo_connection_no_client(self):
        db.client = None
        
        await close_mongo_connection()
        
        assert db.client is None
    
    @pytest.mark.asyncio
    async def test_create_indexes(self):
        mock_database = MagicMock()
        mock_users = MagicMock()
        mock_conversations = MagicMock()
        mock_database.users = mock_users
        mock_database.conversations = mock_conversations
        
        mock_users.create_index = AsyncMock()
        mock_conversations.create_index = AsyncMock()
        
        db.database = mock_database
        
        await create_indexes()
        
        assert mock_users.create_index.call_count == 1
        assert mock_conversations.create_index.call_count == 3
    
    @pytest.mark.asyncio
    async def test_create_indexes_no_database(self):
        db.database = None
        
        await create_indexes()
        
        assert db.database is None
    
    @pytest.mark.asyncio
    async def test_create_indexes_exception(self):
        mock_database = MagicMock()
        mock_users = MagicMock()
        mock_database.users = mock_users
        mock_users.create_index = AsyncMock(side_effect=Exception("Index creation failed"))
        
        db.database = mock_database
        
        await create_indexes()
        
        mock_users.create_index.assert_called_once()
    
    def test_get_database(self):
        mock_database = MagicMock()
        db.database = mock_database
        
        result = get_database()
        
        assert result == mock_database
    
    def test_is_database_available_true(self):
        db.client = MagicMock()
        db.database = MagicMock()
        
        result = is_database_available()
        
        assert result is True
    
    def test_is_database_available_false_no_client(self):
        db.client = None
        db.database = MagicMock()
        
        result = is_database_available()
        
        assert result is False
    
    def test_is_database_available_false_no_database(self):
        db.client = MagicMock()
        db.database = None
        
        result = is_database_available()
        
        assert result is False
    
    def test_is_database_available_exception(self):
        original_client = db.client
        original_database = db.database
        
        try:
            db.client = None
            db.database = None
            
            result = is_database_available()
            assert result is False
        finally:
            db.client = original_client
            db.database = original_database


import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from bson import ObjectId
from datetime import datetime

# Set environment variable to skip MongoDB connection during tests
os.environ["SKIP_MONGODB_CONNECTION"] = "true"

# Mock the database before importing the app
with patch('app.database.get_database') as mock_get_db:
    # Create a mock database with collections
    mock_db = MagicMock()
    mock_db.users = AsyncMock()
    mock_db.conversations = AsyncMock()
    mock_db.messages = AsyncMock()
    
    # Mock database methods
    mock_db.users.find_one.return_value = None
    mock_db.users.insert_one.return_value = MagicMock(inserted_id=ObjectId())
    mock_db.conversations.find_one.return_value = None
    mock_db.conversations.insert_one.return_value = MagicMock(inserted_id=ObjectId())
    
    mock_get_db.return_value = mock_db
    
    # Create a simple test app
    from app.main import app as test_app


# Mock database connection for unit tests
@pytest.fixture(autouse=True)
def mock_database(request):
    # Only apply to unit tests, not integration tests
    # Integration tests will use test_database from conftest_integration.py
    if 'integration' in str(request.node.fspath):
        # Skip mocking for integration tests
        yield
        return
    
    # Mock database connection for unit tests
    with patch('app.database.get_database') as mock_get_db:
        # Create a mock database with collections
        mock_db = MagicMock()
        mock_db.users = AsyncMock()
        mock_db.conversations = AsyncMock()
        mock_db.messages = AsyncMock()
        
        # Mock database methods
        mock_db.users.find_one.return_value = None
        mock_db.users.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        mock_db.conversations.find_one.return_value = None
        mock_db.conversations.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        mock_get_db.return_value = mock_db
        yield mock_get_db


# Mock service container for tests (only for unit tests, not integration tests)
# Integration tests should use real_container_with_mocked_openai from conftest_integration.py
@pytest.fixture(autouse=True)
def mock_service_container(request):
    # Only auto-apply to unit tests, not integration tests
    # Integration tests will use real_container_with_mocked_openai
    if 'integration' in str(request.node.fspath):
        # Skip mocking for integration tests
        yield
        return
    
    # Mock service container for unit tests
    with patch('app.core.container.get_container') as mock_get_container:
        # Create mock services
        mock_container = MagicMock()
        mock_container.user_service = AsyncMock()
        mock_container.conversation_service = AsyncMock()
        mock_container.openai_service = AsyncMock()
        
        # Mock user service methods
        mock_container.user_service.get_user_by_email.return_value = None
        mock_container.user_service.create_user.return_value = MagicMock(
            id=ObjectId(),
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )
        mock_container.user_service.authenticate_user.return_value = MagicMock(
            id=ObjectId(),
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )
        
        # Mock conversation service methods
        mock_container.conversation_service.create_conversation.return_value = MagicMock(
            id=ObjectId(),
            title="Test Conversation",
            user_id="user123",
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_get_container.return_value = mock_container
        yield mock_get_container


@pytest.fixture
def client():
    # Create a test client for the FastAPI app.
    return TestClient(test_app)


# Async client fixture for async tests
@pytest.fixture
async def session():
    # Create an async test client for the FastAPI app.
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# Mock authentication fixture
@pytest.fixture
def mock_auth():
    # Mock authentication for tests.
    with patch('app.auth.dependencies.get_current_user') as mock_get_current_user:
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.email = "test@example.com"
        mock_get_current_user.return_value = mock_user
        yield mock_get_current_user


# Helper function to generate valid ObjectId strings
def generate_object_id() -> str:
    # Generate a valid ObjectId string for testing.
    return str(ObjectId())


# Simple mock database class for testing
class MockDatabase:
    def __init__(self):
        self.conversations = AsyncMock()
        self.users = AsyncMock()


@pytest.fixture
def sample_conversation():
    # Sample conversation data for testing.
    return {
        "id": generate_object_id(),
        "title": "Test Conversation",
        "user_id": "user123",
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_user():
    # Sample user data for testing.
    return {
        "id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True
    }


@pytest.fixture
def sample_message():
    # Sample message data for testing.
    return {
        "id": generate_object_id(),
        "content": "Hello, this is a test message",
        "role": "user",
        "timestamp": datetime.utcnow()
    }

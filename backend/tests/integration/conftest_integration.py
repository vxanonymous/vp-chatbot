# Integration test fixtures that use real services with a test database.
import pytest
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.container import ServiceContainer
from app.database.database import get_database


@pytest.fixture(scope="function")
def test_database():
    # Create a real test database connection using mongomock or real MongoDB
    # Try to use real MongoDB first
    try:
        from app.config import settings
        mongodb_url = os.getenv("TEST_MONGODB_URL", settings.mongodb_url)
        
        # Use async Motor client
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(mongodb_url)
        test_db_name = f"test_vacation_planner_{os.getpid()}_{id(client)}"
        db = client[test_db_name]
        
        yield db
        
        # Cleanup: drop test database after test
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule cleanup
                asyncio.create_task(client.drop_database(test_db_name))
            else:
                loop.run_until_complete(client.drop_database(test_db_name))
            client.close()
        except Exception as e:
            # Ignore cleanup errors
            pass
    except Exception:
        # Fallback: try mongomock if real MongoDB not available
        try:
            from mongomock_motor import AsyncMongoMockClient
            
            client = AsyncMongoMockClient()
            test_db_name = f"test_vacation_planner_{os.getpid()}"
            db = client[test_db_name]
            
            yield db
            # Cleanup
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                drop_task = client.drop_database(test_db_name)
                if loop.is_running():
                    loop.create_task(drop_task)
                else:
                    loop.run_until_complete(drop_task)
                client.close()
            except Exception:
                pass
        except (ImportError, AttributeError):
            # Final fallback: use mock database (not ideal for integration tests)
            from types import SimpleNamespace
            mock_db = MagicMock()
            mock_db.users = MagicMock()
            mock_db.conversations = MagicMock()
            # Ensure update_one returns proper result with integer modified_count
            mock_result = SimpleNamespace()
            mock_result.modified_count = 1  # Ensure it's an int, not a MagicMock
            mock_result.matched_count = 1
            mock_result.upserted_id = None
            mock_db.conversations.update_one = AsyncMock(return_value=mock_result)
            yield mock_db


@pytest.fixture(scope="function")
def real_container(test_database):
    # Create a real ServiceContainer with real services using test database
    container = ServiceContainer()
    
    # Patch both database access points to return our test database
    with patch('app.database.get_database', return_value=test_database), \
         patch('app.core.container.get_database', return_value=test_database):
        # Reset container to force re-initialization
        container.reset()
        
        # Access services to trigger initialization with test database
        _ = container.user_service  # Triggers initialization
        _ = container.conversation_service  # Triggers initialization
        _ = container.openai_service  # Real service (we'll mock OpenAI API calls)
        _ = container.error_recovery  # Real service
        _ = container.vacation_planner  # Real service
        _ = container.proactive_assistant  # Real service
        _ = container.intelligence_service  # Real service
        _ = container.memory  # Real service
        _ = container.conversation_handler  # Real conversation orchestration
        
        yield container
        
        # Cleanup
        container.reset()


@pytest.fixture(scope="function")
def real_container_with_mocked_openai(real_container):
    # Real container with OpenAI API calls mocked to avoid API costs
    # Mock only the OpenAI client, not the entire service
    original_client = real_container.openai_service.client
    
    # Create mock OpenAI client responses
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Test AI response"
    mock_message.function_call = None
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)
    
    # Replace the client
    real_container.openai_service.client = mock_client
    
    yield real_container
    
    # Restore original client
    real_container.openai_service.client = original_client


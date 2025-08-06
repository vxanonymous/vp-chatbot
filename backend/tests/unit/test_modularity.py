"""
Tests for the modularity improvements including:
- Dependency Injection Container
- Service Interfaces
- Configuration Management
- Service Isolation
- Testability Improvements
"""
import pytest  # 
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from bson import ObjectId  # 

from app.core.container import ServiceContainer, get_container, get_user_service, get_conversation_service
from app.core.config_manager import ConfigManager, get_config_manager, get_config
from app.services.user_service import UserService
from app.services.conversation_service import ConversationService
from app.services.openai_service import OpenAIService
from app.services.vacation_intelligence_service import VacationIntelligenceService
from app.services.conversation_memory import ConversationMemory
from app.services.proactive_assistant import ProactiveAssistant
from app.services.error_recovery import ErrorRecoveryService
from app.services.vacation_planner import VacationPlanner
from app.models.user import UserCreate
from app.models.chat import Message, MessageRole
from unittest.mock import MagicMock

# Simple mock database class for testing
class MockDatabase:
    def __init__(self):
        self.conversations = MagicMock()
        self.users = MagicMock()
        
        # Make the mock methods async
        self.conversations.find_one = AsyncMock()
        self.conversations.insert_one = AsyncMock()
        self.conversations.update_one = AsyncMock()
        self.conversations.delete_one = AsyncMock()
        self.users.find_one = AsyncMock()
        self.users.insert_one = AsyncMock()
        self.users.update_one = AsyncMock()
        self.users.delete_one = AsyncMock()

# Simple test service container class for testing
class MockServiceContainer:
    def __init__(self):
        self.mock_db = MockDatabase()
        self.user_service = UserService(self.mock_db.users)
        self.conversation_service = ConversationService(self.mock_db.conversations)
        self.openai_service = OpenAIService()
        self.intelligence_service = VacationIntelligenceService()
        self.memory = ConversationMemory()
        self.proactive_assistant = ProactiveAssistant()
        self.error_recovery = ErrorRecoveryService()
        self.vacation_planner = VacationPlanner()


@pytest.fixture
def mock_db():
    """Provide a mock database for testing."""
    return MockDatabase()


@pytest.fixture
def test_container():
    """Provide a test container with mocked dependencies."""
    return MockServiceContainer()


class TestDependencyInjectionContainer:
    """Test the dependency injection container functionality."""
    
    def test_container_creation(self):
        """Test that the container can be created."""
        container = ServiceContainer()
        assert container is not None
        assert isinstance(container, ServiceContainer)
    
    def test_container_singleton_pattern(self):
        """Test that get_container returns the same instance."""
        container1 = get_container()
        container2 = get_container()
        assert container1 is container2
    
    def test_user_service_lazy_loading(self, mock_db):
        """Test that user service is created lazily."""
        with patch('app.core.container.get_database', return_value=mock_db):
            container = ServiceContainer()
            
            # Service should not exist initially
            assert container._user_service is None
            
            # Service should be created when accessed
            service = container.user_service
            assert service is not None
            assert isinstance(service, UserService)
            
            # Subsequent calls should return the same instance
            service2 = container.user_service
            assert service is service2
    
    def test_conversation_service_lazy_loading(self, mock_db):
        """Test that conversation service is created lazily."""
        with patch('app.core.container.get_database', return_value=mock_db):
            container = ServiceContainer()
            
            # Service should not exist initially
            assert container._conversation_service is None
            
            # Service should be created when accessed
            service = container.conversation_service
            assert service is not None
            assert isinstance(service, ConversationService)
            
            # Subsequent calls should return the same instance
            service2 = container.conversation_service
            assert service is service2
    
    def test_openai_service_lazy_loading(self):
        """Test that OpenAI service is created lazily."""
        container = ServiceContainer()
        
        # Service should not exist initially
        assert container._openai_service is None
        
        # Service should be created when accessed
        service = container.openai_service
        assert service is not None
        assert isinstance(service, OpenAIService)
        
        # Subsequent calls should return the same instance
        service2 = container.openai_service
        assert service is service2
    
    def test_container_reset(self, mock_db):
        """Test that container reset clears all services."""
        with patch('app.core.container.get_database', return_value=mock_db):
            container = ServiceContainer()
            
            # Access services to create them
            container.user_service
            container.conversation_service
            container.openai_service
            
            # Verify services exist
            assert container._user_service is not None
            assert container._conversation_service is not None
            assert container._openai_service is not None
            
            # Reset container
            container.reset()
            
            # Verify services are cleared
            assert container._user_service is None
            assert container._conversation_service is None
            assert container._openai_service is None

    def test_convenience_functions(self, mock_db):
        """Test convenience functions for getting services."""
        # Clear the LRU cache to ensure fresh instances
        get_user_service.cache_clear()
        get_conversation_service.cache_clear()
        
        # Reset the container to ensure fresh instances
        container = get_container()
        container.reset()
        
        # Temporarily disable the global mock for this test
        with patch('app.core.container.get_database', return_value=mock_db):
            with patch('app.core.container.get_container', return_value=container):
                # Test get_user_service
                user_service = get_user_service()
                assert isinstance(user_service, UserService)
                
                # Test get_conversation_service
                conversation_service = get_conversation_service()
                assert isinstance(conversation_service, ConversationService)
    
    def test_test_container_with_mocks(self, test_container):
        """Test that test container works with mocked dependencies."""
        assert isinstance(test_container, MockServiceContainer)
        
        # Test that services are created with mock database
        user_service = test_container.user_service
        assert isinstance(user_service, UserService)
        assert user_service.collection == test_container.mock_db.users
        
        conversation_service = test_container.conversation_service
        assert isinstance(conversation_service, ConversationService)
        assert conversation_service.collection == test_container.mock_db.conversations


class TestServiceInterfaces:
    """Test service interface contracts."""
    
    def test_user_service_implements_interface(self, mock_db):
        """Test that UserService implements IUserService interface."""
        user_service = UserService(mock_db.users)
        
        # Check that all required methods exist
        assert hasattr(user_service, 'create_user')
        assert hasattr(user_service, 'authenticate_user')
        assert hasattr(user_service, 'get_user_by_id')
        assert hasattr(user_service, 'get_user_by_email')
        
        # Check that methods are async
        assert asyncio.iscoroutinefunction(user_service.create_user)
        assert asyncio.iscoroutinefunction(user_service.authenticate_user)
        assert asyncio.iscoroutinefunction(user_service.get_user_by_id)
        assert asyncio.iscoroutinefunction(user_service.get_user_by_email)
    
    def test_conversation_service_implements_interface(self, mock_db):
        """Test that ConversationService implements IConversationService interface."""
        conversation_service = ConversationService(mock_db.conversations)
        
        # Check that all required methods exist
        assert hasattr(conversation_service, 'create_conversation')
        assert hasattr(conversation_service, 'get_conversation')
        assert hasattr(conversation_service, 'add_message')
        assert hasattr(conversation_service, 'update_conversation')
        assert hasattr(conversation_service, 'delete_conversation')
        
        # Check that methods are async
        assert asyncio.iscoroutinefunction(conversation_service.create_conversation)
        assert asyncio.iscoroutinefunction(conversation_service.get_conversation)
        assert asyncio.iscoroutinefunction(conversation_service.add_message)
        assert asyncio.iscoroutinefunction(conversation_service.update_conversation)
        assert asyncio.iscoroutinefunction(conversation_service.delete_conversation)
    
    def test_openai_service_implements_interface(self):
        """Test that OpenAIService implements IOpenAIService interface."""
        openai_service = OpenAIService()
        
        # Check that all required methods exist
        assert hasattr(openai_service, 'generate_response_async')
        assert hasattr(openai_service, 'generate_response')
        
        # Check that methods have correct signatures
        assert asyncio.iscoroutinefunction(openai_service.generate_response_async)
        assert callable(openai_service.generate_response)


class TestConfigurationManagement:
    """Test configuration management functionality."""
    
    def test_config_manager_creation(self):
        """Test that config manager can be created."""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert isinstance(config_manager, ConfigManager)
    
    def test_environment_detection(self):
        """Test environment detection functionality."""
        config_manager = ConfigManager()
        
        # Test environment properties
        assert hasattr(config_manager, 'environment')
        assert hasattr(config_manager, 'is_development')
        assert hasattr(config_manager, 'is_production')
        assert hasattr(config_manager, 'is_testing')
    
    def test_database_config(self):
        """Test database configuration retrieval."""
        config_manager = ConfigManager()
        db_config = config_manager.get_database_config()
        
        assert isinstance(db_config, dict)
        assert 'url' in db_config
        assert 'database_name' in db_config
        assert 'ssl' in db_config
        assert 'timeout' in db_config
    
    def test_openai_config(self):
        """Test OpenAI configuration retrieval."""
        config_manager = ConfigManager()
        openai_config = config_manager.get_openai_config()
        
        assert isinstance(openai_config, dict)
        assert 'api_key' in openai_config
        assert 'model' in openai_config
        assert 'max_tokens' in openai_config
        assert 'temperature' in openai_config
    
    def test_security_config(self):
        """Test security configuration retrieval."""
        config_manager = ConfigManager()
        security_config = config_manager.get_security_config()
        
        assert isinstance(security_config, dict)
        assert 'secret_key' in security_config
        assert 'algorithm' in security_config
        assert 'access_token_expire_minutes' in security_config
        assert 'cors_origins' in security_config
    
    def test_logging_config(self):
        """Test logging configuration retrieval."""
        config_manager = ConfigManager()
        logging_config = config_manager.get_logging_config()
        
        assert isinstance(logging_config, dict)
        assert 'level' in logging_config
        assert 'format' in logging_config
        assert 'file' in logging_config
    
    def test_performance_config(self):
        """Test performance configuration retrieval."""
        config_manager = ConfigManager()
        performance_config = config_manager.get_performance_config()
        
        assert isinstance(performance_config, dict)
        assert 'cache_ttl' in performance_config
        assert 'max_concurrent_requests' in performance_config
        assert 'request_timeout' in performance_config
        assert 'database_timeout' in performance_config
    
    def test_config_caching(self):
        """Test that configuration is cached properly."""
        config_manager = ConfigManager()
        
        # Get config twice
        config1 = config_manager.get_database_config()
        config2 = config_manager.get_database_config()
        
        # Should be the same object (cached)
        assert config1 is config2
    
    def test_config_cache_clear(self):
        """Test that configuration cache can be cleared."""
        config_manager = ConfigManager()
        
        # Get config to populate cache
        config_manager.get_database_config()
        assert len(config_manager._config_cache) > 0
        
        # Clear cache
        config_manager.clear_cache()
        assert len(config_manager._config_cache) == 0
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2
    
    def test_get_config_function(self):
        """Test get_config convenience function."""
        config = get_config()
        assert isinstance(config, dict)
        assert 'environment' in config
        assert 'database' in config
        assert 'openai' in config
        assert 'security' in config
        assert 'logging' in config
        assert 'performance' in config


class TestServiceIsolation:
    """Test that services are properly isolated."""
    
    def test_user_service_isolation(self, test_container):
        """Test that user service operations are isolated."""
        user_service = test_container.user_service
        
        # Mock successful user creation
        test_container.mock_db.users.find_one.return_value = None
        test_container.mock_db.users.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        # Test user creation
        user_data = UserCreate(
            email="isolation@example.com",
            full_name="Isolation Test",
            password="SecurePass123!"
        )
        result = asyncio.run(user_service.create_user(user_data))
        assert result is not None
        assert result.email == "isolation@example.com"

    def test_conversation_service_isolation(self, test_container):
        """Test that conversation service operations are isolated."""
        conversation_service = test_container.conversation_service
        
        # Mock successful conversation creation
        test_container.mock_db.conversations.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        # Test conversation creation
        result = asyncio.run(conversation_service.create_conversation(
            user_id="test_user",
            title="Test Conversation"
        ))
        assert result is not None
        assert result.title == "Test Conversation"
    
    def test_openai_service_isolation(self, test_container):
        """Test that OpenAI service operations are isolated."""
        openai_service = test_container.openai_service
        
        # Test response generation without affecting other services
        messages = [Message(role=MessageRole.USER, content="Hello")]
        result = openai_service.generate_response(messages)
        assert result is not None
        assert "content" in result


class TestTestabilityImprovements:
    """Test improvements in testability."""
    
    def test_service_mocking(self, test_container):
        """Test that services can be easily mocked."""
        # Mock the user service
        mock_user_service = Mock()
        test_container.user_service = mock_user_service
        
        # Verify the mock is used
        user_service = test_container.user_service
        assert user_service is mock_user_service
    
    def test_database_mocking(self, test_container):
        """Test that database operations can be easily mocked."""
        # Mock database operations
        test_container.mock_db.users.find_one.return_value = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "full_name": "Test User",
            "hashed_password": "hashed_password",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # Test that the mock is used
        user_service = test_container.user_service
        result = asyncio.run(user_service.get_user_by_email("test@example.com"))
        assert result is not None
        assert result.email == "test@example.com"
    
    def test_dependency_injection_testing(self, test_container):
        """Test that dependency injection works in tests."""
        # Test that all services are available
        assert test_container.user_service is not None
        assert test_container.conversation_service is not None
        assert test_container.openai_service is not None
        assert test_container.intelligence_service is not None
        assert test_container.memory is not None
        assert test_container.proactive_assistant is not None
        assert test_container.error_recovery is not None
        assert test_container.vacation_planner is not None
        
        # Test that services are of correct types
        assert isinstance(test_container.user_service, UserService)
        assert isinstance(test_container.conversation_service, ConversationService)
        assert isinstance(test_container.openai_service, OpenAIService)
        assert isinstance(test_container.intelligence_service, VacationIntelligenceService)
        assert isinstance(test_container.memory, ConversationMemory)
        assert isinstance(test_container.proactive_assistant, ProactiveAssistant)
        assert isinstance(test_container.error_recovery, ErrorRecoveryService)
        assert isinstance(test_container.vacation_planner, VacationPlanner)


class TestIntegrationWithExistingServices:
    """Test integration between new modularity features and existing services."""
    
    @pytest.mark.asyncio
    async def test_container_with_real_services(self, test_container):
        """Test that container works with real service implementations."""
        # Test user service integration
        user_service = test_container.user_service
        
        # Mock database operations
        test_container.mock_db.users.find_one.return_value = None
        test_container.mock_db.users.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        user_data = UserCreate(
            email="integration@example.com",
            full_name="Integration Test",
            password="SecurePass123!"
        )
        
        result = await user_service.create_user(user_data)
        assert result is not None
        assert result.email == "integration@example.com"

    @pytest.mark.asyncio
    async def test_service_interaction(self, test_container):
        """Test that services can interact through the container."""
        user_service = test_container.user_service
        conversation_service = test_container.conversation_service
        
        # Mock database operations
        test_container.mock_db.users.find_one.return_value = None
        test_container.mock_db.users.insert_one.return_value = Mock(inserted_id=ObjectId())
        test_container.mock_db.conversations.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        # Create user
        user_data = UserCreate(
            email="interaction@example.com",
            full_name="Interaction Test",
            password="SecurePass123!"
        )
        user = await user_service.create_user(user_data)
        
        # Create conversation for user
        conversation = await conversation_service.create_conversation(
            user_id=str(user.id),
            title="Test Interaction"
        )
        
        assert conversation is not None
        assert conversation.user_id == str(user.id)
    
    def test_configuration_integration(self, test_container):
        """Test that configuration management integrates with services."""
        config_manager = get_config_manager()
        
        # Get configuration
        db_config = config_manager.get_database_config()
        openai_config = config_manager.get_openai_config()
        
        # Verify configuration is accessible
        assert db_config is not None
        assert openai_config is not None
        
        # Verify services can access configuration
        openai_service = test_container.openai_service
        assert openai_service is not None


class TestErrorHandling:
    """Test error handling in the modularity improvements."""
    
    def test_container_database_error(self):
        """Test container handles database errors gracefully."""
        with patch('app.core.container.get_database', return_value=None):
            container = ServiceContainer()
            
            # Should raise RuntimeError when database is not available
            with pytest.raises(RuntimeError, match="Database is not available"):
                _ = container.user_service
    
    def test_config_validation(self):
        """Test configuration validation."""
        config_manager = ConfigManager()
        
        # Test validation method exists
        assert hasattr(config_manager, 'validate_config')
        
        # Test validation can be called
        result = config_manager.validate_config()
        assert isinstance(result, bool)
    
    def test_service_creation_errors(self, test_container):
        """Test that service creation errors are handled properly."""
        # Test with invalid database by creating a new container with None database
        with patch('app.core.container.get_database', return_value=None):
            container = ServiceContainer()
            with pytest.raises(RuntimeError, match="Database is not available"):
                _ = container.user_service


class TestPerformanceAndScalability:
    """Test performance and scalability aspects of modularity improvements."""
    
    def test_container_performance(self, mock_db):
        """Test that container operations are performant."""
        import time
        
        with patch('app.core.container.get_database', return_value=mock_db):
            container = ServiceContainer()
            
            # Test service access performance
            start_time = time.time()
            for _ in range(100):
                _ = container.user_service
            end_time = time.time()
            
            # Should be fast (less than 1 second for 100 accesses)
            assert (end_time - start_time) < 1.0
    
    def test_config_caching_performance(self):
        """Test that configuration caching improves performance."""
        import time
        
        config_manager = ConfigManager()
        
        # First access (no cache)
        start_time = time.time()
        config1 = config_manager.get_database_config()
        first_access_time = time.time() - start_time
        
        # Second access (cached)
        start_time = time.time()
        config2 = config_manager.get_database_config()
        second_access_time = time.time() - start_time
        
        # Cached access should be faster
        assert second_access_time < first_access_time
        assert config1 is config2
    
    def test_memory_usage(self, test_container):
        """Test that modularity improvements don't cause memory leaks."""
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and use services
        for _ in range(10):
            user_service = test_container.user_service
            conversation_service = test_container.conversation_service
            openai_service = test_container.openai_service
            
            # Use services
            _ = user_service
            _ = conversation_service
            _ = openai_service
        
        # Get final memory usage
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should be reasonable (not more than 1000 new objects)
        assert (final_objects - initial_objects) < 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
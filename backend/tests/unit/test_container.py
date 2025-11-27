# Tests for ServiceContainer.
import pytest
from unittest.mock import MagicMock, patch

from app.core.container import ServiceContainer, get_container


class TestServiceContainer:
# Test ServiceContainer class.
    
    def test_init(self):
    # Test ServiceContainer initialization.
        container = ServiceContainer()
        
        assert container._user_service is None
        assert container._conversation_service is None
        assert container._openai_service is None
        assert container._intelligence_service is None
        assert container._memory is None
        assert container._proactive_assistant is None
        assert container._error_recovery is None
        assert container._vacation_planner is None
    
    @patch('app.core.container.get_database')
    def test_user_service_database_unavailable(self, mock_get_database):
    # Test user_service when database is unavailable.
        mock_get_database.return_value = None
        
        container = ServiceContainer()
        
        with pytest.raises(RuntimeError, match="Database is not available"):
            _ = container.user_service
    
    @patch('app.core.container.get_database')
    def test_conversation_service_database_unavailable(self, mock_get_database):
    # Test conversation_service when database is unavailable.
        mock_get_database.return_value = None
        
        container = ServiceContainer()
        
        with pytest.raises(RuntimeError, match="Database is not available"):
            _ = container.conversation_service
    
    @patch('app.core.container.get_database')
    def test_user_service_creates_service(self, mock_get_database):
    # Test user_service creates service instance.
        mock_db = MagicMock()
        mock_db.users = MagicMock()
        mock_get_database.return_value = mock_db
        
        container = ServiceContainer()
        service = container.user_service
        
        assert service is not None
        assert container._user_service is not None
    
    @patch('app.core.container.get_database')
    def test_conversation_service_creates_service(self, mock_get_database):
    # Test conversation_service creates service instance.
        mock_db = MagicMock()
        mock_db.conversations = MagicMock()
        mock_get_database.return_value = mock_db
        
        container = ServiceContainer()
        service = container.conversation_service
        
        assert service is not None
        assert container._conversation_service is not None
    
    def test_openai_service_creates_service(self):
    # Test openai_service creates service instance.
        container = ServiceContainer()
        service = container.openai_service
        
        assert service is not None
        assert container._openai_service is not None
    
    def test_intelligence_service_creates_service(self):
    # Test intelligence_service creates service instance.
        container = ServiceContainer()
        service = container.intelligence_service
        
        assert service is not None
        assert container._intelligence_service is not None
    
    def test_memory_creates_service(self):
    # Test memory creates service instance.
        container = ServiceContainer()
        service = container.memory
        
        assert service is not None
        assert container._memory is not None
    
    def test_proactive_assistant_creates_service(self):
    # Test proactive_assistant creates service instance.
        container = ServiceContainer()
        service = container.proactive_assistant
        
        assert service is not None
        assert container._proactive_assistant is not None
    
    def test_error_recovery_creates_service(self):
    # Test error_recovery creates service instance.
        container = ServiceContainer()
        service = container.error_recovery
        
        assert service is not None
        assert container._error_recovery is not None
    
    def test_vacation_planner_creates_service(self):
    # Test vacation_planner creates service instance.
        container = ServiceContainer()
        service = container.vacation_planner
        
        assert service is not None
        assert container._vacation_planner is not None
    
    
    def test_reset(self):
    # Test reset method clears all services.
        container = ServiceContainer()
        container._user_service = MagicMock()
        container._conversation_service = MagicMock()
        container._openai_service = MagicMock()
        container._intelligence_service = MagicMock()
        container._memory = MagicMock()
        container._proactive_assistant = MagicMock()
        container._error_recovery = MagicMock()
        container._vacation_planner = MagicMock()
        
        container.reset()
        
        assert container._user_service is None
        assert container._conversation_service is None
        assert container._openai_service is None
        assert container._intelligence_service is None
        assert container._memory is None
        assert container._proactive_assistant is None
        assert container._error_recovery is None
        assert container._vacation_planner is None


class TestGetContainer:
# Test get_container function.
    
    def test_get_container_returns_singleton(self):
    # Test get_container returns singleton instance.
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2



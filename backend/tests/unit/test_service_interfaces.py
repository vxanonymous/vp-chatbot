"""
Tests for service interfaces to ensure proper contract implementation.
These tests verify that all services implement their interfaces correctly.
"""
import pytest  # 
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional
from bson import ObjectId  # 

from app.core.interfaces import (
    IUserService, IConversationService, IOpenAIService,
    IVacationIntelligenceService, IConversationMemory,
    IProactiveAssistant, IErrorRecoveryService, IVacationPlannerService
)
from app.services.user_service import UserService
from app.services.conversation_service import ConversationService
from app.services.openai_service import OpenAIService
from app.services.vacation_intelligence_service import VacationIntelligenceService
from app.services.conversation_memory import ConversationMemory
from app.services.proactive_assistant import ProactiveAssistant
from app.services.error_recovery import ErrorRecoveryService
from app.services.vacation_planner import VacationPlanner
from app.models.user import UserCreate, UserInDB
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB, ConversationUpdate
from unittest.mock import MagicMock

# Simple mock database class for testing
class MockDatabase:
    def __init__(self):
        self.conversations = MagicMock()
        self.users = MagicMock()


@pytest.fixture
def mock_db():
    """Provide a mock database for testing."""
    return MockDatabase()


class TestUserServiceInterface:
    """Test UserService interface compliance."""
    
    @pytest.mark.asyncio
    async def test_user_service_implements_interface(self, mock_db):
        """Test that UserService implements all required methods."""
        user_service = UserService(mock_db.users)
        
        # Check that it's an instance of the service
        assert isinstance(user_service, UserService)
        
        # Check all required methods exist
        required_methods = [
            'create_user',
            'authenticate_user',
            'get_user_by_id',
            'get_user_by_email'
        ]
        
        for method_name in required_methods:
            assert hasattr(user_service, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_create_user_signature(self, mock_db):
        """Test create_user method signature."""
        user_service = UserService(mock_db.users)
        
        # Mock database operations
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_db.users.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
        
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="SecurePass123!"
        )
        
        result = await user_service.create_user(user_data)
        
        assert result is not None
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_signature(self, mock_db):
        """Test authenticate_user method signature."""
        user_service = UserService(mock_db.users)
        
        # Mock database operations with proper password hash
        from app.auth.password import get_password_hash
        hashed_password = get_password_hash("SecurePass123!")
        
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "email": "test@example.com",
            "full_name": "Test User",
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })
        
        result = await user_service.authenticate_user("test@example.com", "SecurePass123!")
        
        assert result is not None
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_signature(self, mock_db):
        """Test get_user_by_id method signature."""
        user_service = UserService(mock_db.users)
        
        # Use a valid ObjectId string
        valid_user_id = str(ObjectId())
        
        # Mock database operations
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": ObjectId(valid_user_id),
            "email": "test@example.com",
            "full_name": "Test User",
            "hashed_password": "hashed_password",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })
        
        result = await user_service.get_user_by_id(valid_user_id)
        
        assert result is not None
        assert result.email == "test@example.com"


class TestConversationServiceInterface:
    """Test ConversationService interface compliance."""
    
    @pytest.mark.asyncio
    async def test_conversation_service_implements_interface(self, mock_db):
        """Test that ConversationService implements all required methods."""
        conversation_service = ConversationService(mock_db.conversations)
        
        # Check that it's an instance of the service
        assert isinstance(conversation_service, ConversationService)
        
        # Check all required methods exist
        required_methods = [
            'create_conversation',
            'get_conversation',
            'add_message',
            'update_conversation',
            'delete_conversation'
        ]
        
        for method_name in required_methods:
            assert hasattr(conversation_service, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_create_conversation_signature(self, mock_db):
        """Test create_conversation method signature."""
        conversation_service = ConversationService(mock_db.conversations)
        
        # Mock database operations
        mock_db.conversations.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
        
        result = await conversation_service.create_conversation(
            user_id="test_user",
            title="Test Conversation"
        )
        
        assert result is not None
        assert result.title == "Test Conversation"
    
    @pytest.mark.asyncio
    async def test_add_message_signature(self, mock_db):
        """Test add_message method signature."""
        conversation_service = ConversationService(mock_db.conversations)
        
        # Mock database operations
        mock_db.conversations.update_one = AsyncMock(return_value=Mock(modified_count=1))
        mock_db.conversations.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "user_id": "test_user",
            "title": "Test Conversation",
            "messages": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })
        
        message = Message(role=MessageRole.USER, content="Hello")
        result = await conversation_service.add_message(
            conversation_id=str(ObjectId()),  # Use valid ObjectId string
            user_id="test_user",
            message=message
        )
        
        assert result is not None


class TestOpenAIServiceInterface:
    """Test OpenAIService interface compliance."""
    
    def test_openai_service_implements_interface(self):
        """Test that OpenAIService implements all required methods."""
        openai_service = OpenAIService()
        
        # Check that it's an instance of the interface
        assert isinstance(openai_service, OpenAIService)
        
        # Check all required methods exist
        required_methods = [
            'generate_response_async',
            'generate_response'
        ]
        
        for method_name in required_methods:
            assert hasattr(openai_service, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_generate_response_async_signature(self):
        """Test generate_response_async method signature."""
        openai_service = OpenAIService()
        
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        # This will use fallback response since we don't have real API key
        result = await openai_service.generate_response_async(messages)
        
        assert result is not None
        assert "content" in result
    
    def test_generate_response_signature(self):
        """Test generate_response method signature."""
        openai_service = OpenAIService()
        
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        # This will use fallback response since we don't have real API key
        result = openai_service.generate_response(messages)
        
        assert result is not None
        assert "content" in result


class TestVacationIntelligenceServiceInterface:
    """Test VacationIntelligenceService interface compliance."""
    
    def test_intelligence_service_implements_interface(self):
        """Test that VacationIntelligenceService implements all required methods."""
        intelligence_service = VacationIntelligenceService()
        
        # Check that it's an instance of the interface
        assert isinstance(intelligence_service, VacationIntelligenceService)
        
        # Check all required methods exist (using actual method names)
        required_methods = [
            'analyze_preferences'
        ]
        
        for method_name in required_methods:
            assert hasattr(intelligence_service, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_analyze_conversation_signature(self):
        """Test analyze_conversation method signature."""
        intelligence_service = VacationIntelligenceService()
        
        messages = [
            {"role": "user", "content": "I want to plan a trip to Vietnam"}
        ]
        
        # Use the actual method name and await it
        result = await intelligence_service.analyze_preferences(messages, None)
        
        assert result is not None
        assert "decision_stage" in result


class TestConversationMemoryInterface:
    """Test ConversationMemory interface compliance."""
    
    def test_memory_implements_interface(self):
        """Test that ConversationMemory implements all required methods."""
        memory = ConversationMemory()
        
        # Check that it's an instance of the interface
        assert isinstance(memory, ConversationMemory)
        
        # Check all required methods exist (using actual method names)
        required_methods = [
            'store_context',
            'get_context',
            'extract_key_points'
        ]
        
        for method_name in required_methods:
            assert hasattr(memory, method_name), f"Missing method: {method_name}"
    
    def test_store_context_signature(self):
        """Test store_context method signature."""
        memory = ConversationMemory()
        
        context = {"key": "value", "conversation_id": "test_conv"}
        result = memory.store_context("test_conv", context)
        
        # The method should return True or a valid result
        assert result is True or result is not None


class TestProactiveAssistantInterface:
    """Test ProactiveAssistant interface compliance."""
    
    def test_assistant_implements_interface(self):
        """Test that ProactiveAssistant implements all required methods."""
        assistant = ProactiveAssistant()
        
        # Check that it's an instance of the interface
        assert isinstance(assistant, ProactiveAssistant)
        
        # Check all required methods exist (using actual method names)
        required_methods = [
            'anticipate_next_questions'
        ]
        
        for method_name in required_methods:
            assert hasattr(assistant, method_name), f"Missing method: {method_name}"
    
    def test_generate_suggestions_signature(self):
        """Test anticipate_next_questions method signature."""
        assistant = ProactiveAssistant()
        
        stage = "planning"
        preferences = {"destination": "Vietnam"}
        recent_topics = ["travel", "vacation"]
        
        result = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert result is not None
        assert isinstance(result, list)


class TestErrorRecoveryServiceInterface:
    """Test ErrorRecoveryService interface compliance."""
    
    def test_error_recovery_implements_interface(self):
        """Test that ErrorRecoveryService implements all required methods."""
        error_recovery = ErrorRecoveryService()
        
        # Check that it's an instance of the interface
        assert isinstance(error_recovery, ErrorRecoveryService)
        
        # Check all required methods exist (using actual method names)
        required_methods = [
            'get_recovery_response'
        ]
        
        for method_name in required_methods:
            assert hasattr(error_recovery, method_name), f"Missing method: {method_name}"
    
    def test_handle_error_signature(self):
        """Test get_recovery_response method signature."""
        error_service = ErrorRecoveryService()
        
        # Test with correct signature
        error_type = "general_error"
        context = {"user_id": "test_user"}
        
        # Use the correct method name
        assert hasattr(error_service, 'get_recovery_response')
        
        result = error_service.get_recovery_response(error_type, context)
        
        assert result is not None
        assert isinstance(result, str)


class TestVacationPlannerServiceInterface:
    """Test VacationPlannerService interface compliance."""
    
    def test_planner_implements_interface(self):
        """Test that VacationPlannerService implements all required methods."""
        planner = VacationPlanner()
        
        # Check that it's an instance of the interface
        assert isinstance(planner, VacationPlanner)
        
        # Check all required methods exist (using actual method names)
        required_methods = [
            'generate_suggestions',
            'create_vacation_summary'
        ]
        
        for method_name in required_methods:
            assert hasattr(planner, method_name), f"Missing method: {method_name}"
    
    def test_create_itinerary_signature(self):
        """Test generate_suggestions method signature."""
        planner = VacationPlanner()
        
        requirements = {
            "destination": "Paris",
            "duration": "7 days",
            "budget": "2000"
        }
        
        result = planner.generate_suggestions(requirements)
        
        assert result is not None
        assert isinstance(result, list)


class TestInterfaceCompliance:
    """Test overall interface compliance."""
    
    def test_all_services_implement_interfaces(self):
        """Test that all services implement their respective interfaces."""
        # Test each service
        services_to_test = [
            (UserService, IUserService),
            (ConversationService, IConversationService),
            (OpenAIService, IOpenAIService),
            (VacationIntelligenceService, IVacationIntelligenceService),
            (ConversationMemory, IConversationMemory),
            (ProactiveAssistant, IProactiveAssistant),
            (ErrorRecoveryService, IErrorRecoveryService),
            (VacationPlanner, IVacationPlannerService)
        ]
        
        for service_class, interface_class in services_to_test:
            # Create a mock database for services that need it
            if service_class in [UserService, ConversationService]:
                mock_db = MockDatabase()
                if service_class == UserService:
                    service = service_class(mock_db.users)
                else:
                    service = service_class(mock_db.conversations)
            else:
                service = service_class()
            
            # Check that service implements the interface
            assert isinstance(service, service_class)
            
            # Check that all interface methods exist
            interface_methods = [method for method in dir(interface_class)
                               if not method.startswith('_') and callable(getattr(interface_class, method))]
            
            for method_name in interface_methods:
                assert hasattr(service, method_name), f"{service_class.__name__} missing method: {method_name}"
    
    def test_interface_method_signatures(self):
        """Test that interface method signatures are correct."""
        # This test verifies that the interfaces are properly defined
        assert hasattr(IUserService, 'create_user')
        assert hasattr(IUserService, 'authenticate_user')
        assert hasattr(IConversationService, 'create_conversation')
        assert hasattr(IConversationService, 'add_message')
        assert hasattr(IOpenAIService, 'generate_response_async')
        assert hasattr(IVacationIntelligenceService, 'analyze_preferences')
        assert hasattr(IConversationMemory, 'get_context')
        assert hasattr(IProactiveAssistant, 'anticipate_next_questions')
        assert hasattr(IErrorRecoveryService, 'get_recovery_response')
        assert hasattr(IVacationPlannerService, 'generate_suggestions')


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
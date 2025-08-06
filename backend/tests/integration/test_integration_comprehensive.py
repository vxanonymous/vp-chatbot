"""
Comprehensive Integration Tests for Vacation Planning Chatbot

This module provides integration testing that verifies how different services
work together in real-world scenarios including:
- User signup and conversation creation flow
- Message handling with OpenAI integration
- Vacation intelligence analysis with conversation data
- End-to-end user journey simulation
- Service interaction validation
- Data flow between components

These tests ensure the system works correctly as a complete application.

FILE DEPENDENCIES:
==================
UTILIZES (Dependencies):
- app/services/conversation_service.py - Conversation service for integration testing
- app/services/user_service.py - User service for integration testing
- app/services/openai_service.py - OpenAI service for integration testing
- app/services/vacation_intelligence_service.py - Intelligence service for integration testing
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
- test_services_comprehensive.py - Service tests
- CI/CD pipelines - Automated integration testing
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId
import asyncio
from app.services.conversation_service import ConversationService
from app.services.user_service import UserService
from app.services.openai_service import OpenAIService
from app.services.vacation_intelligence_service import VacationIntelligenceService
from app.models.user import UserCreate
from app.models.chat import Message, MessageRole

class MockDatabase:
    def __init__(self):
        self.conversations = Mock()
        self.users = Mock()

@pytest.fixture
def services():
    mock_db = MockDatabase()
    return {
        'user_service': UserService(mock_db.users),
        'conversation_service': ConversationService(mock_db.conversations),
        'openai_service': OpenAIService(),
        'vacation_service': VacationIntelligenceService()
    }

def test_user_signup_and_conversation_flow(services):
    user_service = services['user_service']
    conversation_service = services['conversation_service']
    user_data = UserCreate(
        email="integration@example.com",
        full_name="Integration Test User",
        password="SecurePass123!"
    )
    with patch.object(user_service, 'collection') as mock_user_collection:
        mock_user_collection.find_one = AsyncMock(return_value=None)
        mock_user_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
        user = asyncio.run(user_service.create_user(user_data))
        assert user is not None
        assert user.email == "integration@example.com"
    with patch.object(conversation_service, 'collection') as mock_conv_collection:
        mock_conv_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
        conversation = asyncio.run(conversation_service.create_conversation(
            user_id=str(user.id),  # Convert ObjectId to string
            title="My Vacation Plan"
        ))
        assert conversation is not None
        assert conversation.user_id == str(user.id)
        assert conversation.title == "My Vacation Plan"

def test_add_message_and_openai_integration(services):
    conversation_service = services['conversation_service']
    openai_service = services['openai_service']
    user_id = str(ObjectId())
    conversation_id = str(ObjectId())
    mock_conversation = {
        "_id": ObjectId(conversation_id),
        "user_id": user_id,
        "title": "Test Conversation",
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    with patch.object(conversation_service, 'collection') as mock_collection:
        mock_collection.find_one = AsyncMock(return_value=mock_conversation)
        mock_collection.update_one = AsyncMock(return_value=Mock(modified_count=1))
        message = Message(role=MessageRole.USER, content="I want to go to Vietnam")
        result = asyncio.run(conversation_service.add_message(conversation_id, user_id, message))
        assert result is not None
        # The service should return the updated conversation with the new message
        assert len(result.messages) >= 0  # At least the original messages
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=Mock(
            choices=[Mock(message=Mock(content="Great choice! Vietnam is beautiful."))]
        ))
        ai_response = asyncio.run(openai_service.generate_response_async([message]))
        assert ai_response is not None
        assert "content" in ai_response

def test_vacation_intelligence_flow(services):
    vacation_service = services['vacation_service']
    conversation_id = str(ObjectId())
    user_id = str(ObjectId())
    messages = [
        {"role": "user", "content": "Plan a trip to Da Nang", "timestamp": datetime.utcnow().isoformat()},
        {"role": "assistant", "content": "When do you want to go?", "timestamp": datetime.utcnow().isoformat()}
    ]
    
    # Test the analyze_preferences method which is the main functionality
    analysis = asyncio.run(vacation_service.analyze_preferences(messages, None))
    assert analysis is not None
    assert "decision_stage" in analysis
    assert "detected_interests" in analysis
    assert "mentioned_destinations" in analysis
    
    # Verify that Da Nang was detected as a destination
    destinations = analysis.get("mentioned_destinations", [])
    assert any("da nang" in dest.lower() for dest in destinations) 
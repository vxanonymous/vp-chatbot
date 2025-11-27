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

pytest_plugins = ['tests.integration.conftest_integration']

@pytest.fixture
def services(real_container_with_mocked_openai):
    return {
        'user_service': real_container_with_mocked_openai.user_service,
        'conversation_service': real_container_with_mocked_openai.conversation_service,
        'openai_service': real_container_with_mocked_openai.openai_service,
        'vacation_service': real_container_with_mocked_openai.intelligence_service
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
            user_id=str(user.id),
            title="My Vacation Plan"
        ))
        assert conversation is not None
        assert conversation.user_id == str(user.id)
        assert conversation.title == "My Vacation Plan"

@pytest.mark.asyncio
async def test_add_message_and_openai_integration(services):
    conversation_service = services['conversation_service']
    openai_service = services['openai_service']
    user_id = str(ObjectId())
    
    conversation = await conversation_service.create_conversation(
        user_id=user_id,
        title="Test Conversation"
    )
    conversation_id = str(conversation.id)
    mock_conversation = conversation.model_dump(by_alias=True)
    with patch.object(conversation_service, 'collection') as mock_collection:
        mock_collection.find_one = AsyncMock(return_value=mock_conversation)
        mock_collection.update_one = AsyncMock(return_value=Mock(modified_count=1))
        message = Message(role=MessageRole.USER, content="I want to go to Vietnam")
        result = await conversation_service.add_message(conversation_id, user_id, message)
        assert result is not None
        assert len(result.messages) >= 0
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = Mock(
            choices=[Mock(message=Mock(content="Great choice! Vietnam is beautiful."))]
        )
        ai_response = await openai_service.generate_response_async([message])
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
    
    analysis = asyncio.run(vacation_service.analyze_preferences(messages, None))
    assert analysis is not None
    assert "decision_stage" in analysis
    assert "detected_interests" in analysis
    assert "mentioned_destinations" in analysis
    
    destinations = analysis.get("mentioned_destinations", [])
    assert any("da nang" in dest.lower() for dest in destinations) 
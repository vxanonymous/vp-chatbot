import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.chat import Message, MessageRole, ChatRequest, ChatResponse, ConversationHistory


class TestMessage:
    
    def test_message_creation(self):
        message = Message(role=MessageRole.USER, content="Hello")
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.timestamp is not None
        assert message.metadata is None
    
    def test_message_with_metadata(self):
        metadata = {"key": "value"}
        message = Message(role=MessageRole.ASSISTANT, content="Hi", metadata=metadata)
        assert message.metadata == metadata
    
    def test_message_timestamp_default(self):
        message1 = Message(role=MessageRole.USER, content="Test")
        message2 = Message(role=MessageRole.USER, content="Test")
        assert message1.timestamp is not None
        assert message2.timestamp is not None
    
    def test_message_all_roles(self):
        user_msg = Message(role=MessageRole.USER, content="User message")
        assistant_msg = Message(role=MessageRole.ASSISTANT, content="Assistant message")
        system_msg = Message(role=MessageRole.SYSTEM, content="System message")
        
        assert user_msg.role == MessageRole.USER
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert system_msg.role == MessageRole.SYSTEM


class TestChatRequest:
    
    def test_chat_request_creation(self):
        request = ChatRequest(message="Hello")
        assert request.message == "Hello"
        assert request.conversation_id is None
        assert request.user_preferences is None
    
    def test_chat_request_with_conversation_id(self):
        request = ChatRequest(message="Hello", conversation_id="conv_123")
        assert request.conversation_id == "conv_123"
    
    def test_chat_request_with_preferences(self):
        preferences = {"destinations": ["Paris"]}
        request = ChatRequest(message="Hello", user_preferences=preferences)
        assert request.user_preferences == preferences
    
    def test_chat_request_empty_message(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")
    
    def test_chat_request_too_long_message(self):
        long_message = "a" * 10000
        with pytest.raises(ValidationError):
            ChatRequest(message=long_message)


class TestChatResponse:
    
    def test_chat_response_creation(self):
        response = ChatResponse(response="Hello", conversation_id="conv_123")
        assert response.response == "Hello"
        assert response.conversation_id == "conv_123"
        assert response.suggestions is None
        assert response.vacation_summary is None
    
    def test_chat_response_with_suggestions(self):
        suggestions = ["Suggestion 1", "Suggestion 2"]
        response = ChatResponse(
            response="Hello",
            conversation_id="conv_123",
            suggestions=suggestions
        )
        assert response.suggestions == suggestions
    
    def test_chat_response_with_vacation_summary(self):
        summary = {"destination": "Paris"}
        response = ChatResponse(
            response="Hello",
            conversation_id="conv_123",
            vacation_summary=summary
        )
        assert response.vacation_summary == summary


class TestConversationHistory:
    
    def test_conversation_history_creation(self):
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi")
        ]
        now = datetime.now()
        history = ConversationHistory(
            conversation_id="conv_123",
            messages=messages,
            created_at=now,
            updated_at=now
        )
        assert history.conversation_id == "conv_123"
        assert len(history.messages) == 2
        assert history.created_at == now
        assert history.updated_at == now
        assert history.user_preferences is None
    
    def test_conversation_history_with_preferences(self):
        messages = [Message(role=MessageRole.USER, content="Hello")]
        preferences = {"destinations": ["Paris"]}
        now = datetime.now()
        history = ConversationHistory(
            conversation_id="conv_123",
            messages=messages,
            created_at=now,
            updated_at=now,
            user_preferences=preferences
        )
        assert history.user_preferences == preferences



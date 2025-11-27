import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.openai_service import OpenAIService
from app.models.chat import Message, MessageRole


class TestEnhancedTopicDriftPrevention:
    
    @pytest.fixture
    def openai_service(self):
    # Create OpenAI service with mocked client.
        service = OpenAIService()
        service.client = MagicMock()
        return service
    
    @pytest.fixture
    def mock_openai_client(self, openai_service):
    # Get the mocked OpenAI client.
        return openai_service.client
    
    def test_is_travel_related_with_travel_message(self, openai_service, mock_openai_client):
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "yes"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        message = "I want to plan a trip to Paris"
        result = openai_service._is_travel_related(message)
        
        # Verify result
        assert result is True
        
        # Verify OpenAI was called
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args
        
        # Check the prompt contains the message
        prompt = call_args[1]['messages'][0]['content']
        assert "I want to plan a trip to Paris" in prompt
        assert "travel planning" in prompt.lower()
    
    def test_is_travel_related_with_non_travel_message(self, openai_service, mock_openai_client):
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "no"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        message = "What's the weather like today?"
        result = openai_service._is_travel_related(message)
        
        # Verify result
        assert result is False
        
        # Verify OpenAI was called
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_is_travel_related_without_openai_client(self):
        # Create service without client
        service = OpenAIService()
        service.client = None
        
        travel_message = "I want to book a hotel in Tokyo"
        result = service._is_travel_related(travel_message)
        assert result is True
        
        non_travel_message = "What's 2+2?"
        result = service._is_travel_related(non_travel_message)
        assert result is False
    
    def test_is_travel_related_with_conversation_context(self, openai_service, mock_openai_client):
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "yes"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create conversation history
        history = [
            Message(role=MessageRole.USER, content="I want to go to Italy"),
            Message(role=MessageRole.ASSISTANT, content="Italy is wonderful! What cities interest you?"),
            Message(role=MessageRole.USER, content="I love pasta")
        ]
        
        result = openai_service._is_travel_related("I love pasta", history)
        
        # Verify result
        assert result is True
        
        # Verify OpenAI was called
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args
        
        # Check the prompt contains the user message
        prompt = call_args[1]['messages'][0]['content']
        assert 'I want to go to Italy' in prompt or 'I love pasta' in prompt
    
    def test_generate_topic_redirect_response(self, openai_service):
        message = "What's the capital of France?"
        response = openai_service._generate_topic_redirect_response(message)
        
        # Verify response contains travel-related content
        assert "travel" in response.lower()
        assert len(response) > 50
        
        # Verify it's a redirect response
        redirect_keywords = ["planning", "vacation", "trip", "destination"]
        assert any(keyword in response.lower() for keyword in redirect_keywords)
    
    def test_topic_drift_detection_in_generate_response(self, openai_service, mock_openai_client):
        # Mock the intent classification to return False (non-travel)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "no"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create messages with non-travel content
        messages = [
            Message(role=MessageRole.USER, content="What's the weather like?")
        ]
        
        result = openai_service.generate_response(messages)
        
        # Verify topic drift was detected
        assert result["topic_drift_detected"] is True
        assert "travel" in result["content"].lower()
        assert result["confidence_score"] == 0.8
    
    def test_no_topic_drift_with_travel_message(self, openai_service, mock_openai_client):
        # Mock the intent classification to return True (travel-related)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "yes"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Mock the main response generation
        mock_main_response = MagicMock()
        mock_main_response.choices = [MagicMock()]
        mock_main_response.choices[0].message.content = "I'd love to help you plan your trip to Paris!"
        mock_main_response.choices[0].message.function_call = None
        
        # Set up the mock to return different responses for different calls
        mock_openai_client.chat.completions.create.side_effect = [mock_response, mock_main_response]
        
        # Create messages with travel content
        messages = [
            Message(role=MessageRole.USER, content="I want to go to Paris")
        ]
        
        result = openai_service.generate_response(messages)
        
        # Verify no topic drift was detected
        assert "topic_drift_detected" not in result
        assert "paris" in result["content"].lower()
    
    def test_error_handling_in_intent_classification(self, openai_service, mock_openai_client):
        # Mock an error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        message = "I want to go to Paris"
        result = openai_service._is_travel_related(message)
        
        # Should default to True (fail open)
        assert result is True
    
    def test_empty_response_handling(self, openai_service, mock_openai_client):
        # Mock empty response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        message = "I want to go to Paris"
        result = openai_service._is_travel_related(message)
        
        # Should default to True (fail open)
        assert result is True
    
    def test_topic_drift_with_mixed_conversation(self, openai_service, mock_openai_client):
        # Mock the intent classification to return False for non-travel message
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "no"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create mixed conversation
        messages = [
            Message(role=MessageRole.USER, content="I want to go to Italy"),
            Message(role=MessageRole.ASSISTANT, content="Italy is wonderful! What cities interest you?"),
            Message(role=MessageRole.USER, content="What's the capital of France?")
        ]
        
        result = openai_service.generate_response(messages)
        
        # Verify topic drift was detected
        assert result["topic_drift_detected"] is True
        assert "travel" in result["content"].lower()
    
    def test_topic_drift_prevention_preserves_context(self, openai_service, mock_openai_client):
        # Mock the intent classification to return True (travel-related)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "yes"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Mock the main response generation
        mock_main_response = MagicMock()
        mock_main_response.choices = [MagicMock()]
        mock_main_response.choices[0].message.content = "For your Italy trip, I recommend visiting Rome!"
        mock_main_response.choices[0].message.function_call = None
        
        # Set up the mock to return different responses for different calls
        mock_openai_client.chat.completions.create.side_effect = [mock_response, mock_main_response]
        
        # Create conversation with context
        messages = [
            Message(role=MessageRole.USER, content="I want to go to Italy"),
            Message(role=MessageRole.ASSISTANT, content="Italy is wonderful! What cities interest you?"),
            Message(role=MessageRole.USER, content="I'm interested in Rome")
        ]
        
        result = openai_service.generate_response(messages)
        
        # Verify context was preserved
        assert "topic_drift_detected" not in result
        assert "italy" in result["content"].lower()
        assert "rome" in result["content"].lower()
    
    def test_multiple_topic_drift_attempts(self, openai_service, mock_openai_client):
        # Mock the intent classification to return False for non-travel messages
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "no"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        non_travel_messages = [
            "What's the weather like?",
            "How do I cook pasta?",
            "What's the capital of France?",
            "Tell me a joke"
        ]
        
        for message in non_travel_messages:
            messages = [Message(role=MessageRole.USER, content=message)]
            result = openai_service.generate_response(messages)
            
            # Verify topic drift was detected each time
            assert result["topic_drift_detected"] is True
            assert "travel" in result["content"].lower()
    
    def test_topic_drift_with_edge_cases(self, openai_service, mock_openai_client):
        # Mock the intent classification to return False
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "no"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        edge_cases = [
            "",
            "   ",
            "a",
            "123",
            "!@#$%",
        ]
        
        for message in edge_cases:
            messages = [Message(role=MessageRole.USER, content=message)]
            result = openai_service.generate_response(messages)
            
            # Should handle gracefully
            assert "topic_drift_detected" in result or "content" in result 
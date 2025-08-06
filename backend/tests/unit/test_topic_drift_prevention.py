"""
Tests for topic drift prevention using LLM-based intent classification.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.openai_service import OpenAIService
from app.models.chat import Message, MessageRole


class TestTopicDriftPrevention:
    """Test the topic drift prevention functionality."""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance for testing."""
        service = OpenAIService()
        # Ensure we have a mock client for testing
        service.client = MagicMock()
        return service
    
    @pytest.fixture
    def mock_openai_client(self, openai_service):
        """Mock OpenAI client for testing."""
        return openai_service.client
    
    def test_is_travel_related_with_travel_message(self, openai_service, mock_openai_client):
        """Test that travel-related messages are correctly identified."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "yes"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Test with a travel-related message
        message = "I want to plan a trip to Paris"
        result = openai_service._is_travel_related(message)
        
        assert result is True
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_is_travel_related_with_non_travel_message(self, openai_service, mock_openai_client):
        """Test that non-travel messages are correctly identified."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "no"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Test with a non-travel message
        message = "Can you teach me how to cook pasta?"
        result = openai_service._is_travel_related(message)
        
        assert result is False
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_is_travel_related_without_openai_client(self, openai_service):
        """Test fallback behavior when OpenAI client is not available."""
        # Set client to None to simulate no API key
        openai_service.client = None
        
        # Test with travel keywords
        travel_message = "I want to book a hotel in Tokyo"
        result = openai_service._is_travel_related(travel_message)
        assert result is True
        
        # Test with non-travel keywords
        non_travel_message = "What's the weather like today?"
        result = openai_service._is_travel_related(non_travel_message)
        assert result is False
    
    def test_is_travel_related_with_conversation_context(self, openai_service, mock_openai_client):
        """Test that conversation context is included in the intent check."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "yes"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create conversation history
        conversation_history = [
            Message(role=MessageRole.USER, content="I want to go to Italy"),
            Message(role=MessageRole.ASSISTANT, content="Great! Italy is a wonderful destination."),
            Message(role=MessageRole.USER, content="What about the food there?")
        ]
        
        # Test with context
        message = "What about the food there?"
        result = openai_service._is_travel_related(message, conversation_history)
        
        assert result is True
        # Verify that the context was included in the prompt
        call_args = mock_openai_client.chat.completions.create.call_args
        if call_args:
            prompt = call_args[1]['messages'][0]['content']
            assert 'I want to go to Italy' in prompt or 'What about the food there?' in prompt
    
    def test_generate_topic_redirect_response(self, openai_service):
        """Test that topic redirect responses are generated correctly."""
        message = "Can you teach me to cook?"
        redirect_response = openai_service._generate_topic_redirect_response(message)
        
        # Check that it's a redirect response
        assert "travel" in redirect_response.lower()
        assert len(redirect_response) > 50  # Should be substantial
    
    def test_topic_drift_detection_in_generate_response(self, openai_service, mock_openai_client):
        """Test that topic drift is detected and handled in the main response generation."""
        # Mock the OpenAI response for intent classification
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "no"  # Non-travel message
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create messages with a non-travel message
        messages = [
            Message(role=MessageRole.USER, content="I want to plan a trip to Paris"),
            Message(role=MessageRole.ASSISTANT, content="Paris is wonderful! What would you like to know?"),
            Message(role=MessageRole.USER, content="Can you teach me to cook French food?")
        ]
        
        # Generate response
        result = openai_service.generate_response(messages)
        
        # Should return a redirect response
        assert "topic_drift_detected" in result
        assert result["topic_drift_detected"] is True
        assert "travel" in result["content"].lower()
    
    def test_no_topic_drift_with_travel_message(self, openai_service, mock_openai_client):
        """Test that travel messages don't trigger topic drift detection."""
        # Mock the OpenAI response for intent classification
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "yes"  # Travel message
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Mock the main response generation
        mock_main_response = MagicMock()
        mock_main_choice = MagicMock()
        mock_main_message = MagicMock()
        mock_main_message.content = "Here's some travel advice for Paris!"
        mock_main_choice.message = mock_main_message
        mock_main_response.choices = [mock_main_choice]
        
        # Set up the mock to return different responses for different calls
        mock_openai_client.chat.completions.create.side_effect = [
            mock_response,  # Intent classification
            mock_main_response  # Main response generation
        ]
        
        # Create messages with a travel message
        messages = [
            Message(role=MessageRole.USER, content="I want to plan a trip to Paris"),
            Message(role=MessageRole.ASSISTANT, content="Paris is wonderful! What would you like to know?"),
            Message(role=MessageRole.USER, content="What are the best hotels in Paris?")
        ]
        
        # Generate response
        result = openai_service.generate_response(messages)
        
        # Should not have topic drift detection
        assert "topic_drift_detected" not in result
        assert "hotels" in result["content"].lower() or "paris" in result["content"].lower()
    
    def test_error_handling_in_intent_classification(self, openai_service, mock_openai_client):
        """Test that errors in intent classification are handled gracefully."""
        # Mock an error in the OpenAI call
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Test with any message
        message = "I want to plan a trip"
        result = openai_service._is_travel_related(message)
        
        # Should default to True (fail open) on error
        assert result is True
    
    def test_empty_response_handling(self, openai_service, mock_openai_client):
        """Test handling of empty responses from OpenAI."""
        # Mock empty response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = ""  # Empty response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Test with any message
        message = "I want to plan a trip"
        result = openai_service._is_travel_related(message)
        
        # Should default to True on empty response
        assert result is True 
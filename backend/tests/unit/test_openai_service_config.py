# Tests for OpenAIService config-based functionality.
import pytest
from unittest.mock import patch, MagicMock
from app.services.openai_service import OpenAIService
from app.models.chat import Message, MessageRole


class TestOpenAIServiceDestinationResponses:
# Test destination-specific response functionality.
    
    @pytest.fixture
    def openai_service(self):
        # Create OpenAIService instance.
        from app.config import Settings
        mock_settings = Settings(
            openrouter_api_key="",
            openrouter_model="x-ai/grok-4.1-fast",
            openrouter_temperature=0.8,
            openrouter_max_tokens=2000
        )
        with patch('app.config.get_settings', return_value=mock_settings):
            return OpenAIService()
    
    def test_get_destination_specific_budget_response(self, openai_service):
    # Test destination-specific budget response from config.
        result = openai_service._get_destination_specific_budget_response("Paris")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Paris" in result or "paris" in result.lower()
    
    def test_get_destination_specific_budget_response_fallback(self, openai_service):
    # Test destination-specific budget response fallback.
        result = openai_service._get_destination_specific_budget_response("Unknown")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Unknown" in result
    
    def test_get_destination_specific_timing_response(self, openai_service):
    # Test destination-specific timing response from config.
        result = openai_service._get_destination_specific_timing_response("Paris")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Paris" in result or "paris" in result.lower()
    
    def test_get_destination_specific_activity_response(self, openai_service):
    # Test destination-specific activity response from config.
        result = openai_service._get_destination_specific_activity_response("Paris")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Paris" in result or "paris" in result.lower()
    
    def test_generate_contextual_fallback_with_destination_introduction(self, openai_service):
    # Test contextual fallback with destination introduction from config.
        messages = [
            Message(role=MessageRole.USER, content="I want to go to paris")
        ]
        
        result = openai_service._generate_contextual_fallback_response(messages)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "paris" in result.lower() or "Paris" in result


class TestOpenAIServiceTravelStyles:
# Test travel styles extraction from config.
    
    @pytest.fixture
    def openai_service(self):
        # Create OpenAIService instance.
        from app.config import Settings
        mock_settings = Settings(
            openrouter_api_key="",
            openrouter_model="x-ai/grok-4.1-fast",
            openrouter_temperature=0.8,
            openrouter_max_tokens=2000
        )
        with patch('app.config.get_settings', return_value=mock_settings):
            return OpenAIService()
    
    def test_extract_travel_styles_from_config(self, openai_service):
    # Test travel styles extraction using config.
        text = "I love hiking and climbing mountains"
        result = openai_service._extract_travel_styles(text)
        
        assert isinstance(result, list)
        assert "hiking" in result or "climbing" in result
    
    def test_extract_travel_styles_multiple(self, openai_service):
    # Test travel styles extraction with multiple matches.
        text = "I want adventure and relaxation"
        result = openai_service._extract_travel_styles(text)
        
        assert isinstance(result, list)
        assert "adventure" in result
        assert "relaxation" in result
    
    def test_extract_travel_styles_no_match(self, openai_service):
    # Test travel styles extraction with no matches.
        text = "I want to go somewhere"
        result = openai_service._extract_travel_styles(text)
        
        assert isinstance(result, list)
        assert result == []


class TestOpenAIServiceInterests:
# Test interests extraction from config.
    
    @pytest.fixture
    def openai_service(self):
        # Create OpenAIService instance.
        from app.config import Settings
        mock_settings = Settings(
            openrouter_api_key="",
            openrouter_model="x-ai/grok-4.1-fast",
            openrouter_temperature=0.8,
            openrouter_max_tokens=2000
        )
        with patch('app.config.get_settings', return_value=mock_settings):
            return OpenAIService()
    
    def test_extract_interests_from_config(self, openai_service):
    # Test interests extraction using config.
        text = "I love hiking and visiting museums"
        result = openai_service._extract_interests(text)
        
        assert isinstance(result, list)
        assert "hiking" in result
        assert "museums" in result
    
    def test_extract_interests_multiple_categories(self, openai_service):
    # Test interests extraction with multiple categories.
        text = "I enjoy hiking and cooking"
        result = openai_service._extract_interests(text)
        
        assert isinstance(result, list)
        assert "hiking" in result
        assert "cooking" in result
    
    def test_extract_interests_no_match(self, openai_service):
    # Test interests extraction with no matches.
        text = "I want to travel"
        result = openai_service._extract_interests(text)
        
        assert isinstance(result, list)
        assert result == []



import pytest
from unittest.mock import MagicMock, patch

from app.services.openai_service import OpenAIService
from app.models.chat import Message, MessageRole


class TestOpenAIServiceMockCoverage:
# Test OpenAIService mock initialization and edge cases.
    
    def test_openai_service_init_without_api_key(self):
        # Test OpenAIService initialization without API key
        with patch('app.services.openai_service.settings') as mock_settings:
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
            mock_settings.openrouter_temperature = 0.7
            mock_settings.openrouter_max_tokens = 8000
            
            service = OpenAIService()
            assert service.client is None
            assert service.model == "x-ai/grok-4.1-fast"
    
    def test_openai_service_init_with_api_key(self):
    # Test OpenAIService initialization with API key.
        with patch('app.services.openai_service.OpenAI') as mock_openai:
            with patch('app.services.openai_service.settings') as mock_settings:
                mock_settings.openrouter_api_key = "test-key"
                mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
                mock_settings.openrouter_temperature = 0.7
                mock_settings.openrouter_max_tokens = 8000
                
                service = OpenAIService()
                assert service.client is not None
    
    def test_load_example_interactions_invalid_config(self):
    # Test example_interactions property.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            result = service.example_interactions
            assert isinstance(result, list)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_conversation_title_no_client(self):
    # Test generate_conversation_title when client is None.
        with patch('app.services.openai_service.OpenAI'):
            with patch('app.services.openai_service.settings') as mock_settings:
                mock_settings.openrouter_api_key = None
                mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
                mock_settings.openrouter_temperature = 0.7
                mock_settings.openrouter_max_tokens = 8000
                
                service = OpenAIService()
                result = await service.generate_conversation_title("Test message")
                assert result is not None
    
    def test_generate_contextual_fallback_with_destination_introduction(self):
    # Test _generate_contextual_fallback_response with destination introduction.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            messages = [
                Message(role=MessageRole.USER, content="I want to go to paris")
            ]
            
            result = service._generate_contextual_fallback_response(messages)
            assert isinstance(result, str)
            assert len(result) > 0
            assert "paris" in result.lower()
    
    def test_generate_contextual_fallback_budget_query(self):
    # Test _generate_contextual_fallback_response with budget query.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            messages = [
                Message(role=MessageRole.USER, content="What's the budget for paris?")
            ]
            
            with patch.object(service, '_extract_conversation_context', return_value="Destinations mentioned: Paris"):
                with patch.object(service, '_get_destination_specific_budget_response', return_value="Budget info"):
                    result = service._generate_contextual_fallback_response(messages)
                    assert result is not None
    
    def test_generate_contextual_fallback_timing_query(self):
    # Test _generate_contextual_fallback_response with timing query.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            messages = [
                Message(role=MessageRole.USER, content="When is the best time to visit paris?")
            ]
            
            with patch.object(service, '_extract_conversation_context', return_value="Destinations mentioned: Paris"):
                with patch.object(service, '_get_destination_specific_timing_response', return_value="Timing info"):
                    result = service._generate_contextual_fallback_response(messages)
                    assert result is not None
    
    def test_generate_contextual_fallback_activity_query(self):
    # Test _generate_contextual_fallback_response with activity query.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            messages = [
                Message(role=MessageRole.USER, content="What can I do in paris?")
            ]
            
            with patch.object(service, '_extract_conversation_context', return_value="Destinations mentioned: Paris"):
                with patch.object(service, '_get_destination_specific_activity_response', return_value="Activity info"):
                    result = service._generate_contextual_fallback_response(messages)
                    assert result is not None
    
    def test_generate_contextual_fallback_generic_destination_response(self):
    # Test _generate_contextual_fallback_response with generic destination response.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            messages = [
                Message(role=MessageRole.USER, content="Tell me about paris")
            ]
            
            with patch.object(service, '_extract_conversation_context', return_value="Destinations mentioned: Paris"):
                result = service._generate_contextual_fallback_response(messages)
                assert "paris" in result.lower()
    
    def test_get_destination_specific_budget_response_with_match(self):
    # Test _get_destination_specific_budget_response with matching destination.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            result = service._get_destination_specific_budget_response("Paris")
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Paris" in result or "paris" in result.lower()
    
    def test_get_destination_specific_timing_response_with_match(self):
    # Test _get_destination_specific_timing_response with matching destination.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            result = service._get_destination_specific_timing_response("Paris")
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Paris" in result or "paris" in result.lower()
    
    def test_get_destination_specific_activity_response_with_match(self):
    # Test _get_destination_specific_activity_response with matching destination.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            
            result = service._get_destination_specific_activity_response("Paris")
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Paris" in result or "paris" in result.lower()



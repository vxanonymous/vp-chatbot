# Tests for OpenAIService fallback templates to reach 90% coverage.
import pytest
from unittest.mock import MagicMock, patch

from app.services.openai_service import OpenAIService
from app.models.chat import Message, MessageRole


class TestOpenAIServiceFallbackTemplates:
# Test fallback template coverage.
    
    @pytest.fixture
    def openai_service(self):
    # Create OpenAIService instance.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            service.client = MagicMock()
            return service
    
    def test_get_destination_specific_budget_response_no_fallback_template(self, openai_service):
    # Test _get_destination_specific_budget_response without fallback template.
        result = openai_service._get_destination_specific_budget_response("Unknown")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Unknown" in result
    
    def test_get_destination_specific_timing_response_no_fallback_template(self, openai_service):
    # Test _get_destination_specific_timing_response without fallback template.
        result = openai_service._get_destination_specific_timing_response("Unknown")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Unknown" in result
    
    def test_get_destination_specific_activity_response_no_fallback_template(self, openai_service):
    # Test _get_destination_specific_activity_response without fallback template.
        result = openai_service._get_destination_specific_activity_response("Unknown")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Unknown" in result
    
    def test_generate_fallback_response(self, openai_service):
    # Test _generate_fallback_response.
        with patch.object(openai_service, '_generate_contextual_fallback_response', return_value="Fallback response"):
            result = openai_service._generate_fallback_response("Hello")
            assert result == "Fallback response"


# Tests for OpenAIService _load_example_interactions to reach 90% coverage.
import pytest
from unittest.mock import MagicMock, patch

from app.services.openai_service import OpenAIService


class TestOpenAIServiceLoadExamples:
# Test _load_example_interactions coverage.
    
    @pytest.fixture
    def openai_service(self):
    # Create OpenAIService instance.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            service.client = MagicMock()
            return service
    
    def test_load_example_interactions_fallback_examples(self, openai_service):
    # Test example_interactions property.
        result = openai_service.example_interactions
        assert isinstance(result, list)
        assert len(result) > 0
        assert "user" in result[0]
        assert "assistant" in result[0]



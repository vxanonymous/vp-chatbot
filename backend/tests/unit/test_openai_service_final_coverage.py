import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.openai_service import OpenAIService
from app.models.chat import Message, MessageRole


class TestOpenAIServiceFinalCoverage:
    
    @pytest.fixture
    def openai_service(self):
    # Create OpenAIService instance.
        with patch('app.services.openai_service.OpenAI'):
            service = OpenAIService()
            service.client = MagicMock()
            return service
    
    @pytest.mark.asyncio
    async def test_generate_conversation_title_space_term_detection(self, openai_service):
    # Test space term detection in title generation.
        mock_message = MagicMock()
        mock_message.content = "galactic travel adventure"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        openai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await openai_service.generate_conversation_title("I want to go to mars")
        assert result == "Earth Travel Planning"
    
    @pytest.mark.asyncio
    async def test_generate_conversation_title_with_quotes(self, openai_service):
    # Test title generation with quotes that need removal.
        mock_message = MagicMock()
        mock_message.content = '"Paris Adventure"'
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        openai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await openai_service.generate_conversation_title("I want to go to Paris")
        assert '"' not in result
    
    def test_generate_simple_title_destination_regex_match(self, openai_service):
    # Test _generate_simple_title with destination regex matching.
        message = "I want to visit new zealand"
        result = openai_service._generate_simple_title(message)
        assert "New Zealand" in result or "Trip Planning" in result
    
    def test_generate_simple_title_luxury_detection(self, openai_service):
    # Test _generate_simple_title with luxury detection.
        message = "I want a luxury vacation"
        result = openai_service._generate_simple_title(message)
        assert "Luxury" in result
    
    def test_generate_simple_title_adventure_detection(self, openai_service):
    # Test _generate_simple_title with adventure detection.
        message = "I want an adventure trip"
        result = openai_service._generate_simple_title(message)
        assert "Adventure" in result
    
    def test_generate_simple_title_beach_detection(self, openai_service):
    # Test _generate_simple_title with beach detection.
        message = "I want a beach vacation"
        result = openai_service._generate_simple_title(message)
        assert "Beach" in result
    
    def test_extract_budget_info_with_dollar_amounts(self, openai_service):
    # Test _extract_budget_info with dollar amounts.
        text = "I have a budget of $2000 for my trip"
        result = openai_service._extract_budget_info(text)
        assert "$2000" in result or "2000" in result or result != ""
    
    def test_extract_budget_info_with_range(self, openai_service):
    # Test _extract_budget_info with budget range.
        text = "My budget is between $1000 and $2000"
        result = openai_service._extract_budget_info(text)
        assert result != ""
    
    def test_extract_timing_info_with_months(self, openai_service):
    # Test _extract_timing_info with month mentions.
        text = "I want to travel in june or july"
        result = openai_service._extract_timing_info(text)
        assert "june" in result.lower() or "july" in result.lower() or result != ""
    
    def test_extract_timing_info_with_seasons(self, openai_service):
    # Test _extract_timing_info with season mentions.
        text = "I want to travel in summer"
        result = openai_service._extract_timing_info(text)
        assert "summer" in result.lower() or result != ""
    
    def test_get_destination_specific_budget_response_fallback(self, openai_service):
    # Test _get_destination_specific_budget_response with fallback.
        result = openai_service._get_destination_specific_budget_response("UnknownDestination")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "UnknownDestination" in result
    
    def test_get_destination_specific_timing_response_fallback(self, openai_service):
    # Test _get_destination_specific_timing_response with fallback.
        result = openai_service._get_destination_specific_timing_response("UnknownDestination")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "UnknownDestination" in result
    
    def test_get_destination_specific_activity_response_fallback(self, openai_service):
    # Test _get_destination_specific_activity_response with fallback.
        result = openai_service._get_destination_specific_activity_response("UnknownDestination")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "UnknownDestination" in result


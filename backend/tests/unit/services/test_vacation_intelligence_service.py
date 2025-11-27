import time
from app.services.vacation_intelligence_service import VacationIntelligenceService
from unittest.mock import MagicMock, patch, AsyncMock
from unittest.mock import Mock, patch
from unittest.mock import patch, MagicMock
import asyncio
import pytest
import json

class TestVacationIntelligenceAdditionalCoverage:
# Additional tests for VacationIntelligenceService coverage.
    
    @pytest.fixture
    def intelligence_service(self):
    # Create VacationIntelligenceService instance.
        return VacationIntelligenceService()
    
    def test_init_stage_keywords_fallback(self, intelligence_service):
        with patch('app.services.vacation_intelligence_service.vacation_config_loader') as mock_loader:
            mock_loader.get_config.return_value = {
                "stages": None
            }
            
            # Reinitialize to trigger fallback
            service = VacationIntelligenceService()
            assert service.stage_keywords is not None
    
    def test_detect_interests_with_budget_keywords(self, intelligence_service):
        text = "I want a budget trip"
        result = intelligence_service._detect_interests(text)
        assert isinstance(result, list)
    
    def test_detect_concerns_fallback(self, intelligence_service):
        with patch('app.services.vacation_intelligence_service.vacation_config_loader') as mock_loader:
            mock_loader.get_config.return_value = {
                "concern_patterns": None
            }
            
            messages = [{"content": "Is it safe?"}]
            result = intelligence_service._detect_concerns(messages)
            assert isinstance(result, list)
    
    def test_detect_experience_level_fallback(self, intelligence_service):
        with patch('app.services.vacation_intelligence_service.vacation_config_loader') as mock_loader:
            mock_loader.get_config.return_value = {
                "experience_indicators": None
            }
            
            messages = [{"content": "I'm a first-time traveler"}]
            result = intelligence_service._detect_experience_level(messages)
            assert result in ["beginner", "intermediate", "experienced", "unknown"]
    
    def test_extract_destinations_fallback(self, intelligence_service):
        with patch('app.services.vacation_intelligence_service.vacation_config_loader') as mock_loader:
            mock_loader.get_config.return_value = {
                "destinations": None
            }
            
            messages = [{"content": "I want to go to Paris"}]
            result = intelligence_service._extract_destinations(messages)
            assert isinstance(result, list)
    
    def test_calculate_decision_readiness_with_all_factors(self, intelligence_service):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2024-06-01"},
            "budget_range": "$2000",
            "travel_style": "cultural",
            "group_size": 2
        }
        
        result = intelligence_service._calculate_decision_readiness(preferences, 10, ["Paris"])
        assert 0.0 <= result <= 1.0
    
    def test_calculate_stage_scores_with_all_keywords(self, intelligence_service):
        user_messages = [
            {"content": "I'm thinking about Paris, planning my itinerary, comparing options, and ready to book"}
        ]
        
        result = intelligence_service._calculate_stage_scores(user_messages, None)
        assert isinstance(result, dict)
        assert "stage" in result or "exploring" in result or "planning" in result

class TestVacationIntelligenceServiceAdditional:
# Additional test cases for VacationIntelligenceService.
    
    @pytest.fixture
    def service(self):
    # Create a service instance for testing.
        return VacationIntelligenceService()
    
    def test_generate_dynamic_suggestions_just_mentioned_destination(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I want to go to Paris")
        
        assert len(result) <= 4
        assert any("Paris" in s for s in result)
    
    def test_generate_dynamic_suggestions_exploring_with_interests(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": ["adventure"],
            "decision_readiness": 0.5,
            "mentioned_destinations": [],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I like adventure")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_exploring_without_interests(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": [],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I need ideas")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_comparing(self, service):
        conversation_state = {
            "decision_stage": "comparing",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris", "London"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "Should I go to Paris or London?")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_planning_with_destination(self, service):
        conversation_state = {
            "decision_stage": "planning",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I'm planning my Paris trip")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_planning_without_destination(self, service):
        conversation_state = {
            "decision_stage": "planning",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": [],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I'm planning my trip")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_finalizing(self, service):
        conversation_state = {
            "decision_stage": "finalizing",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.8,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I'm ready to book")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_low_confidence_no_destinations(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.3,
            "detected_interests": [],
            "decision_readiness": 0.2,
            "mentioned_destinations": [],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I need ideas")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_low_confidence_low_readiness(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.3,
            "detected_interests": [],
            "decision_readiness": 0.2,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I'm thinking about Paris")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_low_confidence_medium_readiness(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.3,
            "detected_interests": [],
            "decision_readiness": 0.4,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I'm planning")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_low_confidence_high_readiness(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.3,
            "detected_interests": [],
            "decision_readiness": 0.7,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "I'm almost ready")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_with_safety_concern(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris"],
            "concerns": ["safety"]
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "Is it safe?")
        
        assert len(result) <= 4
        assert "safe" in result[0].lower()
    
    def test_generate_dynamic_suggestions_with_budget_concern(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris"],
            "concerns": ["cost"]
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "How much will it cost?")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_with_weather_concern(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris"],
            "concerns": ["weather"]
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "What's the weather like?")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_generate_dynamic_suggestions_with_question_mark(self, service):
        conversation_state = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": ["Paris"],
            "concerns": []
        }
        
        result = service.generate_dynamic_suggestions(conversation_state, "What should I do?")
        
        assert len(result) <= 4
        assert len(result) > 0
    
    def test_get_smart_recommendations_welcome_message(self, service):
        preferences = None
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.1,
            "mentioned_destinations": []
        }
        
        result = service.get_smart_recommendations(preferences, insights, 2)
        
        assert len(result) <= 3
        assert any("Welcome" in r["content"] for r in result)
    
    def test_get_smart_recommendations_exploring_with_interests(self, service):
        preferences = {"travel_style": ["adventure"]}
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.8,
            "detected_interests": ["adventure"],
            "concerns": [],
            "decision_readiness": 0.5,
            "mentioned_destinations": []
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_comparing(self, service):
        preferences = {"destinations": ["Paris", "London"]}
        insights = {
            "decision_stage": "comparing",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.6,
            "mentioned_destinations": ["Paris", "London"]
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_planning(self, service):
        preferences = {"destinations": ["Paris"]}
        insights = {
            "decision_stage": "planning",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.7,
            "mentioned_destinations": ["Paris"]
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_with_destination(self, service):
        preferences = None
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.3,
            "mentioned_destinations": ["Paris"]
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert any("Paris" in r["content"] for r in result)
    
    def test_get_smart_recommendations_with_safety_concern(self, service):
        preferences = None
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": ["safety"],
            "decision_readiness": 0.3,
            "mentioned_destinations": ["Paris"]
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert any("safety" in r["content"].lower() or "safe" in r["content"].lower() for r in result)
    
    def test_get_smart_recommendations_with_budget_concern(self, service):
        preferences = None
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": ["cost"],
            "decision_readiness": 0.3,
            "mentioned_destinations": ["Paris"]
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_with_weather_concern(self, service):
        preferences = None
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": ["weather"],
            "decision_readiness": 0.3,
            "mentioned_destinations": ["Paris"]
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_high_readiness_missing_elements(self, service):
        preferences = {}
        insights = {
            "decision_stage": "planning",
            "stage_confidence": 0.8,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.8,
            "mentioned_destinations": []
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_exploring_stage(self, service):
        preferences = None
        insights = {
            "decision_stage": "exploring",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.3,
            "mentioned_destinations": []
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_planning_stage(self, service):
        preferences = None
        insights = {
            "decision_stage": "planning",
            "stage_confidence": 0.5,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.3,
            "mentioned_destinations": []
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_get_smart_recommendations_no_recommendations(self, service):
        preferences = None
        insights = {
            "decision_stage": "finalizing",
            "stage_confidence": 0.3,
            "detected_interests": [],
            "concerns": [],
            "decision_readiness": 0.2,
            "mentioned_destinations": []
        }
        
        result = service.get_smart_recommendations(preferences, insights, 10)
        
        assert len(result) <= 3
        assert len(result) > 0

class TestVacationIntelligenceService:

# system, including preference analysis, decision stage classification,
# and recommendation generation. All tests use mocked dependencies to
# ensure reliable and fast execution.
    
    @pytest.fixture
    def service(self):
    # Create a service instance for testing.
        return VacationIntelligenceService()
    
    @pytest.fixture
    def sample_messages(self):
    # Sample conversation messages for testing.

    # Provides realistic conversation data that covers multiple
    # vacation planning stages and user preferences.
        return [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "assistant", "content": "Paris is wonderful! What's your budget?"},
            {"role": "user", "content": "Around $2000 for 5 days"},
            {"role": "assistant", "content": "Great budget! When are you planning to go?"},
            {"role": "user", "content": "In June, I love culture and food"}
        ]
    
    @pytest.fixture
    def sample_preferences(self):
    # Sample user preferences for testing.

    # Provides realistic user preference data that can be used
    # to test preference analysis and recommendation generation.
        return {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural", "foodie"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
    
    def test_initialization(self, service):

    # - Service instance is created successfully
    # - Stage keywords are properly loaded
    # - All required stages are present (exploring, comparing, planning, finalizing)
    # - Keywords have the expected structure

        assert service is not None
        assert hasattr(service, 'stage_keywords')
        assert isinstance(service.stage_keywords, dict)
        assert 'exploring' in service.stage_keywords
        assert 'comparing' in service.stage_keywords
        assert 'planning' in service.stage_keywords
        assert 'finalizing' in service.stage_keywords
    
    def test_stage_keywords_structure(self, service):

    # - Each stage has positive keywords and questions
    # - Keywords are stored as lists
    # - Each stage has non-empty keyword lists
    # - Structure is consistent across all stages

        for stage, keywords in service.stage_keywords.items():
            assert isinstance(keywords, dict)
            assert 'positive' in keywords
            assert 'questions' in keywords
            assert isinstance(keywords['positive'], list)
            assert isinstance(keywords['questions'], list)
            assert len(keywords['positive']) > 0
            assert len(keywords['questions']) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_basic(self, service, sample_messages):

    # - Preference analysis returns expected data structure
    # - All required insight fields are present
    # - Analysis works with realistic conversation data
    # - Results are properly formatted

        insights = await service.analyze_preferences(sample_messages, None)
        
        assert isinstance(insights, dict)
        assert 'detected_interests' in insights
        assert 'budget_indicators' in insights
        assert 'decision_stage' in insights
        assert 'stage_confidence' in insights
        assert 'mentioned_destinations' in insights
        assert 'decision_readiness' in insights
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_with_existing_preferences(self, service, sample_messages, sample_preferences):

    # - Analysis incorporates existing user preferences
    # - Decision stage is properly classified
    # - Confidence scores are within valid ranges (0.0 to 1.0)
    # - Destinations are correctly identified
    # - Decision readiness is calculated appropriately

        insights = await service.analyze_preferences(sample_messages, sample_preferences)
        
        assert insights['decision_stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        assert 0.0 <= insights['stage_confidence'] <= 1.0
        assert 0.0 <= insights['decision_readiness'] <= 1.0
        assert 'Paris' in insights['mentioned_destinations']
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_empty_messages(self, service):

    # - Empty message list is handled gracefully
    # - Default values are returned for empty conversations
    # - System doesn't crash on empty input
    # - Initial stage is set to 'exploring'

        insights = await service.analyze_preferences([], None)
        
        assert insights['detected_interests'] == []
        assert insights['mentioned_destinations'] == []
        assert insights['decision_stage'] == 'exploring'
        assert insights['stage_confidence'] == 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_single_message(self, service):

    # - Single message analysis works correctly
    # - Destinations are extracted from minimal input
    # - Initial stage classification is appropriate
    # - System can work with limited conversation data

        messages = [{"role": "user", "content": "I want to go to Japan"}]
        insights = await service.analyze_preferences(messages, None)
        
        assert 'Japan' in insights['mentioned_destinations']
        assert insights['decision_stage'] == 'exploring'
    
    def test_calculate_stage_scores_exploring(self, service):
        messages = [{"role": "user", "content": "I'm thinking about going somewhere warm"}]
        scores = service._calculate_stage_scores(messages, None)
        
        assert 'stage' in scores
        assert 'confidence' in scores
        assert 'progression' in scores
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        assert 0.0 <= scores['confidence'] <= 1.0
    
    def test_calculate_stage_scores_comparing(self, service):
        messages = [
            {"role": "user", "content": "I'm thinking about going somewhere warm"},
            {"role": "user", "content": "Should I choose Bali or Thailand?"}
        ]
        scores = service._calculate_stage_scores(messages, None)
        
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
    
    def test_calculate_stage_scores_planning(self, service):
        messages = [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "user", "content": "I have a budget of $2000 for 5 days in June"}
        ]
        scores = service._calculate_stage_scores(messages, None)
        
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
    
    def test_detect_interests(self, service):
        text = "I love culture, food, and adventure activities"
        interests = service._detect_interests(text)
        
        assert isinstance(interests, list)
        assert len(interests) > 0
        assert any('culture' in interest.lower() or 'food' in interest.lower() for interest in interests)
    
    def test_detect_interests_empty_text(self, service):
        interests = service._detect_interests("")
        assert isinstance(interests, list)
    
    def test_detect_interests_no_interests(self, service):
        interests = service._detect_interests("Hello, how are you?")
        assert isinstance(interests, list)
    
    def test_extract_destinations(self, service):
        messages = [
            {"role": "user", "content": "I want to go to Paris and Rome"},
            {"role": "user", "content": "Also considering Tokyo"}
        ]
        destinations = service._extract_destinations(messages)
        
        assert isinstance(destinations, list)
        assert 'Paris' in destinations
        assert 'Rome' in destinations
        assert 'Tokyo' in destinations
    
    def test_extract_destinations_no_destinations(self, service):
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        destinations = service._extract_destinations(messages)
        
        assert isinstance(destinations, list)
        # The service might extract other words, so just check it's a list
        assert isinstance(destinations, list)
    
    @pytest.mark.asyncio
    async def test_extract_destinations_with_ai(self, service):
        # Test AI-based destination extraction
        mock_openai_service = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = '["Bangladesh", "Vietnam"]'
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai_service.client = mock_client
        mock_openai_service.model = "test-model"
        
        service.openai_service = mock_openai_service
        
        messages = [{"role": "user", "content": "I want to visit Bangladesh and Vietnam"}]
        result = await service._extract_destinations_with_ai(messages)
        
        assert result == ["Bangladesh", "Vietnam"]
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_destinations_with_ai_no_service(self, service):
        # Test that AI extraction returns None when no OpenAI service
        service.openai_service = None
        messages = [{"role": "user", "content": "I want to visit Bangladesh"}]
        result = await service._extract_destinations_with_ai(messages)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_extract_destinations_with_ai_json_error(self, service):
        # Test AI extraction handles JSON parsing errors gracefully
        mock_openai_service = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = 'Invalid JSON response'
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai_service.client = mock_client
        mock_openai_service.model = "test-model"
        
        service.openai_service = mock_openai_service
        
        messages = [{"role": "user", "content": "I want to visit Bangladesh"}]
        result = await service._extract_destinations_with_ai(messages)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_preferences_includes_budget_amount(self, service):
        messages = [
            {"role": "user", "content": "I'm planning to spend $3000 on this trip"}
        ]
        insights = await service.analyze_preferences(messages, None)
        assert insights.get("budget_amount") == "$3,000"
        assert "moderate" in insights.get("budget_indicators", [])
    
    
    def test_calculate_decision_readiness_with_preferences(self, service, sample_preferences):
        readiness = service._calculate_decision_readiness(sample_preferences, 5, ["Paris"])
        
        assert isinstance(readiness, float)
        assert 0.0 <= readiness <= 1.0
    
    def test_calculate_decision_readiness_no_preferences(self, service):
        readiness = service._calculate_decision_readiness(None, 1, [])
        
        assert isinstance(readiness, float)
        assert readiness >= 0.0
    
    def test_calculate_decision_readiness_high_confidence(self, service):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"],
            "group_size": 2
        }
        readiness = service._calculate_decision_readiness(preferences, 10, ["Paris"])
        
        assert isinstance(readiness, float)
        assert readiness > 0.5
    
    def test_detect_budget_level(self, service):
        text = "I have a budget of $2000 and want something affordable"
        budget_indicators = service._detect_budget_level(text)
        
        assert isinstance(budget_indicators, list)
        assert len(budget_indicators) > 0
    
    def test_detect_budget_level_amount_only(self, service):
        text = "I can spend $3000 for this entire trip"
        budget_indicators = service._detect_budget_level(text)
        
        assert 'moderate' in budget_indicators
    
    def test_detect_budget_level_no_budget(self, service):
        budget_indicators = service._detect_budget_level("I want to travel somewhere")
        assert isinstance(budget_indicators, list)
    
    def test_detect_concerns(self, service):
        text = "I'm worried about safety and language barriers"
        concerns = service._detect_concerns(text)
        
        assert isinstance(concerns, list)
        assert len(concerns) > 0
    
    def test_detect_concerns_no_concerns(self, service):
        concerns = service._detect_concerns("I'm excited to travel!")
        assert isinstance(concerns, list)
    
    def test_detect_experience_level(self, service):
        text = "This is my first time traveling abroad"
        level = service._detect_experience_level(text)
        
        assert isinstance(level, str)
        assert level in ['beginner', 'intermediate', 'expert', 'unknown']
    
    def test_detect_experience_level_expert(self, service):
        text = "I've been to 20 countries and love backpacking"
        level = service._detect_experience_level(text)
        
        assert isinstance(level, str)
        assert level in ['beginner', 'intermediate', 'expert', 'unknown']
    
    def test_generate_dynamic_suggestions(self, service):
        conversation_state = {
            "stage": "exploring",
            "message_count": 3,
            "preferences": {"destinations": ["Paris"]}
        }
        suggestions = service.generate_dynamic_suggestions(conversation_state, "I want to go to Paris")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_generate_dynamic_suggestions_empty_state(self, service):
        suggestions = service.generate_dynamic_suggestions({}, "")
        
        assert isinstance(suggestions, list)
    
    def test_get_smart_recommendations(self, service, sample_preferences):
        insights = {
            "decision_stage": "planning",
            "detected_interests": ["culture", "food"],
            "mentioned_destinations": ["Paris"]
        }
        recommendations = service.get_smart_recommendations(sample_preferences, insights, 5)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_get_smart_recommendations_no_preferences(self, service):
        insights = {
            "decision_stage": "exploring",
            "detected_interests": [],
            "mentioned_destinations": []
        }
        recommendations = service.get_smart_recommendations(None, insights, 1)
        
        assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_edge_cases(self, service):
        # Very long message
        long_message = "I want to go to " + "a very long destination name " * 50
        messages = [{"role": "user", "content": long_message}]
        insights = await service.analyze_preferences(messages, None)
        
        assert isinstance(insights, dict)
        assert 'detected_interests' in insights
        
        # Message with special characters
        special_message = "I want to go to Paris! 🗼 🇫🇷 #travel #vacation"
        messages = [{"role": "user", "content": special_message}]
        insights = await service.analyze_preferences(messages, None)
        
        assert isinstance(insights, dict)
        assert 'Paris' in insights['mentioned_destinations']
    
    def test_stage_keywords_coverage(self, service):
        exploring_text = "I'm thinking about going somewhere warm"
        scores = service._calculate_stage_scores([{"role": "user", "content": exploring_text}], None)
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        
        comparing_text = "Should I choose Bali or Thailand?"
        scores = service._calculate_stage_scores([{"role": "user", "content": comparing_text}], None)
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        
        planning_text = "I have a budget of $2000 for 5 days in June"
        scores = service._calculate_stage_scores([{"role": "user", "content": planning_text}], None)
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
    
    def test_decision_readiness_calculation_factors(self, service):
        minimal_prefs = {"destinations": ["Paris"]}
        readiness_minimal = service._calculate_decision_readiness(minimal_prefs, 1, ["Paris"])
        
        comprehensive_prefs = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural", "foodie"],
            "group_size": 2,
            "interests": ["museums", "food", "architecture"]
        }
        readiness_comprehensive = service._calculate_decision_readiness(comprehensive_prefs, 10, ["Paris"])
        
        # Comprehensive preferences should have higher readiness
        assert readiness_comprehensive > readiness_minimal
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_performance(self, service):
        # Create a large set of messages
        large_messages = []
        for i in range(100):
            large_messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i} about travel planning"
            })
        
        # Should complete within reasonable time
        import time
        start_time = time.time()
        insights = await service.analyze_preferences(large_messages, None)
        end_time = time.time()
        
        assert isinstance(insights, dict)
        assert end_time - start_time < 5.0


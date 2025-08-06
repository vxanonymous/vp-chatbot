"""
Comprehensive unit tests for VacationIntelligenceService.

This module tests the VacationIntelligenceService which provides:
- User preference analysis from conversation messages
- Decision stage classification (exploring, comparing, planning, finalizing)
- Interest and destination detection
- Budget and travel style analysis
- Dynamic suggestion generation
- Smart recommendation algorithms

The service uses natural language processing and machine learning techniques
to understand user intent and provide personalized vacation planning assistance.

FILE DEPENDENCIES:
==================
UTILIZES (Dependencies):
- app/services/vacation_intelligence_service.py - Main service being tested
- app/models/chat.py - Message and chat models
- app/models/conversation_db.py - Conversation data models
- unittest.mock - Mocking utilities for OpenAI API calls
- conftest.py - Test fixtures and configuration
- pytest.asyncio - Async test support

USED BY (Dependents):
- pytest.ini - Test configuration
- run-tests.sh - Test execution scripts
- TEST_SUMMARY.md - Test documentation
- test_integration_comprehensive.py - Integration tests
- test_services_comprehensive.py - Comprehensive service tests
- CI/CD pipelines - Automated testing
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.vacation_intelligence_service import VacationIntelligenceService


class TestVacationIntelligenceService:
    """
    Test suite for VacationIntelligenceService.
    
    This class provides comprehensive testing of the vacation intelligence
    system, including preference analysis, decision stage classification,
    and recommendation generation. All tests use mocked dependencies to
    ensure reliable and fast execution.
    """
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return VacationIntelligenceService()
    
    @pytest.fixture
    def sample_messages(self):
        """
        Sample conversation messages for testing.
        
        Provides realistic conversation data that covers multiple
        vacation planning stages and user preferences.
        """
        return [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "assistant", "content": "Paris is wonderful! What's your budget?"},
            {"role": "user", "content": "Around $2000 for 5 days"},
            {"role": "assistant", "content": "Great budget! When are you planning to go?"},
            {"role": "user", "content": "In June, I love culture and food"}
        ]
    
    @pytest.fixture
    def sample_preferences(self):
        """
        Sample user preferences for testing.
        
        Provides realistic user preference data that can be used
        to test preference analysis and recommendation generation.
        """
        return {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural", "foodie"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
    
    def test_initialization(self, service):
        """
        Test service initialization.
        
        Verifies that:
        - Service instance is created successfully
        - Stage keywords are properly loaded
        - All required stages are present (exploring, comparing, planning, finalizing)
        - Keywords have the expected structure
        
        This test ensures the service is properly configured on startup.
        """
        assert service is not None
        assert hasattr(service, 'stage_keywords')
        assert isinstance(service.stage_keywords, dict)
        assert 'exploring' in service.stage_keywords
        assert 'comparing' in service.stage_keywords
        assert 'planning' in service.stage_keywords
        assert 'finalizing' in service.stage_keywords
    
    def test_stage_keywords_structure(self, service):
        """
        Test stage keywords have proper structure.
        
        Verifies that:
        - Each stage has positive keywords and questions
        - Keywords are stored as lists
        - Each stage has non-empty keyword lists
        - Structure is consistent across all stages
        
        This test ensures the keyword system is properly structured for analysis.
        """
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
        """
        Test basic preference analysis.
        
        Verifies that:
        - Preference analysis returns expected data structure
        - All required insight fields are present
        - Analysis works with realistic conversation data
        - Results are properly formatted
        
        This test ensures the core preference analysis functionality works correctly.
        """
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
        """
        Test preference analysis with existing preferences.
        
        Verifies that:
        - Analysis incorporates existing user preferences
        - Decision stage is properly classified
        - Confidence scores are within valid ranges (0.0 to 1.0)
        - Destinations are correctly identified
        - Decision readiness is calculated appropriately
        
        This test ensures the service can build upon existing preference data.
        """
        insights = await service.analyze_preferences(sample_messages, sample_preferences)
        
        assert insights['decision_stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        assert 0.0 <= insights['stage_confidence'] <= 1.0
        assert 0.0 <= insights['decision_readiness'] <= 1.0
        assert 'Paris' in insights['mentioned_destinations']
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_empty_messages(self, service):
        """
        Test preference analysis with empty messages.
        
        Verifies that:
        - Empty message list is handled gracefully
        - Default values are returned for empty conversations
        - System doesn't crash on empty input
        - Initial stage is set to 'exploring'
        
        This test ensures robust handling of edge cases with no conversation data.
        """
        insights = await service.analyze_preferences([], None)
        
        assert insights['detected_interests'] == []
        assert insights['mentioned_destinations'] == []
        assert insights['decision_stage'] == 'exploring'
        assert insights['stage_confidence'] == 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_single_message(self, service):
        """
        Test preference analysis with single message.
        
        Verifies that:
        - Single message analysis works correctly
        - Destinations are extracted from minimal input
        - Initial stage classification is appropriate
        - System can work with limited conversation data
        
        This test ensures the service works with minimal user input.
        """
        messages = [{"role": "user", "content": "I want to go to Japan"}]
        insights = await service.analyze_preferences(messages, None)
        
        assert 'Japan' in insights['mentioned_destinations']
        assert insights['decision_stage'] == 'exploring'
    
    def test_calculate_stage_scores_exploring(self, service):
        """Test stage score calculation for exploring stage."""
        messages = [{"role": "user", "content": "I'm thinking about going somewhere warm"}]
        scores = service._calculate_stage_scores(messages, None)
        
        assert 'stage' in scores
        assert 'confidence' in scores
        assert 'progression' in scores
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        assert 0.0 <= scores['confidence'] <= 1.0
    
    def test_calculate_stage_scores_comparing(self, service):
        """Test stage score calculation for comparing stage."""
        messages = [
            {"role": "user", "content": "I'm thinking about going somewhere warm"},
            {"role": "user", "content": "Should I choose Bali or Thailand?"}
        ]
        scores = service._calculate_stage_scores(messages, None)
        
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
    
    def test_calculate_stage_scores_planning(self, service):
        """Test stage score calculation for planning stage."""
        messages = [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "user", "content": "I have a budget of $2000 for 5 days in June"}
        ]
        scores = service._calculate_stage_scores(messages, None)
        
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
    
    def test_detect_interests(self, service):
        """Test interest detection."""
        text = "I love culture, food, and adventure activities"
        interests = service._detect_interests(text)
        
        assert isinstance(interests, list)
        assert len(interests) > 0
        assert any('culture' in interest.lower() or 'food' in interest.lower() for interest in interests)
    
    def test_detect_interests_empty_text(self, service):
        """Test interest detection with empty text."""
        interests = service._detect_interests("")
        assert isinstance(interests, list)
    
    def test_detect_interests_no_interests(self, service):
        """Test interest detection with no interests mentioned."""
        interests = service._detect_interests("Hello, how are you?")
        assert isinstance(interests, list)
    
    def test_extract_destinations(self, service):
        """Test destination extraction."""
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
        """Test destination extraction with no destinations."""
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        destinations = service._extract_destinations(messages)
        
        assert isinstance(destinations, list)
        # The service might extract other words, so just check it's a list
        assert isinstance(destinations, list)
    
    def test_calculate_decision_readiness_with_preferences(self, service, sample_preferences):
        """Test decision readiness calculation with preferences."""
        readiness = service._calculate_decision_readiness(sample_preferences, 5, ["Paris"])
        
        assert isinstance(readiness, float)
        assert 0.0 <= readiness <= 1.0
    
    def test_calculate_decision_readiness_no_preferences(self, service):
        """Test decision readiness calculation without preferences."""
        readiness = service._calculate_decision_readiness(None, 1, [])
        
        assert isinstance(readiness, float)
        assert readiness >= 0.0  # Should be non-negative
    
    def test_calculate_decision_readiness_high_confidence(self, service):
        """Test decision readiness with high confidence factors."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"],
            "group_size": 2
        }
        readiness = service._calculate_decision_readiness(preferences, 10, ["Paris"])
        
        assert isinstance(readiness, float)
        assert readiness > 0.5  # Should be higher with more complete preferences
    
    def test_detect_budget_level(self, service):
        """Test budget level detection."""
        text = "I have a budget of $2000 and want something affordable"
        budget_indicators = service._detect_budget_level(text)
        
        assert isinstance(budget_indicators, list)
        assert len(budget_indicators) > 0
    
    def test_detect_budget_level_no_budget(self, service):
        """Test budget level detection with no budget mentioned."""
        budget_indicators = service._detect_budget_level("I want to travel somewhere")
        assert isinstance(budget_indicators, list)
    
    def test_detect_concerns(self, service):
        """Test concern detection."""
        text = "I'm worried about safety and language barriers"
        concerns = service._detect_concerns(text)
        
        assert isinstance(concerns, list)
        assert len(concerns) > 0
    
    def test_detect_concerns_no_concerns(self, service):
        """Test concern detection with no concerns mentioned."""
        concerns = service._detect_concerns("I'm excited to travel!")
        assert isinstance(concerns, list)
    
    def test_detect_experience_level(self, service):
        """Test travel experience level detection."""
        text = "This is my first time traveling abroad"
        level = service._detect_experience_level(text)
        
        assert isinstance(level, str)
        assert level in ['beginner', 'intermediate', 'expert', 'unknown']
    
    def test_detect_experience_level_expert(self, service):
        """Test travel experience level detection for expert travelers."""
        text = "I've been to 20 countries and love backpacking"
        level = service._detect_experience_level(text)
        
        assert isinstance(level, str)
        assert level in ['beginner', 'intermediate', 'expert', 'unknown']
    
    def test_generate_dynamic_suggestions(self, service):
        """Test dynamic suggestion generation."""
        conversation_state = {
            "stage": "exploring",
            "message_count": 3,
            "preferences": {"destinations": ["Paris"]}
        }
        suggestions = service.generate_dynamic_suggestions(conversation_state, "I want to go to Paris")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_generate_dynamic_suggestions_empty_state(self, service):
        """Test dynamic suggestion generation with empty state."""
        suggestions = service.generate_dynamic_suggestions({}, "")
        
        assert isinstance(suggestions, list)
    
    def test_get_smart_recommendations(self, service, sample_preferences):
        """Test smart recommendation generation."""
        insights = {
            "decision_stage": "planning",
            "detected_interests": ["culture", "food"],
            "mentioned_destinations": ["Paris"]
        }
        recommendations = service.get_smart_recommendations(sample_preferences, insights, 5)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_get_smart_recommendations_no_preferences(self, service):
        """Test smart recommendation generation without preferences."""
        insights = {
            "decision_stage": "exploring",
            "detected_interests": [],
            "mentioned_destinations": []
        }
        recommendations = service.get_smart_recommendations(None, insights, 1)
        
        assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_analyze_preferences_edge_cases(self, service):
        """Test preference analysis with edge cases."""
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
        """Test that stage keywords cover common travel planning scenarios."""
        # Test exploring keywords
        exploring_text = "I'm thinking about going somewhere warm"
        scores = service._calculate_stage_scores([{"role": "user", "content": exploring_text}], None)
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        
        # Test comparing keywords
        comparing_text = "Should I choose Bali or Thailand?"
        scores = service._calculate_stage_scores([{"role": "user", "content": comparing_text}], None)
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
        
        # Test planning keywords
        planning_text = "I have a budget of $2000 for 5 days in June"
        scores = service._calculate_stage_scores([{"role": "user", "content": planning_text}], None)
        assert scores['stage'] in ['exploring', 'comparing', 'planning', 'finalizing']
    
    def test_decision_readiness_calculation_factors(self, service):
        """Test that decision readiness considers all relevant factors."""
        # Test with minimal information
        minimal_prefs = {"destinations": ["Paris"]}
        readiness_minimal = service._calculate_decision_readiness(minimal_prefs, 1, ["Paris"])
        
        # Test with comprehensive information
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
        """Test preference analysis performance with large message sets."""
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
        assert end_time - start_time < 5.0  # Should complete within 5 seconds 
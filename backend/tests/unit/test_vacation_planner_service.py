"""
Comprehensive unit tests for VacationPlanner service.

This module tests the VacationPlanner service which provides:
- Vacation plan generation based on user preferences
- Suggestion generation for incomplete preferences
- Vacation summary creation with completeness analysis
- Recommendation generation for activities and destinations
- Budget and travel style analysis
- Duration calculation and planning optimization

The service helps users create detailed vacation plans and provides
intelligent suggestions to improve their travel experience.

FILE DEPENDENCIES:
==================
UTILIZES (Dependencies):
- app/services/vacation_planner.py - Main service being tested
- app/models/chat.py - Message and chat models
- app/models/conversation_db.py - Conversation data models
- unittest.mock - Mocking utilities
- conftest.py - Test fixtures and configuration

USED BY (Dependents):
- pytest.ini - Test configuration
- run-tests.sh - Test execution scripts
- TEST_SUMMARY.md - Test documentation
- test_services_comprehensive.py - Service tests
- test_integration_comprehensive.py - Integration tests
- CI/CD pipelines - Automated testing
"""
import pytest
from unittest.mock import Mock, patch
from app.services.vacation_planner import VacationPlanner


class TestVacationPlanner:
    """Test suite for VacationPlanner."""
    
    @pytest.fixture
    def planner(self):
        """Create a planner instance for testing."""
        return VacationPlanner()
    
    @pytest.fixture
    def sample_preferences(self):
        """Sample user preferences for testing."""
        return {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural", "foodie"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "group_size": 2,
            "interests": ["museums", "food", "architecture"]
        }
    
    def test_initialization(self, planner):
        """Test service initialization."""
        assert planner is not None
        assert hasattr(planner, 'default_suggestions')
        assert isinstance(planner.default_suggestions, list)
        assert len(planner.default_suggestions) > 0
    
    def test_default_suggestions_structure(self, planner):
        """Test default suggestions have proper structure."""
        for suggestion in planner.default_suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
            assert any(keyword in suggestion.lower() for keyword in ["destination", "budget", "travel", "activities"])
    
    def test_generate_suggestions_no_preferences(self, planner):
        """Test suggestion generation without preferences."""
        suggestions = planner.generate_suggestions(None)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert suggestions == planner.default_suggestions
    
    def test_generate_suggestions_empty_preferences(self, planner):
        """Test suggestion generation with empty preferences."""
        suggestions = planner.generate_suggestions({})
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert suggestions == planner.default_suggestions
    
    def test_generate_suggestions_with_destination(self, planner):
        """Test suggestion generation with destination."""
        preferences = {"destinations": ["Paris"]}
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("Paris" in suggestion for suggestion in suggestions)
    
    def test_generate_suggestions_missing_travel_dates(self, planner):
        """Test suggestion generation when travel dates are missing."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("when" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_suggestions_missing_budget(self, planner):
        """Test suggestion generation when budget is missing."""
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("budget" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_suggestions_missing_travel_style(self, planner):
        """Test suggestion generation when travel style is missing."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("kind" in suggestion.lower() or "style" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_suggestions_complete_preferences(self, planner, sample_preferences):
        """Test suggestion generation with complete preferences."""
        suggestions = planner.generate_suggestions(sample_preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should have some suggestions even with complete preferences
        assert len(suggestions) <= 3  # Max 3 suggestions
    
    def test_generate_suggestions_max_limit(self, planner):
        """Test that suggestions are limited to maximum 3."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"]
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert len(suggestions) <= 3
    
    def test_create_vacation_plan_no_preferences(self, planner):
        """Test vacation plan creation without preferences."""
        plan = planner.create_vacation_plan(None)
        
        assert plan is None
    
    def test_create_vacation_plan_empty_preferences(self, planner):
        """Test vacation plan creation with empty preferences."""
        plan = planner.create_vacation_plan({})
        
        assert plan is None
    
    def test_create_vacation_plan_basic_preferences(self, planner):
        """Test vacation plan creation with basic preferences."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert isinstance(plan, dict)
        assert 'destination' in plan
        assert 'duration_days' in plan
        assert 'estimated_budget' in plan
        assert 'suggested_activities' in plan
        assert 'accommodation_recommendations' in plan
        assert 'transportation_options' in plan
        assert 'best_time_to_visit' in plan
        assert 'weather_info' in plan
        assert 'local_tips' in plan
    
    def test_create_vacation_plan_complete_preferences(self, planner, sample_preferences):
        """Test vacation plan creation with complete preferences."""
        plan = planner.create_vacation_plan(sample_preferences)
        
        assert isinstance(plan, dict)
        assert plan['destination'] == 'Paris'
        assert plan['duration_days'] == 5
        assert isinstance(plan['estimated_budget'], dict)
        assert isinstance(plan['suggested_activities'], list)
        assert isinstance(plan['accommodation_recommendations'], list)
        assert isinstance(plan['transportation_options'], list)
        assert isinstance(plan['local_tips'], list)
    
    def test_create_vacation_summary_no_preferences(self, planner):
        """Test vacation summary creation without preferences."""
        summary = planner.create_vacation_summary(None)
        
        assert summary is None
    
    def test_create_vacation_summary_empty_preferences(self, planner):
        """Test vacation summary creation with empty preferences."""
        summary = planner.create_vacation_summary({})
        
        assert summary is None
    
    def test_create_vacation_summary_basic_preferences(self, planner):
        """Test vacation summary creation with basic preferences."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        summary = planner.create_vacation_summary(preferences)
        
        assert isinstance(summary, dict)
        assert 'destination' in summary
        assert 'budget_range' in summary
        assert 'completeness_percentage' in summary
        assert 'missing_info' in summary
        assert 'recommendations' in summary
    
    def test_create_vacation_summary_complete_preferences(self, planner, sample_preferences):
        """Test vacation summary creation with complete preferences."""
        summary = planner.create_vacation_summary(sample_preferences)
        
        assert isinstance(summary, dict)
        assert summary['destination'] == 'Paris'
        assert summary['budget_range'] == 'moderate'
        assert 0 <= summary['completeness_percentage'] <= 100
        assert isinstance(summary['missing_info'], list)
        assert isinstance(summary['recommendations'], list)
    
    def test_calculate_completeness_percentage_minimal(self, planner):
        """Test completeness percentage calculation with minimal preferences."""
        preferences = {"destinations": ["Paris"]}
        percentage = planner._calculate_completeness_percentage(preferences)
        
        assert isinstance(percentage, int)
        assert 0 <= percentage <= 100
        assert percentage < 50  # Should be low with minimal info
    
    def test_calculate_completeness_percentage_complete(self, planner, sample_preferences):
        """Test completeness percentage calculation with complete preferences."""
        percentage = planner._calculate_completeness_percentage(sample_preferences)
        
        assert isinstance(percentage, int)
        assert 0 <= percentage <= 100
        assert percentage > 70  # Should be high with complete info
    
    def test_calculate_completeness_percentage_empty(self, planner):
        """Test completeness percentage calculation with empty preferences."""
        percentage = planner._calculate_completeness_percentage({})
        
        assert isinstance(percentage, int)
        assert percentage == 0
    
    def test_generate_recommendations_basic(self, planner):
        """Test recommendation generation with basic preferences."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        recommendations = planner._generate_recommendations(preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_generate_recommendations_complete(self, planner, sample_preferences):
        """Test recommendation generation with complete preferences."""
        recommendations = planner._generate_recommendations(sample_preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_generate_recommendations_empty(self, planner):
        """Test recommendation generation with empty preferences."""
        recommendations = planner._generate_recommendations({})
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0  # Should have default recommendations
    
    def test_vacation_plan_destination_specific(self, planner):
        """Test that vacation plans are destination-specific."""
        preferences = {
            "destinations": ["Tokyo"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan['destination'] == 'Tokyo'
        assert 'Tokyo' in str(plan['suggested_activities'])
        assert 'Tokyo' in str(plan['local_tips'])
    
    def test_vacation_plan_budget_specific(self, planner):
        """Test that vacation plans consider budget range."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "luxury",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan['budget_range'] == 'luxury'
        assert 'luxury' in str(plan['accommodation_recommendations']).lower()
    
    def test_vacation_plan_duration_calculation(self, planner):
        """Test that vacation plan calculates duration correctly."""
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-10"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan['duration_days'] == 10
    
    def test_vacation_summary_missing_info_detection(self, planner):
        """Test that vacation summary detects missing information."""
        preferences = {
            "destinations": ["Paris"]
            # Missing budget, dates, etc.
        }
        summary = planner.create_vacation_summary(preferences)
        
        assert len(summary['missing_info']) > 0
        assert any('budget' in info.lower() for info in summary['missing_info'])
        assert any('date' in info.lower() for info in summary['missing_info'])
    
    def test_vacation_summary_complete_info(self, planner, sample_preferences):
        """Test that vacation summary handles complete information."""
        summary = planner.create_vacation_summary(sample_preferences)
        
        assert len(summary['missing_info']) == 0 or summary['completeness_percentage'] > 80
    
    def test_suggestions_context_aware(self, planner):
        """Test that suggestions are context-aware."""
        # Test with destination but no budget
        preferences = {"destinations": ["Paris"]}
        suggestions = planner.generate_suggestions(preferences)
        
        assert any("budget" in suggestion.lower() for suggestion in suggestions)
        
        # Test with destination and budget but no dates
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert any("when" in suggestion.lower() for suggestion in suggestions)
    
    def test_vacation_plan_edge_cases(self, planner):
        """Test vacation plan creation with edge cases."""
        # Very long destination name
        preferences = {
            "destinations": ["A very long destination name that might cause issues"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert isinstance(plan, dict)
        assert 'destination' in plan
        
        # Special characters in destination
        preferences = {
            "destinations": ["Paris 🗼"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert isinstance(plan, dict)
        assert 'destination' in plan
    
    def test_suggestions_edge_cases(self, planner):
        """Test suggestion generation with edge cases."""
        # Very large preferences object
        large_preferences = {
            "destinations": ["Paris"] * 10,
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"] * 10,
            "interests": ["museums"] * 20
        }
        suggestions = planner.generate_suggestions(large_preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3  # Should still respect max limit
        
        # Empty strings in preferences
        preferences = {
            "destinations": [""],
            "budget_range": "",
            "travel_dates": {"start": "", "end": ""}
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_completeness_calculation_accuracy(self, planner):
        """Test that completeness calculation is accurate."""
        # Test with known preference combinations
        minimal_prefs = {"destinations": ["Paris"]}
        basic_prefs = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        complete_prefs = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"],
            "group_size": 2,
            "interests": ["museums", "food"]
        }
        
        minimal_score = planner._calculate_completeness_percentage(minimal_prefs)
        basic_score = planner._calculate_completeness_percentage(basic_prefs)
        complete_score = planner._calculate_completeness_percentage(complete_prefs)
        
        # Scores should be in ascending order
        assert minimal_score < basic_score < complete_score
        assert complete_score > 70  # Complete preferences should be high
    
    def test_recommendations_quality(self, planner):
        """Test that recommendations are high quality."""
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural"]
        }
        recommendations = planner._generate_recommendations(preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check that recommendations are substantial
        for rec in recommendations:
            assert len(rec) > 10  # Should be substantial recommendations
            assert any(keyword in rec.lower() for keyword in ["paris", "culture", "visit", "see", "experience"])
    
    def test_vacation_plan_data_types(self, planner, sample_preferences):
        """Test that vacation plan has correct data types."""
        plan = planner.create_vacation_plan(sample_preferences)
        
        assert isinstance(plan['destination'], str)
        assert isinstance(plan['duration_days'], int)
        assert isinstance(plan['estimated_budget'], dict)
        assert isinstance(plan['suggested_activities'], list)
        assert isinstance(plan['accommodation_recommendations'], list)
        assert isinstance(plan['transportation_options'], list)
        assert isinstance(plan['best_time_to_visit'], str)
        assert isinstance(plan['weather_info'], dict)
        assert isinstance(plan['local_tips'], list)
        assert isinstance(plan.get('itinerary'), (list, type(None)))
    
    def test_vacation_summary_data_types(self, planner, sample_preferences):
        """Test that vacation summary has correct data types."""
        summary = planner.create_vacation_summary(sample_preferences)
        
        assert isinstance(summary['destination'], str)
        assert isinstance(summary['budget_range'], str)
        assert isinstance(summary['completeness_percentage'], int)
        assert isinstance(summary['missing_info'], list)
        assert isinstance(summary['recommendations'], list) 
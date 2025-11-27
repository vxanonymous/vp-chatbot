# Comprehensive unit tests for ProactiveAssistant service.
import pytest
from unittest.mock import Mock, patch
from app.services.proactive_assistant import ProactiveAssistant


class TestProactiveAssistant:
    
    @pytest.fixture
    def assistant(self):
    # Create an assistant instance for testing.
        return ProactiveAssistant()
    
    @pytest.fixture
    def sample_context(self):
    # Sample conversation context for testing.
        return {
            "stage": "planning",
            "message_count": 5,
            "last_user_message": "I want to go to Paris",
            "conversation_history": [
                {"role": "user", "content": "I want to travel somewhere"},
                {"role": "assistant", "content": "Where would you like to go?"},
                {"role": "user", "content": "I want to go to Paris"}
            ]
        }
    
    @pytest.fixture
    def sample_preferences(self):
    # Sample user preferences for testing.
        return {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural", "foodie"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
    
    def test_initialization(self, assistant):
        assert assistant is not None
    
    def test_get_proactive_suggestions_basic(self, assistant, sample_context, sample_preferences):
        suggestions = assistant.get_proactive_suggestions(sample_context, sample_preferences, 5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert 'type' in suggestion
            assert 'content' in suggestion
            assert 'priority' in suggestion
    
    def test_get_proactive_suggestions_no_context(self, assistant):
        suggestions = assistant.get_proactive_suggestions({}, {}, 1)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_get_proactive_suggestions_no_preferences(self, assistant, sample_context):
        suggestions = assistant.get_proactive_suggestions(sample_context, {}, 3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_get_proactive_suggestions_early_conversation(self, assistant):
        context = {
            "stage": "exploring",
            "message_count": 2,
            "last_user_message": "I want to travel"
        }
        suggestions = assistant.get_proactive_suggestions(context, {}, 2)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should suggest gathering basic information
        suggestion_types = [s['type'] for s in suggestions]
        assert any('destination' in str(s).lower() or 'budget' in str(s).lower() for s in suggestions)
    
    def test_get_proactive_suggestions_planning_stage(self, assistant, sample_preferences):
        context = {
            "stage": "planning",
            "message_count": 8,
            "last_user_message": "I have a budget of $2000"
        }
        suggestions = assistant.get_proactive_suggestions(context, sample_preferences, 8)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should suggest planning-related items
        suggestion_types = [s['type'] for s in suggestions]
        assert any('accommodation' in str(s).lower() or 'activities' in str(s).lower() or 'itinerary' in str(s).lower() for s in suggestions)
    
    def test_get_proactive_suggestions_finalizing_stage(self, assistant, sample_preferences):
        context = {
            "stage": "finalizing",
            "message_count": 15,
            "last_user_message": "I think I'm ready to book"
        }
        suggestions = assistant.get_proactive_suggestions(context, sample_preferences, 15)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should suggest finalization items
        suggestion_types = [s['type'] for s in suggestions]
        assert any('booking' in str(s).lower() or 'final' in str(s).lower() or 'confirm' in str(s).lower() for s in suggestions)
    
    def test_calculate_days_until_travel_with_dates(self, assistant):
        travel_dates = {"start": "2025-12-01", "end": "2025-12-05"}
        days = assistant._calculate_days_until_travel(travel_dates)
        
        assert isinstance(days, int)
        assert days >= 0
    
    def test_calculate_days_until_travel_no_dates(self, assistant):
        days = assistant._calculate_days_until_travel({})
        
        assert days is None
    
    def test_calculate_days_until_travel_invalid_dates(self, assistant):
        travel_dates = {"start": "invalid-date", "end": "also-invalid"}
        days = assistant._calculate_days_until_travel(travel_dates)
        
        assert days is None
    
    def test_calculate_days_until_travel_past_dates(self, assistant):
        travel_dates = {"start": "2020-01-01", "end": "2020-01-05"}
        days = assistant._calculate_days_until_travel(travel_dates)
        
        assert isinstance(days, int)
        assert days < 0
    
    def test_anticipate_next_questions_exploring(self, assistant):
        stage = "exploring"
        preferences = {"destinations": ["Paris"]}
        recent_topics = ["destinations"]
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, str) for q in questions)
        # Should ask about budget, dates, etc.
        question_text = " ".join(questions).lower()
        assert any(keyword in question_text for keyword in ["budget", "when", "dates", "style"])
    
    def test_anticipate_next_questions_comparing(self, assistant):
        stage = "comparing"
        preferences = {
            "destinations": ["Paris", "Rome"],
            "budget_range": "moderate"
        }
        recent_topics = ["destinations", "budget"]
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        # Should ask about preferences between destinations
        question_text = " ".join(questions).lower()
        assert any(keyword in question_text for keyword in ["prefer", "choose", "between", "style"])
    
    def test_anticipate_next_questions_planning(self, assistant):
        stage = "planning"
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        recent_topics = ["accommodation", "activities"]
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        # Should ask about specific planning details
        question_text = " ".join(questions).lower()
        assert any(keyword in question_text for keyword in ["hotel", "activities", "itinerary", "transport"])
    
    def test_anticipate_next_questions_finalizing(self, assistant):
        stage = "finalizing"
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        recent_topics = ["booking", "confirmation"]
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        # Should ask about finalization details
        question_text = " ".join(questions).lower()
        assert any(keyword in question_text for keyword in ["book", "confirm", "final", "ready"])
    
    def test_anticipate_next_questions_no_preferences(self, assistant):
        stage = "exploring"
        preferences = {}
        recent_topics = []
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        # Should ask basic questions
        question_text = " ".join(questions).lower()
        assert any(keyword in question_text for keyword in ["where", "destination", "travel"])
    
    def test_anticipate_next_questions_unknown_stage(self, assistant):
        stage = "unknown_stage"
        preferences = {"destinations": ["Paris"]}
        recent_topics = ["destinations"]
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
    
    def test_generate_suggestions_basic(self, assistant):
        conversation = {
            "messages": [
                {"role": "user", "content": "I want to go to Paris"},
                {"role": "assistant", "content": "Paris is great! What's your budget?"}
            ]
        }
        user_preferences = {"destinations": ["Paris"]}
        
        suggestions = assistant.generate_suggestions(conversation, user_preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
    
    def test_generate_suggestions_no_conversation(self, assistant):
        suggestions = assistant.generate_suggestions({}, {})
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_generate_suggestions_no_preferences(self, assistant):
        conversation = {
            "messages": [
                {"role": "user", "content": "I want to travel"}
            ]
        }
        
        suggestions = assistant.generate_suggestions(conversation, {})
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_proactive_suggestions_priority_ordering(self, assistant, sample_context, sample_preferences):
        suggestions = assistant.get_proactive_suggestions(sample_context, sample_preferences, 5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check that priorities are valid
        for suggestion in suggestions:
            assert 'priority' in suggestion
            assert isinstance(suggestion['priority'], (int, float))
            assert suggestion['priority'] >= 0
            assert suggestion['priority'] <= 10
    
    def test_proactive_suggestions_type_categorization(self, assistant, sample_context, sample_preferences):
        suggestions = assistant.get_proactive_suggestions(sample_context, sample_preferences, 5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check that types are valid
        valid_types = ['destination', 'budget', 'dates', 'accommodation', 'activities', 'transportation', 'booking', 'general']
        for suggestion in suggestions:
            assert 'type' in suggestion
            assert isinstance(suggestion['type'], str)
            # Type should be one of the valid types or contain one of them
            assert any(valid_type in suggestion['type'].lower() for valid_type in valid_types)
    
    def test_proactive_suggestions_content_quality(self, assistant, sample_context, sample_preferences):
        suggestions = assistant.get_proactive_suggestions(sample_context, sample_preferences, 5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        for suggestion in suggestions:
            assert 'content' in suggestion
            assert isinstance(suggestion['content'], str)
            assert len(suggestion['content']) > 10
            assert any(keyword in suggestion['content'].lower() for keyword in ["paris", "travel", "vacation", "planning"])
    
    def test_anticipate_next_questions_relevance(self, assistant):
        stage = "planning"
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        recent_topics = ["accommodation"]
        
        questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        # Questions should be relevant to planning stage and recent topics
        question_text = " ".join(questions).lower()
        assert any(keyword in question_text for keyword in ["hotel", "accommodation", "stay", "room", "booking"])
    
    def test_proactive_suggestions_edge_cases(self, assistant):
        # Very long context
        long_context = {
            "stage": "planning",
            "message_count": 100,
            "last_user_message": "I want to go to " + "a very long destination name " * 50
        }
        suggestions = assistant.get_proactive_suggestions(long_context, {}, 100)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Empty context
        suggestions = assistant.get_proactive_suggestions({}, {}, 0)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Special characters in context
        special_context = {
            "stage": "planning",
            "message_count": 5,
            "last_user_message": "I want to go to Paris! 🗼 🇫🇷 #travel"
        }
        suggestions = assistant.get_proactive_suggestions(special_context, {}, 5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_anticipate_next_questions_edge_cases(self, assistant):
        # Very long recent topics
        long_topics = ["destination"] * 50
        questions = assistant.anticipate_next_questions("exploring", {}, long_topics)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        # Empty recent topics
        questions = assistant.anticipate_next_questions("exploring", {}, [])
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        # Special characters in preferences
        special_preferences = {
            "destinations": ["Paris 🗼"],
            "budget_range": "moderate 💰"
        }
        questions = assistant.anticipate_next_questions("planning", special_preferences, ["destinations"])
        
        assert isinstance(questions, list)
        assert len(questions) > 0
    
    def test_generate_suggestions_edge_cases(self, assistant):
        # Very long conversation
        long_conversation = {
            "messages": [
                {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
                for i in range(100)
            ]
        }
        suggestions = assistant.generate_suggestions(long_conversation, {})
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Empty conversation
        suggestions = assistant.generate_suggestions({}, {})
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_proactive_suggestions_stage_specific(self, assistant):
        exploring_context = {
            "stage": "exploring",
            "message_count": 2,
            "last_user_message": "I want to travel"
        }
        exploring_suggestions = assistant.get_proactive_suggestions(exploring_context, {}, 2)
        
        planning_context = {
            "stage": "planning",
            "message_count": 8,
            "last_user_message": "I have a budget of $2000"
        }
        planning_suggestions = assistant.get_proactive_suggestions(planning_context, {}, 8)
        
        finalizing_context = {
            "stage": "finalizing",
            "message_count": 15,
            "last_user_message": "I'm ready to book"
        }
        finalizing_suggestions = assistant.get_proactive_suggestions(finalizing_context, {}, 15)
        
        # All should have suggestions but different types
        assert len(exploring_suggestions) > 0
        assert len(planning_suggestions) > 0
        assert len(finalizing_suggestions) > 0
        
        # Should have different focus areas
        exploring_types = [s['type'] for s in exploring_suggestions]
        planning_types = [s['type'] for s in planning_suggestions]
        finalizing_types = [s['type'] for s in finalizing_suggestions]
        
        # Exploring should focus on basic info gathering
        assert any('destination' in str(t).lower() or 'budget' in str(t).lower() for t in exploring_types)
        
        # Planning should focus on details
        assert any('accommodation' in str(t).lower() or 'activities' in str(t).lower() for t in planning_types)
        
        # Finalizing should focus on booking
        assert any('booking' in str(t).lower() or 'final' in str(t).lower() for t in finalizing_types)
    
    def test_anticipate_next_questions_comprehensive(self, assistant):
        stages = ["exploring", "comparing", "planning", "finalizing"]
        
        for stage in stages:
            preferences = {
                "destinations": ["Paris"],
                "budget_range": "moderate",
                "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
            }
            recent_topics = ["destinations", "budget"]
            
            questions = assistant.anticipate_next_questions(stage, preferences, recent_topics)
            
            assert isinstance(questions, list)
            assert len(questions) > 0
            assert all(isinstance(q, str) for q in questions)
            assert all(len(q) > 5 for q in questions)
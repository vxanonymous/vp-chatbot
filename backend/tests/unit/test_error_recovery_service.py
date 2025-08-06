"""
Comprehensive unit tests for ErrorRecoveryService.

This module tests the ErrorRecoveryService which provides:
- Graceful error handling and recovery responses
- Fallback response generation for different error types
- Context-aware error recovery
- Conversation flow validation
- Travel context detection and enhancement
- User experience improvement during errors

The service ensures users always receive helpful responses even when errors occur.

FILE DEPENDENCIES:
==================
UTILIZES (Dependencies):
- app/services/error_recovery.py - Main service being tested
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
from app.services.error_recovery import ErrorRecoveryService


class TestErrorRecoveryService:
    """Test suite for ErrorRecoveryService."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return ErrorRecoveryService()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, 'fallback_responses')
        assert isinstance(service.fallback_responses, dict)
        assert 'general_error' in service.fallback_responses
        assert 'no_context' in service.fallback_responses
        assert 'unclear_input' in service.fallback_responses
        assert 'off_topic' in service.fallback_responses
        assert 'api_error' in service.fallback_responses
    
    def test_fallback_responses_structure(self, service):
        """Test fallback responses have proper structure."""
        for category, responses in service.fallback_responses.items():
            assert isinstance(responses, list)
            assert len(responses) > 0
            for response in responses:
                assert isinstance(response, str)
                assert len(response) > 0
    
    def test_handle_technical_error(self, service):
        """Test technical error handling."""
        response = service.handle_technical_error()
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "technical" in response.lower() or "difficult" in response.lower()
    
    def test_handle_ambiguous_request(self, service):
        """Test ambiguous request handling."""
        message = "I want to travel"
        response = service.handle_ambiguous_request(message)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "details" in response.lower() or "more" in response.lower()
    
    def test_handle_off_topic_message(self, service):
        """Test off-topic message handling."""
        message = "What's the weather like?"
        response = service.handle_off_topic_message(message)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "vacation" in response.lower() or "travel" in response.lower()
    
    def test_get_recovery_response_general_error(self, service):
        """Test recovery response for general error."""
        response = service.get_recovery_response("general_error")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["vacation", "travel", "trip"])
    
    def test_get_recovery_response_no_context(self, service):
        """Test recovery response for no context."""
        response = service.get_recovery_response("no_context")
        

        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["trip", "adventure", "destination", "travel", "plan", "dreams"])
    
    def test_get_recovery_response_unclear(self, service):
        """Test recovery response for unclear input."""
        response = service.get_recovery_response("unclear_input")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["understand", "help", "clarify", "elaborate", "specific"])
    
    def test_get_recovery_response_off_topic(self, service):
        """Test recovery response for off-topic."""
        response = service.get_recovery_response("off_topic")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["vacation", "travel", "planning"])
    
    def test_get_recovery_response_api_error(self, service):
        """Test recovery response for API error."""
        response = service.get_recovery_response("api_error")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["vacation", "travel", "planning"])
    
    def test_get_recovery_response_unknown_error(self, service):
        """Test recovery response for unknown error type."""
        response = service.get_recovery_response("unknown_error_type")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["vacation", "travel", "planning"])
    
    def test_get_recovery_response_with_context(self, service):
        """Test recovery response with context."""
        context = {
            "last_destination": "Paris",
            "stage": "planning"
        }
        response = service.get_recovery_response("general_error", context)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Paris" in response
    
    def test_get_recovery_response_with_context_no_destination(self, service):
        """Test recovery response with context but no destination."""
        context = {
            "stage": "planning"
        }
        response = service.get_recovery_response("general_error", context)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "planning" in response.lower() or "trip" in response.lower()
    
    def test_enhance_with_context(self, service):
        """Test context enhancement."""
        base_response = "Let's plan your vacation."
        context = {
            "last_destination": "Tokyo",
            "stage": "planning"
        }
        enhanced = service._enhance_with_context(base_response, context)
        
        assert isinstance(enhanced, str)
        assert len(enhanced) > len(base_response)
        assert "Tokyo" in enhanced
    
    def test_enhance_with_context_no_destination(self, service):
        """Test context enhancement without destination."""
        base_response = "Let's plan your vacation."
        context = {
            "stage": "planning"
        }
        enhanced = service._enhance_with_context(base_response, context)
        
        assert isinstance(enhanced, str)
        assert len(enhanced) > len(base_response)
        assert "planning" in enhanced.lower() or "trip" in enhanced.lower()
    
    def test_enhance_with_context_empty_context(self, service):
        """Test context enhancement with empty context."""
        base_response = "Let's plan your vacation."
        context = {}
        enhanced = service._enhance_with_context(base_response, context)
        
        assert isinstance(enhanced, str)
        assert enhanced == base_response
    
    def test_validate_conversation_flow_valid(self, service):
        """Test conversation flow validation for valid flow."""
        messages = [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "assistant", "content": "Paris is great! What's your budget?"},
            {"role": "user", "content": "Around $2000"}
        ]
        new_message = "When should I go?"
        
        validation = service.validate_conversation_flow(messages, new_message)
        
        assert isinstance(validation, dict)
        assert 'is_valid' in validation
        assert 'issues' in validation
        assert 'suggestions' in validation
        assert validation['is_valid'] is True
    
    def test_validate_conversation_flow_repetitive(self, service):
        """Test conversation flow validation for repetitive questions."""
        messages = [
            {"role": "user", "content": "What's the weather like in Paris?"},
            {"role": "assistant", "content": "Paris has mild weather..."},
            {"role": "user", "content": "What's the weather like in Paris?"},
            {"role": "assistant", "content": "As I mentioned, Paris has mild weather..."},
            {"role": "user", "content": "What's the weather like in Paris?"}
        ]
        new_message = "What's the weather like in Paris?"
        
        validation = service.validate_conversation_flow(messages, new_message)
        
        assert isinstance(validation, dict)
        assert 'issues' in validation
        assert 'repetitive_questions' in validation['issues']
        assert len(validation['suggestions']) > 0
    
    def test_validate_conversation_flow_off_topic(self, service):
        """Test conversation flow validation for off-topic message."""
        messages = [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "assistant", "content": "Paris is great! What's your budget?"}
        ]
        new_message = "What's the capital of France and what are its main industries?"
        
        validation = service.validate_conversation_flow(messages, new_message)
        
        assert isinstance(validation, dict)
        assert 'issues' in validation
        assert 'possibly_off_topic' in validation['issues']
        assert validation['is_valid'] is False
    
    def test_validate_conversation_flow_short_message(self, service):
        """Test conversation flow validation for short off-topic message."""
        messages = [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "assistant", "content": "Paris is great! What's your budget?"}
        ]
        new_message = "Hi"
        
        validation = service.validate_conversation_flow(messages, new_message)
        
        assert isinstance(validation, dict)
        assert validation['is_valid'] is True  # Short messages shouldn't trigger off-topic
    
    def test_validate_conversation_flow_empty_messages(self, service):
        """Test conversation flow validation with empty messages."""
        validation = service.validate_conversation_flow([], "Hello")
        
        assert isinstance(validation, dict)
        assert validation['is_valid'] is True
    
    def test_validate_conversation_flow_no_new_message(self, service):
        """Test conversation flow validation with no new message."""
        messages = [
            {"role": "user", "content": "I want to go to Paris"}
        ]
        validation = service.validate_conversation_flow(messages, "")
        
        assert isinstance(validation, dict)
        assert validation['is_valid'] is True
    
    def test_has_travel_context_positive(self, service):
        """Test travel context detection for travel-related messages."""
        travel_messages = [
            "I want to travel to Paris",
            "Planning a trip to Japan",
            "Looking for vacation ideas",
            "Need help with hotel booking",
            "What flights are available?",
            "I'm going on holiday",
            "Tour recommendations please",
            "Reservation for accommodation",
            "Itinerary planning help",
            "Transportation options"
        ]
        
        for message in travel_messages:
            assert service._has_travel_context(message) is True
    
    def test_has_travel_context_negative(self, service):
        """Test travel context detection for non-travel messages."""
        non_travel_messages = [
            "What's the weather like?",
            "How do I cook pasta?",
            "What's the capital of France?",
            "Tell me about quantum physics",
            "What's your favorite color?",
            "How to fix a computer",
            "Recipe for chocolate cake",
            "History of ancient Rome",
            "Best programming languages",
            "How to grow tomatoes"
        ]
        
        for message in non_travel_messages:
            assert service._has_travel_context(message) is False
    
    def test_has_travel_context_case_insensitive(self, service):
        """Test travel context detection is case insensitive."""
        assert service._has_travel_context("I want to TRAVEL") is True
        assert service._has_travel_context("PLANNING A TRIP") is True
        assert service._has_travel_context("vacation ideas") is True
    
    def test_has_travel_context_empty_message(self, service):
        """Test travel context detection with empty message."""
        assert service._has_travel_context("") is False
    
    def test_recover_from_error_off_topic(self, service):
        """Test error recovery for off-topic errors."""
        error = "This is off topic and unrelated to travel"
        response = service.recover_from_error(error)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["vacation", "travel", "planning"])
    
    def test_recover_from_error_ambiguous(self, service):
        """Test error recovery for ambiguous errors."""
        error = "The request is ambiguous and unclear"
        response = service.recover_from_error(error)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["details", "clarify", "understand"])
    
    def test_recover_from_error_technical(self, service):
        """Test error recovery for technical errors."""
        error = "Technical API error occurred"
        response = service.recover_from_error(error)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "technical" in response.lower() or "difficult" in response.lower()
    
    def test_recover_from_error_general(self, service):
        """Test error recovery for general errors."""
        error = "Some random error occurred"
        response = service.recover_from_error(error)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["vacation", "travel", "planning"])
    
    def test_fallback_responses_variety(self, service):
        """Test that fallback responses provide variety."""
        responses = set()
        
        # Get multiple responses for the same error type
        for _ in range(10):
            response = service.get_recovery_response("general_error")
            responses.add(response)
        
        # Should have some variety (not all the same)
        assert len(responses) > 1
    
    def test_fallback_responses_consistency(self, service):
        """Test that fallback responses are consistent in structure."""
        for error_type in ["general_error", "no_context", "unclear", "off_topic", "api_error"]:
            response = service.get_recovery_response(error_type)
            
            assert isinstance(response, str)
            assert len(response) > 10  # Should be substantial
            assert any(keyword in response.lower() for keyword in ["vacation", "travel", "trip", "planning", "help"])
    
    def test_context_enhancement_priority(self, service):
        """Test that context enhancement prioritizes destination over stage."""
        base_response = "Let's continue planning."
        context = {
            "last_destination": "Tokyo",
            "stage": "planning"
        }
        enhanced = service._enhance_with_context(base_response, context)
        
        assert "Tokyo" in enhanced
        # Should mention Tokyo specifically, not just generic planning
    
    def test_validation_suggestions_helpful(self, service):
        """Test that validation suggestions are helpful."""
        messages = [
            {"role": "user", "content": "What's the weather like in Paris?"},
            {"role": "assistant", "content": "Paris has mild weather..."},
            {"role": "user", "content": "What's the weather like in Paris?"}
        ]
        new_message = "What's the weather like in Paris?"
        
        validation = service.validate_conversation_flow(messages, new_message)
        
        assert len(validation['suggestions']) > 0
        suggestion = validation['suggestions'][0]
        assert "summarize" in suggestion.lower() or "discussed" in suggestion.lower()
    
    def test_error_recovery_edge_cases(self, service):
        """Test error recovery with edge cases."""
        # Very long error message
        long_error = "Error: " + "x" * 1000
        response = service.recover_from_error(long_error)
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Empty error message
        response = service.recover_from_error("")
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Error with special characters
        special_error = "Error: 🚨💥🔥 Technical failure occurred!"
        response = service.recover_from_error(special_error)
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_conversation_flow_edge_cases(self, service):
        """Test conversation flow validation with edge cases."""
        # Very long message
        long_message = "I want to travel to " + "a very long destination name " * 50
        messages = [{"role": "user", "content": "Hello"}]
        validation = service.validate_conversation_flow(messages, long_message)
        assert isinstance(validation, dict)
        
        # Message with special characters
        special_message = "I want to go to Paris! 🗼 🇫🇷 #travel #vacation"
        validation = service.validate_conversation_flow(messages, special_message)
        assert isinstance(validation, dict)
        assert validation['is_valid'] is True  # Should be valid travel context 
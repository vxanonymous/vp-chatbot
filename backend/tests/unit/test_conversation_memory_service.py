"""
Comprehensive unit tests for ConversationMemory service.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from app.services.conversation_memory import ConversationMemory


class TestConversationMemory:
    """Test suite for ConversationMemory."""
    
    @pytest.fixture
    def memory(self):
        """Create a memory instance for testing."""
        return ConversationMemory()
    
    @pytest.fixture
    def sample_context(self):
        """Sample conversation context for testing."""
        return {
            "destinations": ["Paris"],
            "budget": "$2000",
            "travel_dates": "June 2023",
            "interests": ["culture", "food"]
        }
    
    @pytest.fixture
    def sample_messages(self):
        """Sample conversation messages for testing."""
        return [
            {"role": "user", "content": "I want to go to Paris"},
            {"role": "assistant", "content": "Paris is great! What's your budget?"},
            {"role": "user", "content": "Around $2000"},
            {"role": "assistant", "content": "Great budget! When are you planning to go?"},
            {"role": "user", "content": "In June, I love culture and food"}
        ]
    
    def test_initialization(self, memory):
        """Test service initialization."""
        assert memory is not None
        assert hasattr(memory, 'short_term_memory')
        assert hasattr(memory, 'long_term_memory')
        assert isinstance(memory.short_term_memory, dict)
        assert isinstance(memory.long_term_memory, dict)
    
    def test_update_context(self, memory):
        """Test context update."""
        conversation_id = "conv123"
        memory.update_context(conversation_id, "destination", "Paris")
        
        # Should create conversation entry if it doesn't exist
        assert conversation_id in memory.short_term_memory
    
    def test_store_context_dict(self, memory, sample_context):
        """Test storing context as dictionary."""
        conversation_id = "conv123"
        success = memory.store_context(conversation_id, sample_context)
        
        assert success is True
        assert conversation_id in memory.short_term_memory
        
        # Check that context was stored
        stored_context = memory.short_term_memory[conversation_id]
        assert "destinations" in stored_context
        assert "budget" in stored_context
        assert "travel_dates" in stored_context
        assert "interests" in stored_context
    
    def test_store_context_list(self, memory, sample_messages):
        """Test storing context as list of messages."""
        conversation_id = "conv123"
        success = memory.store_context(conversation_id, sample_messages)
        
        assert success is True
        assert conversation_id in memory.short_term_memory
        
        # Check that messages were stored
        stored_context = memory.short_term_memory[conversation_id]
        assert "messages" in stored_context
        assert stored_context["messages"]["value"] == sample_messages
    
    def test_store_context_generic(self, memory):
        """Test storing generic context."""
        conversation_id = "conv123"
        generic_context = "Some generic context information"
        success = memory.store_context(conversation_id, generic_context)
        
        assert success is True
        assert conversation_id in memory.short_term_memory
        
        # Check that context was stored
        stored_context = memory.short_term_memory[conversation_id]
        assert "context" in stored_context
        assert stored_context["context"]["value"] == generic_context
    
    def test_store_context_with_insights(self, memory, sample_context):
        """Test storing context with insights."""
        conversation_id = "conv123"
        insights = {
            "user_preferences": ["culture", "food"],
            "budget_range": "moderate"
        }
        success = memory.store_context(conversation_id, sample_context, insights)
        
        assert success is True
        assert conversation_id in memory.short_term_memory
        
        # Check that insights were stored
        stored_context = memory.short_term_memory[conversation_id]
        assert "insight_user_preferences" in stored_context
        assert "insight_budget_range" in stored_context
    
    def test_get_context_empty(self, memory):
        """Test getting context for non-existent conversation."""
        context = memory.get_context("nonexistent")
        
        assert isinstance(context, dict)
        assert len(context) == 0
    
    def test_get_context_with_data(self, memory, sample_context):
        """Test getting context with stored data."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        context = memory.get_context(conversation_id)
        
        assert isinstance(context, dict)
        assert len(context) > 0
        assert "destinations" in context
        assert "budget" in context
    
    def test_get_context_relevance_scoring(self, memory, sample_context):
        """Test that context includes relevance scoring."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        context = memory.get_context(conversation_id)
        
        assert isinstance(context, dict)
        for key, data in context.items():
            assert "value" in data
            assert "relevance" in data
            assert isinstance(data["relevance"], float)
            assert 0.0 <= data["relevance"] <= 1.0
    
    def test_get_context_recency_decay(self, memory, sample_context):
        """Test that context relevance decays over time."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        # Get context immediately
        context_immediate = memory.get_context(conversation_id)
        
        # Simulate time passing by modifying timestamps
        for key, data in memory.short_term_memory[conversation_id].items():
            data["timestamp"] = datetime.now(timezone.utc) - timedelta(hours=2)
        
        # Get context after time has passed
        context_delayed = memory.get_context(conversation_id)
        
        # Relevance should be lower after time has passed
        if context_immediate and context_delayed:
            immediate_relevance = sum(data["relevance"] for data in context_immediate.values())
            delayed_relevance = sum(data["relevance"] for data in context_delayed.values())
            assert delayed_relevance <= immediate_relevance
    
    def test_get_context_frequency_boost(self, memory, sample_context):
        """Test that frequently mentioned items have higher relevance."""
        conversation_id = "conv123"
        
        # Store context multiple times to increase frequency
        for _ in range(3):
            memory.store_context(conversation_id, sample_context)
        
        context = memory.get_context(conversation_id)
        
        assert isinstance(context, dict)
        # Items mentioned multiple times should have higher relevance
        for key, data in context.items():
            if data.get("mentioned_count", 0) > 1:
                assert data["relevance"] > 0.3  # Should be above threshold
    
    def test_extract_key_points(self, memory, sample_messages):
        """Test key points extraction from messages."""
        key_points = memory.extract_key_points(sample_messages)
        
        assert isinstance(key_points, dict)
        assert "destinations" in key_points
        assert "requirements" in key_points
        assert "preferences" in key_points
        assert "concerns" in key_points
        assert "decisions_made" in key_points
        
        # Should extract destinations
        assert len(key_points["destinations"]) > 0
        assert any("paris" in dest.lower() for dest in key_points["destinations"])
    
    def test_extract_key_points_empty_messages(self, memory):
        """Test key points extraction from empty messages."""
        key_points = memory.extract_key_points([])
        
        assert isinstance(key_points, dict)
        assert all(len(value) == 0 for value in key_points.values())
    
    def test_extract_key_points_requirements(self, memory):
        """Test extraction of requirements from messages."""
        messages = [
            {"role": "user", "content": "I need a hotel near the Eiffel Tower"},
            {"role": "user", "content": "It's important to have good food options"},
            {"role": "user", "content": "I must have air conditioning"}
        ]
        
        key_points = memory.extract_key_points(messages)
        
        assert len(key_points["requirements"]) > 0
        assert any("hotel" in req.lower() for req in key_points["requirements"])
        assert any("food" in req.lower() for req in key_points["requirements"])
    
    def test_extract_key_points_preferences(self, memory):
        """Test extraction of preferences from messages."""
        messages = [
            {"role": "user", "content": "I prefer cultural activities"},
            {"role": "user", "content": "I like trying local food"},
            {"role": "user", "content": "I love visiting museums"}
        ]
        
        key_points = memory.extract_key_points(messages)
        
        assert len(key_points["preferences"]) > 0
        assert any("cultural" in pref.lower() for pref in key_points["preferences"])
        assert any("food" in pref.lower() for pref in key_points["preferences"])
    
    def test_extract_key_points_decisions(self, memory):
        """Test extraction of decisions from messages."""
        messages = [
            {"role": "user", "content": "I decided to go to Paris"},
            {"role": "user", "content": "I'm going to book the hotel tomorrow"},
            {"role": "user", "content": "I will visit the Louvre"}
        ]
        
        key_points = memory.extract_key_points(messages)
        
        assert len(key_points["decisions_made"]) > 0
        assert any("paris" in decision.lower() for decision in key_points["decisions_made"])
        assert any("book" in decision.lower() for decision in key_points["decisions_made"])
    
    def test_clear_context(self, memory, sample_context):
        """Test clearing context for a specific conversation."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        # Verify context exists
        assert conversation_id in memory.short_term_memory
        
        # Clear context
        memory.clear_context(conversation_id)
        
        # Verify context is cleared
        assert conversation_id not in memory.short_term_memory
    
    def test_clear_context_nonexistent(self, memory):
        """Test clearing context for non-existent conversation."""
        # Should not raise an error
        memory.clear_context("nonexistent")
    
    def test_cleanup_old_contexts(self, memory, sample_context):
        """Test cleanup of old conversation contexts."""
        # Create multiple conversations
        for i in range(5):
            conversation_id = f"conv{i}"
            memory.store_context(conversation_id, sample_context)
        
        # Verify all conversations exist
        assert len(memory.short_term_memory) == 5
        
        # Simulate old timestamps for some conversations
        for i in range(3):
            conversation_id = f"conv{i}"
            for key, data in memory.short_term_memory[conversation_id].items():
                data["timestamp"] = datetime.now(timezone.utc) - timedelta(hours=25)
        
        # Clean up old contexts
        memory.cleanup_old_contexts(max_age_hours=24)
        
        # Should have cleaned up old conversations
        assert len(memory.short_term_memory) < 5
    
    def test_cleanup_old_contexts_no_old(self, memory, sample_context):
        """Test cleanup when no contexts are old."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        initial_count = len(memory.short_term_memory)
        
        # Clean up old contexts
        memory.cleanup_old_contexts(max_age_hours=24)
        
        # Should not have cleaned up anything
        assert len(memory.short_term_memory) == initial_count
    
    def test_context_persistence_across_calls(self, memory, sample_context):
        """Test that context persists across multiple calls."""
        conversation_id = "conv123"
        
        # Store context
        memory.store_context(conversation_id, sample_context)
        
        # Get context multiple times
        context1 = memory.get_context(conversation_id)
        context2 = memory.get_context(conversation_id)
        context3 = memory.get_context(conversation_id)
        
        # All should be the same
        assert context1 == context2 == context3
    
    def test_context_update_existing(self, memory, sample_context):
        """Test updating existing context."""
        conversation_id = "conv123"
        
        # Store initial context
        memory.store_context(conversation_id, sample_context)
        
        # Update with new context
        new_context = {"budget": "$3000", "new_interest": "shopping"}
        memory.store_context(conversation_id, new_context)
        
        # Get updated context
        context = memory.get_context(conversation_id)
        
        # Should have both old and new context
        assert "destinations" in context  # From original
        assert "budget" in context  # Updated
        assert "new_interest" in context  # New
    
    def test_context_mentioned_count_tracking(self, memory, sample_context):
        """Test that mentioned count is tracked correctly."""
        conversation_id = "conv123"
        
        # Store context multiple times
        for _ in range(3):
            memory.store_context(conversation_id, sample_context)
        
        # Check mentioned count
        stored_context = memory.short_term_memory[conversation_id]
        for key, data in stored_context.items():
            assert data["mentioned_count"] == 3
    
    def test_context_relevance_calculation(self, memory, sample_context):
        """Test relevance calculation formula."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        context = memory.get_context(conversation_id)
        
        for key, data in context.items():
            relevance = data["relevance"]
            
            # Relevance should be between 0 and 1
            assert 0.0 <= relevance <= 1.0
            
            # Should be calculated based on recency and frequency
            # Formula: (recency_score * 0.7) + (frequency_score * 0.3)
            assert relevance <= 1.0  # Maximum possible relevance
    
    def test_context_edge_cases(self, memory):
        """Test context handling with edge cases."""
        conversation_id = "conv123"
        
        # Very large context
        large_context = {f"key_{i}": f"value_{i}" for i in range(1000)}
        success = memory.store_context(conversation_id, large_context)
        
        assert success is True
        assert conversation_id in memory.short_term_memory
        
        # Empty context
        success = memory.store_context("conv456", {})
        assert success is True
        
        # None context
        success = memory.store_context("conv789", None)
        assert success is True
        
        # Very long string context
        long_context = "x" * 10000
        success = memory.store_context("conv999", long_context)
        assert success is True
    
    def test_messages_edge_cases(self, memory):
        """Test message handling with edge cases."""
        # Very long messages
        long_messages = [
            {"role": "user", "content": "x" * 10000},
            {"role": "assistant", "content": "y" * 10000}
        ]
        key_points = memory.extract_key_points(long_messages)
        
        assert isinstance(key_points, dict)
        
        # Empty messages
        key_points = memory.extract_key_points([])
        assert isinstance(key_points, dict)
        
        # Messages with special characters
        special_messages = [
            {"role": "user", "content": "I want to go to Paris! 🗼 🇫🇷 #travel"},
            {"role": "assistant", "content": "Paris is great! 🌍 ✈️"}
        ]
        key_points = memory.extract_key_points(special_messages)
        
        assert isinstance(key_points, dict)
        assert "paris" in str(key_points).lower()
    
    def test_cleanup_edge_cases(self, memory):
        """Test cleanup with edge cases."""
        # Cleanup with no conversations
        memory.cleanup_old_contexts(max_age_hours=24)
        
        # Cleanup with negative max age
        memory.cleanup_old_contexts(max_age_hours=-1)
        
        # Cleanup with very large max age
        memory.cleanup_old_contexts(max_age_hours=1000000)
    
    def test_memory_isolation(self, memory):
        """Test that conversations are isolated from each other."""
        # Store context for two different conversations
        memory.store_context("conv1", {"destination": "Paris"})
        memory.store_context("conv2", {"destination": "Tokyo"})
        
        # Get contexts
        context1 = memory.get_context("conv1")
        context2 = memory.get_context("conv2")
        
        # Should be different
        assert context1 != context2
        assert "paris" in str(context1).lower()
        assert "tokyo" in str(context2).lower()
    
    def test_context_metadata_structure(self, memory, sample_context):
        """Test that context metadata has proper structure."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        stored_context = memory.short_term_memory[conversation_id]
        
        for key, data in stored_context.items():
            assert "value" in data
            assert "timestamp" in data
            assert "mentioned_count" in data
            
            assert isinstance(data["timestamp"], datetime)
            assert isinstance(data["mentioned_count"], int)
            assert data["mentioned_count"] >= 1
    
    def test_relevance_threshold_filtering(self, memory, sample_context):
        """Test that only relevant context is returned."""
        conversation_id = "conv123"
        memory.store_context(conversation_id, sample_context)
        
        # Make context very old to reduce relevance
        for key, data in memory.short_term_memory[conversation_id].items():
            data["timestamp"] = datetime.now(timezone.utc) - timedelta(hours=10)
        
        context = memory.get_context(conversation_id)
        
        # Should only include context with relevance > 0.3
        for key, data in context.items():
            assert data["relevance"] > 0.3 
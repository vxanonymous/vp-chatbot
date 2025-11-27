# Unit tests for RequestDeduplicator service.
import asyncio
import pytest
import time
from app.services.request_deduplicator import RequestDeduplicator

class TestRequestDeduplicator:
    # Test suite for RequestDeduplicator service.
    
    @pytest.fixture
    def deduplicator(self):
        # Create a RequestDeduplicator instance for testing.
        return RequestDeduplicator(ttl=60, max_cache_size=100)
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, deduplicator):
        # Test that identical requests return cached results.
        call_count = 0
        
        async def test_coro():
            nonlocal call_count
            call_count += 1
            return {"response": "test response", "count": call_count}
        
        # First call should execute
        result1, is_cached1 = await deduplicator.get_or_execute(
            user_id="user1",
            message="test message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached1
        assert result1["count"] == 1
        assert call_count == 1
        
        # Second call should return cached result
        result2, is_cached2 = await deduplicator.get_or_execute(
            user_id="user1",
            message="test message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert is_cached2
        assert result2["count"] == 1  # Should still be 1, not 2
        assert call_count == 1  # Coroutine should not be called again
    
    @pytest.mark.asyncio
    async def test_cache_miss_different_message(self, deduplicator):
        # Test that different messages result in cache misses.
        call_count = 0
        
        async def test_coro():
            nonlocal call_count
            call_count += 1
            return {"response": f"response {call_count}"}
        
        # First call
        result1, is_cached1 = await deduplicator.get_or_execute(
            user_id="user1",
            message="message 1",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached1
        assert call_count == 1
        
        # Different message should cause cache miss
        result2, is_cached2 = await deduplicator.get_or_execute(
            user_id="user1",
            message="message 2",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached2
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_miss_different_user(self, deduplicator):
        # Test that different users result in cache misses.
        call_count = 0
        
        async def test_coro():
            nonlocal call_count
            call_count += 1
            return {"response": f"response {call_count}"}
        
        # First call for user1
        result1, is_cached1 = await deduplicator.get_or_execute(
            user_id="user1",
            message="same message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached1
        assert call_count == 1
        
        # Same message for different user should cause cache miss
        result2, is_cached2 = await deduplicator.get_or_execute(
            user_id="user2",
            message="same message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached2
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, deduplicator):
        # Test that cache entries expire after TTL.
        deduplicator._ttl = 0.1  # Very short TTL for testing
        call_count = 0
        
        async def test_coro():
            nonlocal call_count
            call_count += 1
            return {"response": f"response {call_count}"}
        
        # First call
        result1, is_cached1 = await deduplicator.get_or_execute(
            user_id="user1",
            message="test message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached1
        assert call_count == 1
        
        # Immediate second call should be cached
        result2, is_cached2 = await deduplicator.get_or_execute(
            user_id="user1",
            message="test message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert is_cached2
        assert call_count == 1
        
        # Wait for expiration
        await asyncio.sleep(0.15)
        
        # After expiration, should execute again
        result3, is_cached3 = await deduplicator.get_or_execute(
            user_id="user1",
            message="test message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached3
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, deduplicator):
        # Test that cache respects max size limit.
        deduplicator._max_cache_size = 3
        call_count = 0
        
        async def test_coro(msg):
            nonlocal call_count
            call_count += 1
            return {"response": f"response for {msg}", "count": call_count}
        
        # Fill cache to max size
        for i in range(3):
            await deduplicator.get_or_execute(
                user_id="user1",
                message=f"message {i}",
                conversation_id=None,
                coro=lambda: test_coro(f"message {i}")
            )
        
        assert len(deduplicator._cache) == 3
        
        # Add one more, should remove oldest
        await deduplicator.get_or_execute(
            user_id="user1",
            message="message 3",
            conversation_id=None,
            coro=lambda: test_coro("message 3")
        )
        
        # Cache should still be at max size
        assert len(deduplicator._cache) <= deduplicator._max_cache_size
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, deduplicator):
        # Test that clear_cache removes all entries.
        async def test_coro():
            return {"response": "test"}
        
        for i in range(5):
            await deduplicator.get_or_execute(
                user_id="user1",
                message=f"message {i}",
                conversation_id=None,
                coro=test_coro
            )
        
        assert len(deduplicator._cache) > 0
        
        # Clear cache
        await deduplicator.clear_cache()
        
        assert len(deduplicator._cache) == 0
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, deduplicator):
        # Test that cache stats are returned correctly.
        async def test_coro():
            return {"response": "test"}
        
        # Add some entries
        await deduplicator.get_or_execute(
            user_id="user1",
            message="message 1",
            conversation_id=None,
            coro=test_coro
        )
        
        stats = await deduplicator.get_cache_stats()
        
        assert "total_entries" in stats
        assert "valid_entries" in stats
        assert "expired_entries" in stats
        assert "max_size" in stats
        assert "ttl" in stats
        assert stats["total_entries"] >= 1
        assert stats["valid_entries"] >= 1
    
    @pytest.mark.asyncio
    async def test_conversation_id_affects_cache_key(self, deduplicator):
        # Test that conversation_id is part of the cache key.
        call_count = 0
        
        async def test_coro():
            nonlocal call_count
            call_count += 1
            return {"response": f"response {call_count}"}
        
        # First call without conversation_id
        result1, is_cached1 = await deduplicator.get_or_execute(
            user_id="user1",
            message="same message",
            conversation_id=None,
            coro=test_coro
        )
        
        assert not is_cached1
        assert call_count == 1
        
        # Same message with conversation_id should be different cache key
        result2, is_cached2 = await deduplicator.get_or_execute(
            user_id="user1",
            message="same message",
            conversation_id="conv123",
            coro=test_coro
        )
        
        assert not is_cached2
        assert call_count == 2



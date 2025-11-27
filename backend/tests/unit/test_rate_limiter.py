# Tests for rate limiter middleware.
import pytest
import asyncio
from datetime import datetime, timedelta

from app.middleware.rate_limiter import RateLimiter


class TestRateLimiter:
    # Test rate limiter functionality
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        # Test rate limit exceeded scenario
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Make requests up to the limit
        allowed1, remaining1 = await limiter.is_allowed("user1")
        assert allowed1 is True
        
        allowed2, remaining2 = await limiter.is_allowed("user1")
        assert allowed2 is True
        
        # This should exceed the limit
        allowed3, remaining3 = await limiter.is_allowed("user1")
        assert allowed3 is False
        assert remaining3 == 0
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit(self):
        # Test resetting rate limit
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Make requests
        await limiter.is_allowed("user1")
        await limiter.is_allowed("user1")
        
        # Reset
        await limiter.reset("user1")
        
        # Should be able to make requests again
        allowed, remaining = await limiter.is_allowed("user1")
        assert allowed is True
    
    def test_get_remaining(self):
        # Test get_remaining without consuming
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Initially should have all requests remaining
        remaining = limiter.get_remaining("user1")
        assert remaining == 5
        
        # After making requests (async), check remaining
        # Note: get_remaining doesn't consume, so it should still show 5
        # But we need to actually make requests to test properly
        import asyncio
        async def make_requests():
            await limiter.is_allowed("user1")
            await limiter.is_allowed("user1")
            return limiter.get_remaining("user1")
        
        remaining = asyncio.run(make_requests())
        assert remaining == 3  # 5 - 2 = 3
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_expiry(self):
        # Test that old requests are cleaned up
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Make requests
        await limiter.is_allowed("user1")
        await limiter.is_allowed("user1")
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should be able to make requests again
        allowed, remaining = await limiter.is_allowed("user1")
        assert allowed is True




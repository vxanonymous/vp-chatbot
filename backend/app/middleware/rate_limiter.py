# Rate limiting middleware for API endpoints.
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    # Simple in-memory rate limiter for API endpoints.
    # For production, consider using Redis-based rate limiting
    # for distributed systems.
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        # Initialize rate limiter with max requests per time window
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        # Check if request is allowed for the given identifier
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            # Clean old requests
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            request_count = len(self._requests[identifier])
            
            if request_count >= self.max_requests:
                remaining = 0
                return False, remaining
            
            # Add current request
            self._requests[identifier].append(now)
            remaining = self.max_requests - request_count - 1
            
            return True, remaining
    
    async def reset(self, identifier: str):
        # Reset rate limit counters for the given identifier.
        async with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]

    def get_remaining(self, identifier: str) -> int:
        # Get remaining requests for an identifier (without consuming).
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        recent_requests = [
            req_time for req_time in self._requests.get(identifier, [])
            if req_time > window_start
        ]
        return max(0, self.max_requests - len(recent_requests))


# Global rate limiter instance
chat_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)  # 20 requests per minute
openai_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)  # 10 OpenAI calls per minute



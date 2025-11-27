# Request deduplication service to cache identical requests and reduce redundant API calls.
import asyncio
import hashlib
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RequestDeduplicator:
    # Caches identical requests to avoid redundant processing and API calls.
    # Reduces OpenAI API costs and improves response times for duplicate requests.
    
    def __init__(self, ttl: int = 60, max_cache_size: int = 1000):
        # Initialize request deduplicator
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self._ttl = ttl
        self._max_cache_size = max_cache_size
    
    def _generate_key(self, user_id: str, message: str, conversation_id: Optional[str] = None) -> str:
        # Generate a unique cache key from request parameters
        content = f"{user_id}:{conversation_id or 'new'}:{message.strip().lower()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def get_or_execute(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str],
        coro: Callable[[], Any]
    ) -> tuple[Any, bool]:
        # Get cached response or execute the coroutine and cache the result
        key = self._generate_key(user_id, message, conversation_id)
        
        async with self._lock:
            # Check cache
            if key in self._cache:
                cached_result, timestamp = self._cache[key]
                age = time.time() - timestamp
                
                if age < self._ttl:
                    logger.debug(f"Cache hit for request key: {key[:8]}... (age: {age:.2f}s)")
                    return cached_result, True
                else:
                    # Expired entry, remove it
                    del self._cache[key]
                    logger.debug(f"Cache expired for request key: {key[:8]}...")
            
            # Cleanup old entries if cache is too large
            if len(self._cache) >= self._max_cache_size:
                await self._cleanup_expired()
            
            # If still at max size, remove oldest entry
            if len(self._cache) >= self._max_cache_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
                logger.debug(f"Cache full, removed oldest entry: {oldest_key[:8]}...")
        
        # Execute the coroutine (outside the lock to avoid blocking)
        try:
            result = await coro()
            
            # Cache the result
            async with self._lock:
                self._cache[key] = (result, time.time())
                logger.debug(f"Cached result for request key: {key[:8]}...")
            
            return result, False
        except Exception as e:
            logger.error(f"Error executing coroutine for deduplication: {e}")
            raise
    
    async def _cleanup_expired(self) -> None:
        # Remove expired entries from cache.
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self._ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def clear_cache(self) -> None:
        # Clear all cached entries.
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} cached entries")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        # Get cache statistics
        async with self._lock:
            current_time = time.time()
            valid_entries = sum(
                1 for _, timestamp in self._cache.values()
                if current_time - timestamp < self._ttl
            )
            
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_entries,
                "expired_entries": len(self._cache) - valid_entries,
                "max_size": self._max_cache_size,
                "ttl": self._ttl
            }


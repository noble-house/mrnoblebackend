import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
from ..config import settings
from ..services.logger import log_error, get_logger

logger = get_logger("cache_service")

class CacheService:
    """Redis-based caching service for MrNoble."""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,  # We'll handle encoding/decoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            log_error(e, context={"operation": "cache_init"})
            self.redis_client = None
            self.connected = False
            logger.warning("Redis cache not available, running without cache")
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage in Redis."""
        try:
            if isinstance(data, (str, int, float, bool)):
                return json.dumps(data).encode('utf-8')
            else:
                return pickle.dumps(data)
        except Exception as e:
            log_error(e, context={"operation": "cache_serialize"})
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from Redis."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fallback to pickle
                return pickle.loads(data)
            except Exception as e:
                log_error(e, context={"operation": "cache_deserialize"})
                return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.connected:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            log_error(e, context={"operation": "cache_get", "key": key})
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.connected:
            return False
        
        try:
            serialized_value = self._serialize(value)
            ttl = ttl or settings.CACHE_TTL
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            log_error(e, context={"operation": "cache_set", "key": key})
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.connected:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            log_error(e, context={"operation": "cache_delete", "key": key})
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.connected:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            log_error(e, context={"operation": "cache_exists", "key": key})
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        if not self.connected:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            log_error(e, context={"operation": "cache_clear_pattern", "pattern": pattern})
            return 0
    
    def get_or_set(self, key: str, func, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """Get value from cache or set it using a function."""
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # If not in cache, compute and store
        try:
            value = func(*args, **kwargs)
            self.set(key, value, ttl)
            return value
        except Exception as e:
            log_error(e, context={"operation": "cache_get_or_set", "key": key})
            # Return the computed value even if caching fails
            return func(*args, **kwargs)
    
    def invalidate_related(self, entity_type: str, entity_id: Optional[int] = None):
        """Invalidate cache entries related to an entity."""
        patterns = [
            f"*{entity_type}*",
            f"*{entity_type}:{entity_id}*" if entity_id else None,
            f"*dashboard*",
            f"*stats*"
        ]
        
        for pattern in patterns:
            if pattern:
                self.clear_pattern(pattern)

# Cache key generators
class CacheKeys:
    """Centralized cache key generation."""
    
    @staticmethod
    def job(job_id: int) -> str:
        return f"job:{job_id}"
    
    @staticmethod
    def candidate(candidate_id: int) -> str:
        return f"candidate:{candidate_id}"
    
    @staticmethod
    def application(application_id: int) -> str:
        return f"application:{application_id}"
    
    @staticmethod
    def interview_link(token: str) -> str:
        return f"interview_link:{token}"
    
    @staticmethod
    def dashboard_stats() -> str:
        return "dashboard:stats"
    
    @staticmethod
    def recent_activity() -> str:
        return "dashboard:recent_activity"
    
    @staticmethod
    def ai_embedding(text_hash: str) -> str:
        return f"ai:embedding:{text_hash}"
    
    @staticmethod
    def ai_skills(text_hash: str) -> str:
        return f"ai:skills:{text_hash}"

# Global cache instance
cache_service = CacheService()

# Decorator for caching function results
def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result and cache it
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

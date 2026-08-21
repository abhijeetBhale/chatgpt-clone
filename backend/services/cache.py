"""Redis caching service for chat data."""
import json
import redis.asyncio as redis
from typing import Optional, Any
from settings import settings


class CacheService:
    """Redis-based cache service with fallback to in-memory cache."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: dict = {}
        self._connected = False
    
    async def connect(self):
        """Connect to Redis."""
        if not settings.CACHE_ENABLED:
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self.redis_client.ping()
            self._connected = True
            print("Redis cache connected")
        except Exception as e:
            print(f"Redis connection failed, using in-memory cache: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_key(self, prefix: str, entity_id: str) -> str:
        """Generate cache key."""
        return f"boostai:{prefix}:{entity_id}"
    
    async def get(self, prefix: str, entity_id: str) -> Optional[Any]:
        """Get value from cache."""
        if not settings.CACHE_ENABLED:
            return None
            
        key = self._get_key(prefix, entity_id)
        
        try:
            if self._connected and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Fallback to in-memory cache
                import time
                cached = self.memory_cache.get(key)
                if cached and cached["expires"] > time.time():
                    return cached["value"]
                elif cached:
                    del self.memory_cache[key]
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def set(self, prefix: str, entity_id: str, value: Any, ttl: int = None):
        """Set value in cache."""
        if not settings.CACHE_ENABLED:
            return
            
        key = self._get_key(prefix, entity_id)
        ttl = ttl or settings.CACHE_TTL
        
        try:
            serialized = json.dumps(value, default=str)
            
            if self._connected and self.redis_client:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                # Fallback to in-memory cache
                import time
                self.memory_cache[key] = {
                    "value": value,
                    "expires": time.time() + ttl
                }
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def delete(self, prefix: str, entity_id: str):
        """Delete value from cache."""
        key = self._get_key(prefix, entity_id)
        
        try:
            if self._connected and self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        try:
            if self._connected and self.redis_client:
                keys = []
                async for key in self.redis_client.scan_iter(match=f"boostai:{pattern}*"):
                    keys.append(key)
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                # For in-memory cache, iterate and delete matching keys
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"boostai:{pattern}")]
                for key in keys_to_delete:
                    del self.memory_cache[key]
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
    
    async def flush_user_cache(self, user_id: str):
        """Flush all cache entries for a user."""
        await self.delete_pattern(f"chat:{user_id}")
        await self.delete_pattern(f"userchats:{user_id}")


# Singleton instance
cache = CacheService()

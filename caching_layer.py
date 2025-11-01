"""
Caching Layer Module
Redis-based caching for API responses, database queries, and frequently accessed data
"""

import json
from datetime import timedelta
from typing import Any, Optional, Callable
import hashlib
from functools import wraps

class CacheManager:
    """In-memory cache manager with Redis-like interface for serverless compatibility"""
    
    def __init__(self):
        self.cache = {}
        self.ttls = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Check if expired
            if key in self.ttls:
                import time
                if time.time() > self.ttls[key]:
                    del self.cache[key]
                    del self.ttls[key]
                    return None
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (default 5 minutes)"""
        import time
        self.cache[key] = value
        self.ttls[key] = time.time() + ttl
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttls:
                del self.ttls[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.get(key) is not None
    
    def clear(self) -> bool:
        """Clear all cache"""
        self.cache.clear()
        self.ttls.clear()
        return True
    
    def keys(self, pattern: str = '*') -> list:
        """Get all keys matching pattern"""
        if pattern == '*':
            return list(self.cache.keys())
        
        # Simple pattern matching
        import re
        regex = pattern.replace('*', '.*')
        return [k for k in self.cache.keys() if re.match(regex, k)]
    
    def ttl_remaining(self, key: str) -> int:
        """Get remaining TTL for key"""
        if key not in self.ttls:
            return -1
        
        import time
        remaining = int(self.ttls[key] - time.time())
        return max(0, remaining)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        keys = self.keys(pattern)
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count


class CacheService:
    """High-level caching service with decorators and utilities"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.default_ttl = 300  # 5 minutes
        
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [prefix]
        
        # Add positional args
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # Add keyword args
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}:{v}")
        
        # Create hash for long keys
        key_str = ":".join(key_parts)
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_str
    
    def cached(self, ttl: int = None, key_prefix: str = None):
        """Decorator to cache function results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                prefix = key_prefix or f"func:{func.__name__}"
                cache_key = self.generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                cache_ttl = ttl or self.default_ttl
                self.cache.set(cache_key, result, cache_ttl)
                
                return result
            
            # Add cache management methods
            wrapper.invalidate = lambda *args, **kwargs: self.cache.delete(
                self.generate_key(key_prefix or f"func:{func.__name__}", *args, **kwargs)
            )
            wrapper.invalidate_all = lambda: self.cache.invalidate_pattern(
                f"{key_prefix or f'func:{func.__name__}'}:*"
            )
            
            return wrapper
        return decorator
    
    def cache_api_response(self, endpoint: str, params: dict, response: Any, ttl: int = 60):
        """Cache API response"""
        cache_key = self.generate_key(f"api:{endpoint}", params)
        return self.cache.set(cache_key, response, ttl)
    
    def get_api_response(self, endpoint: str, params: dict) -> Optional[Any]:
        """Get cached API response"""
        cache_key = self.generate_key(f"api:{endpoint}", params)
        return self.cache.get(cache_key)
    
    def cache_query_result(self, query: str, params: tuple, result: Any, ttl: int = 300):
        """Cache database query result"""
        cache_key = self.generate_key("query", query, params)
        return self.cache.set(cache_key, result, ttl)
    
    def get_query_result(self, query: str, params: tuple) -> Optional[Any]:
        """Get cached query result"""
        cache_key = self.generate_key("query", query, params)
        return self.cache.get(cache_key)
    
    def cache_user_data(self, user_id: str, data: Any, ttl: int = 600):
        """Cache user-specific data"""
        cache_key = f"user:{user_id}"
        return self.cache.set(cache_key, data, ttl)
    
    def get_user_data(self, user_id: str) -> Optional[Any]:
        """Get cached user data"""
        cache_key = f"user:{user_id}"
        return self.cache.get(cache_key)
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache for user"""
        return self.cache.invalidate_pattern(f"user:{user_id}*")
    
    def cache_analytics(self, metric: str, filters: dict, result: Any, ttl: int = 1800):
        """Cache analytics data (30 minutes default)"""
        cache_key = self.generate_key(f"analytics:{metric}", filters)
        return self.cache.set(cache_key, result, ttl)
    
    def get_analytics(self, metric: str, filters: dict) -> Optional[Any]:
        """Get cached analytics"""
        cache_key = self.generate_key(f"analytics:{metric}", filters)
        return self.cache.get(cache_key)
    
    def invalidate_analytics(self, metric: str = None):
        """Invalidate analytics cache"""
        pattern = f"analytics:{metric}:*" if metric else "analytics:*"
        return self.cache.invalidate_pattern(pattern)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        total_keys = len(self.cache.cache)
        
        # Group by prefix
        key_types = {}
        for key in self.cache.cache.keys():
            prefix = key.split(':')[0] if ':' in key else 'other'
            key_types[prefix] = key_types.get(prefix, 0) + 1
        
        # Calculate memory usage (rough estimate)
        import sys
        memory_bytes = sum(
            sys.getsizeof(k) + sys.getsizeof(v) 
            for k, v in self.cache.cache.items()
        )
        
        return {
            'total_keys': total_keys,
            'by_type': key_types,
            'memory_mb': round(memory_bytes / (1024 * 1024), 2)
        }
    
    def warm_cache(self, data_loaders: list):
        """Warm up cache with frequently accessed data"""
        for loader in data_loaders:
            try:
                key = loader.get('key')
                func = loader.get('func')
                ttl = loader.get('ttl', self.default_ttl)
                
                if key and func:
                    result = func()
                    self.cache.set(key, result, ttl)
            except Exception as e:
                print(f"Cache warming error for {loader.get('key')}: {e}")
        
        return self.get_cache_stats()


class CacheInvalidationService:
    """Service for managing cache invalidation strategies"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        
    def on_create(self, entity_type: str, entity_id: str):
        """Invalidate cache when entity is created"""
        patterns = [
            f"api:{entity_type}:list:*",
            f"analytics:{entity_type}:*",
            f"query:SELECT * FROM {entity_type}*"
        ]
        
        for pattern in patterns:
            self.cache.cache.invalidate_pattern(pattern)
    
    def on_update(self, entity_type: str, entity_id: str):
        """Invalidate cache when entity is updated"""
        patterns = [
            f"api:{entity_type}:{entity_id}:*",
            f"api:{entity_type}:list:*",
            f"analytics:{entity_type}:*",
            f"query:SELECT * FROM {entity_type}*",
            f"{entity_type}:{entity_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.cache.invalidate_pattern(pattern)
    
    def on_delete(self, entity_type: str, entity_id: str):
        """Invalidate cache when entity is deleted"""
        patterns = [
            f"api:{entity_type}:{entity_id}:*",
            f"api:{entity_type}:list:*",
            f"analytics:{entity_type}:*",
            f"query:SELECT * FROM {entity_type}*",
            f"{entity_type}:{entity_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.cache.invalidate_pattern(pattern)
    
    def on_user_action(self, user_id: str, action_type: str):
        """Invalidate cache for user actions"""
        self.cache.invalidate_user_cache(user_id)
        
        # Invalidate related analytics
        if action_type in ['lead_update', 'deal_update', 'contact_update']:
            self.cache.invalidate_analytics()
    
    def scheduled_invalidation(self, entity_type: str, max_age_hours: int = 24):
        """Scheduled cache invalidation for old data"""
        # In production, this would be called by a cron job
        pattern = f"{entity_type}:*"
        return self.cache.cache.invalidate_pattern(pattern)

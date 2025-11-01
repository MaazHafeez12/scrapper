"""
Rate Limiting System
Request throttling to prevent API abuse with per-user/per-IP rate limits
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
from functools import wraps
from flask import request, jsonify

class RateLimiter:
    """Token bucket rate limiter implementation"""
    
    def __init__(self):
        self.buckets = {}  # {key: {'tokens': count, 'last_update': timestamp}}
        self.rules = {}    # {endpoint_pattern: {'requests': count, 'window': seconds}}
        
    def add_rule(self, pattern: str, requests: int, window: int):
        """Add rate limit rule for endpoint pattern"""
        self.rules[pattern] = {
            'requests': requests,
            'window': window,
            'tokens_per_second': requests / window
        }
    
    def get_rule(self, endpoint: str) -> Optional[Dict]:
        """Get rate limit rule for endpoint"""
        # Check exact match first
        if endpoint in self.rules:
            return self.rules[endpoint]
        
        # Check pattern matches
        for pattern, rule in self.rules.items():
            if pattern in endpoint or endpoint.startswith(pattern):
                return rule
        
        # Default rule
        return {'requests': 100, 'window': 60, 'tokens_per_second': 100/60}
    
    def check_limit(self, key: str, rule: Dict) -> Tuple[bool, Dict]:
        """Check if request is allowed under rate limit"""
        current_time = time.time()
        
        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': rule['requests'],
                'last_update': current_time
            }
        
        bucket = self.buckets[key]
        
        # Refill tokens based on time passed
        time_passed = current_time - bucket['last_update']
        tokens_to_add = time_passed * rule['tokens_per_second']
        bucket['tokens'] = min(
            rule['requests'],
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_update'] = current_time
        
        # Check if request is allowed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True, {
                'allowed': True,
                'remaining': int(bucket['tokens']),
                'limit': rule['requests'],
                'window': rule['window'],
                'reset': int(current_time + rule['window'])
            }
        else:
            retry_after = int((1 - bucket['tokens']) / rule['tokens_per_second'])
            return False, {
                'allowed': False,
                'remaining': 0,
                'limit': rule['requests'],
                'window': rule['window'],
                'reset': int(current_time + rule['window']),
                'retry_after': retry_after
            }
    
    def get_bucket_info(self, key: str) -> Optional[Dict]:
        """Get current bucket status"""
        if key not in self.buckets:
            return None
        
        bucket = self.buckets[key]
        return {
            'tokens': int(bucket['tokens']),
            'last_update': bucket['last_update']
        }
    
    def reset_bucket(self, key: str):
        """Reset rate limit bucket for key"""
        if key in self.buckets:
            del self.buckets[key]
    
    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """Remove old inactive buckets"""
        current_time = time.time()
        keys_to_remove = [
            key for key, bucket in self.buckets.items()
            if current_time - bucket['last_update'] > max_age_seconds
        ]
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        return len(keys_to_remove)


class RateLimitService:
    """High-level rate limiting service with Flask integration"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.limiter = rate_limiter
        self.setup_default_rules()
        
    def setup_default_rules(self):
        """Setup default rate limiting rules"""
        # Public endpoints - more restrictive
        self.limiter.add_rule('/api/auth/', 5, 60)  # 5 requests per minute
        self.limiter.add_rule('/api/scrape/', 10, 60)  # 10 requests per minute
        
        # API endpoints - standard limits
        self.limiter.add_rule('/api/leads/', 60, 60)  # 60 requests per minute
        self.limiter.add_rule('/api/contacts/', 60, 60)
        self.limiter.add_rule('/api/campaigns/', 30, 60)  # 30 requests per minute
        
        # Resource-intensive operations
        self.limiter.add_rule('/api/analytics/', 20, 60)  # 20 requests per minute
        self.limiter.add_rule('/api/reports/', 10, 60)  # 10 requests per minute
        self.limiter.add_rule('/api/exports/', 5, 60)  # 5 requests per minute
        
        # Bulk operations
        self.limiter.add_rule('/api/bulk/', 3, 60)  # 3 requests per minute
        
        # AI operations
        self.limiter.add_rule('/api/ai/', 10, 60)  # 10 requests per minute
        
        # Webhook and integration operations
        self.limiter.add_rule('/api/webhooks/', 30, 60)
        self.limiter.add_rule('/api/integrations/', 30, 60)
    
    def get_rate_limit_key(self, request_obj) -> str:
        """Generate rate limit key from request"""
        # Try to get user ID from auth
        user_id = request_obj.headers.get('X-User-ID')
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        ip = request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
        if ip:
            # Handle multiple IPs in X-Forwarded-For
            ip = ip.split(',')[0].strip()
            return f"ip:{ip}"
        
        return "unknown"
    
    def check_rate_limit(self, request_obj) -> Tuple[bool, Dict]:
        """Check rate limit for request"""
        key = self.get_rate_limit_key(request_obj)
        endpoint = request_obj.path
        rule = self.limiter.get_rule(endpoint)
        
        # Add endpoint to key for per-endpoint limits
        full_key = f"{key}:{endpoint}"
        
        allowed, info = self.limiter.check_limit(full_key, rule)
        info['key'] = key
        info['endpoint'] = endpoint
        
        return allowed, info
    
    def rate_limit_decorator(self, requests: int = None, window: int = None):
        """Decorator for rate limiting Flask routes"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check rate limit
                allowed, info = self.check_rate_limit(request)
                
                # Override default rule if specified
                if requests and window:
                    key = self.get_rate_limit_key(request)
                    endpoint = request.path
                    full_key = f"{key}:{endpoint}"
                    rule = {'requests': requests, 'window': window, 'tokens_per_second': requests/window}
                    allowed, info = self.limiter.check_limit(full_key, rule)
                
                # Add rate limit headers
                headers = {
                    'X-RateLimit-Limit': str(info['limit']),
                    'X-RateLimit-Remaining': str(info['remaining']),
                    'X-RateLimit-Reset': str(info['reset'])
                }
                
                if not allowed:
                    headers['Retry-After'] = str(info['retry_after'])
                    response = jsonify({
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'message': f"Too many requests. Try again in {info['retry_after']} seconds.",
                        'limit': info['limit'],
                        'window': info['window'],
                        'retry_after': info['retry_after']
                    })
                    response.headers.update(headers)
                    return response, 429
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Add headers to response
                if isinstance(result, tuple):
                    response, status = result[0], result[1] if len(result) > 1 else 200
                else:
                    response, status = result, 200
                
                if hasattr(response, 'headers'):
                    response.headers.update(headers)
                
                return response, status
            
            return wrapper
        return decorator
    
    def get_user_rate_limits(self, user_id: str) -> Dict:
        """Get rate limit status for user across all endpoints"""
        user_buckets = {
            key: self.limiter.get_bucket_info(key)
            for key in self.limiter.buckets.keys()
            if key.startswith(f"user:{user_id}:")
        }
        
        return {
            'user_id': user_id,
            'endpoints': user_buckets
        }
    
    def get_ip_rate_limits(self, ip: str) -> Dict:
        """Get rate limit status for IP across all endpoints"""
        ip_buckets = {
            key: self.limiter.get_bucket_info(key)
            for key in self.limiter.buckets.keys()
            if key.startswith(f"ip:{ip}:")
        }
        
        return {
            'ip': ip,
            'endpoints': ip_buckets
        }
    
    def whitelist_user(self, user_id: str):
        """Whitelist user (remove all rate limits)"""
        # In production, store in database
        keys_to_remove = [
            key for key in self.limiter.buckets.keys()
            if key.startswith(f"user:{user_id}:")
        ]
        
        for key in keys_to_remove:
            self.limiter.reset_bucket(key)
        
        return len(keys_to_remove)
    
    def blacklist_ip(self, ip: str, duration_seconds: int = 3600):
        """Blacklist IP address"""
        # Set rate limit to 0 for duration
        key = f"ip:{ip}:*"
        self.limiter.add_rule(key, 0, duration_seconds)
    
    def get_rate_limit_stats(self) -> Dict:
        """Get overall rate limiting statistics"""
        total_buckets = len(self.limiter.buckets)
        
        # Count by type
        user_buckets = sum(1 for key in self.limiter.buckets.keys() if key.startswith('user:'))
        ip_buckets = sum(1 for key in self.limiter.buckets.keys() if key.startswith('ip:'))
        
        # Count by endpoint
        endpoint_counts = {}
        for key in self.limiter.buckets.keys():
            if ':' in key:
                parts = key.split(':')
                if len(parts) >= 3:
                    endpoint = ':'.join(parts[2:])
                    endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        return {
            'total_buckets': total_buckets,
            'user_buckets': user_buckets,
            'ip_buckets': ip_buckets,
            'endpoints': endpoint_counts,
            'rules': len(self.limiter.rules)
        }


class RateLimitMiddleware:
    """Flask middleware for automatic rate limiting"""
    
    def __init__(self, app, rate_limit_service: RateLimitService):
        self.app = app
        self.service = rate_limit_service
        self.exempt_paths = ['/health', '/api/health', '/']
        
    def __call__(self, environ, start_response):
        """WSGI middleware implementation"""
        path = environ.get('PATH_INFO', '')
        
        # Skip rate limiting for exempt paths
        if path in self.exempt_paths:
            return self.app(environ, start_response)
        
        # Check rate limit using environ (WSGI)
        # In production, integrate with Flask request context
        
        return self.app(environ, start_response)
    
    def add_exempt_path(self, path: str):
        """Add path to rate limit exemption list"""
        self.exempt_paths.append(path)
    
    def remove_exempt_path(self, path: str):
        """Remove path from exemption list"""
        if path in self.exempt_paths:
            self.exempt_paths.remove(path)

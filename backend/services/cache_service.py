"""
LLM Response Cache Service
Caches LLM responses to avoid redundant API calls and improve performance
"""
import hashlib
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """In-memory cache for LLM responses with TTL support"""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache service
        
        Args:
            ttl_seconds: Time to live for cached items (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        logger.info(f"✅ Cache service initialized with TTL: {ttl_seconds}s")
    
    def _generate_key(self, prompt: str, context: str = "", model: str = "") -> str:
        """
        Generate cache key from prompt, context, and model
        
        Args:
            prompt: User question/prompt
            context: Document context
            model: Model name
            
        Returns:
            Hash string as cache key
        """
        combined = f"{prompt}|{context}|{model}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, prompt: str, context: str = "", model: str = "") -> Optional[str]:
        """
        Get cached response
        
        Args:
            prompt: User question/prompt
            context: Document context
            model: Model name
            
        Returns:
            Cached response or None if not found/expired
        """
        key = self._generate_key(prompt, context, model)
        
        if key in self._cache:
            cached_item = self._cache[key]
            
            # Check if expired
            if time.time() < cached_item['expires_at']:
                self.hits += 1
                logger.info(f"🎯 Cache HIT (hits: {self.hits}, misses: {self.misses})")
                return cached_item['response']
            else:
                # Remove expired item
                del self._cache[key]
                logger.debug(f"🗑️ Removed expired cache entry")
        
        self.misses += 1
        logger.info(f"❌ Cache MISS (hits: {self.hits}, misses: {self.misses})")
        return None
    
    def set(self, prompt: str, response: str, context: str = "", model: str = ""):
        """
        Store response in cache
        
        Args:
            prompt: User question/prompt
            response: LLM response to cache
            context: Document context
            model: Model name
        """
        key = self._generate_key(prompt, context, model)
        
        self._cache[key] = {
            'response': response,
            'created_at': time.time(),
            'expires_at': time.time() + self.ttl_seconds,
            'prompt': prompt[:100],  # Store first 100 chars for debugging
        }
        
        logger.info(f"💾 Cached response (key: {key[:12]}..., total cached: {len(self._cache)})")
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"🧹 Cache cleared ({count} entries removed)")
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if current_time >= item['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"🗑️ Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_cached': len(self._cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'ttl_seconds': self.ttl_seconds
        }


# Global cache instance
llm_cache = CacheService(ttl_seconds=3600)  # 1 hour TTL

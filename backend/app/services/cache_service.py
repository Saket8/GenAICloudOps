import json
import asyncio
import logging
import os
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import hashlib
import redis
from redis.exceptions import ConnectionError, TimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Centralized caching service with Redis backend and File-Based fallback mechanisms"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_dir = os.path.join(os.getcwd(), '.cache')
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "redis_available": False,
            "file_cache_available": False
        }
        
        # Cache configuration
        self.default_ttl = 300  # 5 minutes
        self.max_local_cache_size = 1000
        
        self._initialize_fs_cache()
        self._initialize_redis()
    
    def _initialize_fs_cache(self):
        """Initialize filesystem cache directory"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            self.cache_stats["file_cache_available"] = True
        except Exception as e:
            logger.warning(f"Failed to create cache directory: {e}")
            self.cache_stats["file_cache_available"] = False

    def _initialize_redis(self):
        """Initialize Redis connection with proper error handling"""
        if not settings.REDIS_ENABLED:
            logger.info("Redis caching disabled via configuration")
            return
            
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=0.5,  # Reduced from 5s to prevent blocking
                socket_connect_timeout=0.5,  # Reduced from 5s to prevent blocking
                retry_on_timeout=False,  # Don't retry during startup
                health_check_interval=30
            )
            
            # Test connection removed for lazy loading
            # self.redis_client.ping()
            self.cache_stats["redis_available"] = True
            logger.info("✅ Centralized cache service initialized with Redis (lazy)")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using local/file cache: {e}")
            self.redis_client = None
            self.cache_stats["redis_available"] = False
    
    def _generate_cache_key(self, namespace: str, key: str, params: Optional[Dict] = None) -> str:
        """Generate a standardized cache key"""
        key_parts = [namespace, key]
        
        if params:
            # Sort params for consistent key generation
            sorted_params = sorted(params.items())
            params_str = json.dumps(sorted_params, default=str, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            key_parts.append(params_hash)
        
        return ":".join(key_parts)
    
    def _get_file_path(self, cache_key: str) -> str:
        """Generate safe file path for a cache key"""
        # Hash the key to avoid invalid filename characters
        safe_filename = hashlib.md5(cache_key.encode()).hexdigest() + ".pickle"
        return os.path.join(self.cache_dir, safe_filename)

    async def get(self, namespace: str, key: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached data with fallback mechanisms (Redis -> Memory -> File)"""
        cache_key = self._generate_cache_key(namespace, key, params)
        
        try:
            # 1. Try Redis first
            if self.redis_client:
                try:
                    data = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.get, cache_key
                    )
                    if data:
                        self.cache_stats["hits"] += 1
                        return json.loads(data)
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis get failed: {e}")
            
            # 2. Try Memory Cache
            if cache_key in self.local_cache:
                entry = self.local_cache[cache_key]
                if entry["expires_at"] > datetime.now():
                    self.cache_stats["hits"] += 1
                    return entry["data"]
                else:
                    # Expired entry
                    del self.local_cache[cache_key]
            
            # 3. Try File Cache (Persistence)
            file_path = self._get_file_path(cache_key)
            if os.path.exists(file_path):
                try:
                    # Simple lock for file read to prevent race conditions if multiple async tasks try to read/delete
                    async with asyncio.Lock(): 
                         data = await asyncio.to_thread(self._read_pickle, file_path)
                         
                    if data and data["expires_at"] > datetime.now():
                        # Populate memory cache for next time
                        self.local_cache[cache_key] = data
                        self.cache_stats["hits"] += 1
                        return data["data"]
                    elif data:
                        # Expired file, remove it
                        await asyncio.to_thread(os.remove, file_path)
                except Exception as e:
                    logger.warning(f"File cache read error: {e}")

            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return None
    
    def _read_pickle(self, path: str):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def _write_pickle(self, path: str, data: Any):
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    async def set(self, namespace: str, key: str, data: Any, ttl: Optional[int] = None, params: Optional[Dict] = None):
        """Set cached data (Redis + Memory + File)"""
        cache_key = self._generate_cache_key(namespace, key, params)
        ttl = ttl or self.default_ttl
        
        try:
            serialized_data = json.dumps(data, default=str)
            expiration = datetime.now() + timedelta(seconds=ttl)
            
            # 1. Set Redis
            if self.redis_client:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.setex, cache_key, ttl, serialized_data
                    )
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis set failed: {e}")
            
            # 2. Set Memory
            cache_entry = {
                "data": data,
                "expires_at": expiration,
                "created_at": datetime.now()
            }
            self._set_local_cache(cache_key, cache_entry)
            
            # 3. Set File
            file_path = self._get_file_path(cache_key)
            try:
                await asyncio.to_thread(self._write_pickle, file_path, cache_entry)
            except Exception as e:
                logger.warning(f"File cache write failed: {e}")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1
    
    def _set_local_cache(self, cache_key: str, entry: Dict[str, Any]):
        """Set data in local cache with size management"""
        # Clean up expired entries and manage size
        if len(self.local_cache) >= self.max_local_cache_size:
            self._cleanup_local_cache()
        
        self.local_cache[cache_key] = entry
    
    def _cleanup_local_cache(self):
        """Clean up expired entries and enforce size limits"""
        now = datetime.now()
        expired = [k for k, v in self.local_cache.items() if v["expires_at"] <= now]
        for k in expired: del self.local_cache[k]
        
        # If still too large, remove oldest entries
        if len(self.local_cache) >= self.max_local_cache_size:
            sorted_entries = sorted(self.local_cache.items(), key=lambda x: x[1]["created_at"])
            to_remove = len(sorted_entries) - self.max_local_cache_size + 100 # Remove a batch
            for i in range(to_remove):
                if i < len(sorted_entries):
                    del self.local_cache[sorted_entries[i][0]]
    
    async def delete(self, namespace: str, key: str, params: Optional[Dict] = None):
        """Delete cached data"""
        cache_key = self._generate_cache_key(namespace, key, params)
        
        try:
            # Delete from Redis
            if self.redis_client:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.delete, cache_key
                    )
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis delete failed: {e}")
            
            # Delete from local cache
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
            
            # Delete from file cache
            file_path = self._get_file_path(cache_key)
            if os.path.exists(file_path):
                await asyncio.to_thread(os.remove, file_path)
                
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def clear_namespace(self, namespace: str):
        """Clear all cache entries for a namespace (Best effort for file/memory)"""
        try:
            # Clear from Redis
            if self.redis_client:
                try:
                    pattern = f"{namespace}:*"
                    keys = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.keys, pattern
                    )
                    if keys:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.redis_client.delete, *keys
                        )
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis namespace clear failed: {e}")
            
            # Clear from local cache
            keys_to_delete_local = [
                key for key in self.local_cache.keys()
                if key.startswith(f"{namespace}:")
            ]
            for key in keys_to_delete_local:
                del self.local_cache[key]
            
            # Clear from file cache (best effort, requires scanning files)
            # For simplicity and performance, we won't scan all files for namespace prefix.
            # Individual deletes are handled by _get_file_path hashing.
            # A full namespace clear for file cache would involve iterating through the cache_dir
            # and checking the original cache_key (if stored) or re-generating it.
            # For now, we rely on individual deletes and TTL for file cache cleanup.
                
        except Exception as e:
            logger.error(f"Cache namespace clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "local_cache_size": len(self.local_cache),
            "total_requests": total_requests
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache system"""
        health_status = {
            "redis_available": False,
            "local_cache_available": True, # Memory cache is always available
            "file_cache_available": self.cache_stats["file_cache_available"],
            "redis_latency_ms": None,
            "status": "unhealthy"
        }
        
        # Test Redis
        if self.redis_client:
            try:
                start_time = datetime.now()
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.ping
                )
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                health_status["redis_available"] = True
                health_status["redis_latency_ms"] = round(latency, 2)
                
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
        
        # Overall status
        if health_status["redis_available"] or health_status["local_cache_available"] or health_status["file_cache_available"]:
            health_status["status"] = "healthy"
        
        return health_status

# Global cache service instance
cache_service = CacheService()
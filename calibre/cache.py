import json
import os
import time
import asyncio
from typing import Any, Optional, Callable
from functools import wraps

class PersistentCache:
    def __init__(
        self, 
        cache_file: str = 'app_cache.json',
        max_size: int = 100, 
        default_ttl: int = 3600
    ):
        self._cache_file = cache_file
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache = {}
        self._lock = asyncio.Lock()
        self._load_cache()

    def _load_cache(self):
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    loaded_cache = json.load(f)
                    current_time = time.time()
                    self._cache = {
                        k: v for k, v in loaded_cache.items() 
                        if v['expires_at'] > current_time
                    }
            else:
                self._cache = {}
        except (json.JSONDecodeError, IOError):
            self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            print(f"Cache save error: {e}")

    async def init(self, prefix: str = ""):
        """Metodo compatibile con FastAPICache"""
        pass

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            self._cleanup()
            entry = self._cache.get(key)
            
            if entry and entry['expires_at'] > time.time():
                return entry['value']
            
            if entry:
                del self._cache[key]
                self._save_cache()
            
            return None

    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> None:
        async with self._lock:
            self._cleanup()

            if len(self._cache) >= self._max_size:
                oldest_key = min(
                    self._cache, 
                    key=lambda k: self._cache[k]['timestamp']
                )
                del self._cache[oldest_key]

            ttl = expire or self._default_ttl
            current_time = time.time()
            
            self._cache[key] = {
                'value': value,
                'timestamp': current_time,
                'expires_at': current_time + ttl
            }

            self._save_cache()

    def _cleanup(self):
        current_time = time.time()
        expired_keys = [
            k for k, v in self._cache.items() 
            if v['expires_at'] <= current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self._save_cache()

    async def clear(self, key: Optional[str] = None):
        async with self._lock:
            if key:
                if key in self._cache:
                    del self._cache[key]
            else:
                self._cache.clear()
            
            self._save_cache()

class FastAPICache:
    _instance = None

    @classmethod
    async def init(cls, backend, prefix=""):
        if not cls._instance:
            cls._instance = backend
            await cls._instance.init(prefix)
        return cls._instance

    @classmethod
    async def clear(cls, key: Optional[str] = None):
        if cls._instance:
            await cls._instance.clear(key)

def cache(expire: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{json.dumps(args)}_{json.dumps(kwargs)}"
            cache_instance = FastAPICache._instance

            # Recupera dalla cache se presente
            cached_result = await cache_instance.get(key)
            if cached_result is not None:
                return cached_result

            # Calcola risultato
            result = await func(*args, **kwargs)

            # Salva in cache
            await cache_instance.set(key, result, expire)
            return result
        return wrapper
    return decorator
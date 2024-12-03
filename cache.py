from typing import Optional, Any
import aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

class CacheManager:
    """
    Gestore centralizzato per caching con Redis
    """
    
    @classmethod
    async def init_cache(cls, redis_url: str = "redis://localhost:6379/0"):
        """
        Inizializza la cache Redis globale per l'applicazione
        
        Args:
            redis_url (str): URL di connessione a Redis
        """
        redis = aioredis.from_url(
            redis_url, 
            encoding="utf8", 
            decode_responses=True
        )
        FastAPICache.init(RedisBackend(redis), prefix="calibre_cache")

    @classmethod
    @cache(expire=3600)  # Cache di default 1 ora
    async def cached_query(
        cls, 
        key: str, 
        query_func: callable, 
        *args, 
        expire: int = 3600, 
        **kwargs
    ) -> Optional[Any]:
        """
        Esegue una funzione con caching Redis.
        """
        try:
            result = await query_func(*args, **kwargs)
            print(f"Result from query_func: {result}")  # Debug output
            return result
        except Exception as e:
            print(f"Errore in cached_query: {e}")
            return None
    
    
        @classmethod
        async def invalidate_cache(cls, key: str):
            """
            Invalida una specifica chiave in cache
            
            Args:
                key (str): Chiave da rimuovere
            """
            await FastAPICache.clear(key)

    @classmethod
    async def clear_all_cache(cls):
        """
        Cancella completamente la cache
        """
        await FastAPICache.clear()

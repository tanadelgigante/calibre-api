import json
import os
import time
import asyncio
from typing import Any, Optional
from functools import wraps

class PersistentCache:
    def __init__(
        self, 
        cache_file: str = 'app_cache.json',
        max_size: int = 100, 
        default_ttl: int = 3600
    ):
        """
        Inizializza la cache persistente.
        
        Args:
            cache_file (str): Il percorso del file di cache.
            max_size (int): La dimensione massima della cache.
            default_ttl (int): Il tempo di vita predefinito per gli elementi della cache.
        """
        self._cache_file = cache_file
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache = {}
        self._lock = asyncio.Lock()
        print(f"[INFO] Inizializzazione della cache con file: {self._cache_file}")
        self._load_cache()

    def _load_cache(self):
        """
        Carica la cache dal file se esiste, altrimenti inizializza una cache vuota.
        """
        try:
            if os.path.exists(self._cache_file):
                print(f"[INFO] Caricamento della cache dal file: {self._cache_file}")
                with open(self._cache_file, 'r') as f:
                    loaded_cache = json.load(f)
                    current_time = time.time()
                    self._cache = {
                        k: v for k, v in loaded_cache.items() 
                        if v['expires_at'] > current_time
                    }
            else:
                print(f"[INFO] File di cache non trovato. Inizializzazione di una nuova cache.")
                self._cache = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Errore durante il caricamento della cache: {e}")
            self._cache = {}

    def _save_cache(self):
        """
        Salva la cache corrente nel file.
        """
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
            print(f"[INFO] Cache salvata con successo nel file: {self._cache_file}")
        except IOError as e:
            print(f"[ERROR] Errore nel salvataggio della cache: {e}")

    async def init(self, prefix: str = ""):
        """Metodo compatibile con FastAPICache (non utilizzato)."""
        pass

    async def get(self, key: str) -> Optional[Any]:
        """
        Recupera un valore dalla cache.
        
        Args:
            key (str): La chiave dell'elemento della cache.
        
        Returns:
            Optional[Any]: Il valore della cache se presente e non scaduto, altrimenti None.
        """
        async with self._lock:
            self._cleanup()
            entry = self._cache.get(key)
            if entry and entry['expires_at'] > time.time():
                print(f"[INFO] Elemento cache trovato per chiave: {key}")
                return entry['value']
            if entry:
                print(f"[INFO] Elemento cache scaduto per chiave: {key}")
                del self._cache[key]
                self._save_cache()
            print(f"[INFO] Nessun elemento cache trovato per chiave: {key}")
            return None

    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> None:
        """
        Aggiunge un elemento alla cache.
        
        Args:
            key (str): La chiave dell'elemento della cache.
            value (Any): Il valore da memorizzare nella cache.
            expire (Optional[int]): Tempo di vita in secondi (TTL) dell'elemento della cache. Usa il TTL predefinito se non specificato.
        """
        async with self._lock:
            self._cleanup()

            if len(self._cache) >= self._max_size:
                oldest_key = min(
                    self._cache, 
                    key=lambda k: self._cache[k]['timestamp']
                )
                print(f"[INFO] Rimozione dell'elemento cache più vecchio: {oldest_key}")
                del self._cache[oldest_key]

            ttl = expire or self._default_ttl
            current_time = time.time()
            
            self._cache[key] = {
                'value': value,
                'timestamp': current_time,
                'expires_at': current_time + ttl
            }

            print(f"[INFO] Elemento cache impostato per chiave: {key}")
            self._save_cache()

    def _cleanup(self):
        """
        Rimuove gli elementi scaduti dalla cache.
        """
        current_time = time.time()
        expired_keys = [
            k for k, v in self._cache.items() 
            if v['expires_at'] <= current_time
        ]
        
        for key in expired_keys:
            print(f"[INFO] Rimozione dell'elemento cache scaduto: {key}")
            del self._cache[key]
        
        if expired_keys:
            self._save_cache()

    async def clear(self, key: Optional[str] = None):
        """
        Cancella un elemento specifico o tutta la cache.
        
        Args:
            key (Optional[str]): La chiave dell'elemento da cancellare. Se None, cancella tutta la cache.
        """
        async with self._lock:
            if key:
                if key in self._cache:
                    print(f"[INFO] Cancellazione dell'elemento cache per chiave: {key}")
                    del self._cache[key]
            else:
                print(f"[INFO] Cancellazione di tutta la cache")
                self._cache.clear()
            
            self._save_cache()

class FastAPICache:
    _instance = None

    @classmethod
    async def init(cls, backend, prefix=""):
        """
        Inizializza l'istanza del backend della cache.
        
        Args:
            backend: Il backend della cache.
            prefix (str): Il prefisso per la cache.
        """
        if not cls._instance:
            cls._instance = backend
            await cls._instance.init(prefix)
            print(f"[INFO] FastAPICache inizializzata con backend: {backend}")
        return cls._instance

    @classmethod
    async def clear(cls, key: Optional[str] = None):
        """
        Cancella un elemento specifico o tutta la cache.
        
        Args:
            key (Optional[str]): La chiave dell'elemento da cancellare. Se None, cancella tutta la cache.
        """
        if cls._instance:
            print(f"[INFO] Cancellazione cache per chiave: {key}")
            await cls._instance.clear(key)

def cache(expire: int = 3600):
    """
    Decoratore per memorizzare il risultato di una funzione nella cache.
    
    Args:
        expire (int): Tempo di vita in secondi (TTL) dell'elemento della cache.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{json.dumps(args)}_{json.dumps(kwargs)}"
            cache_instance = FastAPICache._instance

            # Recupera dalla cache se presente
            cached_result = await cache_instance.get(key)
            if cached_result is not None:
                print(f"[INFO] Risultato cache recuperato per chiave: {key}")
                return cached_result

            # Calcola risultato
            result = await func(*args, **kwargs)

            # Salva in cache
            await cache_instance.set(key, result, expire)
            print(f"[INFO] Risultato cache salvato per chiave: {key}")
            return result
        return wrapper
    return decorator

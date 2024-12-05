# main.py
import os

from fastapi import FastAPI, Depends
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from datetime import datetime
from calibre.cache import PersistentCache, FastAPICache, cache
from calibre.database import CalibreDatabase
from calibre.models import LibraryStatsModel, BookModel, BookSearchParams
from calibre.security import TokenManager

# Configurazioni da variabili d'ambiente
CALIBRE_LIBRARY_PATH = os.getenv('CALIBRE_LIBRARY_PATH', '/calibre-library')

# Inizializzazione applicazione
app = FastAPI(
    title="Calibre Library API",
    description="API per gestione libreria Calibre con autenticazione token"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializzazione database Calibre
calibre_db = CalibreDatabase(CALIBRE_LIBRARY_PATH)


# Endpoint statistiche libreria con caching
@app.get("/statistics", response_model=LibraryStatsModel)
async def get_library_statistics(
    _: bool=Depends(TokenManager.validate_api_token)
):

    @cache(expire=3600)  # Cache per 1 ora
    async def fetch_stats():
        stats = calibre_db.get_database_stats()
        if not stats:
            raise HTTPException(status_code=500, detail="Failed to fetch library statistics")
        
        stats['last_updated'] = datetime.now()
        return stats

    return await fetch_stats()


# Endpoint ricerca libri
@app.get("/books/search", response_model=list[BookModel])
async def search_books(
    params: BookSearchParams=Depends(),
    _: bool=Depends(TokenManager.validate_api_token)
):
    """
    Ricerca libri con filtri multipli.
    Richiede token API valido.
    """

    @cache(expire=1800)  # Cache per 30 minuti
    async def search_function():
        return calibre_db.search_books(
            title=params.title,
            author=params.author,
            limit=params.limit
        )

    return await search_function()

    
# Endpoint swagger
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(token: str):
    if token == TokenManager.API_KEY:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Calibre Library API"
        )
    raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/redoc", include_in_schema=False)
async def custom_redoc(token: str):
    if token == TokenManager.API_KEY:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="Calibre Library API"
        )
    raise HTTPException(status_code=403, detail="Invalid token")


# Configurazione all'avvio dell'applicazione
@app.on_event("startup")
async def startup_event():
    os.makedirs('/app/cache', exist_ok=True)
    persistent_cache = PersistentCache(
        cache_file='/app/cache/calibre_cache.json',
        max_size=100,
        default_ttl=3600
    )
    await FastAPICache.init(persistent_cache, prefix="calibre_")
    TokenManager.init_token()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

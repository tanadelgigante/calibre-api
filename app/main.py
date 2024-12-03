# main.py
import os

from fastapi import FastAPI, Depends
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from app.cache import CacheManager
from app.database import CalibreDatabase
from app.models import LibraryStatsModel, BookModel, BookSearchParams
from app.security import TokenManager

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
    """
    Recupera statistiche complete della libreria Calibre.
    Richiede token API valido.
    """

    async def fetch_stats():
        return calibre_db.get_database_stats()

    return await CacheManager.cached_query(
        key="library_stats",
        query_func=fetch_stats,
        expire=3600  # Cache valida per 1 ora
    )


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

    async def search_function():
        return calibre_db.search_books(
            title=params.title,
            author=params.author,
            limit=params.limit
        )

    # Genera chiave di cache basata sui parametri
    cache_key = f"book_search_{params.title}_{params.author}_{params.limit}"
    
    return await CacheManager.cached_query(
        key=cache_key,
        query_func=search_function,
        expire=1800  # Cache valida per 30 minuti
    )

    
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
    await CacheManager.init_cache()
    TokenManager.init_token()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

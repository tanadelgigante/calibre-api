import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from app.database import CalibreDatabase
from app.models import LibraryStatsModel, BookModel, BookSearchParams
from app.security import SecurityManager
from app.cache import CacheManager

# Configurazioni da variabili d'ambiente
CALIBRE_LIBRARY_PATH = os.getenv('CALIBRE_LIBRARY_PATH', '/calibre-library')
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')

# Inizializzazione applicazione
app = FastAPI(
    title="Calibre Library API",
    description="API per gestione libreria Calibre con autenticazione e caching"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permettere origine specifiche in produzione
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializzazione database Calibre
calibre_db = CalibreDatabase(CALIBRE_LIBRARY_PATH)

# Rotte di autenticazione
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint per generazione token di autenticazione.
    In un'implementazione reale, verificare le credenziali contro un database utenti.
    """
    # Esempio di autenticazione (da sostituire con vera logica)
    if form_data.username == "admin" and form_data.password == "password":
        access_token = SecurityManager.create_access_token(
            {"sub": form_data.username}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Credenziali non valide")

# Endpoint statistiche libreria con caching
@app.get("/statistics", response_model=LibraryStatsModel)
async def get_library_statistics(
    username: str = Depends(SecurityManager.get_current_user)
):
    """
    Recupera statistiche complete della libreria Calibre.
    Richiede autenticazione e utilizza caching.
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
    params: BookSearchParams = Depends(),
    username: str = Depends(SecurityManager.get_current_user)
):
    """
    Ricerca libri con filtri multipli.
    Supporta ricerca per titolo, autore e numero massimo di risultati.
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

# Configurazione cache all'avvio dell'applicazione
@app.on_event("startup")
async def startup_event():
    await CacheManager.init_cache()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
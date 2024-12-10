from datetime import datetime
import os
import subprocess

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from database import CalibreDatabase
from models import LibraryStatsModel, BookModel, BookSearchParams
from security import TokenManager

# Configurazioni da variabili d'ambiente
CALIBRE_LIBRARY_PATH = os.getenv('CALIBRE_LIBRARY_PATH', '/calibre-library')
print(f"[INFO] CALIBRE_LIBRARY_PATH: {CALIBRE_LIBRARY_PATH}")

# Application information
APP_NAME = "Calibre API"
APP_VERSION = "1.0.0"
APP_AUTHOR = "@ilgigante77"
APP_WEBSITE = "http://example.com"

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
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

    @app.get("/calibre/stats", response_model=LibraryStatsModel)
    async def get_library_statistics(_: bool=Depends(TokenManager.validate_api_token)):
        """
        Endpoint per ottenere le statistiche della libreria.
        """
        print(f"[DEBUG] Richiesta per /statistics")

        async def fetch_stats():
            stats = calibre_db.get_database_stats()
            if not stats:
                raise HTTPException(status_code=500, detail="Failed to fetch library statistics")
            stats['last_updated'] = datetime.now()
            return stats

        return await fetch_stats()

    @app.get("/calibre/books/search", response_model=list[BookModel])
    async def search_books(
        params: BookSearchParams=Depends(),
        _: bool=Depends(TokenManager.validate_api_token)
    ):
        """
        Endpoint per la ricerca di libri.
        """
        print(f"[DEBUG] Richiesta per /books/search con parametri: {params}")

        async def search_function():
            return calibre_db.search_books(
                title=params.title,
                author=params.author,
                limit=params.limit
            )

        return await search_function()

    @app.get("/calibre/docs", include_in_schema=False)
    async def custom_swagger_ui(token: str):
        """
        Endpoint per la documentazione Swagger UI.
        """
        if token == TokenManager.API_KEY:
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title="Calibre Library API"
            )
        raise HTTPException(status_code=403, detail="Invalid token")

    @app.get("/calibre/redoc", include_in_schema=False)
    async def custom_redoc(token: str):
        """
        Endpoint per la documentazione ReDoc.
        """
        if token == TokenManager.API_KEY:
            return get_redoc_html(
                openapi_url="/openapi.json",
                title="Calibre Library API"
            )
        raise HTTPException(status_code=403, detail="Invalid token")

    @app.on_event("startup")
    async def startup_event():
        """
        Eventi da eseguire all'avvio dell'applicazione.
        """
        TokenManager.init_token()

    return app

def system_setup():
    """
    Esegue lo script di configurazione del sistema operativo necessario per il modulo.
    """
    script_path = os.path.join(os.path.dirname(__file__), 'setup.sh')
    if os.path.exists(script_path):
        print(f"[INFO] Esecuzione dello script di setup: {script_path}")
        subprocess.run(['bash', script_path], check=True)
    else:
        raise FileNotFoundError(f"Il file {script_path} non esiste.")

def register(flask_app):
    """
    Registra il modulo CalibreLibraryAPI come plug-in.
    """
    print(f"[INFO] Registrazione del modulo CalibreLibraryAPI come plug-in")
    system_setup()
    fastapi_app = create_app()
    
    @flask_app.route('/calibre/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    def proxy_to_fastapi(path):
        return fastapi_app.openapi()
    
    print("[INFO] Calibre endpoints mounted on Flask app")


# Per esecuzione stand-alone
if __name__ == "__main__":
    print(f"[INFO] Avvio dell'applicazione {APP_NAME}")
    print(f"[INFO] Versione: {APP_VERSION}")
    print(f"[INFO] Autore: {APP_AUTHOR}")
    print(f"[INFO] Sito web: {APP_WEBSITE}")
    app = create_app()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

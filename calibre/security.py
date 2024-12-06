from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
import os

class TokenManager:
    API_KEY = None

    @classmethod
    def init_token(cls):
        """
        Inizializza il token statico dall'ambiente.
        Deve essere chiamato all'avvio dell'applicazione.
        """
        print("[INFO] Inizializzazione del token API")
        cls.API_KEY = os.getenv('API_TOKEN', None)
        
        if not cls.API_KEY or len(cls.API_KEY) != 32:
            raise ValueError("API Token deve essere una stringa di 32 caratteri")
        print(f"[DEBUG] Token API inizializzato: {'***' if cls.API_KEY else 'None'}")

    @classmethod
    def validate_api_token(cls, 
        api_key_header: str = Security(APIKeyHeader(name="X-API-Token", auto_error=False)),
        api_key_query: str = Security(APIKeyQuery(name="api_token", auto_error=False))
    ):
        """
        Valida il token API passato nell'header o nella query string.
        """
        print(f"[DEBUG] Validazione del token API")
        
        if not cls.API_KEY:
            print(f"[ERROR] Token non configurato")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Token non configurato"
            )
        
        # Controlla se il token è nell'header o nella query string
        api_key = api_key_header or api_key_query
        
        print(f"[DEBUG] Token ricevuto: {'***' if api_key else 'None'}")
        
        if not api_key or api_key != cls.API_KEY:
            print(f"[ERROR] Token non valido: {'***' if api_key else 'None'}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Token non valido"
            )
        
        print(f"[INFO] Token validato con successo")
        return True

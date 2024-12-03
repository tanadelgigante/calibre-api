# security.py
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
        cls.API_KEY = os.getenv('API_TOKEN', None)
        
        if not cls.API_KEY or len(cls.API_KEY) != 32:
            raise ValueError("API Token deve essere una stringa di 32 caratteri")

    @classmethod
    def validate_api_token(cls, api_key: str = Security(APIKeyHeader(name="X-API-Token", auto_error=False)) | 
                                                 Security(APIKeyQuery(name="api_token", auto_error=False))):
        """
        Valida il token API passato nell'header o nella query string.
        """
        if not cls.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Token non configurato"
            )
        
        if not api_key or api_key != cls.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Token non valido"
            )
        
        return True
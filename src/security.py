import configparser
import os

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery


class TokenManager:
    API_KEY = None

    @classmethod
    def init_token(cls):
        """
        Inizializza il token statico dall'ambiente.
        Deve essere chiamato all'avvio dell'applicazione.
        """
        print("[INFO] Inizializzazione del token API")
        cls.API_KEY = load_property('API_TOKEN', None)

        if not cls.API_KEY:
            print(f"[ERROR] API Token deve essere valorizzato")
            raise ValueError("API Token deve essere valorizzato")
        print(f"[INFO] Token API inizializzato")

    @classmethod
    def validate_api_token(cls,
        api_key_header: str=Security(APIKeyHeader(name="X-API-Token", auto_error=False)),
        api_key_query: str=Security(APIKeyQuery(name="api_token", auto_error=False))
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


def load_property(prop_name, default=None):
    """
    Load a property with a two-step fallback strategy:
    1. Check environment variables
    2. Check configuration file

    Args:
        prop_name (str): Name of the property to load
        default (any, optional): Default value if property not found

    Returns:
        The value of the property or the default
    """
    # Step 1: Check configuration file
    try:
        config = configparser.ConfigParser()
        config.read('/config/calibre.conf')
        print(f"[DEBUG] Cerco token in file")
        # Look for the property in the 'calibre' section
        if 'calibre' in config.sections():
            file_value = config.get('calibre', prop_name.lower(), fallback=default)
            print(f"[DEBUG] Trovato token in file")
            return file_value
    except Exception as e:
        print(f"Error reading configuration file: {e}")

    # Step 2: Check environment variables (case-insensitive)
    env_value = os.getenv(prop_name.upper())
    if env_value is not None:
        print(f"[DEBUG] Trovato token in environment")
        return env_value

    # Return default if nothing found
    return default

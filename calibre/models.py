from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class UserCreate(BaseModel):
    """
    Modello per la creazione di un utente con campi obbligatori e validazione.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)

    @validator('email') 
    def validate_email(cls, v):
        """
        Validatore per l'email. Verifica se l'email contiene il simbolo '@'.
        """
        if '@' not in v:
            raise ValueError('Email non valida')
        return v


class UserResponse(BaseModel):
    """
    Modello per la risposta dell'utente con informazioni di base.
    """
    id: int
    username: str
    email: str
    created_at: datetime


class BookModel(BaseModel):
    """
    Modello per rappresentare un libro con dettagli opzionali.
    """
    id: int
    title: str
    author: str
    rating: Optional[float] = None
    published_date: Optional[datetime] = None


class LibraryStatsModel(BaseModel):
    """
    Modello per rappresentare le statistiche della libreria.
    """
    total_books: int = 0
    total_authors: int = 0
    total_publishers: int = 0
    last_updated: Optional[datetime] = None


class BookSearchParams(BaseModel):
    """
    Modello per i parametri di ricerca dei libri con validazione del limite.
    """
    title: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100

    @validator('limit')
    def validate_limit(cls, v):
        """
        Validatore per il limite dei risultati della ricerca.
        """
        if v < 1 or v > 1000:
            raise ValueError('Limite deve essere tra 1 e 1000')
        return v


class TokenModel(BaseModel):
    """
    Modello per rappresentare un token di accesso.
    """
    access_token: str
    token_type: str = "bearer"

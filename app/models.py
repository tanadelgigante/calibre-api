from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)

    @validator('email') 
    def validate_email(self, v):
        if '@' not in v:
            raise ValueError('Email non valida')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class BookModel(BaseModel):
    id: int
    title: str
    author: str
    rating: Optional[float] = None
    published_date: Optional[datetime] = None

class LibraryStatsModel(BaseModel):
    total_books: int
    read_books: int
    unread_books: int
    series_books: int
    last_updated: datetime = datetime.now()

class BookSearchParams(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100

    @validator('limit')
    def validate_limit(self, v):
        if v < 1 or v > 1000:
            raise ValueError('Limite deve essere tra 1 e 1000')
        return v

class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
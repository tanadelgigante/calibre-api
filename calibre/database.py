from typing import Optional, List, Dict
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

class DatabaseLockError(Exception):
    """Custom exception for database lock errors"""
    pass

class CalibreDatabase:
    def __init__(self, library_path: str):
        self.library_path = library_path
        self.db_path = os.path.join(library_path, "metadata.db")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Calibre Database not found in {self.db_path}")
        
        self.engine = create_engine(
            f'sqlite:///{self.db_path}', 
            connect_args={'check_same_thread': False}
        )


    def get_database_stats(self) -> Dict:
        try:
            with self.database_lock():
                with self.engine.connect() as connection:
                    stats_query = text("""
                        SELECT 
                            (SELECT COUNT(*) FROM books) as total_books,
                            (SELECT COUNT(*) FROM authors) as total_authors,
                            (SELECT COUNT(*) FROM publishers) as total_publishers
                    """)
                    
                    result = connection.execute(stats_query).first()
                    return {
                        'total_books': result['total_books'],
                        'total_authors': result['total_authors'],
                        'total_publishers': result['total_publishers']
                    }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def search_books(
        self, 
        title: Optional[str] = None, 
        author: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict]:
        try:
            with self.database_lock():
                with self.engine.connect() as connection:
                    query = text("""
                        SELECT 
                            books.id, 
                            books.title, 
                            authors.name as author
                        FROM books
                        JOIN books_authors_link ON books.id = books_authors_link.book
                        JOIN authors ON books_authors_link.author = authors.id
                        WHERE 1=1
                        {title_filter}
                        {author_filter}
                        LIMIT :limit
                    """)

                    filters = {
                        'title_filter': 'AND books.title LIKE :title' if title else '',
                        'author_filter': 'AND authors.name LIKE :author' if author else ''
                    }

                    params = {
                        'limit': limit,
                        'title': f'%{title}%' if title else None,
                        'author': f'%{author}%' if author else None
                    }

                    query = text(query.text.format(**filters))
                    result = connection.execute(query, params)
                    
                    return [dict(row) for row in result]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database search error: {str(e)}")
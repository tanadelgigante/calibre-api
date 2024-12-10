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
        """
        Initializes the CalibreDatabase instance.
        Args:
            library_path (str): The path to the Calibre library.
        """
        self.library_path = library_path
        self.db_path = os.path.join(library_path, "metadata.db")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Calibre Database not found in {self.db_path}")
        print(f"[INFO] Calibre Database found at {self.db_path}")
        
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            connect_args={'check_same_thread': False}
        )

    def get_database_stats(self) -> Dict:
        """
        Retrieves statistics from the Calibre database.
        Returns:
            Dict: A dictionary with the total counts of books, authors, and publishers.
        """
        try:
            with self.engine.connect() as connection:
                stats_query = text("""
                    SELECT 
                        (SELECT COUNT(*) FROM books) as total_books,
                        (SELECT COUNT(*) FROM authors) as total_authors,
                        (SELECT COUNT(*) FROM publishers) as total_publishers
                """)
                result = connection.execute(stats_query).first()
                print(f"[DEBUG] Database stats retrieved: {result}")
                return {
                    'total_books': result[0],
                    'total_authors': result[1],
                    'total_publishers': result[2]
                }
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def search_books(
            self, 
            title: Optional[str] = None, 
            author: Optional[str] = None, 
            limit: int = 100
        ) -> List[Dict]:
            try:
                with self.engine.connect() as connection:
                    title_filter = "AND books.title LIKE :title" if title else ""
                    author_filter = "AND authors.name LIKE :author" if author else ""
                    query = text(f"""
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
    
                    params = {
                        'limit': limit,
                        'title': f'%{title}%' if title else None,
                        'author': f'%{author}%' if author else None
                    }
    
                    print(f"[DEBUG] Parametri della query SQL: {params}")
                    result = connection.execute(query, params)
                    # Usa l'API di SQLAlchemy per ottenere i risultati come dizionari
                    books = [dict(row._mapping) for row in result]
                    print(f"[DEBUG] Risultati trovati: {books}")
                    return books
            except SQLAlchemyError as e:
                raise HTTPException(status_code=500, detail=f"Database search error: {str(e)}")

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
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    def get_extended_stats(self) -> Dict:
        """
        Retrieves extended statistics from the Calibre database.
        """
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT
                        (SELECT COUNT(*) FROM books) as total_books,
                        (SELECT COUNT(*) FROM tags) as tags_count,
                        (SELECT COUNT(*) FROM series) as series_count,
                        (SELECT COUNT(*) FROM authors) as total_authors,
                        (SELECT COUNT(*) FROM publishers) as total_publishers,
                        (SELECT AVG(rating) FROM books) as avg_rating
                """)
                result = connection.execute(query).first()
                lang_query = text("SELECT DISTINCT lang_code FROM languages")
                langs = [r[0] for r in connection.execute(lang_query).fetchall()]
                
                return {
                    'total_books': result[0],
                    'tags_count': result[1],
                    'series_count': result[2],
                    'total_authors': result[3],
                    'total_publishers': result[4],
                    'avg_rating': float(result[5]) if result[5] else 0.0,
                    'languages': langs
                }
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

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

    def get_books_by_series(self, series_name: str) -> List[Dict]:
        """
        Retrieves books belonging to a specific series.
        """
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT b.id, b.title, b.author
                    FROM books b
                    JOIN books_series_link bsl ON b.id = bsl.book
                    JOIN series s ON bsl.series = s.id
                    WHERE s.name = :series_name
                """)
                result = connection.execute(query, {"series_name": series_name}).fetchall()
                return [{'id': r[0], 'title': r[1], 'author': r[2]} for r in result]
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    def get_books_by_language(self, lang_code: str) -> List[Dict]:
        """
        Retrieves books belonging to a specific language.
        """
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT b.id, b.title, b.author
                    FROM books b
                    JOIN books_languages_link bll ON b.id = bll.book
                    JOIN languages l ON bll.lang_code = l.id
                    WHERE l.lang_code = :lang_code
                """)
                result = connection.execute(query, {"lang_code": lang_code}).fetchall()
                return [{'id': r[0], 'title': r[1], 'author': r[2]} for r in result]
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    def get_rating_distribution(self) -> Dict:
        """
        Retrieves rating distribution from the Calibre database.
        """
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT rating, COUNT(*) as count
                    FROM books
                    WHERE rating IS NOT NULL
                    GROUP BY rating
                    ORDER BY rating
                """)
                result = connection.execute(query).fetchall()
                return {str(r[0]): r[1] for r in result}
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    def update_book_metadata(self, book_id: int, fields: Dict) -> bool:
        """
        Updates book metadata in the Calibre database.
        """
        try:
            with self.engine.connect() as connection:
                set_clause = ", ".join([f"{k} = :{k}" for k in fields.keys()])
                query = text(f"UPDATE books SET {set_clause} WHERE id = :id")
                params = fields.copy()
                params["id"] = book_id
                connection.execute(query, params)
                connection.commit()
                return True
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    def delete_book(self, book_id: int) -> bool:
        """
        Deletes a book from the Calibre database.
        """
        try:
            with self.engine.connect() as connection:
                query = text("DELETE FROM books WHERE id = :id")
                connection.execute(query, {"id": book_id})
                connection.commit()
                return True
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")

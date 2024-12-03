from typing import Optional, List, Dict
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException 

import os 
import fcntl 

class DatabaseLockError(Exception):
    """Eccezione personalizzata per errori di lock del database"""
    pass

class CalibreDatabase:
    def __init__(self, library_path: str):
        """
        Inizializza la connessione al database Calibre.
        
        Args:
            library_path (str): Percorso della libreria Calibre
        """
        self.library_path = library_path
        self.db_path = os.path.join(library_path, "metadata.db")
        self.lock_path = os.path.join(library_path, ".calibre.lock")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database Calibre non trovato in {self.db_path}")
        
        # Configurazione motore SQLAlchemy
        self.engine = create_engine(
            f'sqlite:///{self.db_path}', 
            connect_args={'check_same_thread': False}
        )
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        """
        Contesto per gestire sessioni database in modo sicuro.
        Gestisce automaticamente commit e rollback.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    def acquire_lock(self, blocking: bool = True) -> bool:
        """
        Acquisisce un lock esclusivo sul file del database.
        
        Args:
            blocking (bool): Se True, attende fino ad acquisizione lock
        
        Returns:
            bool: True se lock acquisito, False altrimenti
        """
        try:
            self.lock_file = open(self.lock_path, 'w')
            
            # Modalità di lock configurabile
            lock_type = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
            fcntl.flock(self.lock_file.fileno(), lock_type)
            
            return True
        except (IOError, BlockingIOError):
            return False

    def release_lock(self):
        """Rilascia il lock sul database"""
        try:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            os.unlink(self.lock_path)
        except Exception:
            pass

    def get_database_stats(self) -> Dict:
        """
        Recupera statistiche complete del database.
        """
        try:
            with self.session_scope() as session:
                stats_query = text("""
                    SELECT 
                        (SELECT COUNT(*) FROM books) as total_books,
                        (SELECT COUNT(*) FROM books WHERE rating > 0) as read_books,
                        (SELECT COUNT(*) FROM books WHERE rating = 0) as unread_books,
                        (SELECT COUNT(DISTINCT series) FROM books WHERE series IS NOT NULL) as series_books
                """)
                
                result = session.execute(stats_query).first()
                print("Database stats query result:", result)  # Debug output
                
                # Restituzione dei dati con valori di default se mancanti
                return {
                    'total_books': result['total_books'] if result and 'total_books' in result else 0,
                    'read_books': result['read_books'] if result and 'read_books' in result else 0,
                    'unread_books': result['unread_books'] if result and 'unread_books' in result else 0,
                    'series_books': result['series_books'] if result and 'series_books' in result else 0,
                }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")


    def search_books(
        self, 
        title: Optional[str] = None, 
        author: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Ricerca libri con filtri multipli.
        
        Args:
            title (str, optional): Filtro per titolo
            author (str, optional): Filtro per autore
            limit (int): Numero massimo di risultati
        
        Returns:
            List[Dict]: Lista di libri corrispondenti
        """
        with self.session_scope() as session:
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

            # Costruzione dinamica dei filtri
            filters = {
                'title_filter': 'AND books.title LIKE :title' if title else '',
                'author_filter': 'AND authors.name LIKE :author' if author else ''
            }

            # Preparazione dei parametri
            params = {
                'limit': limit,
                'title': f'%{title}%' if title else None,
                'author': f'%{author}%' if author else None
            }

            query = text(query.text.format(**filters))
            result = session.execute(query, params)
            
            return [dict(row) for row in result]
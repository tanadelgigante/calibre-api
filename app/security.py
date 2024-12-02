from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

# Configurazioni di sicurezza
SECRET_KEY = "your-secret-key"  # Dovrebbe essere un segreto sicuro caricato da variabili ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class TokenData(BaseModel):
    username: Optional[str] = None

class SecurityManager:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica la corrispondenza tra password in chiaro e hash.
        
        Args:
            plain_password (str): Password in formato testo
            hashed_password (str): Password hashata da confrontare
        
        Returns:
            bool: True se le password corrispondono
        """
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        """
        Genera hash sicuro della password.
        
        Args:
            password (str): Password in formato testo
        
        Returns:
            str: Password hashata
        """
        return cls.pwd_context.hash(password)

    @classmethod
    def create_access_token(
        cls, 
        data: Dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Genera token di accesso JWT.
        
        Args:
            data (Dict): Payload del token
            expires_delta (Optional[timedelta]): Tempo di scadenza token
        
        Returns:
            str: Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt

    @classmethod
    def decode_token(cls, token: str) -> TokenData:
        """
        Decodifica e valida un token JWT.
        
        Args:
            token (str): Token JWT da decodificare
        
        Returns:
            TokenData: Dati estratti dal token
        
        Raises:
            HTTPException: Se token non è valido
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token non valido"
                )
            
            return TokenData(username=username)
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Impossibile validare le credenziali"
            )

    @classmethod
    def get_current_user(cls, token: str = Depends(oauth2_scheme)) -> str:
        """
        Ottiene l'utente corrente dal token JWT.
        
        Args:
            token (str): Token JWT
        
        Returns:
            str: Username dell'utente
        """
        token_data = cls.decode_token(token)
        return token_data.username

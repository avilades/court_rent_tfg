from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from . import crud, models, schemas, database
from .database import get_db
from typing import Optional

# --- Constantes de Configuración ---
# ¡En una aplicación de producción real, estas claves deben estar en variables de entorno!
SECRET_KEY = "supersecretkey" # CAMBIAR PARA PRODUCCIÓN
ALGORITHM = "HS256"           # Algoritmo de cifrado para el token JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Tiempo de vida del token (30 minutos)

# OAuth2PasswordBearer es una clase que le indica a FastAPI 
# que el cliente enviará un token en la cabecera "Authorization" como tipo "Bearer".
# "tokenUrl" es la URL relativa donde el usuario envía usuario/password para obtener el token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- Dependencias de Autenticación ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    """
    Decodifica el token JWT, extrae el email (subject) y busca al usuario en la base de datos.
    Si algo falla o el usuario no existe, lanza una excepción 401 (No autorizado).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se han podido validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodificamos el token usando nuestra clave secreta y algoritmo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        # Si el token es inválido o ha expirado, JWTError será capturado
        raise credentials_exception
        
    # Buscamos al usuario en la base de datos usando el email extraído del token
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Capa de abstracción adicional para verificar si el usuario está activo.
    Actualmente solo devuelve el usuario, pero permite añadir validaciones 
    facilmente (ej. comprobar si la cuenta está bloqueada).
    """
    return current_user

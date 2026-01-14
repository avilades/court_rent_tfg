from datetime import datetime, timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import crud, schemas, dependencies, database
from ..dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import jwt

# Router para gestionar la autenticación de usuarios
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Genera un token JWT firmado.
    :param data: Diccionario con los datos a incluir en el token (ej. 'sub': email).
    :param expires_delta: Tiempo opcional de expiración.
    :return: El token codificado en formato string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Por defecto expira en 15 minutos si no se especifica
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Añadimos la fecha de expiración al payload del token
    to_encode.update({"exp": expire})
    
    # Firmamos el token con nuestra clave secreta y algoritmo configurado
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Endpoint para registrar un nuevo usuario en el sistema.
    Valida que el email no esté ya registrado antes de proceder.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    
    new_user = crud.create_user(db=db, user=user)
    logging.info(f"Nuevo usuario registrado: {new_user.email}")
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Endpoint de inicio de sesión compatible con OAuth2.
    Verifica las credenciales y devuelve un token de acceso JWT.
    """
    # 1. Buscar al usuario por email (username en el formulario de OAuth2)
    user = crud.get_user_by_email(db, email=form_data.username)
    
    # 2. Verificar contraseña
    if not user or not crud.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generar el token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logging.info(f"Inicio de sesión exitoso: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}

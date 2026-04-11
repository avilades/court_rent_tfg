from datetime import datetime, timedelta
import logging
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import crud, schemas, dependencies, database, models
from ..dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from ..services.notification_service import (
    send_and_record_notification,
    generate_welcome_email,
    generate_password_reset_email,
)
from ..templates import templates
from jose import JWTError, jwt


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


def create_password_reset_token(email: str, expires_delta: timedelta | None = None) -> str:
    """Genera un token JWT temporal para restablecer contraseña."""
    payload = {"sub": email, "type": "password_reset"}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> str:
    """Verifica el JWT de restablecimiento y devuelve el email asociado."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Token de restablecimiento inválido")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Token de restablecimiento inválido")
        return email
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Token de restablecimiento inválido o caducado") from exc


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

    try:
        html_content = generate_welcome_email(new_user.name)
        email_sent = send_and_record_notification(
            db=db,
            user_id=new_user.user_id,
            recipient_email=new_user.email,
            notification_type="welcome_email",
            subject="¡Bienvenido a Reserva de Pistas!",
            html_content=html_content,
        )
        if not email_sent:
            logging.warning(f"No se pudo enviar el email de bienvenida a {new_user.email}")
    except Exception as e:
        logging.error(f"Error al enviar email de bienvenida a {new_user.email}: {e}")

    return new_user

@router.get("/password-reset-request", response_class=HTMLResponse)
def password_reset_request_page(request: Request):
    """Muestra el formulario de solicitud de restablecimiento de contraseña."""
    return templates.TemplateResponse("request_password_reset.html", {"request": request})


@router.post("/password-reset-request")
def password_reset_request(data: schemas.PasswordResetRequest, request: Request, db: Session = Depends(database.get_db)):
    """Envía un enlace de restablecimiento de contraseña al email indicado."""
    user = crud.get_user_by_email(db, email=data.email)
    if not user:
        # No se revela si el usuario existe o no por seguridad.
        return {"msg": "Si existe una cuenta asociada, recibirás un correo para restablecer la contraseña."}

    reset_token = create_password_reset_token(user.email)
    reset_url = f"{request.url_for('password_reset_page')}?token={quote(reset_token, safe='')}"
    html_content = generate_password_reset_email(user.name, reset_url)

    try:
        send_and_record_notification(
            db=db,
            user_id=user.user_id,
            recipient_email=user.email,
            notification_type="password_reset",
            subject="Restablece tu contraseña",
            html_content=html_content,
        )
    except Exception as exc:
        logging.error(f"Error al enviar el email de restablecimiento a {user.email}: {exc}")

    return {"msg": "Si existe una cuenta asociada, recibirás un correo para restablecer la contraseña."}


@router.get("/password-reset", response_class=HTMLResponse)
def password_reset_page(request: Request, token: str | None = None):
    """Muestra el formulario para introducir la nueva contraseña usando el token recibido."""
    if not token:
        raise HTTPException(status_code=400, detail="Token de restablecimiento requerido")
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


@router.post("/password-reset")
def password_reset_confirm(data: schemas.PasswordResetConfirm, db: Session = Depends(database.get_db)):
    """Aplica la nueva contraseña usando el token de restablecimiento."""
    email = verify_password_reset_token(data.token)
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    crud.update_user_password(db, user.user_id, data.new_password)
    return {"msg": "Contraseña actualizada correctamente"}


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

@router.get("/me", response_model=schemas.UserWithPermissions)
def get_me(current_user: models.User = Depends(dependencies.get_current_user)):
    """
    Endpoint para obtener la información del usuario actualmente autenticado,
    incluyendo sus permisos.
    """
    return current_user

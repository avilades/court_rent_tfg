from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)

# --- Esquemas Pydantic ---
# Los esquemas se utilizan para la validación de datos y la serialización (conversión a JSON).
# Actúan como el "contrato" entre nuestra API y el mundo exterior.

# --- Esquemas de Usuario ---

class UserBase(BaseModel):
    """Atributos comunes para un usuario."""
    name: str
    surname: str
    email: EmailStr

class UserCreate(UserBase):
    """Datos necesarios para crear un nuevo usuario (incluye contraseña)."""
    password: str


class UserResponse(UserBase):
    """Datos de usuario que devolvemos en las respuestas de la API."""
    user_id: int
    # ¡Nunca devolvemos el password_hash por razones de seguridad!

    class Config:
        # Permite que Pydantic lea datos directamente desde objetos SQLAlchemy
        from_attributes = True 

# --- Esquemas de Permisos ---

class PermissionResponse(BaseModel):
    """Respuesta con los permisos asignados a un usuario."""
    is_admin: bool
    can_rent: bool
    can_edit_schedule: bool
    can_edit_price: bool

    class Config:
        from_attributes = True

class UserWithPermissions(UserResponse):
    """Extensión de UserResponse que incluye la información de sus permisos."""
    permissions: Optional[PermissionResponse] = None

# --- Esquemas de Tokens (Autenticación JWT) ---

class Token(BaseModel):
    """Estructura del token que se envía al cliente tras un login exitoso."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Datos contenidos dentro del payload del token (ej. email)."""
    email: Optional[str] = None

class UserLogin(BaseModel):
    """Estructura esperada para el formulario de inicio de sesión."""
    email: str
    password: str

# --- Esquemas de Pistas ---

class CourtResponse(BaseModel):
    """Información básica de una pista."""
    court_id: int
    is_covered: bool

    class Config:
        from_attributes = True

# --- Esquemas de Disponibilidad y Horarios ---

class SlotBase(BaseModel):
    """Representa un hueco de tiempo específico y su estado de disponibilidad."""
    court_id: int
    start_time: datetime # Marca de tiempo completa ISO
    end_time: datetime
    is_available: bool
    price_amount: Optional[float] = None  # Precio aplicable para este slot

# --- Esquemas de Reservas ---

class BookingCreate(BaseModel):
    """Datos necesarios para realizar una nueva reserva."""
    court_id: int
    date: str       # Formato "YYYY-MM-DD"
    time_slot: str  # Formato "HH:MM" (hora de inicio)

class BookingResponse(BaseModel):
    """Información que se devuelve tras consultar o realizar una reserva."""
    booking_id: int
    court_id: int
    start_time: datetime
    is_cancelled: bool
    price_amount: Optional[float] = None # Campo calculado/enriquecido con el precio pagado

    class Config:
        from_attributes = True

# --- Esquemas de Precios ---

class PriceUpdate(BaseModel):
    """Esquema para actualizar un precio."""
    demand_id: int
    amount: float
    start_date: datetime # Fecha de inicio del nuevo precio

class UserPasswordReset(BaseModel):
    """Esquema para el reseteo de contraseña por un administrador."""
    user_id: int
    new_password: str


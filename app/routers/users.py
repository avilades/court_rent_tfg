from fastapi import APIRouter

# Router para futuras operaciones relacionadas con la gestión de usuarios
# (Ej: actualizar perfil, cambiar contraseña, etc.)
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

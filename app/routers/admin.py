from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user
from ..database import engine

# Definición del router para las operaciones administrativas
router = APIRouter(
    prefix="/admin",
    tags=["Admin"] # Categoría para la documentación automática (Swagger)
)

@router.post("/price")
def create_price(price: int, description: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Endpoint para crear un nuevo precio (tarifa).
    Requiere que el usuario autenticado tenga el permiso 'is_admin' y 'can_edit_price'.
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de administrador")
        
    if not current_user.permissions.can_edit_price:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar precios")
    
    # Lógica simplificada para demostración
    # TODO: Implementar la creación real del registro en models.Price
    return {"msg": "Precio creado correctamente (simulación)"}

@router.post("/reset-database")
def reset_database(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    ⚠️ PELIGRO: Este endpoint borra y recrea todas las tablas de la base de datos.
    Se utiliza únicamente para desarrollo y depuración para resetear el estado del sistema.
    Requiere permisos de administrador.
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de administrador")

    try:
        # Cerramos la sesión actual para evitar bloqueos
        db.close()
        
        # Eliminamos todas las tablas existentes
        models.Base.metadata.drop_all(bind=engine)
        
        # Volvemos a crear las tablas vacías
        models.Base.metadata.create_all(bind=engine)
        
        return {"msg": "Base de datos reseteada con éxito. Reinicia la aplicación para recargar datos iniciales."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al resetear la base de datos: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import logging
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user
from ..database import engine
from ..templates import templates

# Definición del router para las operaciones administrativas
router = APIRouter(
    prefix="/admin",
    tags=["Admin"] # Categoría para la documentación automática (Swagger)
)

@router.get("/", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Panel de administración (solo accesible para usuarios con permisos)."""
    logging.info("Renderizando panel de administración...")
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/stats", response_class=HTMLResponse)
async def admin_stats_page(request: Request):
    """Panel de estadísticas para el administrador."""
    logging.info("Renderizando panel de estadísticas...")
    return templates.TemplateResponse("admin_stats.html", {"request": request})

@router.get("/precio", response_class=HTMLResponse)
async def price_page(request: Request):
    """Vista para la gestión de precios (Panel Admin)."""
    logging.info("Renderizando página de gestión de precios...")
    return templates.TemplateResponse("precio.html", {"request": request})

@router.get("/reservas", response_class=HTMLResponse)
async def admin_reservas_page(request: Request):
    """Vista de gestión de todas las reservas (Panel Admin)."""
    logging.info("Renderizando página de todas las reservas...")
    return templates.TemplateResponse("admin_reservas.html", {"request": request})

@router.get("/prices")
def get_prices(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lista todos los precios vigentes (is_active=True).
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    prices = db.query(models.Price).filter(models.Price.is_active == True).all()
    # Retornamos los campos necesarios para el frontend
    return [{"price_id": p.price_id, "demand_id": p.demand_id, "amount": p.amount, "description": p.description} for p in prices]

@router.post("/prices/update")
def update_price(data: schemas.PriceUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Actualiza un precio aplicando lógica de versionado:
    1. Busca el precio actual para ese demand_id.
    2. Le pone fecha_fin (end_date) y lo desactiva.
    3. Crea uno nuevo con el nuevo importe y la fecha_inicio proporcionada.
    """
    if not current_user.permissions.is_admin or not current_user.permissions.can_edit_price:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar precios")

    # 1. Buscar el precio actual (activo) para ese demand_id
    current_price = db.query(models.Price).filter(
        models.Price.demand_id == data.demand_id,
        models.Price.is_active == True
    ).first()

    if not current_price:
        raise HTTPException(status_code=404, detail="Precio actual no encontrado")

    # 2. Cerrar el precio antiguo
    # Ponemos la fecha de fin igual a la fecha de inicio del nuevo precio
    current_price.end_date = data.start_date
    current_price.is_active = False

    # 3. Crear el nuevo precio
    new_price = models.Price(
        amount=data.amount,
        start_date=data.start_date,
        end_date=None,
        description=current_price.description, # Mantenemos la descripción (Alta, Media, Baja)
        is_active=True,
        demand_id=data.demand_id
    )
    
    db.add(new_price)
    db.commit()
    db.refresh(new_price)

    return {"msg": "Precio actualizado correctamente", "new_price_id": new_price.price_id}

@router.get("/stats-data")
def get_stats(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Calcula estadísticas de uso e ingresos.
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # 1. Tasa de ocupación (Últimos 30 días)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_bookings = db.query(models.Booking).filter(
        models.Booking.start_time >= thirty_days_ago,
        models.Booking.is_cancelled == False
    ).count()
    
    # 2. Ingresos totales (Agrupados por mes)
    income_by_price = db.query(
        func.sum(models.Price.amount)
    ).join(
        models.Booking, models.Booking.price_id == models.Price.price_id
    ).filter(
        models.Booking.is_cancelled == False
    ).scalar() or 0.0

    # 3. Ocupación por pista
    occupancy_by_court = db.query(
        models.Booking.court_id, func.count(models.Booking.booking_id)
    ).filter(
        models.Booking.is_cancelled == False
    ).group_by(models.Booking.court_id).all()
    
    court_stats = {f"Pista {c_id}": count for c_id, count in occupancy_by_court}

    return {
        "total_bookings_30d": total_bookings,
        "total_income": round(income_by_price, 2),
        "court_occupancy": court_stats
    }

@router.get("/courts")
def list_courts(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lista las pistas con su estado de mantenimiento.
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    courts = db.query(models.Court).all()
    return courts

@router.post("/courts/{court_id}/maintenance")
def toggle_maintenance(court_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Activa o desactiva el modo mantenimiento de una pista.
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    court = db.query(models.Court).filter(models.Court.court_id == court_id).first()
    if not court:
        raise HTTPException(status_code=404, detail="Pista no encontrada")
    
    court.is_maintenance = not court.is_maintenance
    db.commit()
    db.refresh(court)
    
    return {"msg": f"Pista {court_id} {'en mantenimiento' if court.is_maintenance else 'activa'}", "is_maintenance": court.is_maintenance}

@router.get("/bookings/daily")
def get_daily_bookings(date: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retorna todas las reservas para una fecha específica, con detalles del usuario y precio.
    """
    if not current_user.permissions.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    from datetime import datetime, time
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (YYYY-MM-DD)")

    # Definir rango del día
    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date, time.max)

    # Consulta con joins para obtener info de usuario y precio histórico
    bookings = db.query(models.Booking).filter(
        models.Booking.start_time >= start_dt,
        models.Booking.start_time <= end_dt
    ).order_by(models.Booking.start_time.asc()).all()

    results = []
    for b in bookings:
        results.append({
            "booking_id": b.booking_id,
            "court_id": b.court_id,
            "start_time": b.start_time.isoformat(),
            "user_email": b.user.email,
            "price_amount": b.price_snapshot.amount if b.price_snapshot else "N/A",
            "is_cancelled": b.is_cancelled
        })
    
    return results

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

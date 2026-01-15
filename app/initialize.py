from sqlalchemy.orm import Session
from datetime import time
from . import models, schemas, crud
import logging

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)

# --- Operaciones de Inicialización del Administrador ---

def initialize_admin_user(db: Session):
    """
    Crea el usuario administrador por defecto si no existe en la base de datos.
    También se asegura de que tenga los permisos necesarios.
    """
    # 1. Comprobar si el usuario 'admin' existe
    if db.query(models.User).filter(models.User.name == "admin").count() == 0:
        # Si no existe, lo creamos con una contraseña por defecto
        crud.create_user(db, schemas.UserCreate(
            name="admin", 
            surname="admin", 
            email="admin@example.com", 
            password="admin000"
        ))
        logger.info("Usuario administrador creado.")
    else:
        logger.info("El usuario administrador ya existe.")

    # 2. Verificar y actualizar permisos de administrador
    # Nos aseguramos de que el usuario 'admin' tenga permisos de admin y de edición.
    admin_user = db.query(models.User).filter(models.User.name == "admin").first()
    if admin_user:
        has_full_permissions = db.query(models.Permission).filter(
            models.Permission.user_id == admin_user.user_id,
            models.Permission.is_admin == True,
            models.Permission.can_edit_schedule == True,
            models.Permission.can_edit_price == True
        ).count() > 0

        if not has_full_permissions:
            update_admin_user_permission(db, admin_user.user_id)
        else:
            logger.info("Los permisos de administrador ya son correctos.")

def update_admin_user_permission(db: Session, user_id: int):
    """
    Actualiza la tabla de permisos para otorgar privilegios totales a un usuario.
    """
    db.query(models.Permission).filter(
        models.Permission.user_id == user_id
    ).update({
        models.Permission.is_admin: True,
        models.Permission.can_edit_schedule: True,
        models.Permission.can_edit_price: True
    })
    db.commit() 
    logger.info("Permisos de administrador actualizados.")

# --- Inicialización de Datos Maestros ---

def initialize_demands(db: Session):
    """
    Crea los tipos de demanda (Alta, Media, Baja) si no existen.
    Esto es crucial para el sistema dinámico de precios.
    """
    required_demands = [
        {"description": "Demanda alta", "is_active": True},
        {"description": "Demanda media", "is_active": True},
        {"description": "Demanda baja", "is_active": True}
    ]
    
    for demand_data in required_demands:
        existing_demand = db.query(models.Demand).filter(
            models.Demand.description == demand_data["description"]
        ).first()
        
        if not existing_demand:
            new_demand = models.Demand(**demand_data)
            db.add(new_demand)
    
    db.commit()
    logger.info("Tipos de demanda inicializados.")

def initialize_prices(db: Session):
    """
    Establece los precios base para cada tipo de demanda si no están definidos.
    Precios: Alta -> 30€, Media -> 20€, Baja -> 10€.
    """
    required_prices = [
        {"amount": 30, "description": "Precio de pista", "is_active": True, "demand_id": 1},
        {"amount": 20, "description": "Precio de pista", "is_active": True, "demand_id": 2},
        {"amount": 10, "description": "Precio de pista", "is_active": True, "demand_id": 3}
    ]
    
    for price_data in required_prices:
        # Verificamos si ya existe un precio para esa demanda
        existing_price = db.query(models.Price).filter(
            models.Price.demand_id == price_data["demand_id"]
        ).first()
        
        if not existing_price:
            new_price = models.Price(**price_data)
            db.add(new_price)
    
    db.commit()
    logger.info("Precios inicializados.")

def initialize_courts(db: Session):
    """
    Crea las 8 pistas de la instalación.
    Asumimos que las pistas 5 a 8 son cubiertas (is_covered=True).
    """
    if db.query(models.Court).count() == 0:
        for i in range(1, 9):
            # i > 4 significa que pistas 5, 6, 7 y 8 están cubiertas
            court = models.Court(court_id=i, is_covered=(i > 4)) 
            db.add(court)
        db.commit()
    logger.info("Pistas inicializadas.")     

def initialize_schedules(db: Session):
    """
    Configura el horario semanal completo con los bloques de 90 minutos y su demanda asociada.
    """
    # Si ya hay horarios, no re-inicializamos
    if db.query(models.Schedule).count() > 0:
        return
    
    # Definición de los bloques horarios de 90 minutos
    time_slots = [
        time(8, 0), time(9, 30), time(11, 0), time(12, 30),
        time(14, 0), time(15, 30), time(17, 0), time(18, 30),
        time(20, 0), time(21, 30)
    ]
    
    # Lógica para Días de Diario (Lunes a Viernes, 0-4)
    # Mañanas/Tardes (antes de las 17:00): Demanda Baja (ID 3)
    # Noches (a partir de las 17:00): Demanda Alta (ID 1)
    for day in range(5):
        for slot in time_slots:
            demand_id = 3 if slot < time(17, 0) else 1
            schedule = models.Schedule(
                day_of_week=day,
                is_weekend=False,
                start_time=slot,
                demand_id=demand_id
            )
            db.add(schedule)
    
    # Sábado (Día 5): Todo el día Demanda Alta (ID 1)
    for slot in time_slots:
        schedule = models.Schedule(
            day_of_week=5,
            is_weekend=True,
            start_time=slot,
            demand_id=1
        )
        db.add(schedule)
    
    # Domingo (Día 6): 
    # Mañana hasta 17:00: Demanda Alta (ID 1)
    # Noche post 17:00: Demanda Baja (ID 3)
    for slot in time_slots:
        demand_id = 1 if slot < time(17, 0) else 3
        schedule = models.Schedule(
            day_of_week=6,
            is_weekend=True,
            start_time=slot,
            demand_id=demand_id
        )
        db.add(schedule)
    
    db.commit()
    logger.info("Horarios semanales inicializados.")


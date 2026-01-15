from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
from datetime import datetime, timedelta

# --- Security Configuration ---
# Configuración de seguridad para el hashing de contraseñas.
# 'pbkdf2_sha256' es un algoritmo robusto y recomendado por defecto.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """
    Verifica si una contraseña en texto plano coincide con su hash almacenado.
    :param plain_password: La contraseña introducida por el usuario.
    :param hashed_password: El hash recuperado de la base de datos.
    :return: True si coinciden, False en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Genera un hash seguro para la contraseña proporcionada.
    :param password: Password en texto plano.
    :return: String con el hash generado.
    """
    return pwd_context.hash(password)

# --- User Operations ---

def get_user_by_email(db: Session, email: str):
    """
    Busca un usuario en la base de datos por su dirección de correo electrónico.
    :param db: Sesión de la base de datos.
    :param email: Email a buscar.
    :return: Objeto User si se encuentra, None si no.
    """
    return db.query(models.User).filter(models.User.email == email).first()  

def create_user(db: Session, user: schemas.UserCreate):
    """
    Crea un nuevo usuario en el sistema.
    Realiza tres pasos principales:
    1. Hashea la contraseña para mayor seguridad.
    2. Crea la instancia del usuario y la guarda.
    3. Asigna permisos por defecto (puede alquilar, pero no es admin).
    """
    # 1. Hashear la contraseña
    fake_hashed_password = get_password_hash(user.password)
    
    # 2. Crear instancia del usuario
    db_user = models.User(
        email=user.email, 
        name=user.name, 
        surname=user.surname, 
        password_hash=fake_hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 3. Crear permisos por defecto
    # Por defecto: can_rent=True (puede alquilar pistas), is_admin=False.
    db_perm = models.Permission(
        user_id=db_user.user_id,
        is_admin=False,
        can_rent=True,
        can_edit_schedule=False,
        can_edit_price=False
    )
    db.add(db_perm)
    db.commit()

    return db_user

# --- Court Operations ---

def get_courts(db: Session):
    """
    Recupera todas las pistas de tenis/pádel registradas.
    """
    return db.query(models.Court).all()

# --- Booking Operations ---

def get_user_bookings(db: Session, user_id: int, date_from: str = None, date_to: str = None):
    """
    Obtiene las reservas de un usuario específico, con opción de filtrado por fechas.
    Además, enriquece la respuesta con el importe del precio en el momento de la reserva.
    :param user_id: ID del usuario.
    :param date_from: Fecha inicial (ISO format).
    :param date_to: Fecha final (ISO format).
    """
    from datetime import datetime, timedelta
    
    query = db.query(models.Booking).filter(models.Booking.user_id == user_id)
    
    # Aplicar filtros de fecha si se proporcionan
    if date_from:
        from_date = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(models.Booking.start_time >= from_date)
    
    if date_to:
        to_date = datetime.strptime(date_to, "%Y-%m-%d")
        # Se suma 1 día para incluir todo el día final en el filtro <
        to_date = to_date + timedelta(days=1)
        query = query.filter(models.Booking.start_time < to_date)
    
    # Ordenamos por fecha de reserva descendente (más recientes primero)
    bookings = query.order_by(models.Booking.start_time.desc()).all()
    
    # Construimos el resultado incluyendo el importe del precio desde la relación price_snapshot
    result = []
    for b in bookings:
        booking_dict = {
            "booking_id": b.booking_id,
            "court_id": b.court_id,
            "start_time": b.start_time,
            "is_cancelled": b.is_cancelled,
            # Recuperamos el importe del precio de la tabla 'prices' asociada en el momento del alquiler
            "price_amount": b.price_snapshot.amount if b.price_snapshot else None
        }
        result.append(booking_dict)
    return result

def create_booking(db: Session, booking_data: schemas.BookingCreate, user_id: int):
    """
    Crea una nueva reserva de pista.
    Valida la disponibilidad, calcula el precio según el horario/demanda y registra la reserva.
    """
    # 1. Parsear la fecha y hora de la reserva
    start_dt = datetime.strptime(f"{booking_data.date} {booking_data.time_slot}", "%Y-%m-%d %H:%M")
    
    # 2. Verificar si la pista ya está reservada para ese horario
    existing = db.query(models.Booking).filter(
        models.Booking.court_id == booking_data.court_id,
        models.Booking.start_time == start_dt,
        models.Booking.is_cancelled == False
    ).first()
    
    if existing:
        return None # Conflicto: la pista ya está ocupada
    
    # 3. Determinar el ID del precio aplicable según el horario (Schedule) y la demanda activa en el momento de la reserva
    day_of_week = start_dt.weekday()
    time_obj = start_dt.time()
    
    # Buscamos el demand_id para ese horario
    schedule = db.query(models.Schedule).filter(
        models.Schedule.day_of_week == day_of_week,
        models.Schedule.start_time == time_obj
    ).first()
    
    if not schedule:
        return None
    
    # Buscamos el precio vigente para esa demanda en la fecha de la reserva
    from sqlalchemy import or_
    price = db.query(models.Price).filter(
        models.Price.demand_id == schedule.demand_id,
        models.Price.start_date <= start_dt,
        or_(models.Price.end_date == None, models.Price.end_date > start_dt)
    ).order_by(models.Price.start_date.desc()).first()
    
    price_id = price.price_id if price else None
    
    if not price_id:
        # Esto no debería ocurrir si el sistema está bien inicializado
        return None 
    
    # 4. Crear el registro de la reserva
    new_booking = models.Booking(
        user_id=user_id,
        court_id=booking_data.court_id,
        start_time=start_dt,
        price_id=price_id,
        is_cancelled=False
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    # Retornamos un diccionario con la información relevante, incluyendo el precio
    return {
        "booking_id": new_booking.booking_id,
        "court_id": new_booking.court_id,
        "start_time": new_booking.start_time,
        "is_cancelled": new_booking.is_cancelled,
        "price_amount": new_booking.price_snapshot.amount if new_booking.price_snapshot else None
    }

def cancel_booking_logic(db: Session, booking_id: int, user_id: int):
    """
    Marca una reserva como cancelada.
    Solo permite cancelar si la reserva pertenece al usuario especificado.
    """
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == booking_id, 
        models.Booking.user_id == user_id
    ).first()
    
    if booking:
        booking.is_cancelled = True
        db.commit()
    
    return booking

def get_all_users(db: Session):
    """
    Recupera todos los usuarios registrados.
    """
    return db.query(models.User).all()

def update_user_password(db: Session, user_id: int, new_password: str):
    """
    Actualiza la contraseña de un usuario.
    :param db: Sesión de la base de datos.
    :param user_id: ID del usuario.
    :param new_password: Nueva contraseña en texto plano.
    :return: Objeto User actualizado o None if not found.
    """
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user:
        db_user.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(db_user)
    return db_user

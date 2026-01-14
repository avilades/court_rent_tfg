from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user

# Router para gestionar las reservas de pistas
router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.get("/my-bookings", response_model=List[schemas.BookingResponse])
def read_my_bookings(
    date_from: str = None, 
    date_to: str = None,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Recupera todas las reservas del usuario autenticado.
    Opcional: filtrar por rango de fechas (date_from, date_to en formato YYYY-MM-DD).
    """
    return crud.get_user_bookings(db, user_id=current_user.user_id, date_from=date_from, date_to=date_to)

@router.post("/book", response_model=schemas.BookingResponse)
def book_court(booking: schemas.BookingCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Realiza una nueva reserva de pista.
    Verifica los permisos del usuario y posibles conflictos de horario.
    """
    # 1. Verificar si el usuario tiene permiso para alquilar
    if not current_user.permissions.can_rent:
         raise HTTPException(status_code=403, detail="No tienes permisos para realizar alquileres")

    # 2. Intentar crear la reserva en la base de datos
    new_booking = crud.create_booking(db, booking, user_id=current_user.user_id)
    if not new_booking:
         raise HTTPException(status_code=409, detail="El horario seleccionado ya está ocupado")
    
    return new_booking

@router.get("/search", response_model=List[schemas.SlotBase])
def search_available_slots(date: str, db: Session = Depends(get_db)):
    """
    Busca y devuelve la disponibilidad de todas las pistas para una fecha específica.
    Lógica:
    1. Define los bloques horarios estándar (90 min).
    2. Cruza con las reservas existentes para marcar cuáles están ocupadas.
    3. Obtiene el precio dinámico aplicable según el horario (Schedule).
    """
    from datetime import datetime, timedelta, time as dt_time
    
    # Bloques horarios definidos en el sistema
    start_times = [
        "08:00", "09:30", "11:00", "12:30", "14:00", 
        "15:30", "17:00", "18:30", "20:00", "21:30"
    ]
    
    # Parseo de la fecha objetivo
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    day_of_week = target_date.weekday()  # 0=Lunes, 6=Domingo
    courts = crud.get_courts(db)
    
    available_slots = []
    
    # Optimizacion: Obtenemos todas las reservas ACTIVAS para ese día de una sola vez
    existing_bookings = db.query(models.Booking).filter(
        models.Booking.is_cancelled == False
    ).all()
    
    # Creamos un set de claves "pista_hora" para una búsqueda rápida en memoria
    booked_keys = set()
    for b in existing_bookings:
        if b.start_time.date() == target_date:
            key = f"{b.court_id}_{b.start_time.strftime('%H:%M')}"
            booked_keys.add(key)
    
    # Obtenemos los precios vigentes para el día de la semana correspondiente (JOIN con Price)
    results = db.query(models.Schedule, models.Price).join(
        models.Price, models.Price.demand_id == models.Schedule.demand_id
    ).filter(
        models.Schedule.day_of_week == day_of_week,
        models.Price.is_active == True
    ).all()
    
    # Mapa auxiliar para obtener el precio según la hora de inicio
    time_price_map = {}
    for sched, price in results:
        time_str = sched.start_time.strftime('%H:%M')
        time_price_map[time_str] = price.amount
    
    # Generamos la matriz de disponibilidad (Pistas x Horarios)
    for court in courts:
        for t_str in start_times:
            key = f"{court.court_id}_{t_str}"
            is_taken = key in booked_keys
            
            # Construcción de las marcas de tiempo de inicio y fin
            start_dt = datetime.strptime(f"{date} {t_str}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=90)
            
            # Recuperamos el precio dinámico asignado a este bloque
            price_amount = time_price_map.get(t_str)
            
            # Solo devolvemos los slots que NO están ocupados (o según lógica deseada)
            if not is_taken:
                available_slots.append(schemas.SlotBase(
                    court_id=court.court_id,
                    start_time=start_dt,
                    end_time=end_dt,
                    is_available=True,
                    price_amount=price_amount
                ))
                
    return available_slots

@router.post("/cancel/{booking_id}")
def cancel_booking(booking_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Cancela una reserva existente.
    Verifica que el usuario sea el propietario de la reserva.
    """
    booking = crud.cancel_booking_logic(db, booking_id, current_user.user_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no estás autorizado")
    
    return {"msg": "Reserva cancelada correctamente"}


from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user
from .. import weather_service
from ..services.notification_service import (
    send_and_record_notification,
    generate_booking_confirmation_email,
    generate_cancellation_email
)
from ..services.task_service import schedule_reminder_task, cancel_pending_task


# inicializamos el logger
logger = logging.getLogger(__name__)

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
    
    logging.info(f"Busqueda de reservas para el usuario {current_user.email} con fechas {date_from} - {date_to}")   
    
    return crud.get_user_bookings(db, user_id=current_user.user_id, date_from=date_from, date_to=date_to)

@router.post("/book", response_model=schemas.BookingResponse)
def book_court(booking: schemas.BookingCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Realiza una nueva reserva de pista.
    Verifica los permisos del usuario y posibles conflictos de horario.
    Envía notificaciones: confirmación y programa recordatorio 24h antes.
    """
    # 1. Verificar si el usuario tiene permiso para alquilar
    if not current_user.permissions.can_rent:
         raise HTTPException(status_code=403, detail="No tienes permisos para realizar alquileres")

    # 2. Intentar crear la reserva en la base de datos
    new_booking = crud.create_booking(db, booking, user_id=current_user.user_id)
    if not new_booking:
         raise HTTPException(status_code=409, detail="El horario seleccionado ya está ocupado")
    
    logging.info(f"Reserva creada: Usuario={current_user.email}, Pista={new_booking['court_id']}, Fecha={new_booking['start_time'].date()}, Hora={new_booking['start_time'].strftime('%H:%M')}")
    
    # 3. Enviar notificación de confirmación
    try:
        from datetime import datetime as dt, timedelta
        start_datetime = new_booking['start_time']
        end_datetime = start_datetime + timedelta(minutes=90)
        price = new_booking.get('price_amount', 0)
        
        html_content = generate_booking_confirmation_email(
            user_name=current_user.name,
            court_number=new_booking['court_id'],
            start_time=start_datetime.strftime("%d/%m/%Y %H:%M"),
            end_time=end_datetime.strftime("%H:%M"),
            price=price
        )
        
        send_and_record_notification(
            db=db,
            user_id=current_user.user_id,
            recipient_email=current_user.email,
            notification_type="booking_confirmation",
            subject=f"✓ Reserva Confirmada - Pista {new_booking['court_id']}",
            html_content=html_content,
            booking_id=new_booking['booking_id']
        )
        
        # 4. Programar recordatorio para 24h antes
        schedule_reminder_task(
            db=db,
            booking_id=new_booking['booking_id'],
            user_id=current_user.user_id,
            recipient_email=current_user.email,
            court_number=new_booking['court_id'],
            start_time=start_datetime
        )
        
        logging.info(f"Notificaciones enviadas para reserva {new_booking['booking_id']}")
    except Exception as e:
        logging.error(f"Error al enviar notificaciones para reserva {new_booking['booking_id']}: {str(e)}")
    
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
    from sqlalchemy import or_
    
    # Bloques horarios definidos en el sistema
    start_times = [
        "08:00", "09:30", "11:00", "12:30", "14:00", 
        "15:30", "17:00", "18:30", "20:00", "21:30"
    ]
    
    # Parseo de la fecha objetivo
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    day_of_week = target_date.weekday()  # 0=Lunes, 6=Domingo
    
    # Rango del día para filtros
    start_of_day = datetime.combine(target_date, dt_time.min)
    end_of_day = datetime.combine(target_date, dt_time.max)
    
    # Solo buscamos en pistas que NO estén en mantenimiento
    courts = db.query(models.Court).filter(models.Court.is_maintenance == False).all()
    
    available_slots = []
    
    # Optimizacion: Obtenemos solo las reservas ACTIVAS para ese día específico
    existing_bookings = db.query(models.Booking).filter(
        models.Booking.start_time >= start_of_day,
        models.Booking.start_time <= end_of_day,
        models.Booking.is_cancelled == False
    ).all()
    
    # Creamos un set de claves "pista_hora" para una búsqueda rápida en memoria
    booked_keys = {f"{b.court_id}_{b.start_time.strftime('%H:%M')}" for b in existing_bookings}
    
    # Obtenemos los horarios para el día de la semana
    schedules = db.query(models.Schedule).filter(models.Schedule.day_of_week == day_of_week).all()
    
    # Mapa de demanda por hora
    time_demand_map = {s.start_time.strftime('%H:%M'): s.demand_id for s in schedules}
    
    # Optimizacion: Obtenemos los precios vigentes para esa fecha una sola vez
    # Buscamos los precios que cubren el rango del día solicitado
    prices_query = db.query(models.Price).filter(
        models.Price.start_date <= end_of_day,
        or_(models.Price.end_date == None, models.Price.end_date > start_of_day)
    ).order_by(models.Price.start_date.desc()).all()
    
    # Creamos un mapa de demand_id -> price_amount (el más reciente/vigente)
    demand_price_map = {}
    for p in prices_query:
        if p.demand_id not in demand_price_map:
            demand_price_map[p.demand_id] = p.amount
    
    # Generamos la matriz de disponibilidad (Pistas x Horarios)
    for court in courts:
        for t_str in start_times:
            key = f"{court.court_id}_{t_str}"
            is_taken = key in booked_keys
            
            # Si ya está ocupada, no hace falta procesar el precio si solo devolvemos slots libres
            if is_taken:
                continue
                
            # Construcción de las marcas de tiempo de inicio y fin
            start_dt = datetime.strptime(f"{date} {t_str}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=90)
            
            # Recuperamos el ID de demanda para este bloque
            demand_id = time_demand_map.get(t_str)
            price_amount = demand_price_map.get(demand_id) if demand_id else None
            
            available_slots.append(schemas.SlotBase(
                court_id=court.court_id,
                start_time=start_dt,
                end_time=end_dt,
                is_available=True,
                price_amount=price_amount
            ))
    
    logging.info(f"Busqueda de disponibilidad para el dia {date}")
    
    return available_slots

@router.post("/cancel/{booking_id}")
def cancel_booking(booking_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Cancela una reserva existente.
    Verifica que el usuario sea el propietario de la reserva.
    Envía notificación de cancelación y cancela cualquier recordatorio programado.
    """
    # 1. Obtener la reserva antes de cancelarla para enviar notificación
    booking_record = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    if not booking_record or booking_record.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no estás autorizado")
    
    # Guardar información para la notificación
    court_number = booking_record.court_id
    start_time = booking_record.start_time
    price_amount = booking_record.price_snapshot.amount if booking_record.price_snapshot else 0
    
    # 2. Cancelar la reserva en la BD
    booking = crud.cancel_booking_logic(db, booking_id, current_user.user_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no estás autorizado")
    
    logging.info(f"Reserva cancelada: ID={booking_id}, Usuario={current_user.email}")
    
    # 3. Enviar notificación de cancelación
    try:
        html_content = generate_cancellation_email(
            user_name=current_user.name,
            court_number=court_number,
            start_time=start_time.strftime("%d/%m/%Y %H:%M"),
            refund_amount=price_amount
        )
        
        send_and_record_notification(
            db=db,
            user_id=current_user.user_id,
            recipient_email=current_user.email,
            notification_type="cancellation",
            subject=f"✗ Reserva Cancelada - Pista {court_number}",
            html_content=html_content,
            booking_id=booking_id
        )
        
        # 4. Cancelar el recordatorio programado
        cancel_pending_task(db, booking_id)
        
        logging.info(f"Notificación de cancelación enviada para reserva {booking_id}")
    except Exception as e:
        logging.error(f"Error al enviar notificación de cancelación para reserva {booking_id}: {str(e)}")
    
    return {"msg": "Reserva cancelada correctamente"}

@router.get("/weather")
def get_weather(date: str):
    """
    Retorna la predicción meteorológica para una fecha dada.
    """
    return weather_service.get_weather_prediction(date)


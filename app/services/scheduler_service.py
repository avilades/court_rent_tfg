"""
Servicio de tareas programadas usando APScheduler.
Se encarga de enviar recordatorios 24h antes de una reserva.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from .. import models, database
from .notification_service import (
    send_email,
    create_notification_record,
    generate_reminder_email
)

logger = logging.getLogger(__name__)

# Instancia global del scheduler
scheduler = BackgroundScheduler()
scheduler_configured = False


def init_scheduler():
    """
    Inicializa el scheduler de tareas programadas.
    Se llama una sola vez al startup de la aplicación.
    """
    global scheduler_configured
    
    if scheduler_configured:
        return
    
    try:
        scheduler.start()
        scheduler_configured = True
        logger.info("APScheduler inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar APScheduler: {str(e)}")


def schedule_reminder_email(booking_id: int, user_id: int, recipient_email: str, 
                           court_number: int, start_time: datetime) -> bool:
    """
    Programa un email de recordatorio para 24h antes de la reserva.
    
    Args:
        booking_id: ID de la reserva
        user_id: ID del usuario
        recipient_email: Email del usuario
        court_number: Número de pista
        start_time: Fecha/hora de la reserva
        
    Returns:
        bool: True si se programó exitosamente
    """
    try:
        # Calcular cuándo enviar el email (24h antes)
        reminder_time = start_time - timedelta(hours=24)
        
        # Si la hora ya pasó, no programar
        if reminder_time < datetime.utcnow():
            logger.warning(f"No se puede programar recordatorio para booking {booking_id}: la hora ya pasó")
            return False
        
        # Crear la tarea
        job_id = f"reminder_booking_{booking_id}"
        
        # Programar la tarea
        scheduler.add_job(
            func=_send_reminder_task,
            trigger=DateTrigger(run_date=reminder_time),
            id=job_id,
            args=[booking_id, user_id, recipient_email, court_number, start_time],
            replace_existing=True,
            name=f"Recordatorio reserva {booking_id}"
        )
        
        logger.info(f"Recordatorio programado para booking {booking_id} a las {reminder_time}")
        return True
        
    except Exception as e:
        logger.error(f"Error programando recordatorio para booking {booking_id}: {str(e)}")
        return False


def _send_reminder_task(booking_id: int, user_id: int, recipient_email: str, 
                       court_number: int, start_time: datetime):
    """
    Tarea interna que ejecuta APScheduler para enviar el recordatorio.
    Se ejecuta automáticamente a la hora programada.
    """
    try:
        # Obtener sesión de base de datos
        db = database.SessionLocal()
        
        # Obtener usuario
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        
        if not user:
            logger.error(f"Usuario {user_id} no encontrado al enviar recordatorio")
            return
        
        # Generar contenido del email
        start_time_str = start_time.strftime("%d/%m/%Y %H:%M")
        html_content = generate_reminder_email(user.name, court_number, start_time.strftime("%H:%M"))
        
        # Enviar y registrar notificación
        email_sent = send_email(recipient_email, "⏰ Recordatorio de tu reserva", html_content)
        
        create_notification_record(
            db=db,
            user_id=user_id,
            recipient_email=recipient_email,
            notification_type="reminder_24h",
            subject="⏰ Recordatorio de tu reserva",
            content=html_content,
            booking_id=booking_id,
            is_sent=email_sent
        )
        
        if email_sent:
            logger.info(f"Recordatorio enviado exitosamente para booking {booking_id}")
        else:
            logger.error(f"Error al enviar recordatorio para booking {booking_id}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error en _send_reminder_task para booking {booking_id}: {str(e)}")


def cancel_reminder(booking_id: int):
    """
    Cancela un recordatorio programado para una reserva.
    Se usa cuando el usuario cancela la reserva.
    
    Args:
        booking_id: ID de la reserva
    """
    try:
        job_id = f"reminder_booking_{booking_id}"
        
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Recordatorio cancelado para booking {booking_id}")
        
    except Exception as e:
        logger.error(f"Error cancelando recordatorio para booking {booking_id}: {str(e)}")


def shutdown_scheduler():
    """
    Detiene el scheduler. Se llama al shutdown de la aplicación.
    """
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("APScheduler detenido correctamente")
    except Exception as e:
        logger.error(f"Error al detener APScheduler: {str(e)}")

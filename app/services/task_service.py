"""
Servicio mejorado de tareas programadas usando una tabla de BD.
Persiste las tareas y es más confiable que APScheduler con BackgroundScheduler.

Este servicio:
1. Guarda las tareas en la BD (tabla scheduled_tasks)
2. Provee un endpoint para procesar tareas pendientes (llamado por un worker/cron)
3. Implementa reintentos automáticos
4. Mantiene un historial de ejecuciones
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import json
from .. import models, database
from .notification_service import (
    send_email,
    create_notification_record,
    generate_reminder_email
)

logger = logging.getLogger(__name__)


def schedule_reminder_task(
    db: Session,
    booking_id: int,
    user_id: int,
    recipient_email: str,
    court_number: int,
    start_time: datetime
) -> bool:
    """
    Crea una tarea programada en la BD para enviar un recordatorio 24h antes.
    
    Esta función persiste la tarea, por lo que sobrevive a reinicios de la aplicación.
    
    Args:
        db: Sesión de base de datos
        booking_id: ID de la reserva
        user_id: ID del usuario
        recipient_email: Email del usuario
        court_number: Número de pista
        start_time: Fecha/hora de la reserva
        
    Returns:
        bool: True si se creó la tarea exitosamente
    """
    try:
        # Calcular cuándo enviar (24h antes)
        scheduled_for = start_time - timedelta(hours=24)
        
        # Si la hora ya pasó, no crear la tarea
        if scheduled_for < datetime.utcnow():
            logger.warning(
                f"No se puede programar recordatorio para booking {booking_id}: "
                f"la hora ya pasó (scheduled_for={scheduled_for}, now={datetime.utcnow()})"
            )
            return False
        
        # Preparar datos de la tarea
        task_data = {
            "recipient_email": recipient_email,
            "court_number": court_number,
            "start_time_str": start_time.isoformat()
        }
        
        # Crear registro en la BD
        scheduled_task = models.ScheduledTask(
            user_id=user_id,
            booking_id=booking_id,
            task_type="reminder_24h",
            scheduled_for=scheduled_for,
            task_data=json.dumps(task_data),
            is_executed=False
        )
        
        db.add(scheduled_task)
        db.commit()
        db.refresh(scheduled_task)
        
        logger.info(
            f"✓ Tarea programada creada: booking_id={booking_id}, "
            f"scheduled_for={scheduled_for.isoformat()}, task_id={scheduled_task.task_id}"
        )
        
        return True
        
    except Exception as e:
        logger.error(
            f"✗ Error creando tarea programada para booking {booking_id}: {str(e)}",
            exc_info=True
        )
        db.rollback()
        return False


def process_pending_tasks(db: Session) -> dict:
    """
    Procesa todas las tareas programadas que están pendientes.
    
    Esta función debería ser llamada periodicamente por:
    - Un cron job externo
    - Un worker de Celery
    - Un endpoint POST interno (como APScheduler hace polling)
    
    Returns:
        dict: Estadísticas de ejecución {
            "total_processed": int,
            "successful": int,
            "failed": int,
            "still_pending": int
        }
    """
    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "still_pending": 0
    }
    
    try:
        # Obtener todas las tareas pendientes que ya deberían haberse ejecutado
        pending_tasks = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.is_executed == False,
            models.ScheduledTask.scheduled_for <= datetime.utcnow()
        ).all()
        
        logger.info(f"Procesando {len(pending_tasks)} tareas pendientes...")
        
        for task in pending_tasks:
            success = _execute_task(db, task)
            
            if success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            
            stats["total_processed"] += 1
        
        # Contar tareas que todavía están pendientes (futuro)
        still_pending = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.is_executed == False,
            models.ScheduledTask.scheduled_for > datetime.utcnow()
        ).count()
        
        stats["still_pending"] = still_pending
        
        logger.info(
            f"✓ Procesamiento completado: "
            f"{stats['successful']} exitosas, "
            f"{stats['failed']} fallidas, "
            f"{stats['still_pending']} pendientes"
        )
        
    except Exception as e:
        logger.error(f"✗ Error procesando tareas: {str(e)}", exc_info=True)
    
    return stats


def _execute_task(db: Session, task: models.ScheduledTask) -> bool:
    """
    Ejecuta una tarea programada.
    
    Args:
        db: Sesión de base de datos
        task: Objeto ScheduledTask a ejecutar
        
    Returns:
        bool: True si ejecutó exitosamente
    """
    try:
        # Parsear datos
        task_data = json.loads(task.task_data)
        
        if task.task_type == "reminder_24h":
            return _execute_reminder_task(db, task, task_data)
        else:
            logger.error(f"Tipo de tarea desconocida: {task.task_type}")
            task.is_executed = True
            task.executed_at = datetime.utcnow()
            task.last_error = f"Unknown task type: {task.task_type}"
            db.commit()
            return False
            
    except Exception as e:
        logger.error(f"✗ Error ejecutando tarea {task.task_id}: {str(e)}", exc_info=True)
        
        # Registrar el error en la BD
        task.retry_count += 1
        task.last_error = str(e)
        
        # Marcar como ejecutada después de 3 reintentos
        if task.retry_count >= 3:
            task.is_executed = True
            task.executed_at = datetime.utcnow()
            logger.error(f"✗ Tarea {task.task_id} abortada tras 3 reintentos")
        
        db.commit()
        return False


def _execute_reminder_task(db: Session, task: models.ScheduledTask, task_data: dict) -> bool:
    """
    Ejecuta una tarea de recordatorio de reserva.
    
    Args:
        db: Sesión de base de datos
        task: Objeto ScheduledTask
        task_data: Datos de la tarea (diccionario)
        
    Returns:
        bool: True si ejecutó exitosamente
    """
    try:
        recipient_email = task_data.get("recipient_email")
        court_number = task_data.get("court_number")
        start_time_str = task_data.get("start_time_str")
        
        # Obtener usuario
        user = db.query(models.User).filter(
            models.User.user_id == task.user_id
        ).first()
        
        if not user:
            raise ValueError(f"Usuario {task.user_id} no encontrado")
        
        # Parsear fecha
        from datetime import datetime as dt_class
        start_time = dt_class.fromisoformat(start_time_str)
        
        # Generar y enviar email
        html_content = generate_reminder_email(
            user_name=user.name,
            court_number=court_number,
            start_time=start_time.strftime("%H:%M")
        )
        
        email_sent = send_email(
            to_email=recipient_email,
            subject="⏰ Recordatorio de tu reserva",
            html_content=html_content
        )
        
        # Registrar notificación
        create_notification_record(
            db=db,
            user_id=task.user_id,
            recipient_email=recipient_email,
            notification_type="reminder_24h",
            subject="⏰ Recordatorio de tu reserva",
            content=html_content,
            booking_id=task.booking_id,
            is_sent=email_sent
        )
        
        # Marcar tarea como ejecutada
        task.is_executed = True
        task.executed_at = datetime.utcnow()
        db.commit()
        
        if email_sent:
            logger.info(
                f"✓ Recordatorio enviado: booking_id={task.booking_id}, "
                f"email={recipient_email}, task_id={task.task_id}"
            )
        else:
            logger.warning(
                f"⚠️ Email de recordatorio no se envió (pero tarea marcada como ejecutada): "
                f"booking_id={task.booking_id}, email={recipient_email}"
            )
        
        return email_sent
        
    except Exception as e:
        logger.error(
            f"✗ Error ejecutando tarea de recordatorio {task.task_id}: {str(e)}",
            exc_info=True
        )
        
        # Registrar error
        task.retry_count += 1
        task.last_error = str(e)
        
        # Después de 3 reintentos, marcar como ejecutada (dar por fallida)
        if task.retry_count >= 3:
            task.is_executed = True
            task.executed_at = datetime.utcnow()
            logger.error(f"✗ Tarea {task.task_id} abortada tras 3 reintentos")
        
        db.commit()
        return False


def cancel_pending_task(db: Session, booking_id: int) -> bool:
    """
    Cancela una tarea programada pendiente (cuando se cancela una reserva).
    
    Args:
        db: Sesión de base de datos
        booking_id: ID de la reserva cuya tarea se va a cancelar
        
    Returns:
        bool: True si se encontró y canceló la tarea
    """
    try:
        task = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.booking_id == booking_id,
            models.ScheduledTask.is_executed == False
        ).first()
        
        if task:
            task.is_executed = True
            task.executed_at = datetime.utcnow()
            task.last_error = "Task cancelled due to booking cancellation"
            db.commit()
            
            logger.info(f"✓ Tarea programada cancelada: booking_id={booking_id}, task_id={task.task_id}")
            return True
        else:
            logger.info(f"⚠️ No se encontró tarea programada para booking {booking_id}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error cancelando tarea para booking {booking_id}: {str(e)}")
        return False


def get_task_statistics(db: Session) -> dict:
    """
    Obtiene estadísticas sobre las tareas programadas.
    
    Returns:
        dict: Estadísticas {
            "total_tasks": int,
            "executed": int,
            "pending_overdue": int,
            "pending_future": int,
            "failed": int
        }
    """
    try:
        total = db.query(models.ScheduledTask).count()
        executed = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.is_executed == True
        ).count()
        pending_overdue = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.is_executed == False,
            models.ScheduledTask.scheduled_for <= datetime.utcnow()
        ).count()
        pending_future = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.is_executed == False,
            models.ScheduledTask.scheduled_for > datetime.utcnow()
        ).count()
        failed = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.is_executed == True,
            models.ScheduledTask.last_error != None
        ).count()
        
        return {
            "total_tasks": total,
            "executed": executed,
            "pending_overdue": pending_overdue,
            "pending_future": pending_future,
            "failed": failed
        }
    except Exception as e:
        logger.error(f"✗ Error obteniendo estadísticas: {str(e)}")
        return {}

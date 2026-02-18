"""
Servicio de notificaciones para enviar emails a usuarios.
Soporta diferentes tipos de notificaciones:
- Confirmación de reserva
- Recordatorio 24h antes
- Cancelación de reserva
- Actualización de precios
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sqlalchemy.orm import Session
from .. import models
import os

logger = logging.getLogger(__name__)

# Configuración de email (se carga desde variables de entorno)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@courtrent.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Envía un email SMTP.
    
    Args:
        to_email: Dirección de correo del destinatario
        subject: Asunto del email
        html_content: Contenido HTML del email
        
    Returns:
        bool: True si se envió correctamente, False si hubo error
    """
    try:
        # Crear mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = to_email
        
        # Adjuntar contenido HTML
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Enviar email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        
        logger.info(f"Email enviado exitosamente a {to_email}: {subject}")
        return True
        
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP al enviar email a {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar email a {to_email}: {str(e)}")
        return False


def create_notification_record(
    db: Session,
    user_id: int,
    recipient_email: str,
    notification_type: str,
    subject: str,
    content: str,
    booking_id: int = None,
    scheduled_for: datetime = None,
    is_sent: bool = False
) -> models.Notification:
    """
    Crea un registro de notificación en la base de datos.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario destinatario
        recipient_email: Email del destinatario
        notification_type: Tipo de notificación ('booking_confirmation', 'reminder_24h', etc)
        subject: Asunto del email
        content: Contenido del email
        booking_id: ID de la reserva asociada (opcional)
        scheduled_for: Fecha/hora en la que se debe enviar (si es programada)
        is_sent: Si ya fue enviada
        
    Returns:
        models.Notification: Objeto de notificación creado
    """
    notification = models.Notification(
        user_id=user_id,
        booking_id=booking_id,
        notification_type=notification_type,
        subject=subject,
        content=content,
        recipient_email=recipient_email,
        scheduled_for=scheduled_for,
        is_sent=is_sent,
        sent_at=datetime.utcnow() if is_sent else None
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    logger.info(f"Notificación registrada: tipo={notification_type}, usuario={user_id}, reserva={booking_id}")
    
    return notification


def send_and_record_notification(
    db: Session,
    user_id: int,
    recipient_email: str,
    notification_type: str,
    subject: str,
    html_content: str,
    booking_id: int = None
) -> bool:
    """
    Envía un email Y crea el registro en la base de datos.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        recipient_email: Email del destinatario
        notification_type: Tipo de notificación
        subject: Asunto del email
        html_content: Contenido HTML del email
        booking_id: ID de la reserva (opcional)
        
    Returns:
        bool: True si se envió correctamente
    """
    # Intenta enviar el email
    email_sent = send_email(recipient_email, subject, html_content)
    
    # Registra la notificación independientemente de si se envió o no
    create_notification_record(
        db=db,
        user_id=user_id,
        recipient_email=recipient_email,
        notification_type=notification_type,
        subject=subject,
        content=html_content,
        booking_id=booking_id,
        is_sent=email_sent,
        scheduled_for=None
    )
    
    return email_sent


# ============================================================
# TEMPLATES DE EMAILS (Funciones que generan HTML)
# ============================================================

def generate_booking_confirmation_email(user_name: str, court_number: int, start_time: str, end_time: str, price: float) -> str:
    """Genera HTML para confirmación de reserva."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2ecc71; text-align: center;">✓ Reserva Confirmada</h2>
                
                <p>Hola <strong>{user_name}</strong>,</p>
                
                <p>Tu reserva ha sido confirmada exitosamente. Aquí están los detalles:</p>
                
                <div style="background-color: #f0f8ff; padding: 15px; border-left: 4px solid #2ecc71; margin: 20px 0;">
                    <p><strong>📍 Pista:</strong> Pista {court_number}</p>
                    <p><strong>📅 Fecha y Hora:</strong> {start_time} - {end_time}</p>
                    <p><strong>💰 Precio:</strong> ${price:.2f}</p>
                </div>
                
                <p style="color: #555; font-size: 14px;">
                    <strong>⚠️ Recuerda:</strong> Puedes cancelar tu reserva hasta 24 horas antes de la hora de inicio sin penalización.
                </p>
                
                <p>¡Disfruta tu actividad!</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">Court Rent - Sistema de Reservas</p>
            </div>
        </body>
    </html>
    """


def generate_reminder_email(user_name: str, court_number: int, start_time: str) -> str:
    """Genera HTML para recordatorio 24h antes."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #f39c12; text-align: center;">⏰ Recordatorio de Reserva</h2>
                
                <p>Hola <strong>{user_name}</strong>,</p>
                
                <p>Tu reserva está a pocas horas. ¡No olvides los detalles!</p>
                
                <div style="background-color: #fffacd; padding: 15px; border-left: 4px solid #f39c12; margin: 20px 0;">
                    <p><strong>📍 Pista:</strong> Pista {court_number}</p>
                    <p><strong>📅 Hora:</strong> Mañana a las {start_time}</p>
                </div>
                
                <p style="color: #555; font-size: 14px;">
                    Llega 10 minutos antes de tu horario. ¡Esperamos verte!
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">Court Rent - Sistema de Reservas</p>
            </div>
        </body>
    </html>
    """


def generate_cancellation_email(user_name: str, court_number: int, start_time: str, refund_amount: float) -> str:
    """Genera HTML para cancelación de reserva."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #e74c3c; text-align: center;">✗ Reserva Cancelada</h2>
                
                <p>Hola <strong>{user_name}</strong>,</p>
                
                <p>Tu reserva ha sido cancelada.</p>
                
                <div style="background-color: #ffe0e0; padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0;">
                    <p><strong>📍 Pista:</strong> Pista {court_number}</p>
                    <p><strong>📅 Fecha:</strong> {start_time}</p>
                    <p><strong>💰 Reembolso:</strong> ${refund_amount:.2f}</p>
                </div>
                
                <p style="color: #555; font-size: 14px;">
                    El reembolso será procesado en 3-5 días hábiles.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">Court Rent - Sistema de Reservas</p>
            </div>
        </body>
    </html>
    """


def generate_price_update_email(user_name: str, new_price: float, time_slot: str) -> str:
    """Genera HTML para notificación de cambio de precio."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #3498db; text-align: center;">💰 Actualización de Precios</h2>
                
                <p>Hola <strong>{user_name}</strong>,</p>
                
                <p>Nos complace informarte que hemos actualizado nuestras tarifas.</p>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <p><strong>⏰ Horario:</strong> {time_slot}</p>
                    <p><strong>💰 Nuevo Precio:</strong> ${new_price:.2f}</p>
                </div>
                
                <p style="color: #555; font-size: 14px;">
                    Consulta nuestra página de reservas para ver todos los horarios y precios actualizados.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">Court Rent - Sistema de Reservas</p>
            </div>
        </body>
    </html>
    """

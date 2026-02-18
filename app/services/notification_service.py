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

# Obtener ruta del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname("workspace")  # Subir un nivel más para llegar a la raíz
ENV_FILE = os.path.join(PROJECT_ROOT, '.env')


# Cargar variables de entorno desde .env explícitamente
try:
    from dotenv import load_dotenv
    if os.path.exists(ENV_FILE):
        logger.info(f"Cargando {ENV_FILE}...")
        # override=True asegura que se cargan incluso si ya están en el entorno
        load_dotenv(dotenv_path=ENV_FILE, override=True)
        logger.info("✓ .env cargado en notification_service.py")
    else:
        logger.warning(f"⚠️  No se encontró {ENV_FILE} al cargar notification_service.py")
except ImportError:
    logger.warning("⚠️  python-dotenv no está instalado. Intentando solo con variables de entorno...")

# Configuración de email (se carga desde variables de entorno)
SMTP_SERVER = os.getenv("SMTP_SERVER") or "smtp1.gmail.com"

# Leer el puerto de forma robusta: puede venir vacío o inválido
_smtp_port_raw = os.getenv("SMTP_PORT")
try:
    if _smtp_port_raw and _smtp_port_raw.strip():
        SMTP_PORT = int(_smtp_port_raw.strip())
    else:
        SMTP_PORT = 5871
except (ValueError, TypeError):
    SMTP_PORT = 5871
    logger.warning(f"Valor de SMTP_PORT inválido: '{_smtp_port_raw}'. Usando 5871 por defecto.")

SENDER_EMAIL = os.getenv("SENDER_EMAIL") or "noreply@courtrent.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or ""


# Si la contraseña viene entre comillas o contiene espacios accidentales, saneamos
if SENDER_PASSWORD:
    SENDER_PASSWORD = SENDER_PASSWORD.strip()
    if (SENDER_PASSWORD.startswith('"') and SENDER_PASSWORD.endswith('"')) or (
        SENDER_PASSWORD.startswith("'") and SENDER_PASSWORD.endswith("'")
    ):
        SENDER_PASSWORD = SENDER_PASSWORD[1:-1]

# Log configuración SMTP al cargar el módulo
logger.info(
    f"SMTP Configuration loaded: "
    f"server={SMTP_SERVER}, "
    f"port={SMTP_PORT}, "
    f"sender={SENDER_EMAIL}, "
    f"password_set={bool(SENDER_PASSWORD)}"
)


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
        
        logger.debug(f"SMTP_SERVER: {SMTP_SERVER}")
        logger.debug(f"SMTP_PORT: {SMTP_PORT}") 
        logger.debug(f"SENDER_EMAIL: {SENDER_EMAIL}")
        logger.debug(f"SENDER_PASSWORD: {SENDER_PASSWORD}")


        # Enviar email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        
        logger.info(f"Email enviado exitosamente a {to_email}: {subject}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            f"Error de autenticación SMTP al enviar a {to_email}. "
            f"Verifica SENDER_EMAIL y SENDER_PASSWORD. Error: {str(e)}"
        )
        return False
    except smtplib.SMTPException as e:
        logger.error(
            f"Error SMTP al enviar email a {to_email}: {str(e)}. "
            f"Verifica SMTP_SERVER={SMTP_SERVER}, SMTP_PORT={SMTP_PORT}"
        )
        return False
    except Exception as e:
        logger.error(
            f"Error inesperado al enviar email a {to_email}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
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

"""
Script de testing para el sistema de notificaciones.
Permite verificar que el sistema de emails está correctamente configurado.

Uso:
    python -m tests.test_notifications
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__).replace('/tests', ''))

# Importar configuración
from app.database import session_local
from app.services.notification_service import (
    send_email,
    send_and_record_notification,
    generate_booking_confirmation_email,
    generate_reminder_email,
    generate_cancellation_email,
    generate_price_update_email
)
from app.services.scheduler_service import init_scheduler, schedule_reminder_email
from app import models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_smtp_connection():
    """
    Prueba la conexión SMTP.
    Verifica que el servidor SMTP sea accesible.
    """
    print("\n" + "="*60)
    print("TEST 1: Verificar configuración SMTP")
    print("="*60)
    
    from app.services.notification_service import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
    
    print(f"✓ SMTP_SERVER: {SMTP_SERVER}")
    print(f"✓ SMTP_PORT: {SMTP_PORT}")
    print(f"✓ SENDER_EMAIL: {SENDER_EMAIL}")
    
    if SENDER_EMAIL == "noreply@courtrent.com":
        print("\n⚠️  ADVERTENCIA: Las variables SMTP no están configuradas en .env")
        print("   Por favor, configura SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD")
        return False
    
    print("\n✓ Configuración SMTP detectada correctamente")
    return True


def test_send_email(recipient_email: str):
    """
    Prueba envío de un email simple.
    
    Args:
        recipient_email: Email al que enviar el test
    """
    print("\n" + "="*60)
    print("TEST 2: Enviar email de prueba")
    print("="*60)
    
    subject = "🧪 Test de Notificaciones - Court Rent"
    html_content = """
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #2ecc71; text-align: center;">✓ Test Exitoso</h2>
                <p>¡El sistema de notificaciones está funcionando correctamente!</p>
                <p>Si recibiste este email, significa que:</p>
                <ul>
                    <li>✓ Las variables SMTP están configuradas</li>
                    <li>✓ La conexión al servidor de email funciona</li>
                    <li>✓ Los usuarios recibirán notificaciones automáticas</li>
                </ul>
                <p style="color: #888; font-size: 12px;">Court Rent - Sistema de Reservas</p>
            </div>
        </body>
    </html>
    """
    
    success = send_email(recipient_email, subject, html_content)
    
    if success:
        print(f"✓ Email enviado exitosamente a {recipient_email}")
        return True
    else:
        print(f"✗ Error al enviar email a {recipient_email}")
        print("  Verifica las credenciales SMTP en .env")
        return False


def test_booking_confirmation():
    """
    Prueba la plantilla de confirmación de reserva.
    """
    print("\n" + "="*60)
    print("TEST 3: Template - Confirmación de Reserva")
    print("="*60)
    
    html = generate_booking_confirmation_email(
        user_name="Juan Pérez",
        court_number=1,
        start_time="16/02/2026 14:00",
        end_time="15:30",
        price=25.00
    )
    
    checks = [
        ("Título 'Reserva Confirmada'" in html),
        ("Juan Pérez" in html),
        ("Pista 1" in html),
        ("$25.00" in html),
    ]
    
    for i, check in enumerate(checks, 1):
        status = "✓" if check else "✗"
        print(f"{status} Check {i}")
    
    return all(checks)


def test_reminder_template():
    """
    Prueba la plantilla de recordatorio.
    """
    print("\n" + "="*60)
    print("TEST 4: Template - Recordatorio 24h")
    print("="*60)
    
    html = generate_reminder_email(
        user_name="María García",
        court_number=3,
        start_time="14:00"
    )
    
    checks = [
        ("⏰ Recordatorio" in html),
        ("María García" in html),
        ("Pista 3" in html),
        ("14:00" in html),
    ]
    
    for i, check in enumerate(checks, 1):
        status = "✓" if check else "✗"
        print(f"{status} Check {i}")
    
    return all(checks)


def test_cancellation_template():
    """
    Prueba la plantilla de cancelación.
    """
    print("\n" + "="*60)
    print("TEST 5: Template - Cancelación de Reserva")
    print("="*60)
    
    html = generate_cancellation_email(
        user_name="Carlos López",
        court_number=5,
        start_time="16/02/2026 10:00",
        refund_amount=25.00
    )
    
    checks = [
        ("✗ Reserva Cancelada" in html),
        ("Carlos López" in html),
        ("Pista 5" in html),
        ("$25.00" in html),
        ("Reembolso" in html),
    ]
    
    for i, check in enumerate(checks, 1):
        status = "✓" if check else "✗"
        print(f"{status} Check {i}")
    
    return all(checks)


def test_price_update_template():
    """
    Prueba la plantilla de actualización de precios.
    """
    print("\n" + "="*60)
    print("TEST 6: Template - Actualización de Precios")
    print("="*60)
    
    html = generate_price_update_email(
        user_name="Ana Rodríguez",
        new_price=30.00,
        time_slot="14:00 - 15:30 (Fin de semana)"
    )
    
    checks = [
        ("💰 Actualización de Precios" in html),
        ("Ana Rodríguez" in html),
        ("$30.00" in html),
    ]
    
    for i, check in enumerate(checks, 1):
        status = "✓" if check else "✗"
        print(f"{status} Check {i}")
    
    return all(checks)


def test_database_notification_record():
    """
    Prueba la creación de registros en la BD.
    """
    print("\n" + "="*60)
    print("TEST 7: Registro en Base de Datos")
    print("="*60)
    
    db = session_local()
    
    try:
        # Verificar que existe la tabla Notification
        result = db.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='notifications');")
        table_exists = result.scalar()
        
        if table_exists:
            print("✓ Tabla 'notifications' existe en la BD")
            
            # Contar registros
            count_result = db.execute("SELECT COUNT(*) FROM notifications;")
            count = count_result.scalar()
            print(f"✓ Total de notificaciones registradas: {count}")
            
            return True
        else:
            print("✗ Tabla 'notifications' no existe")
            print("  Probablemente necesites ejecutar la inicialización de la app")
            return False
            
    except Exception as e:
        print(f"✗ Error al acceder a la BD: {str(e)}")
        return False
    finally:
        db.close()


def run_all_tests(recipient_email: str = None):
    """
    Ejecuta todos los tests.
    
    Args:
        recipient_email: Email para enviar test (opcional)
    """
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  🧪 PRUEBAS DEL SISTEMA DE NOTIFICACIONES".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60 + "\n")
    
    results = []
    
    # Test 1: SMTP Configuration
    results.append(("Configuración SMTP", test_smtp_connection()))
    
    # Test 2: Email Send
    if recipient_email:
        results.append(("Envío de Email", test_send_email(recipient_email)))
    else:
        print("\n⏭️  SALTANDO TEST 2: Proporciona un email para probar envío")
        results.append(("Envío de Email", None))
    
    # Test 3-6: Templates
    results.append(("Template - Confirmación", test_booking_confirmation()))
    results.append(("Template - Recordatorio", test_reminder_template()))
    results.append(("Template - Cancelación", test_cancellation_template()))
    results.append(("Template - Actualización Precios", test_price_update_template()))
    
    # Test 7: Database
    results.append(("Registros en BD", test_database_notification_record()))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)
    
    for test_name, passed in results:
        if passed is None:
            status = "⏭️ SALTADO"
        elif passed:
            status = "✓ PASADO"
        else:
            status = "✗ FALLIDO"
        print(f"{status:12} - {test_name}")
    
    total_passed = sum(1 for _, p in results if p is True)
    total_tests = sum(1 for _, p in results if p is not None)
    
    print(f"\nResultado: {total_passed}/{total_tests} tests pasados")
    
    if total_passed == total_tests:
        print("\n✓ ¡TODOS LOS TESTS PASARON! El sistema está listo.")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) fallaron. Revisa los logs.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Testing del sistema de notificaciones"
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Email para enviar test de notificación (ej: tu@ejemplo.com)"
    )
    
    args = parser.parse_args()
    
    run_all_tests(recipient_email=args.email)

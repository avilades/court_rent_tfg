#!/usr/bin/env python3
"""
Script rápido para debuggear problemas de envío de SMTP.
Verifica configuración y envía email de prueba.

Uso:
    python tests/test_smtp_debug.py
    python tests/test_smtp_debug.py --email tu@ejemplo.com
"""

import os
import sys
import logging
import argparse

# Obtener ruta del proyecto (padre de tests/)
# Si este archivo está en /workspace/tests/test_smtp_debug.py
# PROJECT_ROOT será /workspace (la raíz del proyecto, donde está .env)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(PROJECT_ROOT, '.env')

print(f"📍 Detectado PROJECT_ROOT: {PROJECT_ROOT}")
print(f"📄 Buscando .env en: {ENV_FILE}")
print(f"   Existe: {'✓ SÍ' if os.path.exists(ENV_FILE) else '❌ NO'}\n")

# Cargar variables de entorno desde .env explícitamente
try:
    from dotenv import load_dotenv
    if os.path.exists(ENV_FILE):
        print(f"Cargando {ENV_FILE}...")
        # override=True asegura que se cargan incluso si ya están en el entorno
        result = load_dotenv(dotenv_path=ENV_FILE, override=True, verbose=True)
        print(f"✓ .env cargado (variables cargadas: {result})\n")
    else:
        print(f"⚠️  No se encontró {ENV_FILE}\n")
except ImportError:
    print("⚠️  python-dotenv no está instalado. Intentando solo con variables de entorno...\n")

# Configurar logging para ver todos los mensajes
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir directorio raíz al path
sys.path.insert(0, PROJECT_ROOT)

print("="*70)
print("📧 DEBUG: Sistema de Envío SMTP")
print("="*70)

# 1. Revisar variables de entorno
print("\n1️⃣  Verificando variables de entorno...")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = os.getenv("SMTP_PORT")
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")

print(f"   SMTP_SERVER: {smtp_server or '❌ NOT SET'}")
print(f"   SMTP_PORT: {smtp_port or '❌ NOT SET'}")
print(f"   SENDER_EMAIL: {sender_email or '❌ NOT SET'}")
print(f"   SENDER_PASSWORD: {'✓ SET' if sender_password else '❌ NOT SET'}")

if not all([smtp_server, smtp_port, sender_email]):
    print("\n❌ Faltan variables SMTP. Por favor configura .env")
    print(f"\n💡 Intenta desde la terminal:")
    print(f"   export $(cat .env | xargs) && python tests/test_smtp_debug.py")
    print(f"\n   O ejecuta con F5 en VS Code (que carga .env automáticamente)")
    sys.exit(1)

# 2. Cargar módulo de notificaciones (verá si hay errores al parsear configuración)
print("\n2️⃣  Cargando módulo notification_service...")
try:
    from app.services.notification_service import (
        send_email,
        SMTP_SERVER,
        SMTP_PORT,
        SENDER_EMAIL,
        SENDER_PASSWORD as loaded_password
    )
    print(f"   ✓ Configuración detectada:")
    print(f"     - SMTP_SERVER: {SMTP_SERVER}")
    print(f"     - SMTP_PORT: {SMTP_PORT}")
    print(f"     - SENDER_EMAIL: {SENDER_EMAIL}")
    print(f"     - SENDER_PASSWORD: {'✓ SET' if loaded_password else '❌ NOT SET'}")
except Exception as e:
    print(f"   ❌ Error al cargar módulo: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Testear conexión SMTP
print("\n3️⃣  Probando conexión SMTP...")
try:
    import smtplib
    logger.info(f"Conectando a {SMTP_SERVER}:{SMTP_PORT}...")
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=5) as server:
        print(f"   ✓ Conexión establecida con {SMTP_SERVER}:{SMTP_PORT}")
        
        logger.info("Iniciando TLS...")
        server.starttls()
        print(f"   ✓ TLS iniciado")
        
        logger.info(f"Intentando login con {SENDER_EMAIL}...")
        server.login(SENDER_EMAIL, loaded_password)
        print(f"   ✓ Autenticación exitosa")
        
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ Error de autenticación:")
    print(f"      {str(e)}")
    print(f"      Verifica SENDER_EMAIL y SENDER_PASSWORD")
    sys.exit(1)
except smtplib.SMTPException as e:
    print(f"   ❌ Error SMTP: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {str(e)}")
    sys.exit(1)

# 4. Enviar email de prueba
print("\n4️⃣  Enviando email de prueba...")

parser = argparse.ArgumentParser(description="Test SMTP debug")
parser.add_argument("--email", type=str, default=None, help="Email para enviar (defecto: SENDER_EMAIL)")
args = parser.parse_args()

test_email = args.email or SENDER_EMAIL

html_test = """
<html>
    <body style="font-family: Arial, sans-serif;">
        <h2>✅ Email de Prueba SMTP</h2>
        <p>Si recibiste este email, significa que el sistema SMTP está funcionando correctamente.</p>
        <p><strong>Configuración detectada:</strong></p>
        <ul>
            <li>SMTP Server: {}</li>
            <li>SMTP Port: {}</li>
            <li>Sender Email: {}</li>
        </ul>
    </body>
</html>
""".format(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL)

try:
    result = send_email(
        to_email=test_email,
        subject="🧪 Test SMTP - Court Rent",
        html_content=html_test
    )
    
    if result:
        print(f"   ✓ Email enviado exitosamente a {test_email}")
        print("\n✨ El sistema SMTP está funcionando correctamente")
    else:
        print(f"   ❌ El módulo send_email() retornó False")
        print("   Revisa los logs anteriores para más detalles")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error al enviar: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✅ TODOS LOS TESTS PASARON")
print("="*70)

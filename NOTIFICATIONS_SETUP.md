# 📧 Sistema de Notificaciones por Email

Este documento explica cómo configurar y usar el sistema de notificaciones que se ha añadido a la aplicación Court Rent.

## 📋 Descripción General

El sistema de notificaciones envía emails automáticos a los usuarios en los siguientes eventos:

1. **Confirmación de Reserva** - Se envía inmediatamente después de hacer una reserva
2. **Recordatorio 24h** - Se envía automáticamente 24 horas antes de la reserva
3. **Cancelación** - Se envía cuando el usuario cancela una reserva
4. **Actualización de Precios** - Notifica cambios en las tarifas (uso futuro)

## 🔧 Configuración Necesaria

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

La nueva dependencia principal es **APScheduler** para programar tareas.

### 2. Configurar Variables de Entorno

Edita tu archivo `.env` en la raíz del proyecto y añade las siguientes variables:

```env
# ====== Configuración del Sistema de Notificaciones por Email ======
SMTP_SERVER=smtp.gmail.com      # Servidor SMTP
SMTP_PORT=587                   # Puerto SMTP
SENDER_EMAIL=tu_email@gmail.com # Email desde el que se enviarán notificaciones
SENDER_PASSWORD=tu_contraseña   # Contraseña de aplicación
```

### 3. Configurar Gmail (Recomendado)

Si usas Gmail, sigue estos pasos:

1. Abre https://myaccount.google.com/apppasswords
2. Selecciona "Correo" y "Windows Computer" (o tu dispositivo)
3. Google generará una contraseña de 16 caracteres
4. Usa esa contraseña en `SENDER_PASSWORD` (sin espacios)

**Nota:** Debes tener habilitada la verificación en dos pasos en tu cuenta de Gmail.

### 4. Usar Otro Proveedor de Email

Si prefieres usar otro servicio (SendGrid, Office 365, etc.):

```python
# Para Outlook/Office 365
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SENDER_EMAIL=tu_email@outlook.com

# Para SendGrid
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SENDER_EMAIL=apikey  # Siempre "apikey" para SendGrid
SENDER_PASSWORD=SG.xxxxx...  # Tu API key de SendGrid
```

## 🏗️ Arquitectura del Sistema

### Archivos Nuevos:

- **`app/services/notification_service.py`** - Servicio de envío de emails
- **`app/services/scheduler_service.py`** - Servicio de tareas programadas con APScheduler
- **`app/models.py`** (actualizado) - Modelo Notification para registrar el historial

### Flujo de Funcionamiento:

```
Usuario hace reserva
    ↓
1. Se crea la reserva en BD
    ↓
2. Se genera email HTML de confirmación
    ↓
3. Se intenta enviar el email (send_email)
    ↓
4. Se registra en la BD que se intentó enviar (Notification record)
    ↓
5. Se programa una tarea para enviar recordatorio 24h después
```

## 🚀 Flujos de Notificaciones

### Flujo de Confirmación + Recordatorio

```python
POST /bookings/book
├─ Crear reserva en BD
├─ Enviar email de confirmación (inmediato)
├─ Registrar intento de envío en BD
└─ Programar recordatorio para 24h antes
   └─ [24h después] Enviar recordatorio automáticamente
```

### Flujo de Cancelación

```python
POST /bookings/cancel/{booking_id}
├─ Verificar que el usuario es dueño
├─ Marcar reserva como cancelada
├─ Enviar email de cancelación
├─ Registrar intento de envío en BD
└─ Cancelar cualquier recordatorio programado
```

## 📊 Base de Datos

Nuevo modelo `Notification` en la tabla `notifications`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| notification_id | Integer | ID único |
| user_id | Integer | Usuario destinatario |
| booking_id | Integer | Reserva asociada (o NULL) |
| notification_type | String | Tipo: booking_confirmation, reminder_24h, cancellation, etc |
| subject | String | Asunto del email |
| content | String | Cuerpo HTML del email |
| recipient_email | String | Email del destinatario |
| is_sent | Boolean | ¿Se envió exitosamente? |
| sent_at | DateTime | Cuándo se envió |
| created_at | DateTime | Cuándo se creó el registro |
| scheduled_for | DateTime | Cuándo se envió (tareas programadas) |

## ⚙️ Funciones Principales

### `send_email(to_email, subject, html_content)`
Envía un email SMTP.
- Retorna `True` si tuvo éxito
- Retorna `False` si hubo error SMTP

### `send_and_record_notification(...)`
Envía un email Y registra el intento en BD.
- Única llamada necesaria para notificaciones síncronas

### `schedule_reminder_email(booking_id, user_id, ...)`
Programa un recordatorio para 24h antes de la reserva.
- Usa APScheduler automáticamente
- Se ejecuta a la hora exacta programada

## ⚠️ Manejo de Errores

El sistema está diseñado para ser resiliente:

- Si falla el envío de email, se registra el intento fallido
- Si falla la programación de un recordatorio, se loguea el error pero no rompe la reserva
- Los emails son sin-sincronos (no bloquean la API)

Todos los errores se registran en los logs en `logs/app.log`

## 🧪 Testing

Para probar el sistema de notificaciones:

```bash
# 1. Asegúrate de que .env tiene las credenciales SMTP correctas
# 2. Inicia la aplicación
docker-compose up

# 3. Haz una reserva a través de la API/interfaz web
# 4. Deberías recibir un email de confirmación en pocos segundos

# 5. Espera 24h (o cambia la hora del servidor para testing)
# 6. Recibirás automáticamente el recordatorio
```

## 🔍 Debugging

Para ver si los emails se están enviando correctamente:

```bash
# Ver logs de la aplicación
docker-compose logs app | grep -i notification

# Ver la tabla de notificaciones en BD
# Abre pgAdmin en http://localhost:5050
# Query: SELECT * FROM notifications ORDER BY created_at DESC;
```

## 📝 Próximos Mejoras Posibles

1. **Cola de Email con Celery**: Para proyectos más grandes, usar Celery + Redis
2. **Templates HTML mejorados**: Agregar logos, estilos más profesionales
3. **Notificaciones SMS**: Integrar Twilio para alertas por SMS
4. **Preferencias del Usuario**: Permitir que usuarios elijan qué notificaciones reciben
5. **Integración con terceros**: SendGrid, Mailgun, AWS SES para producción

## 🚨 Limitaciones Actuales

- **Sin cola de mensajes**: Las tareas se programan en memoria (APScheduler). Si reinicia la app, se pierden las tareas pendientes. Para producción, usar Celery + Redis.
- **Sin validación de bounce**: No detecta emails inválidos automáticamente.
- **Sin tracking de open/click**: No sabe si el usuario abrió el email.

## 💡 Notas de Implementación

- APScheduler se inicializa en `app/main.py` en el evento `startup`
- El scheduler se detiene automáticamente en el evento `shutdown`
- Las credenciales SMTP se cargan desde `.env` en `notification_service.py`
- Los templates HTML se generan dinámicamente en funciones de `notification_service.py`

---

**Versión**: 1.0  
**Fecha**: Febrero 2026  
**Autor**: Sistema de Notificaciones Court Rent

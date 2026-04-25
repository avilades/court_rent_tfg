# 🔧 Sistema Mejorado de Tareas Programadas - Guía de Debugging

## ❌ Problema Identificado

Los recordatorios automáticos de 24 horas **no se estaban enviando** porque:

1. **APScheduler con BackgroundScheduler no persiste datos** - Si la app se reinicia, se pierden todos los recordatorios programados
2. **Sin mecanismo de reintentos** - Si falla el envío, no hay forma de recuperarse
3. **Difícil de debuggear** - Sin visibilidad sobre qué tareas estaban programadas o fallaron
4. **Sin recuperación tras reinicios** - Los recordatorios de hace 24+ horas desaparecían si reiniciaba Docker

## ✅ Solución Implementada

Se reemplazó APScheduler + BackgroundScheduler con un sistema híbrido más robusto:

### Arquitectura Nueva:

```
Reserva creada
    ↓
1. schedule_reminder_task() [task_service.py]
    ↓
2. Crea registro en tabla scheduled_tasks (BD)
    ↓
3. Task Worker polls cada 60 segundos
    ↓
4. Encuentra tareas que ya deben ejecutarse
    ↓
5. process_pending_tasks() ejecuta las tareas
    ↓
6. Envía emails + registra en notifications
    ↓
7. Marca tarea como ejecutada en BD
```

### Cambios en la Base de Datos:

**Tabla nueva: `scheduled_tasks`**
```sql
- task_id (Integer, PK)
- user_id (Integer, FK)
- booking_id (Integer, FK)
- task_type (String): 'reminder_24h', etc.
- scheduled_for (DateTime): Cuándo ejecutar
- task_data (JSON): Datos para ejecutar la tarea
- is_executed (Boolean): ¿Ya se ejecutó?
- executed_at (DateTime): Cuándo se ejecutó
- retry_count (Integer): Número de reintentos
- last_error (String): Último mensaje de error
- created_at (DateTime): Registro creado
```

## 🚀 Cómo Funciona Ahora

### 1. Crear una Reserva
```
POST /bookings/book
├─ Crea reserva en BD
├─ Envía confirmación inmediata
└─ Crea tarea en scheduled_tasks para 24h antes
   (ejemplo: reserva a 2026-02-20 14:00 → tarea programada 2026-02-19 14:00)
```

### 2. Task Worker Procesa Tareas
El worker (`app/workers/task_worker.py`) corre continuamente:
```python
Cada 60 segundos:
├─ Consulta BD para tareas with scheduled_for <= ahora AND is_executed=False
├─ Ejecuta cada tarea
├─ Registra resultado
└─ Marca como ejecutada (o reintenta si falla)
```

### 3. Recuperación Automática tras Reinicios
Al iniciar la app:
```python
1. init_scheduler() - inicia el APScheduler (para reintentos)
2. process_pending_tasks() - ejecuta cualquier tarea que haya quedado pendiente
   → Esto recupera tareas que se programaron durante el downtime
```

## 📊 Flujo Completo de Recordatorio

```
Hora 0: Usuario crea reserva para hora 24
├─ Se crea en scheduled_tasks con scheduled_for = hora 23 (24h antes)

Hora 10: Task Worker revisa tareas (no hay nada pendiente)
├─ Log: "📊 Estado: 1 pendiente"

Hora 23:00: Task Worker revisa tareas
├─ ¡Encuentra 1 tarea vencida!
├─ Ejecuta _execute_reminder_task()
├─ Envía email al usuario
├─ Registra en notifications tabla
├─ Marca scheduled_tasks.is_executed = True
└─ Log: "✓ Recordatorio enviado: booking_id=123, email=user@example.com"

Hora 24:00: Usuario recibe recordatorio 1 hora antes
```

## 🛠️ Endpoints para Debugging

### Ver Estadísticas de Tareas (Admin)
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/admin/tasks/stats
```

Response:
```json
{
  "scheduled_tasks": {
    "total_tasks": 42,
    "executed": 38,
    "pending_overdue": 2,        ← ⚠️ Problemas aquí
    "pending_future": 2,
    "failed": 1
  }
}
```

### Procesar Tareas Manualmente (Admin)
```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/admin/tasks/process
```

Response:
```json
{
  "message": "Tareas procesadas",
  "statistics": {
    "total_processed": 2,
    "successful": 2,
    "failed": 0,
    "still_pending": 5
  }
}
```

## 🐛 Debugging - Qué Revisar

### 1. Verificar que la Tarea se Creó
```sql
-- En pgAdmin, query:
SELECT * FROM scheduled_tasks 
WHERE booking_id = 123
ORDER BY created_at DESC;
```

**Debería mostrar:**
- task_type = 'reminder_24h'
- is_executed = false
- scheduled_for = fecha de la reserva - 24 horas

### 2. Ver si la Tarea se Ejecutó
```sql
SELECT * FROM scheduled_tasks 
WHERE booking_id = 123;
```

**Después de que pase la hora:**
- is_executed = true
- executed_at = fecha/hora actual
- last_error = NULL (si fue exitoso)

### 3. Revisar Logs del Task Worker
```bash
# En Docker:
docker-compose logs task_worker -f

# Debería mostrar:
# "⏳ Encontradas 2 tareas vencidas. Procesando..."
# "✓ Recordatorio enviado"
```

### 4. Revisar Tabla notifications
```sql
SELECT * FROM notifications 
WHERE booking_id = 123
ORDER BY created_at DESC;
```

**Debería mostrar:**
- notification_type = 'reminder_24h'
- is_sent = true
- sent_at = fecha/hora

## 🚨 Si Los Recordatorios AÚN NO van

Hazlo en este orden:

### Paso 1: Verificar SMTP
```bash
python tests/test_notifications.py --email tu_email@ejemplo.com
```

Debe decir "✓ Email enviado exitosamente"

### Paso 2: Verificar que Task Worker está corriendo
```bash
docker-compose ps
```

Debería ver:
```
court_rent-task_worker-1  python app/workers/task_worker.py 60  Up
```

Si dice "Exited", revisa los logs:
```bash
docker-compose logs task_worker
```

### Paso 3: Verificar que la Tarea se creó
En pgAdmin, ejecutar:
```sql
SELECT COUNT(*) FROM scheduled_tasks;
```

Debería ser > 0 si has hecho al menos 1 reserva

### Paso 4: Hacer que el Worker Procese Tareas Manualmente
```bash
# Via API (si eres admin):
curl -X POST http://localhost:8000/admin/tasks/process \
  -H "Authorization: Bearer YOUR_TOKEN"

# O directamente en Python:
python -c "
from app.database import session_local
from app.services.task_service import process_pending_tasks
db = session_local()
result = process_pending_tasks(db)
print(result)
"
```

### Paso 5: Revisar Logs de la Aplicación
```bash
docker-compose logs app -f
```

Busca líneas con "Recordatorio" o errores

## 📅 Cómo Testear Sin Esperar 24 Horas

### Opción 1: Crear Tarea Manualmente
```python
# En un script o terminal Python:
from app.database import session_local
from app.services.task_service import schedule_reminder_task
from datetime import datetime, timedelta

db = session_local()

# Programar para 5 minutos desde ahora (en lugar de 24h)
now = datetime.utcnow()
in_five_minutes = now + timedelta(minutes=5)

schedule_reminder_task(
    db=db,
    booking_id=999,
    user_id=1,
    recipient_email="test@example.com",
    court_number=1,
    start_time=in_five_minutes + timedelta(hours=24)  # Reserva en 24.08 horas
)

# Esperar 5 minutos...
# Luego ejecutar:
# python -c "from app.database import session_local; from app.services.task_service import process_pending_tasks; db = session_local(); print(process_pending_tasks(db))"
```

### Opción 2: Modificar scheduled_for Directamente
```sql
-- En pgAdmin:
UPDATE scheduled_tasks 
SET scheduled_for = NOW() 
WHERE task_id = 1;

-- Luego ejecutar:
-- curl -X POST http://localhost:8000/admin/tasks/process -H "Authorization: Bearer TOKEN"
```

## 📝 Resumen de Cambios

| Archivo | Cambio |
|---------|--------|
| `app/models.py` | + Tabla `ScheduledTask` para persistencia |
| `app/services/task_service.py` | NUEVO: Gestión de tareas en BD |
| `app/services/scheduler_service.py` | Mantiene APScheduler (para reintentos) |
| `app/routers/bookings.py` | Usa `schedule_reminder_task()` en lugar de `schedule_reminder_email()` |
| `app/routers/admin.py` | + Endpoints para ver/procesar tareas |
| `app/main.py` | Procesa tareas pendientes en startup |
| `app/workers/task_worker.py` | NUEVO: Worker que procesa tareas periodicamente |
| `docker-compose.yml` | + Servicio `task_worker` |

## ✨ Ventajas del Nuevo Sistema

✅ **Persistencia** - Tareas guardadas en BD, sobreviven a reinicios  
✅ **Observabilidad** - Puedes ver qué tareas hay, cuáles fallaron  
✅ **Reintentos** - Reintenta 3 veces antes de abandonar  
✅ **Recuperación** - Al iniciar, procesa tareas pendientes del downtime  
✅ **Escalable** - Puedes tener múltiples workers en paralelo  
✅ **Testeable** - Fácil de debuggear con SQL queries  
✅ **Sin dependencias pesadas** - No requiere Redis, RabbitMQ, etc.

## 🚀 Próximos Pasos Opcionales

Para un sistema aún más robusto:

1. **Celery + Redis**: Para distribución en múltiples workers
2. **Sentry**: Para logging de errores centralizadoó
3. **APScheduler con SQLAlchemy jobstore**: Guardar jobs de APScheduler en BD
4. **Temporal**: Orquestación avanzada de tareas (enterprise)

---

**Versión**: 2.0 (Sistema Persistente)  
**Fecha**: Febrero 2026

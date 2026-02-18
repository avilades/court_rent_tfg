# Court Rent Application 🎾

Aplicación web para la gestión de alquiler de pistas deportivas.
Desarrollada con **FastAPI**, **SQLAlchemy**, **PostgreSQL** y **Docker**.

## Prerrequisitos

*   Docker y Docker Compose instalados.

## Cómo ejecutar el proyecto

1.  **Configuración Inicial**:
    *   Crea un archivo `.env` en la raíz del proyecto (puedes copiar `.env.example`).
    *   Asegúrate de configurar las variables necesarias (DATABASE_URL, etc).

2.  **Arrancar con Docker**:
    Desde la raíz del proyecto, ejecuta:

    ```bash
    docker-compose up --build
    ```

    Esto levantará tanto la base de datos PostgreSQL como la aplicación web.

3.  Abre tu navegador en: [http://localhost:8000](http://localhost:8000)



## Acceso a la Base de Datos (pgAdmin)

La aplicación incluye pgAdmin 4 preconfigurado para gestionar la base de datos.

1.  Accede a: [http://localhost:5050](http://localhost:5050)
2.  Inicia sesión en pgAdmin con:
    *   **Email**: `admin@admin.com`
    *   **Password**: `root`
3.  Añade un nuevo servidor ("Add New Server") con los siguientes datos:
    *   **General** > **Name**: `Court Rent DB` (o el que prefieras)
    *   **Connection** > **Host name/address**: `db` (o `localhost` si conectas desde fuera de docker)
    *   **Connection** > **Port**: `5432`
    *   **Connection** > **Username**: `user`
    *   **Connection** > **Password**: `password`
    *   **Connection** > **Maintenance database**: `court_rent`

## Funcionalidades

*   **Usuarios**: Registro y Login con autenticación JWT.
*   **Reservas**:
    *   Búsqueda de pistas disponibles por día y hora.
    *   Tramos de 90 minutos configurables.
    *   Cálculo dinámico de precios basado en demanda (Alta, Media, Baja).
    *   Cancelación de reservas (política de cancelación de 24h).
*   **Administración**:
    *   Panel de control centralizado (`/admin`).
    *   Gestión de tarifas con histórico de precios (versionado).
    *   Estadísticas de ocupación e ingresos en tiempo real.
    *   Mantenimiento de pistas (activación/desactivación).
*   **Persistencia**: Base de datos PostgreSQL con diseño relacional completo.

## Estructura del Código

El código está organizado siguiendo las mejores prácticas de FastAPI:

*   `app/main.py`: Punto de entrada y configuración.
*   `app/models.py`: Definición de las tablas (SQLAlchemy).
*   `app/routers/`: Módulos de la API (`auth`, `bookings`, `admin`).
*   `tests/`: Scripst de utilidad y pruebas.
*   `app/templates.py`: Configuración centralizada de Jinja2.

## Documentación Detallada

Para más información, consulta los siguientes documentos:
Para más información, consulta los siguientes documentos en este repositorio:
- 📄 [Project documentation](PROJECT_DOCUMENTATION.md): Detalle técnico de clases y funciones.
- ⚡ [Application flow](APPLICATION_FLOW.md): Diagramas de flujo y recorridos de usuario.

## Task worker & reminders

El sistema de recordatorios se persiste en la base de datos (tabla `scheduled_tasks`) y se procesa mediante un worker independiente.
Revisa `app/services/task_service.py` y `app/workers/task_worker.py` para la implementación principal.

Puedes ejecutar el worker de estas formas:

```bash
# Levantar toda la pila (recomendado):
docker-compose up --build

# Levantar solo el servicio worker (si está definido en docker-compose):
docker-compose up task_worker

# Ejecutar el worker directamente (dev):
python app/workers/task_worker.py 60
```

Variables de entorno relevantes para el envío de emails (añadir en tu `.env`):

- `SMTP_SERVER` (e.g. `smtp.gmail.com`)
- `SMTP_PORT` (e.g. `587`)
- `SENDER_EMAIL`
- `SENDER_PASSWORD`

Consulta `NOTIFICATIONS_SETUP.md` para más detalles de configuración.

## Usuarios de Prueba

Para acceder como administrador:
- **Email**: `admin@admin.com`
- **Password**: `admin123` (Configurado en la inicialización)

Puedes registrar un nuevo usuario en la pantalla de inicio. Por defecto tendrá permisos para alquilar.
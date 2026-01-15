# Court Rent Application 🎾

Aplicación web para la gestión de alquiler de pistas deportivas.
Desarrollada con **FastAPI**, **SQLAlchemy**, **PostgreSQL** y **Docker**.

## Prerrequisitos

*   Docker Desktop instado y corriendo.
*   VS Code con la extensión "Dev Containers".

## Cómo ejecutar el proyecto

1.  Abre esta carpeta en VS Code.
2.  Cuando aparezca la notificación "Folder contains a Dev Container configuration file...", haz clic en **Reopen in Container**.
    *   Alternativamente: `F1` > `Dev Containers: Reopen in Container`.
3.  Espera a que se construya el contenedor (la primera vez puede tardar unos minutos).
4.  Una vez dentro, abre una terminal integrada y ejecuta:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5.  Abre tu navegador en: [http://localhost:8000](http://localhost:8000)

## Acceso a la Base de Datos (pgAdmin)

La aplicación incluye pgAdmin 4 preconfigurado para gestionar la base de datos.

1.  Accede a: [http://localhost:5050](http://localhost:5050)
2.  Inicia sesión en pgAdmin con:
    *   **Email**: `admin@admin.com`
    *   **Password**: `root`
3.  Añade un nuevo servidor ("Add New Server") con los siguientes datos:
    *   **General** > **Name**: `Court Rent DB` (o el que prefieras)
    *   **Connection** > **Host name/address**: `db`
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
*   `app/crud.py`: Operaciones de base de datos.
*   `app/templates.py`: Configuración centralizada de Jinja2.

## Documentación Detallada

Para más información, consulta los siguientes documentos:
- 📄 [PROJECT_DOCUMENTATION.md](file:///d:/GIT/court_rent_tfg/PROJECT_DOCUMENTATION.md): Detalle técnico de clases y funciones.
- ⚡ [APPLICATION_FLOW.md](file:///d:/GIT/court_rent_tfg/APPLICATION_FLOW.md): Diagramas de flujo y recorridos de usuario.

## Usuarios de Prueba

Para acceder como administrador:
- **Email**: `admin@admin.com`
- **Password**: `admin123` (Configurado en la inicialización)

Puedes registrar un nuevo usuario en la pantalla de inicio. Por defecto tendrá permisos para alquilar.
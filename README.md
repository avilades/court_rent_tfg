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

*   **Usuarios**: Registro y Login.
*   **Reservas**:
    *   Búsqueda de pistas disponibles por día y hora.
    *   Tramos de 90 minutos (8:00 - 23:00).
    *   Cancelación de reservas (política de cancelación de 24h).
*   **Persistencia**: Base de datos PostgreSQL con volumen persistente.

## Estructura del Código

El código está ampliamente comentado para fines educativos.

*   `app/models.py`: Definición de las tablas de base de datos.
*   `app/routers/`: Endpoints de la API divididos por funcionalidad.
*   `app/crud.py`: Lógica de acceso a datos.

## Usuarios de Prueba

Puedes registrar un nuevo usuario en la pantalla de inicio. Por defecto tendrá permisos para alquilar.
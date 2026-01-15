# Documentación del Proyecto: Reserva de Pistas

Este documento proporciona una visión detallada de la estructura del proyecto, los archivos que lo componen y la funcionalidad de cada clase y función.

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

- `app/`: Directorio principal de la aplicación.
    - `routers/`: Contiene los endpoints de la API organizados por módulos.
    - `static/`: Archivos estáticos (CSS, JS).
    - `templates/`: Plantillas HTML para el frontend.
- `logs/`: Directorio donde se almacenan los archivos de log.
- `requirements.txt`: Dependencias del proyecto.
- `reset_db.py`: Script para resetear la base de datos.

---

## Núcleo de la Aplicación (`app/`)

### `main.py`
Punto de entrada de la aplicación FastAPI. Configura la aplicación, monta archivos estáticos, incluye los routers y maneja el evento de inicio.

- **Funciones:**
    - `startup_event()`: Se ejecuta al iniciar la aplicación. Inicializa la conexión a la base de datos y carga los datos por defecto (admin, demandas, precios, pistas, horarios).
    - `home(request)`: Renderiza la página de login.
    - `register_page(request)`: Renderiza la página de registro.
    - `dashboard(request)`: Renderiza el panel principal para los usuarios.
    - `book_page(request)`: Renderiza la página para realizar reservas.
    - `reservations_page(request)`: Renderiza la página de mis reservas.
    - `admin_page(request)`: Renderiza el panel de administración.

### `models.py`
Define los modelos de la base de datos utilizando SQLAlchemy. Representa las tablas de la base de datos a través de clases orientadas a objetos.

- **Clases:**
    - `User`: Representa a un usuario registrado.
    - `Permission`: Almacena los permisos específicos para cada usuario (isAdmin, canRent, etc.).
    - `Court`: Representa una pista deportiva.
    - `Demand`: Almacena la relación entre tipos de demanda (alta, media, baja) y sus descripciones.
    - `Price`: Histórico de precios asociados a tipos de demanda.
    - `Schedule`: Define los slots de disponibilidad semanal.
    - `Holiday`: Excepciones de fechas (festivos).
    - `Booking`: Representa una reserva realizada por un usuario.

### `schemas.py`
Define los esquemas de Pydantic para la validación de datos y la serialización JSON. Actúa como el contrato entre la API y el cliente.

- **Clases:**
    - `UserBase`, `UserCreate`, `UserResponse`: Modelos para el manejo de datos de usuario.
    - `PermissionResponse`: Esquema para devolver los permisos de un usuario.
    - `Token`, `TokenData`: Esquemas para el manejo de autenticación JWT.
    - `CourtResponse`: Esquema para información de pistas.
    - `SlotBase`: Esquema para representar la disponibilidad de slots y su precio.
    - `BookingCreate`, `BookingResponse`: Modelos para la creación y visualización de reservas.

### `crud.py`
Contiene las operaciones "Create, Read, Update, Delete" sobre la base de datos. Centraliza la lógica de interacción con el motor de base de datos.

- **Funciones:**
    - `get_user_by_email(db, email)`: Busca un usuario por su correo electrónico.
    - `create_user(db, user)`: Registra un nuevo usuario y le asigna permisos por defecto.
    - `get_courts(db)`: Obtiene la lista de todas las pistas.
    - `get_user_bookings(db, user_id, date_from, date_to)`: Recupera las reservas de un usuario con filtros opcionales de fecha.
    - `create_booking(db, booking_data, user_id)`: Procesa la creación de una reserva, verificando conflictos y asignando el precio activo.
    - `cancel_booking_logic(db, booking_id, user_id)`: Marca una reserva como cancelada.

### `database.py`
Configura la conexión a la base de datos PostgreSQL, el motor (engine) y la factoría de sesiones.

- **Funciones:**
    - `get_db()`: Dependencia que cede una sesión de base de datos y la cierra al finalizar la petición.

### `dependencies.py`
Contiene utilidades y dependencias para la seguridad y el manejo de tokens JWT.

- **Funciones:**
    - `get_current_user(token, db)`: Decodifica un token JWT, valida el usuario y lo devuelve.
    - `get_current_active_user(current_user)`: Valida si el usuario actual está activo.

### `initialize.py`
Script de inicialización de datos base para la aplicación (semilla de datos).

- **Funciones:**
    - `initialize_admin_user(db)`: Crea el usuario administrador por defecto.
    - `initialize_demands(db)`: Crea los niveles de demanda (Alta, Media, Baja).
    - `initialize_prices(db)`: Crea los precios iniciales asociados a las demandas.
    - `initialize_courts(db)`: Registra las pistas disponibles.
    - `initialize_schedules(db)`: Genera los horarios semanales para todas las pistas.

### `logging_config.py`
Configura el sistema de logs de la aplicación.

- **Funciones:**
    - `setup_logging()`: Configura la rotación diaria de archivos de log con el formato `court_reservation_YYYYMMDD.log`.

---

## Routers de la API (`app/routers/`)

### `auth.py`
Endpoints para la autenticación y registro de usuarios.

- **Funciones:**
    - `register(user, db)`: Ruta para el registro de nuevos usuarios.
    - `login(form_data, db)`: Ruta para obtener el token de acceso JWT.

### `bookings.py`
Endpoints relacionados con la gestión de reservas y búsqueda de disponibilidad.

- **Funciones:**
    - `read_my_bookings(date_from, date_to, current_user, db)`: Devuelve las reservas del usuario actual.
    - `book_court(booking, current_user, db)`: Realiza una nueva reserva.
    - `search_available_slots(date, db)`: Busca slots libres y sus precios para una fecha específica.
    - `cancel_booking(booking_id, current_user, db)`: Cancela una reserva existente.

### `admin.py`
Endpoints para tareas administrativas.

- **Funciones:**
    - `create_price(price, description, current_user, db)`: (Simulado) Creación de nuevos precios.
    - `reset_database(db)`: DANGER: Elimina y recrea todas las tablas de la base de datos.

### `users.py`
Router reservado para futuras implementaciones de gestión de perfiles de usuario.

---

## Otros Archivos

### `reset_db.py`
Script independiente para limpiar y recrear la estructura de la base de datos desde la línea de comandos.

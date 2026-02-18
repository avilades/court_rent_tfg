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
- `tests/reset_db.py`: Script para resetear la base de datos.
- `.env`: Variables de entorno (secreto).
- `.env.example`: Ejemplo de variables de entorno.
- `Dockerfile`: Definición de la imagen Docker de la app.
- `docker-compose.yml`: Orquestación de servicios (App + DB).

---

## Configuración y Variables de Entorno

### `.env`
Archivo ubicado en la raíz del proyecto (no subido a git) que contiene secretos y configuraciones sensibles.
- `OPENWEATHER_API_KEY`: Clave de API para OpenWeatherMap.
- `SECRET_KEY`: Clave secreta para firmar tokens JWT.
- `ALGORITHM`: Algoritmo de encriptación (ej. HS256).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración de la sesión.
- `DATABASE_URL`: String de conexión a la base de datos.

### `app/conf/config.json`
Archivo JSON para configuraciones generales de la aplicacion que pueden ser versionadas.
- Coordenadas por defecto (Latitud/Longitud).
- Otros parámetros de negocio no críticos.

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

### `templates.py` [NEW]
Centraliza la configuración del motor de plantillas Jinja2 para evitar dependencias circulares entre `main.py` y los routers.

- **Objetos:**
    - `templates`: Instancia de `Jinja2Templates` apuntando al directorio `app/templates`.

### `weather_service.py` [NEW]
Servicio encargado de la integración con la API de OpenWeatherMap.
- **Funciones:**
    - `get_weather_prediction(date_str)`: Obtiene la predicción del clima para una fecha dada.
    - `_get_mock_weather(target_date)`: Genera datos simulados si la API falla o no hay key.
    - `initialize_config()`: Carga configuración inicial desde `app/conf/config.json`.

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
Centraliza todos los endpoints relacionados con la administración del sistema, tanto de interfaz (HTML) como de API (JSON).

- **Funciones de Interfaz (HTML):**
    - `admin_page(request)`: Renderiza el panel de administración principal.
    - `admin_stats_page(request)`: Renderiza la página de analíticas.
    - `price_page(request)`: Renderiza la página de gestión de precios.
    - `admin_reservas_page(request)`: Renderiza la página con el histórico total de reservas.

- **Funciones de API (JSON/Operaciones):**
    - `get_prices(current_user, db)`: Lista todos los precios vigentes.
    - `update_price(data, current_user, db)`: Actualiza un precio con lógica de versionado (cierra el antiguo, crea uno nuevo).
    - `get_stats_data(current_user, db)`: Calcula estadísticas de uso, ingresos y ocupación por pista.
    - `list_courts(current_user, db)`: Lista todas las pistas y su estado.
    - `toggle_maintenance(court_id, current_user, db)`: Activa/Desactiva el estado de mantenimiento de una pista.
    - `get_daily_bookings(date, current_user, db)`: Lista detallada de reservas para un día específico.
    - `reset_database(current_user, db)`: **⚠️ PELIGRO**: Borra y recrea todas las tablas del sistema (solo desarrollo).
    - `list_users(current_user, db)`: [NEW] Lista todos los usuarios registrados.
    - `reset_user_password(data, current_user, db)`: [NEW] Resetea la contraseña de un usuario específico.

### `users.py`
Router reservado para futuras implementaciones de gestión de perfiles de usuario.

---

## Otros Archivos

### `tests/reset_db.py`
Script independiente para limpiar y recrear la estructura de la base de datos desde la línea de comandos.

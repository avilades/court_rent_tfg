from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging

from . import models, database, dependencies
from .routers import auth, bookings, admin, users
from .initialize import initialize_schedules, initialize_prices, initialize_courts, initialize_admin_user, initialize_demands
from .logging_config import setup_logging
from .templates import templates
from .conf.config_json import initialize_lat_lon
from .services.scheduler_service import init_scheduler, shutdown_scheduler
initialize_lat_lon()  # Cargamos la configuración al iniciar la aplicación
# --- Configuración Inicial ---

# Inicializamos el sistema de logs (registro de eventos)
setup_logging()

# Crear las tablas de la base de datos si no existen.
# Nota: En sistemas de producción reales es mejor usar herramientas como Alembic para migraciones.
models.Base.metadata.create_all(bind=database.engine)

# Instanciamos la aplicación FastAPI
app = FastAPI(title="Reserva de Pistas")

# Montamos la carpeta de archivos estáticos (CSS, Imágenes, JS) para que sean accesibles vía URL
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# --- Inclusión de Routers para organizar la API ---
app.include_router(auth.router)     # Rutas de autenticación (login/registro)
app.include_router(bookings.router) # Rutas de gestión de reservas
app.include_router(admin.router)    # Rutas de administración

# --- Middleware de Logging de Peticiones ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware global que intercepta cada petición HTTP para registrarla en el log.
    Captura: Método, Ruta, Dirección IP, Parámetros, Cuerpo, Código de estado y Tiempo de proceso.
    """
    import time
    start_time = time.time()
    
    # 1. Obtener información básica
    client_ip = request.client.host if request.client else "unknown"
    query_params = dict(request.query_params)
    
    # 2. Capturar el cuerpo de la petición de forma segura
    body = b""
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        # Re-inyectamos el cuerpo en el canal de recepción para que FastAPI pueda leerlo después
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive

    # Loguear la petición entrante con todos sus detalles
    log_msg = f">>> Petición: {request.method} {request.url.path} | IP: {client_ip}"
    if query_params:
        log_msg += f" | QueryParams: {query_params}"
    if body:
        # Intentamos decodificar como texto, si falla lo dejamos como bytes truncados
        try:
            log_msg += f" | Body: {body.decode('utf-8')}"
        except:
            log_msg += f" | Body: <binary data: {len(body)} bytes>"
    
    logging.debug(log_msg)

    # 3. Procesar la petición
    response = await call_next(request)

    # 4. Información de la respuesta saliente
    process_time = time.time() - start_time
    logging.info(f"<<< Respuesta: {request.method} {request.url.path} - Status {response.status_code} - Tiempo: {process_time:.3f}s")
    
    return response

# --- Eventos de Inicio (Startup) ---
@app.on_event("startup")
def startup_event():
    """
    Este evento se ejecuta automáticamente al arrancar el servidor.
    Se utiliza para inicializar datos maestros necesarios para que la aplicación funcione.
    """
    
    logging.info("Iniciando eventos de arranque...")
    logging.info("Inicializando datos maestros...")
    db = next(database.get_db())
    initialize_admin_user(db)    # Crea el usuario admin si no existe
    initialize_demands(db)       # Inicializa tipos de demanda (Alta, Media, Baja)
    initialize_prices(db)        # Inicializa precios base
    initialize_courts(db)        # Crea las pistas si no existen
    initialize_schedules(db)     # Genera el cuadrante horario semanal
    initialize_lat_lon()         # Inicializa datos para el clima
    logging.info("Datos maestros inicializados.")
    
    # Inicializar el scheduler de tareas programadas
    init_scheduler()
    logging.info("Sistemas de notificación inicializados.")

# --- Rutas del Frontend (Servicio de HTML) ---
# Estas rutas devuelven páginas web completas en lugar de solo datos JSON.

# --- Eventos de Apagón (Shutdown) ---
@app.on_event("shutdown")
def shutdown_event():
    """
    Este evento se ejecuta automáticamente al detener el servidor.
    Se utiliza para limpiar recursos o realizar acciones finales.
    """
    logging.info("Iniciando apagado")
    logging.info("Limpieza de recursos...")
    
    # Detener el scheduler
    shutdown_scheduler()
    
    logging.info("Eventos de apagón completados.")
    #logging.info("\n\n\n\n")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal: Formulario de inicio de sesión."""
    logging.info("Renderizando página principal...")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro de nuevos usuarios."""
    logging.info("Renderizando página de registro...")
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Panel de control principal tras iniciar sesión."""
    logging.info("Renderizando panel de control...")
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/book", response_class=HTMLResponse)
async def book_page(request: Request):
    """Vista para realizar una nueva reserva de pistas."""
    logging.info("Renderizando página de reserva...")
    return templates.TemplateResponse("book.html", {"request": request})

@app.get("/reservations", response_class=HTMLResponse)
async def reservations_page(request: Request):
    """Vista para que el usuario consulte y cancele sus propias reservas."""
    logging.info("Renderizando página de reservas...")
    return templates.TemplateResponse("reservations.html", {"request": request})



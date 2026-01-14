from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging

from . import models, database, dependencies
from .routers import auth, bookings, admin, users
from .initialize import initialize_schedules, initialize_prices, initialize_courts, initialize_admin_user, initialize_demands
from .logging_config import setup_logging

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

# Configuración del motor de plantillas Jinja2 para servir archivos HTML
templates = Jinja2Templates(directory="app/templates")

# --- Inclusión de Routers para organizar la API ---
app.include_router(auth.router)      # Rutas de autenticación (login/registro)
app.include_router(bookings.router) # Rutas de gestión de reservas
app.include_router(admin.router)    # Rutas de administración

# --- Eventos de Inicio (Startup) ---
@app.on_event("startup")
def startup_event():
    """
    Este evento se ejecuta automáticamente al arrancar el servidor.
    Se utiliza para inicializar datos maestros necesarios para que la aplicación funcione.
    """
    db = next(database.get_db())
    initialize_admin_user(db)    # Crea el usuario admin si no existe
    initialize_demands(db)       # Inicializa tipos de demanda (Alta, Media, Baja)
    initialize_prices(db)        # Inicializa precios base
    initialize_courts(db)        # Crea las pistas
    initialize_schedules(db)     # Genera el cuadrante horario semanal

# --- Rutas del Frontend (Servicio de HTML) ---
# Estas rutas devuelven páginas web completas en lugar de solo datos JSON.

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal: Formulario de inicio de sesión."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro de nuevos usuarios."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Panel de control principal tras iniciar sesión."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/book", response_class=HTMLResponse)
async def book_page(request: Request):
    """Vista para realizar una nueva reserva de pistas."""
    return templates.TemplateResponse("book.html", {"request": request})

@app.get("/reservations", response_class=HTMLResponse)
async def reservations_page(request: Request):
    """Vista para que el usuario consulte y cancele sus propias reservas."""
    return templates.TemplateResponse("reservations.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Panel de administración (solo accesible para usuarios con permisos)."""
    return templates.TemplateResponse("admin.html", {"request": request})

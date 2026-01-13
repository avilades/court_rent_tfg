from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, database, crud, dependencies
from .routers import auth, bookings, admin, users
from .insert_schedules import initialize_schedules

# Create Database Tables if they don't exist
# In production, use Alembic for migrations!
models.Base.metadata.create_all(bind=database.engine)

#app = FastAPI(title="Court Rent App")
app = FastAPI(title="Reserva de Psitas")

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates Configuration
templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(admin.router)
# app.include_router(users.router) # To be implemented

# Initialize Data (Courts, Prices, Schedules)
@app.on_event("startup")
def startup_event():
    db = next(database.get_db())
    crud.initialize_admin_user(db)
    crud.initialize_courts(db)
    crud.initialize_prices(db)
    initialize_schedules(db)

# --- Frontend Routes ---
# These return HTML instead of JSON

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/book", response_class=HTMLResponse)
async def book_page(request: Request):
    return templates.TemplateResponse("book.html", {"request": request})

@app.get("/reservations", response_class=HTMLResponse)
async def reservations_page(request: Request):
    return templates.TemplateResponse("reservations.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

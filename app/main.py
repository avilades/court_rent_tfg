from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, database, crud, dependencies
from .routers import auth, bookings, admin, users

# Create Database Tables if they don't exist
# In production, use Alembic for migrations!
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Court Rent App")

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates Configuration
templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(bookings.router)
# app.include_router(admin.router) # To be implemented
# app.include_router(users.router) # To be implemented

# Initialize Data (Courts)
@app.on_event("startup")
def startup_event():
    db = next(database.get_db())
    crud.initialize_courts(db)
    crud.initialize_prices(db)

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

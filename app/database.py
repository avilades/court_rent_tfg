from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import logging
import os

logger = logging.getLogger(__name__)

# --- Configuración de la Base de Datos ---
# 'db' es el nombre del servicio de base de datos definido en docker-compose.yml.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://user:password@db:5432/court_rent"
    logger.warning("DATABASE_URL not set in environment, using default")


# El 'engine' es el punto de entrada de SQLAlchemy. Se encarga de gestionar
logger.info(f"Creando engine de base de datos con URL: {DATABASE_URL}")
if not DATABASE_URL or DATABASE_URL.strip() == "":
    raise ValueError("DATABASE_URL no puede estar vacío")
engine = create_engine(DATABASE_URL)

# 2. session_local
# Cada instancia de session_local será una sesión de base de datos única.
# autocommit=False: los cambios no se guardan automáticamente, hay que hacer .commit()
# autoflush=False: no se envían los cambios a la DB antes de cada consulta automáticamente.
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base (Clase Base Declarativa)
# Todos nuestros modelos de base de datos (tablas) heredarán de esta clase.
# Esto permite que SQLAlchemy mapee las clases Python a tablas SQL.
Base = declarative_base()

# --- Dependencia para FastAPI ---
def get_db() -> Generator:
    """
    Función generadora que actúa como dependencia para inyectar la sesión de la DB en las rutas.
    
    ¿Por qué usar esto?
    FastAPI permite la inyección de dependencias. Esto asegura que:
    1. Se abra una sesión nueva para cada petición HTTP.
    2. La sesión se CIERRE automáticamente al finalizar la petición (gracias al 'finally').
    3. El uso de 'yield' permite pausar la ejecución de la función, entregar la sesión
       a la ruta, y retomar aquí después para realizar la limpieza (cerrar conexión).
    """
    db = session_local()
    try:
        logger.debug("Conectando a la base de datos")
        yield db
        
    finally:
        logger.debug("Cerrando conexion a la base de datos")
        db.close()

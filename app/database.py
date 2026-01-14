from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# --- Configuración de la Base de Datos ---
# Utilizamos PostgreSQL como motor de persistencia.
# El formato de la URL es: postgresql://<usuario>:<contraseña>@<host>:<puerto>/<nombre_db>
# 'db' es el nombre del servicio de base de datos definido en docker-compose.yml.
DATABASE_URL = "postgresql://user:password@db:5432/court_rent"

# 1. Creación del Engine (Motor)
# El 'engine' es el punto de entrada de SQLAlchemy. Se encarga de gestionar
# la conexión real con la base de datos y de traducir las consultas de Python a SQL.
engine = create_engine(DATABASE_URL)

# 2. SessionLocal
# sessionmaker crea una clase de "fábrica" para sesiones. 
# Cada instancia de SessionLocal será una sesión de base de datos única.
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
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# --- Database Configuration ---
# Explanation: We are using PostgreSQL as our persistence layer.
# The URL format is: postgresql://<user>:<password>@<host>:<port>/<dbname>
# 'db' is the hostname of our database service defined in docker-compose.yml
DATABASE_URL = "postgresql://user:password@db:5432/court_rent"

# 1. Create Engine
# The engine is the starting point for any SQLAlchemy application. It's essentially
# a home base for the actual database connection and its capabilities.
engine = create_engine(DATABASE_URL)

# 2. SessionLocal
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base
# This class is the base class for our models. All our database models
# will inherit from this class so SQLAlchemy knows about them.
Base = declarative_base()

# --- Dependency ---
def get_db() -> Generator:
    """
    Dependency function to yield a database session.
    
    Why use this?
    FastAPI supports dependency injection. This validation ensures that 
    we open a new session for each request and CLOSE it when the request is done.
    The 'yield' keyword allows us to pause execution, return the session to the route,
    and then resume execution (to close the session) after the route finishes.
    """
    db = session_local()
    try:
        yield db
    finally:
        db.close()

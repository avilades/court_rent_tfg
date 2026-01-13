"""
Script to reset the database by dropping and recreating all tables.
WARNING: This will delete all data!
"""
from app.database import engine
from app.models import Base

if __name__ == "__main__":
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete!")

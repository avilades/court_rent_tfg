from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# --- Models Definition ---
# These classes represent our database tables (Object Relational Mapping - ORM).
# Each class inherits from 'Base', linking it to our SQLAlchemy configuration.

class User(Base):
    """
    Represents a registered user in the system.
    Relevant requirements: "Users must be registered... Users table"
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Relationships
    # One-to-One relationship with Permissions
    permissions = relationship("Permission", back_populates="user", uselist=False, cascade="all, delete-orphan")
    # One-to-Many relationship with Bookings
    bookings = relationship("Booking", back_populates="user")

class Permission(Base):
    """
    Stores specific permissions for each user.
    Relevant requirements: "Permissions table, rent=1 by default..."
    """
    __tablename__ = "permissions"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    
    # Using Boolean for 'bit' as requested (SQLAlchemy maps this correctly to Postgres)
    is_admin = Column(Boolean, default=False)        # 'Admin'
    can_rent = Column(Boolean, default=True)         # 'Rent' (Default 1)
    can_edit_schedule = Column(Boolean, default=False) # 'Schedule' (Default 0)
    can_edit_price = Column(Boolean, default=False)    # 'Price' (Default 0)

    # Relationship back to User
    user = relationship("User", back_populates="permissions")

class Court(Base):
    """
    Represents a sport court.
    Relevant requirements: "8 courts numbered 1 to 8... Courts table"
    """
    __tablename__ = "courts"

    court_id = Column(Integer, primary_key=True, index=True) # 1-8
    is_covered = Column(Boolean, default=False) # 'Cover'

    bookings = relationship("Booking", back_populates="court")

class Price(Base):
    """
    Historical record of prices.
    Relevant requirements: "Price table... historical storage"
    """
    __tablename__ = "prices"

    price_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False) # 'Priceo' (Assuming cents or whole currency unit)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True) # Open-ended by default until replaced
    description = Column(String, nullable=True)

    # Relationship to historical bookings and schedules
    bookings = relationship("Booking", back_populates="price_snapshot")
    schedules = relationship("Schedule", back_populates="price_config")

class Schedule(Base):
    """
    Defines availability slots for the week.
    Relevant requirements: "Schedules table... fixed slots"
    """
    __tablename__ = "schedules"

    schedule_id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 6=Sunday
    is_weekend = Column(Boolean, default=False)
    start_time = Column(Time, nullable=False) # e.g., 08:00:00
    
    # Current active price for this slot
    price_id = Column(Integer, ForeignKey("prices.price_id"))
    
    price_config = relationship("Price", back_populates="schedules")

class Holiday(Base):
    """
    Specific exception dates.
    Relevant requirements: "Holidays table"
    """
    __tablename__ = "holidays"

    date = Column(DateTime, primary_key=True)

class Booking(Base):
    """
    Represents a reservation.
    Relevant requirements: "Historico... UserID, CourtID, PriceID..."
    """
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    court_id = Column(Integer, ForeignKey("courts.court_id"))
    
    # We link to the specific Price ID active AT THE MOMENT of booking to preserve history
    price_id = Column(Integer, ForeignKey("prices.price_id")) 
    
    start_time = Column(DateTime, nullable=False) # 'HoraAlquiler' - Full timestamp
    created_at = Column(DateTime, default=datetime.utcnow) # 'Reservada'
    is_cancelled = Column(Boolean, default=False) # 'Cancelada'

    # Relationships
    user = relationship("User", back_populates="bookings")
    court = relationship("Court", back_populates="bookings")
    price_snapshot = relationship("Price", back_populates="bookings")

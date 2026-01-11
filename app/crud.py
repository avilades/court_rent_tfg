from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
from datetime import datetime, timedelta

# --- Security Configuration ---
# 'pbkdf2_sha256' is a robust password hashing algorithm available by default.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- User Operations ---

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # 1. Hash the password
    fake_hashed_password = get_password_hash(user.password)
    
    # 2. Create User Instance
    db_user = models.User(
        email=user.email, 
        name=user.name, 
        surname=user.surname, 
        password_hash=fake_hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 3. Create Default Permissions
    # Requirement: Default rent=1, admin=0, etc.
    db_perm = models.Permission(
        user_id=db_user.user_id,
        is_admin=False,
        can_rent=True,
        can_edit_schedule=False,
        can_edit_price=False
    )
    db.add(db_perm)
    db.commit()

    return db_user

# --- Court Operations ---
def get_courts(db: Session):
    return db.query(models.Court).all()

def initialize_courts(db: Session):
    """Creates the 8 courts if they don't exist."""
    if db.query(models.Court).count() == 0:
        for i in range(1, 9):
            court = models.Court(court_id=i, is_covered=(i > 4)) # Example: 5-8 covered
            db.add(court)
        db.commit()

def initialize_prices(db: Session):
    """Creates a default price if none exist."""
    if db.query(models.Price).count() == 0:
        default_price = models.Price(
            price_id=1,
            amount=10, # 10 currency units
            description="Default Price"
        )
        db.add(default_price)
        db.commit()

# --- Booking Operations ---
def get_user_bookings(db: Session, user_id: int):
    # Order by booking time descending (newest first)
    return db.query(models.Booking)\
             .filter(models.Booking.user_id == user_id)\
             .order_by(models.Booking.start_time.desc())\
             .all()

def create_booking(db: Session, booking_data: schemas.BookingCreate, user_id: int):
    # Parse input strings to datetime
    start_dt = datetime.strptime(f"{booking_data.date} {booking_data.time_slot}", "%Y-%m-%d %H:%M")
    
    # Check if already booked
    existing = db.query(models.Booking).filter(
        models.Booking.court_id == booking_data.court_id,
        models.Booking.start_time == start_dt,
        models.Booking.is_cancelled == False
    ).first()
    
    if existing:
        return None # Conflict

    # Find active price (simplified for now, assume ID 1 exists)
    # Ideally should query the Schedule to find the PriceID for this slot
    # For MVP initialization we will need to create a dummy price.
    
    new_booking = models.Booking(
        user_id=user_id,
        court_id=booking_data.court_id,
        start_time=start_dt,
        price_id=1, # Default price ID fallback
        is_cancelled=False
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking

def cancel_booking_logic(db: Session, booking_id: int, user_id: int):
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id, models.Booking.user_id == user_id).first()
    if booking:
        booking.is_cancelled = True
        db.commit()
    return booking

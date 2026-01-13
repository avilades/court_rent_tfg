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
def get_user_bookings(db: Session, user_id: int, date_from: str = None, date_to: str = None):
    """Order by booking time descending (newest first) and include price_amount.
    Optionally filter by date range."""
    from datetime import datetime, timedelta
    
    query = db.query(models.Booking).filter(models.Booking.user_id == user_id)
    
    # Apply date filters if provided
    if date_from:
        from_date = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(models.Booking.start_time >= from_date)
    
    if date_to:
        to_date = datetime.strptime(date_to, "%Y-%m-%d")
        # Add 1 day to include the entire end date
        to_date = to_date + timedelta(days=1)
        query = query.filter(models.Booking.start_time < to_date)
    
    bookings = query.order_by(models.Booking.start_time.desc()).all()
    
    # Enrich with price_amount from the price_snapshot relationship
    result = []
    for b in bookings:
        # Create a dict-like object with price_amount
        booking_dict = {
            "booking_id": b.booking_id,
            "court_id": b.court_id,
            "start_time": b.start_time,
            "is_cancelled": b.is_cancelled,
            "price_amount": b.price_snapshot.amount if b.price_snapshot else None
        }
        result.append(booking_dict)
    return result

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

    # Find price from Schedule based on day of week and time
    day_of_week = start_dt.weekday()
    time_obj = start_dt.time()
    
    schedule = db.query(models.Schedule).filter(
        models.Schedule.day_of_week == day_of_week,
        models.Schedule.start_time == time_obj
    ).first()
    
    # Use schedule's price_id if found, otherwise fallback to 1
    price_id = schedule.price_id if schedule and schedule.price_id else 1
    
    new_booking = models.Booking(
        user_id=user_id,
        court_id=booking_data.court_id,
        start_time=start_dt,
        price_id=price_id,
        is_cancelled=False
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    # Return with price_amount for response
    return {
        "booking_id": new_booking.booking_id,
        "court_id": new_booking.court_id,
        "start_time": new_booking.start_time,
        "is_cancelled": new_booking.is_cancelled,
        "price_amount": new_booking.price_snapshot.amount if new_booking.price_snapshot else None
    }

def cancel_booking_logic(db: Session, booking_id: int, user_id: int):
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id, models.Booking.user_id == user_id).first()
    if booking:
        booking.is_cancelled = True
        db.commit()
    return booking

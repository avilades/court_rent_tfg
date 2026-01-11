from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.get("/my-bookings", response_model=List[schemas.BookingResponse])
def read_my_bookings(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get all bookings for the current user.
    """
    return crud.get_user_bookings(db, user_id=current_user.user_id)

@router.post("/book", response_model=schemas.BookingResponse)
def book_court(booking: schemas.BookingCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Book a court.
    Checks for conflicts and permissions.
    """
    if not current_user.permissions.can_rent:
         raise HTTPException(status_code=403, detail="User does not have rent permissions")

    new_booking = crud.create_booking(db, booking, user_id=current_user.user_id)
    if not new_booking:
         raise HTTPException(status_code=409, detail="Time slot already booked")
    
    return new_booking


    return new_booking

@router.get("/search", response_model=List[schemas.SlotBase])
def search_available_slots(date: str, db: Session = Depends(get_db)):
    """
    Returns specific slots availability for a given date.
    Logic:
    1. Define standard slots (8:00 - 23:00, 90 mins).
    2. Check booking table for existence.
    """
    from datetime import datetime, timedelta
    
    # Define slots: 8:00, 9:30, 11:00, 12:30, 14:00, 15:30, 17:00, 18:30, 20:00, 21:30
    start_times = [
        "08:00", "09:30", "11:00", "12:30", "14:00", 
        "15:30", "17:00", "18:30", "20:00", "21:30"
    ]
    
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    courts = crud.get_courts(db)
    
    available_slots = []
    
    # Get all bookings for that day to minimize DB queries (optimization)
    existing_bookings = db.query(models.Booking).filter(
        models.Booking.is_cancelled == False
        # In real app filter by date range, here relying on standard check
    ).all()
    
    booked_keys = set()
    for b in existing_bookings:
        if b.start_time.date() == target_date:
            # Key: court_id + time string
            key = f"{b.court_id}_{b.start_time.strftime('%H:%M')}"
            booked_keys.add(key)
    
    for court in courts:
        for t_str in start_times:
            key = f"{court.court_id}_{t_str}"
            is_taken = key in booked_keys
            
            # Construct start/end time
            start_dt = datetime.strptime(f"{date} {t_str}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=90)
            
            if not is_taken:
                available_slots.append(schemas.SlotBase(
                    court_id=court.court_id,
                    start_time=start_dt,
                    end_time=end_dt,
                    is_available=True
                ))
                
    return available_slots

@router.post("/cancel/{booking_id}")
def cancel_booking(booking_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = crud.cancel_booking_logic(db, booking_id, current_user.user_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not authorized")
    return {"msg": "Booking cancelled"}


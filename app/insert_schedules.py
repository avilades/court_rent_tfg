from sqlalchemy.orm import Session
from datetime import time
from . import models

def initialize_schedules(db: Session):
    """Creates all schedule entries if they don't exist."""
    if db.query(models.Schedule).count() > 0:
        return  # Already initialized
    
    # Time slots for each day
    time_slots = [
        time(8, 0),   # 08:00
        time(9, 30),  # 09:30
        time(11, 0),  # 11:00
        time(12, 30), # 12:30
        time(14, 0),  # 14:00
        time(15, 30), # 15:30
        time(17, 0),  # 17:00
        time(18, 30), # 18:30
        time(20, 0),  # 20:00
        time(21, 30), # 21:30
    ]
    
    # Days 0-4: Monday to Friday (weekdays)
    # For weekdays: morning/afternoon (08:00-15:30) use price_id=3, evening (17:00-21:30) use price_id=1
    for day in range(5):  # Monday (0) to Friday (4)
        for slot in time_slots:
            # Determine price based on time
            if slot < time(17, 0):
                price_id = 3  # Morning/afternoon price
            else:
                price_id = 1  # Evening price
            
            schedule = models.Schedule(
                day_of_week=day,
                is_weekend=False,
                start_time=slot,
                price_id=price_id
            )
            db.add(schedule)
    
    # Saturday (day_of_week = 5) - All slots use price_id=1
    for slot in time_slots:
        schedule = models.Schedule(
            day_of_week=5,
            is_weekend=True,
            start_time=slot,
            price_id=1
        )
        db.add(schedule)
    
    # Sunday (day_of_week = 6) - Morning/afternoon use price_id=1, evening uses price_id=3
    for slot in time_slots:
        if slot < time(17, 0):
            price_id = 1
        else:
            price_id = 3
        
        schedule = models.Schedule(
            day_of_week=6,
            is_weekend=True,
            start_time=slot,
            price_id=price_id
        )
        db.add(schedule)
    
    db.commit()

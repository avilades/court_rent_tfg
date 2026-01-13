from sqlalchemy.orm import Session
from datetime import time
from . import models, schemas, crud
import logging

logger = logging.getLogger(__name__)
# --- Admin user Operattions ---

def initialize_admin_user(db: Session):
    """Creates admin user if it dosen't exist."""
    if db.query(models.User).filter(models.User.name == "admin").count() == 0:
        crud.create_user(db, schemas.UserCreate(name="admin", surname="admin", email="admin@example.com", password="admin000"))
        logger.info("Admin user created.")
    else:
        logger.info("Admin user already exists.")
    """check admin permission"""
    if db.query(models.User).join(models.Permission).filter(
             models.User.name == "admin"
            ,models.Permission.is_admin == True
            ,models.Permission.can_edit_schedule == True
            ,models.Permission.can_edit_price == True
        ).count() == 0:
        """update admin permission"""
        update_admin_user_permission(db, db.query(models.User).filter(models.User.name == "admin").first().user_id)
    else:
        logger.info("Admin permission already exists.")

def update_admin_user_permission(db: Session, user_id: int):
    """update admin permission"""
    db.query(models.Permission).filter(
        models.Permission.user_id == user_id
    ).update({
        models.Permission.is_admin: True,
        models.Permission.can_edit_schedule: True,
        models.Permission.can_edit_price: True
    })
    db.commit() 
    logger.info("Admin permission updated.")

def initialize_demands(db: Session):
    """Creates default demands if they don't exist."""
    # Define all required demands
    required_demands = [
        {"description": "Demanda alta", "is_active": True},
        {"description": "Demanda media", "is_active": True},
        {"description": "Demanda baja", "is_active": True}
    ]
    
    # Check and create each demand if it doesn't exist
    for demand_data in required_demands:
        existing_demand = db.query(models.Demand).filter(
            models.Demand.description == demand_data["description"]
        ).first()
        
        if not existing_demand:
            new_demand = models.Demand(**demand_data)
            db.add(new_demand)
    
    # Commit all new demands at once
    db.commit()
    logger.info("Demands initialized.")

def initialize_prices(db: Session):
    """Creates default prices if they don't exist."""
    # Define all required prices
    required_prices = [
        {"amount": 30, "description": "Precio de pista", "is_active": True, "demand_id": 1},
        {"amount": 20, "description": "Precio de pista", "is_active": True, "demand_id": 2},
        {"amount": 10, "description": "Precio de pista", "is_active": True, "demand_id": 3}
    ]
    
    # Check and create each price if it doesn't exist
    for price_data in required_prices:
        existing_price = db.query(models.Price).filter(
            models.Price.demand_id == price_data["demand_id"]
        ).first()
        
        if not existing_price:
            new_price = models.Price(**price_data)
            db.add(new_price)
    
    # Commit all new prices at once
    db.commit()
    logger.info("Prices initialized.")
def initialize_courts(db: Session):
    """Creates the 8 courts if they don't exist."""
    if db.query(models.Court).count() == 0:
        for i in range(1, 9):
            court = models.Court(court_id=i, is_covered=(i > 4)) # Example: 5-8 covered
            db.add(court)
        db.commit()
    logger.info("Courts initialized.")     
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
                demand_id = 3  # Morning/afternoon demand
            else:
                demand_id = 1  # Evening demand
            
            schedule = models.Schedule(
                day_of_week=day,
                is_weekend=False,
                start_time=slot,
                demand_id=demand_id
            )
            db.add(schedule)
    
    # Saturday (day_of_week = 5) - All slots use demand_id=1
    for slot in time_slots:
        schedule = models.Schedule(
            day_of_week=5,
            is_weekend=True,
            start_time=slot,
            demand_id=1
        )
        db.add(schedule)
    
    # Sunday (day_of_week = 6) - Morning/afternoon use demand_id=1, evening uses demand_id=3
    for slot in time_slots:
        if slot < time(17, 0):
            demand_id = 1
        else:
            demand_id = 3
        
        schedule = models.Schedule(
            day_of_week=6,
            is_weekend=True,
            start_time=slot,
            demand_id=demand_id
        )
        db.add(schedule)
    
    db.commit()

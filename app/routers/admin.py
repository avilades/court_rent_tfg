from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user
from ..database import engine

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.post("/price")
def create_price(price: int, description: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.permissions.can_edit_price:
        raise HTTPException(status_code=403, detail="Not authorized")
    # simplified logic
    return {"msg": "Price created (simulation)"}

@router.post("/reset-database")
def reset_database(db: Session = Depends(get_db)):
    """
    DANGER: This endpoint drops and recreates all database tables.
    Use only for development/debugging purposes.
    """
    try:
        # Close the current session
        db.close()
        
        # Drop all tables
        models.Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables
        models.Base.metadata.create_all(bind=engine)
        
        return {"msg": "Database reset successfully. Restart the application to reinitialize data."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user

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

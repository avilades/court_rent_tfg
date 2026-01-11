from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, time

# --- Pydantic Schemas ---
# Schemas are used for data validation and serialization (converting to JSON).
# They act as the contract between our API and the outside world.

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    surname: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    user_id: int
    # We don't return the password_hash for security!

    class Config:
        from_attributes = True # Allows Pydantic to read from SQLAlchemy objects

# --- Permission Schemas ---
class PermissionResponse(BaseModel):
    is_admin: bool
    can_rent: bool
    can_edit_schedule: bool
    can_edit_price: bool

    class Config:
        from_attributes = True

class UserWithPermissions(UserResponse):
    permissions: Optional[PermissionResponse] = None

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Validation for Login Form ---
# (Usually we might use OAuth2PasswordRequestForm, but explicit schemas help learning)
class UserLogin(BaseModel):
    email: str
    password: str

# --- Court Schemas ---
class CourtResponse(BaseModel):
    court_id: int
    is_covered: bool

    class Config:
        from_attributes = True

# --- Schedule/Availability Schemas ---
class SlotBase(BaseModel):
    court_id: int
    start_time: datetime # Full ISO timestamp
    end_time: datetime
    is_available: bool

# --- Booking Schemas ---
class BookingCreate(BaseModel):
    court_id: int
    date: str # "YYYY-MM-DD"
    time_slot:str # "HH:MM" start time

class BookingResponse(BaseModel):
    booking_id: int
    court_id: int
    start_time: datetime
    is_cancelled: bool
    price_amount: Optional[int] = None # Enriched field

    class Config:
        from_attributes = True

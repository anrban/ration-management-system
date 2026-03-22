# schemas/user.py
# Pydantic schemas define what data looks like when it comes IN (request) or goes OUT (response).
# Think of them as blueprints/contracts for your API.

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    """Data needed to register a new user (officer)"""
    username: str
    email: EmailStr          # Pydantic auto-validates email format
    password: str
    role: str                # Must match one of UserRole values
    district: Optional[str] = None


class UserLogin(BaseModel):
    """Data needed to log in"""
    username: str
    password: str


class UserResponse(BaseModel):
    """What we send back when returning user info (no password!)"""
    id: str
    username: str
    email: str
    role: str
    district: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True   # Allows Pydantic to read from SQLAlchemy model objects


class Token(BaseModel):
    """What we return after successful login"""
    access_token: str
    token_type: str          # Always "bearer"

# routers/auth.py
# Handles user registration and login.
# Think of this as the "gate" of the system - you must log in to get a token,
# then use that token to access other parts of the system.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt

from database import get_db
from models import User
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from auth.jwt import create_access_token

router = APIRouter()




def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new officer/user in the system.
    Steps:
    1. Check if username or email already exists
    2. Hash the password
    3. Save user to database
    4. Return user details (without password)
    """
    # Check for duplicate username or email
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        district=user_data.district,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)   # Refresh to get the auto-generated ID

    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        role=new_user.role.value if hasattr(new_user.role, "value") else new_user.role,
        district=new_user.district,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Logs in a user and returns a JWT token.
    Steps:
    1. Find the user by username
    2. Verify the password
    3. Create and return a JWT token
    """
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled. Contact admin."
        )

    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token, token_type="bearer")

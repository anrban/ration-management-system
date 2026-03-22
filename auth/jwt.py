# auth/jwt.py
# JWT = JSON Web Token
# Think of it like a DIGITAL STAMP that proves "this user is logged in"
# When a user logs in → we give them a token (JWT)
# They send this token with every request → we verify it to identify them

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db

# Secret key used to sign the token - keep this private!
SECRET_KEY = os.getenv("SECRET_KEY", "my-simple-secret-key-for-dev")
ALGORITHM = "HS256"                          # The algorithm used to encode the token
ACCESS_TOKEN_EXPIRE_MINUTES = 30             # Token expires after 30 minutes

# This tells FastAPI where the login endpoint is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict) -> str:
    """
    Creates a JWT token with an expiry time.
    data: usually {"sub": username}
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Reads the token from the request header and returns the logged-in user.
    If token is invalid or expired → raises 401 Unauthorized error.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    from models import User
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

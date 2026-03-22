# database.py
# SQLite is used here - it's a simple file-based database.
# No need to install any server or Docker. Just run the app and it creates a .db file automatically.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This creates a file called ration.db in the same folder as this script
DATABASE_URL = "sqlite:///./ration.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
)

# SessionLocal is used to talk to the database in each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all our database models
Base = declarative_base()


def get_db():
    """
    This function gives us a database session for each request.
    It automatically closes the session when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# main.py
# This is the ENTRY POINT of the application.
# It creates the FastAPI app, registers all the routers, and sets up middleware.
# Run this file to start the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers (each handles a different section of the API)
from routers import auth, beneficiaries, distributions, analytics, admin

# Import database objects to create tables on startup
from database import Base, engine
Base.metadata.create_all(bind=engine)

# ─── Create all database tables automatically ─────────────────────────────────
# This replaces the need for Alembic/migrations for a student project.
# On first run, it creates the .db file and all tables automatically.
Base.metadata.create_all(bind=engine)

# ─── Create the FastAPI app ───────────────────────────────────────────────────
#    - QR code generation for distributions
app = FastAPI(
    title="Digital Ration Management System",
    description="""
    A backend API for managing government ration distribution.
    
    Features:
    - User authentication with JWT tokens
    - Role-based access control (RBAC)
    - Beneficiary registration and verification
    - Ration distribution tracking
    - Duplicate/fraud detection using fuzzy matching
    - Analytics dashboard
    - Immutable audit logs
    """,
    version="1.0.0",
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# This allows a frontend (React/HTML) running on a different port to talk to this API.
# In production, replace "*" with your actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)

# ─── Register Routers ─────────────────────────────────────────────────────────
# Each router handles one group of related endpoints.
# prefix = the URL path prefix for that group of routes.
app.include_router(auth.router,            prefix="/auth",           tags=["Authentication"])
app.include_router(beneficiaries.router,   prefix="/beneficiaries",  tags=["Beneficiaries"])
app.include_router(distributions.router,   prefix="/distributions",  tags=["Distributions"])
app.include_router(analytics.router,       prefix="/analytics",      tags=["Analytics"])
app.include_router(admin.router,           prefix="/admin",          tags=["Admin"])


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    """Simple endpoint to verify the server is running."""
    return {
        "status": "healthy",
        "service": "Digital Ration Management System",
        "docs": "Visit /docs for interactive API documentation"
    }

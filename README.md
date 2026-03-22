# Digital Ration Management System

A backend REST API built with **FastAPI** and **SQLite** to digitize 
government ration distribution, eliminate duplicate beneficiaries, 
and maintain a transparent audit trail.

## Tech Stack
- **FastAPI** — REST API framework
- **SQLAlchemy** — ORM for database operations
- **SQLite** — File-based database (no server needed)
- **JWT** — Authentication via JSON Web Tokens
- **bcrypt** — Secure password hashing
- **RapidFuzz** — Fuzzy matching for duplicate detection

## Features
- JWT-based authentication
- Role-based access control (super_admin, district_officer, field_agent, auditor)
- Beneficiary registration with fuzzy duplicate detection
- Ration distribution tracking
- Auto fraud detection — flags repeated distributions within 30 days
- Immutable audit logs
- Analytics dashboard with coverage stats

## How to Run
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://localhost:8000/docs for interactive API documentation.

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register new officer |
| POST | /auth/login | Login and get JWT token |
| POST | /beneficiaries/register | Register beneficiary |
| GET  | /beneficiaries/ | List all beneficiaries |
| POST | /beneficiaries/{id}/verify | Verify a beneficiary |
| POST | /distributions/record | Record a distribution |
| GET  | /analytics/summary | Dashboard statistics |
| GET  | /admin/audit-logs | Full audit trail |

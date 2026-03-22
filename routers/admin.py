# routers/admin.py
# Admin-only routes for managing users, viewing audit logs, and flagging duplicates.
# All routes here require elevated permissions (super_admin or district_officer level).

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Beneficiary, AuditLog, FraudFlag, User, VerificationStatus
from auth.rbac import require_permission

router = APIRouter()


@router.post("/flag-duplicate", status_code=201, summary="Flag a beneficiary as duplicate")
def flag_duplicate(
    beneficiary_id: str,
    reason: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("delete")),  # Only super_admin can do this
):
    """
    Marks a beneficiary as a duplicate and creates a fraud flag.
    Steps:
    1. Find the beneficiary
    2. Set their status to DUPLICATE (they can no longer receive rations)
    3. Create a FraudFlag record explaining why
    """
    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    # Update beneficiary status to DUPLICATE
    beneficiary.verification_status = VerificationStatus.DUPLICATE
    db.commit()

    # Create a permanent fraud flag record
    flag = FraudFlag(
        beneficiary_id=beneficiary_id,
        reason=reason,
        flagged_by=current_user.id,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)

    return {
        "message": "Beneficiary has been flagged as duplicate and deactivated",
        "flag_id": str(flag.id),
        "beneficiary_id": beneficiary_id,
    }


@router.get("/audit-logs", summary="View all audit logs")
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("read")),
):
    """
    Returns the audit trail - every important action ever done in the system.
    Useful for investigations, accountability, and compliance checks.
    """
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())  # Latest first
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": str(a.id),
                "beneficiary_id": str(a.beneficiary_id) if a.beneficiary_id else None,
                "action": a.action,
                "performed_by": str(a.performed_by) if a.performed_by else None,
                "ip_address": a.ip_address,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in items
        ],
    }


@router.get("/users", summary="List all system users (officers)")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_users")),  # Only super_admin
):
    """Returns list of all registered officers/staff in the system."""
    query = db.query(User)
    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "role": u.role.value if hasattr(u.role, "value") else u.role,
                "district": u.district,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.patch("/users/{user_id}/deactivate", summary="Deactivate a user account")
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_users")),
):
    """Deactivates a user account so they can no longer log in."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    return {"message": f"User '{user.username}' has been deactivated"}

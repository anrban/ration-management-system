# routers/beneficiaries.py
# Handles all operations related to beneficiaries (people who receive rations).
# CRUD = Create, Read, Update, Delete

import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models import Beneficiary, AuditLog, VerificationStatus
from schemas.beneficiary import BeneficiaryCreate, BeneficiaryResponse, BeneficiaryVerify
from auth.rbac import require_permission
from services.deduplication import check_for_duplicates

router = APIRouter()


@router.post("/register", response_model=BeneficiaryResponse, status_code=201)
def register_beneficiary(
    data: BeneficiaryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write")),   # Only users with "write" permission
):
    """
    Registers a new beneficiary.
    Steps:
    1. Check if national_id already exists (exact match)
    2. Run fuzzy duplicate check (catches spelling variations)
    3. Save to database
    """
    # Step 1: Exact duplicate check
    existing = db.query(Beneficiary).filter(
        Beneficiary.national_id == data.national_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A beneficiary with this national ID already exists"
        )

    # Step 2: Fuzzy duplicate check (catches "Ram Kumar" vs "Raam Kumaar")
    duplicates = check_for_duplicates(data.model_dump(), db)
    if duplicates:
        raise HTTPException(
            status_code=409,   # 409 = Conflict
            detail={
                "message": "Potential duplicate beneficiaries found. Review before registering.",
                "duplicates": duplicates
            }
        )

    # Step 3: Save new beneficiary
    beneficiary = Beneficiary(
        national_id=data.national_id,
        ration_card_no=data.ration_card_no,
        name=data.name,
        phone=data.phone,
        address=data.address,
        district=data.district,
        household_size=data.household_size,
        income_bracket=data.income_bracket,
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return _to_response(beneficiary)


@router.post("/{beneficiary_id}/verify", response_model=BeneficiaryResponse)
def verify_beneficiary(
    beneficiary_id: str,
    data: BeneficiaryVerify,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write")),
):
    """
    An officer verifies or rejects a beneficiary.
    Also creates an audit log entry to track who did what and when.
    """
    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    # Update verification status
    beneficiary.verification_status = data.verification_status
    beneficiary.verified_by = current_user.id
    beneficiary.verified_at = datetime.utcnow()
    db.commit()

    # Create audit log - this records every verification action permanently
    audit = AuditLog(
        beneficiary_id=beneficiary.id,
        action="VERIFIED",
        performed_by=current_user.id,
        metadata_json=json.dumps({
            "new_status": data.verification_status,
            "remarks": data.remarks
        }),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()
    db.refresh(beneficiary)
    return _to_response(beneficiary)


@router.get("/", summary="List all beneficiaries with optional filters")
def list_beneficiaries(
    district: Optional[str] = Query(None, description="Filter by district name"),
    status: Optional[str] = Query(None, description="Filter by verification status"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("read")),
):
    """
    Returns a paginated list of beneficiaries.
    Supports filtering by district and verification status.
    skip + limit = pagination (like page numbers)
    """
    query = db.query(Beneficiary)

    if district:
        query = query.filter(Beneficiary.district == district)
    if status:
        query = query.filter(Beneficiary.verification_status == status)

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_to_response(b) for b in items],
    }


@router.get("/{beneficiary_id}/history", summary="Get ration distribution history for one beneficiary")
def get_beneficiary_history(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("read")),
):
    """Returns all distribution records for a specific beneficiary."""
    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    from models import DistributionLog
    distributions = db.query(DistributionLog).filter(
        DistributionLog.beneficiary_id == beneficiary_id
    ).all()

    history = []
    for d in distributions:
        history.append({
            "id": str(d.id),
            "ration_type": d.ration_type.value if hasattr(d.ration_type, "value") else d.ration_type,
            "quantity_kg": d.quantity_kg,
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            "distribution_center": d.distribution_center,
            "acknowledged": d.acknowledged,
        })

    return {"beneficiary_id": beneficiary_id, "total_distributions": len(history), "history": history}


# ─── Helper function ──────────────────────────────────────────────────────────

def _to_response(b: Beneficiary) -> BeneficiaryResponse:
    """Converts a database model object into a Pydantic response schema"""
    return BeneficiaryResponse(
        id=str(b.id),
        national_id=b.national_id,
        ration_card_no=b.ration_card_no,
        name=b.name,
        phone=b.phone,
        address=b.address,
        district=b.district,
        household_size=b.household_size,
        income_bracket=b.income_bracket,
        verification_status=b.verification_status.value if hasattr(b.verification_status, "value") else b.verification_status,
        is_active=b.is_active,
        created_at=b.created_at,
    )

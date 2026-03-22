# routers/analytics.py
# Provides dashboard-level stats and reports.
# Uses SQLAlchemy's func module to run aggregate queries (COUNT, SUM, etc.)

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import DistributionLog, Beneficiary, FraudFlag
from auth.rbac import require_permission

router = APIRouter()


@router.get("/summary", summary="Get overall system statistics")
def get_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view_analytics")),
):
    """
    Returns high-level stats:
    - Total beneficiaries registered
    - How many are verified
    - Total ration distributions done
    - Total kilograms of ration distributed
    - Open fraud flags
    - Coverage rate (what % of beneficiaries are verified)
    """
    total_beneficiaries = db.query(func.count(Beneficiary.id)).scalar() or 0

    verified_count = db.query(func.count(Beneficiary.id)).filter(
        Beneficiary.verification_status == "verified"
    ).scalar() or 0

    total_distributions = db.query(func.count(DistributionLog.id)).scalar() or 0

    # SUM of all quantity_kg values in distribution_logs table
    total_ration_kg = db.query(func.sum(DistributionLog.quantity_kg)).scalar() or 0.0

    open_fraud_flags = db.query(func.count(FraudFlag.id)).filter(
        FraudFlag.resolved == False
    ).scalar() or 0

    # Coverage rate = (verified / total) * 100
    coverage_rate = round((verified_count / total_beneficiaries) * 100, 2) if total_beneficiaries else 0.0

    return {
        "total_beneficiaries": total_beneficiaries,
        "verified_beneficiaries": verified_count,
        "pending_verification": total_beneficiaries - verified_count,
        "total_distributions": total_distributions,
        "total_ration_distributed_kg": total_ration_kg,
        "open_fraud_flags": open_fraud_flags,
        "coverage_rate_percent": coverage_rate,
    }


@router.get("/distribution-trends", summary="Daily distribution trends for the last N days")
def distribution_trends(
    days: int = Query(30, ge=1, le=365, description="Number of past days to show"),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view_analytics")),
):
    """
    Groups distributions by date and shows:
    - How many distributions happened each day
    - Total KG distributed each day

    Useful for identifying peak distribution days or gaps.
    """
    since = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        func.date(DistributionLog.delivered_at).label("date"),
        func.count(DistributionLog.id).label("count"),
        func.sum(DistributionLog.quantity_kg).label("total_kg"),
    ).filter(
        DistributionLog.delivered_at >= since
    ).group_by(
        func.date(DistributionLog.delivered_at)
    ).all()

    return [
        {
            "date": str(r.date),
            "distributions_count": r.count,
            "total_kg": round(r.total_kg or 0, 2),
        }
        for r in results
    ]


@router.get("/fraud-flags", summary="List all unresolved fraud flags")
def list_fraud_flags(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view_analytics")),
):
    """Returns all open (unresolved) fraud/duplicate flags."""
    flags = db.query(FraudFlag).filter(FraudFlag.resolved == False).all()

    return [
        {
            "id": str(f.id),
            "beneficiary_id": str(f.beneficiary_id) if f.beneficiary_id else None,
            "reason": f.reason,
            "flagged_by": str(f.flagged_by) if f.flagged_by else None,
            "resolved": f.resolved,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in flags
    ]

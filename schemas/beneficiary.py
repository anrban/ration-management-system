# schemas/beneficiary.py

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class BeneficiaryCreate(BaseModel):
    """Data required to register a new beneficiary"""
    national_id: str
    ration_card_no: Optional[str] = None
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    household_size: int = 1
    income_bracket: Optional[str] = None   # BPL / APL / AAY


class BeneficiaryVerify(BaseModel):
    """Data needed to verify or reject a beneficiary"""
    verification_status: str     # "verified" or "rejected" or "duplicate"
    remarks: Optional[str] = None


class BeneficiaryResponse(BaseModel):
    """What we send back when returning beneficiary info"""
    id: str
    national_id: str
    ration_card_no: Optional[str] = None
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    household_size: int
    income_bracket: Optional[str] = None
    verification_status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

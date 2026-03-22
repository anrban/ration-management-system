# schemas/distribution.py

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DistributionCreate(BaseModel):
    """Data required to record a new ration distribution"""
    beneficiary_id: str
    ration_type: str          # rice / wheat / oil / sugar / kerosene
    quantity_kg: float
    unit_price: Optional[float] = None
    total_value: Optional[float] = None
    distribution_center: Optional[str] = None
    #qr_code_hash: Optional[str] = None
    remarks: Optional[str] = None


class DistributionResponse(BaseModel):
    """What we send back after recording a distribution"""
    id: str
    beneficiary_id: str
    ration_type: str
    quantity_kg: float
    unit_price: Optional[float] = None
    total_value: Optional[float] = None
    distributed_by: str
    distribution_center: Optional[str] = None
    delivered_at: Optional[datetime] = None
    acknowledged: bool
    #qr_code_hash: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True




# models.py
# This file defines our database TABLES using Python classes.
# Each class = one table in the database.
# Each class variable = one column in that table.

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text
from database import Base


# ─── ENUMS (Fixed set of choices for a column) ────────────────────────────────

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    DISTRICT_OFFICER = "district_officer"
    FIELD_AGENT = "field_agent"
    AUDITOR = "auditor"


class RationType(str, enum.Enum):
    RICE = "rice"
    WHEAT = "wheat"
    OIL = "oil"
    SUGAR = "sugar"
    KEROSENE = "kerosene"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


# ─── USER TABLE (Officers / Staff who use the system) ─────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)   # Never store plain passwords!
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False)     # What role this user has
    district = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── BENEFICIARY TABLE (People who receive rations) ───────────────────────────

class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    national_id = Column(String(20), unique=True, nullable=False)   # Aadhar / ID number
    ration_card_no = Column(String(20), unique=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(15))
    address = Column(Text)
    district = Column(String(100))
    household_size = Column(Integer, default=1)
    income_bracket = Column(String(50))               # BPL / APL / AAY
    verification_status = Column(Enum(VerificationStatus, values_callable=lambda x: [e.value for e in x]), default=VerificationStatus.PENDING)
    verified_by = Column(String, ForeignKey("users.id"))  # Which officer verified
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# ─── DISTRIBUTION LOG TABLE (Records of rations given out) ────────────────────

class DistributionLog(Base):
    __tablename__ = "distribution_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    beneficiary_id = Column(String, ForeignKey("beneficiaries.id"), nullable=False)
    ration_type = Column(Enum(RationType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    unit_price = Column(Float)
    total_value = Column(Float)
    distributed_by = Column(String, ForeignKey("users.id"), nullable=False)
    distribution_center = Column(String(150))
    delivered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)   # Did the beneficiary confirm receipt?
    #qr_code_hash = Column(String)                   # Proof via QR scan
    remarks = Column(Text)


# ─── AUDIT LOG TABLE (Tracks every important action - cannot be deleted) ───────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    beneficiary_id = Column(String, ForeignKey("beneficiaries.id"))
    action = Column(String(100))                    # e.g. "VERIFIED", "DISTRIBUTION"
    performed_by = Column(String, ForeignKey("users.id"))
    metadata_json = Column(Text)                    # Extra info stored as JSON string
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)


# ─── FRAUD FLAG TABLE (Marks suspicious or duplicate beneficiaries) ────────────

class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    beneficiary_id = Column(String, ForeignKey("beneficiaries.id"))
    reason = Column(Text, nullable=False)
    flagged_by = Column(String, ForeignKey("users.id"))
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# services/deduplication.py
# This service checks if a new beneficiary is a DUPLICATE of someone already in the system.
# It uses FUZZY MATCHING - even if names are slightly different (spelling errors), it can detect duplicates.
# Example: "Ram Kumar" and "Raam Kumaar" would still match with high similarity.

from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from models import Beneficiary


def check_for_duplicates(new_beneficiary: dict, db: Session, threshold: int = 85):
    """
    Compares the new beneficiary's name and address against all existing records.

    How it works:
    - fuzz.token_sort_ratio("Ram Kumar", "Kumar Ram") = 100 (ignores word order)
    - We weight name more than address (60% name + 40% address)
    - If combined score >= threshold → it's a potential duplicate

    Returns: list of potential duplicates with their similarity scores
    """
    # Only check active, non-duplicate records
    existing_records = db.query(Beneficiary).filter(
        Beneficiary.verification_status != "duplicate"
    ).all()

    duplicates = []

    for existing in existing_records:
        # Compare names (case-insensitive, word-order insensitive)
        name_score = fuzz.token_sort_ratio(
            new_beneficiary["name"].lower(),
            existing.name.lower()
        )

        # Compare addresses
        address_score = fuzz.token_sort_ratio(
            (new_beneficiary.get("address") or "").lower(),
            (existing.address or "").lower()
        )

        # Weighted average: name matters more than address
        combined_score = (name_score * 0.6) + (address_score * 0.4)

        if combined_score >= threshold:
            duplicates.append({
                "id": str(existing.id),
                "name": existing.name,
                "national_id": existing.national_id,
                "district": existing.district,
                "similarity_score": round(combined_score, 2),
            })

    return duplicates

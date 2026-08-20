"""
FDA 21 CFR Part 11 & EU Annex 11 Electronic Signature Engine.
Provides dual-credential verification, regulatory reason codes, and unalterable cryptographic signature sealing.
"""

import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum

from ..security.rbac import DEFAULT_ENTERPRISE_USERS, Role


class SignatureReason(str, Enum):
    CALIBRATION_PERFORMED = "I have performed this calibration in accordance with approved laboratory SOPs."
    TECHNICAL_REVIEW = "I have reviewed the mathematical uncertainty budget and conformity decisions."
    APPROVAL_RELEASE = "I approve this calibration record and authorize release of the calibration certificate."
    AUDIT_SIGN_OFF = "I have verified the cryptographic audit trail and confirm regulatory compliance."


SIGNATURE_SEAL_KEY = b"21CFR11_ENTERPRISE_SIGNATURE_SEAL_SECRET_2026"


def execute_electronic_signature(
    calculation_id: str,
    calculation_sha256: str,
    username: str,
    password_plain: str,
    reason: SignatureReason,
    meaning: str = "Approved & Certified",
) -> Dict[str, Any]:
    """
    Execute compliant 21 CFR Part 11 electronic signature ceremony.
    Requires active user re-authentication, explicit reason, and cryptographic sealing.
    """
    user = DEFAULT_ENTERPRISE_USERS.get(username)
    if not user:
        return {"error": "Invalid signature credentials: user not found."}

    # Verify password
    pw_hash = hashlib.sha256(password_plain.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(pw_hash, user["password_hash"]):
        return {"error": "Invalid signature credentials: password rejected."}

    ts = datetime.now(timezone.utc).isoformat()
    raw_sig_payload = f"{calculation_id}:{calculation_sha256}:{username}:{user['role'].value}:{reason.value}:{ts}"
    sig_seal = hmac.new(SIGNATURE_SEAL_KEY, raw_sig_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    sig_token = f"SIG-21CFR11-{calculation_id}-{sig_seal[:16].upper()}"

    signature_manifest = {
        "signature_token": sig_token,
        "calculation_id": calculation_id,
        "calculation_sha256": calculation_sha256,
        "signer": {
            "username": username,
            "full_name": user["full_name"],
            "role": user["role"].value,
            "badge_id": user["badge_id"],
            "email": user["email"],
        },
        "signing_reason": reason.value,
        "signing_meaning": meaning,
        "timestamp_utc": ts,
        "signature_hash": sig_seal,
        "compliance_statement": "This electronic signature complies with FDA Title 21 CFR Part 11 and EU EudraLex Annex 11 requirements for electronic records.",
        "status": "SEALED_AND_BINDING",
    }

    return signature_manifest


def verify_electronic_signature(sig_manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify the cryptographic seal and integrity of an electronic signature block.
    """
    calc_id = sig_manifest.get("calculation_id")
    calc_hash = sig_manifest.get("calculation_sha256")
    signer = sig_manifest.get("signer", {})
    username = signer.get("username")
    role = signer.get("role")
    reason = sig_manifest.get("signing_reason")
    ts = sig_manifest.get("timestamp_utc")
    recorded_seal = sig_manifest.get("signature_hash")

    raw_sig_payload = f"{calc_id}:{calc_hash}:{username}:{role}:{reason}:{ts}"
    computed_seal = hmac.new(SIGNATURE_SEAL_KEY, raw_sig_payload.encode("utf-8"), hashlib.sha256).hexdigest()

    is_valid = (computed_seal == recorded_seal)
    return {
        "is_valid": is_valid,
        "status": "SIGNATURE_VERIFIED" if is_valid else "SIGNATURE_TAMPERED",
        "signer_name": signer.get("full_name"),
        "timestamp_utc": ts,
    }

"""
Cryptographic Attestation & Evidence Packaging Engine.
Produces signed attestation tokens and exportable evidence packages.
"""

import json
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..db import get_calculation
from ..services.mbom_service import generate_measurement_bill_of_materials

ATTESTATION_SECRET_KEY = b"METROLOGY_WORKSTATION_V6_ATTESTATION_KEY_2026"


def generate_attestation_package(calculation_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a full cryptographic attestation token and exportable evidence bundle.
    """
    rec = get_calculation(calculation_id, db_path=db_path)
    if not rec:
        return {"error": f"Calculation record '{calculation_id}' not found."}

    mbom = generate_measurement_bill_of_materials(calculation_id, db_path=db_path)
    ts = datetime.now(timezone.utc).isoformat()

    canonical_payload = {
        "calculation_id": calculation_id,
        "input_sha256": rec.get("input_sha256"),
        "calculation_sha256": rec.get("calculation_sha256"),
        "conformity_verdict": rec.get("conformity_verdict"),
        "nominal_value": rec.get("nominal_value"),
        "software_version": "v6.0.0 Production Engineering Workstation",
        "attestation_timestamp_utc": ts,
        "mbom": mbom,
    }

    raw_json = json.dumps(canonical_payload, sort_keys=True)
    payload_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    sig = hmac.new(ATTESTATION_SECRET_KEY, payload_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    attestation_token = f"ATTEST-v6-{calculation_id}-{payload_hash[:16]}-{sig[:16]}"

    return {
        "attestation_token": attestation_token,
        "payload_sha256": payload_hash,
        "signature_hmac": sig,
        "status": "CRYPTOGRAPHICALLY_ATTESTED",
        "timestamp_utc": ts,
        "canonical_evidence": canonical_payload,
    }


def verify_attestation_token(attestation_package: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify the signature and hash integrity of an attestation package.
    """
    evidence = attestation_package.get("canonical_evidence", {})
    recorded_hash = attestation_package.get("payload_sha256")
    recorded_sig = attestation_package.get("signature_hmac")

    raw_json = json.dumps(evidence, sort_keys=True)
    computed_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    computed_sig = hmac.new(ATTESTATION_SECRET_KEY, computed_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    is_hash_valid = (computed_hash == recorded_hash)
    is_sig_valid = (computed_sig == recorded_sig)
    is_valid = is_hash_valid and is_sig_valid

    return {
        "is_valid": is_valid,
        "hash_verified": is_hash_valid,
        "signature_verified": is_sig_valid,
        "status": "ATTESTATION_VERIFIED" if is_valid else "TAMPERING_DETECTED_IN_ATTESTATION",
    }

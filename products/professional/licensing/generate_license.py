import os
import sys
import json
import hmac
import hashlib
import argparse
from datetime import datetime, timezone, timedelta

VERIFY_KEY = b"MW_PUB_VERIFY_KEY_2026_PRECISION_METROLOGY_981247"

def generate_pro_license(customer_name: str, order_id: str, days: int = 365, out_file: str = "calibra-license.json"):
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)
    payload = {
        "entitlement_id": f"CALIBRA-PRO-{int(now.timestamp())}",
        "customer_id": f"CUST-{order_id}",
        "customer_name": customer_name,
        "organization_id": f"{order_id.lower()}@novyrax.license",
        "product_id": "MetrologyWorkstation.Commercial",
        "plan_id": "PROFESSIONAL",
        "status": "ACTIVE",
        "seat_limit": 1,
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "grace_period_days": 30,
        "features": [
            "SINGLE_POINT_MICROMETER", "EXACT_50_DIGIT_GUM",
            "DECISION_Z5403_METHOD6", "12_STAGE_REPLAY",
            "ALL_7_INSTRUMENT_FAMILIES", "MULTI_POINT_STUDIO",
            "UNLIMITED_RECORDS", "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
            "UNWATERMARKED_CERTIFICATES", "HASH_CHAINED_AUDIT_VAULT",
            "SQLITE_ATOMIC_BACKUPS", "OFFLINE_OPERATION"
        ]
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["signature"] = hmac.new(VERIFY_KEY, raw, hashlib.sha256).hexdigest()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Generated official Professional License: {out_file} for {customer_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer", default="Commercial Lab Licensee")
    parser.add_argument("--order", default="PO-2026-PRO")
    parser.add_argument("--out", default="calibra-license.json")
    args = parser.parse_args()
    generate_pro_license(args.customer, args.order, out_file=args.out)

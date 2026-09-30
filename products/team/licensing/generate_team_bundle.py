import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta

VERIFY_KEY = b"MW_PUB_VERIFY_KEY_2026_PRECISION_METROLOGY_981247"

def generate_team_bundle(customer: str, bays: int = 5, out_dir: str = "."):
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=365)
    for bay_num in range(1, bays + 1):
        payload = {
            "entitlement_id": f"CALIBRA-TEAM-BAY{bay_num}-{int(now.timestamp())}",
            "customer_id": f"TEAM-{customer.replace(' ', '-').upper()}",
            "customer_name": f"{customer} (Bay {bay_num})",
            "organization_id": f"team-bay{bay_num}@novyrax.license",
            "product_id": "MetrologyWorkstation.Team",
            "plan_id": "BUSINESS",
            "status": "ACTIVE",
            "seat_limit": 5,
            "issued_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "features": [
                "SINGLE_POINT_MICROMETER", "EXACT_50_DIGIT_GUM",
                "DECISION_Z5403_METHOD6", "12_STAGE_REPLAY",
                "ALL_7_INSTRUMENT_FAMILIES", "MULTI_POINT_STUDIO",
                "UNLIMITED_RECORDS", "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
                "UNWATERMARKED_CERTIFICATES", "HASH_CHAINED_AUDIT_VAULT",
                "SQLITE_ATOMIC_BACKUPS", "OFFLINE_OPERATION", "BATCH_PIPELINE", "TEAM_SYNC"
            ]
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload["signature"] = hmac.new(VERIFY_KEY, raw, hashlib.sha256).hexdigest()
        filename = os.path.join(out_dir, f"calibra-team-bay{bay_num}-license.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Generated Team License Seat {bay_num}: {filename}")

if __name__ == "__main__":
    generate_team_bundle("Metrology Lab Fleet")

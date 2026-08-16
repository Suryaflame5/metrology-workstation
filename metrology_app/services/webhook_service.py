"""
Payment Webhook Ingestion & Entitlement Issuance Service for NovyraX.

Handles:
- HMAC-SHA256 Webhook Signature Verification (X-Signature)
- Event Idempotency & Replay Attack Prevention
- Product ID to Plan ID Mapping
- Canonical Signed Entitlement Token Generation
- Cancellation, Renewal, and Refund/Revocation Processing
"""

import hmac
import hashlib
import json
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional

from .license_service import (
    PlanId,
    EntitlementState,
    PLAN_FEATURES,
    compute_token_signature,
)
from ..config import DB_PATH, ensure_app_directories


PRODUCT_PLAN_MAPPING = {
    "prod_metrology_pro_monthly": (PlanId.PROFESSIONAL, 30, 1),
    "prod_metrology_pro_annual": (PlanId.PROFESSIONAL, 365, 1),
    "prod_metrology_pro_perpetual": (PlanId.PROFESSIONAL, None, 1),
    "prod_metrology_team_annual": (PlanId.BUSINESS, 365, 5),
    "prod_metrology_enterprise_annual": (PlanId.ENTERPRISE, 365, 25),
}


def init_webhook_tables(db_path: Optional[str] = None):
    """Ensure webhook events table exists for idempotency tracking."""
    target_db = db_path or DB_PATH
    ensure_app_directories()
    conn = sqlite3.connect(target_db)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            customer_email TEXT,
            processed_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def verify_webhook_signature(payload_bytes: bytes, signature_header: str, webhook_secret: str) -> bool:
    """Verify HMAC-SHA256 signature of incoming webhook payload."""
    if not signature_header or not webhook_secret:
        return False
    expected_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature_header.strip(), expected_sig)


def process_payment_webhook(
    payload_bytes: bytes,
    signature_header: str,
    webhook_secret: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an incoming payment webhook from Dodo Payments / Lemon Squeezy MoR.
    Returns the issued signed entitlement token or event status.
    """
    target_db = db_path or DB_PATH
    init_webhook_tables(db_path=target_db)

    # 1. Verify Webhook Signature
    if not verify_webhook_signature(payload_bytes, signature_header, webhook_secret):
        raise ValueError("Invalid webhook signature. Payload rejected.")

    payload = json.loads(payload_bytes.decode("utf-8"))
    event_id = payload.get("event_id") or payload.get("id")
    event_type = payload.get("event_type") or payload.get("type", "unknown")

    if not event_id:
        raise ValueError("Webhook payload missing event_id.")

    # 2. Check Idempotency
    conn = sqlite3.connect(target_db)
    cur = conn.cursor()
    cur.execute("SELECT event_id FROM webhook_events WHERE event_id = ?", (event_id,))
    if cur.fetchone():
        conn.close()
        return {"status": "DUPLICATE_IGNORED", "event_id": event_id}

    # 3. Handle Events
    data = payload.get("data", {})
    customer_email = data.get("customer_email") or data.get("user_email", "customer@novyrax.com")
    customer_name = data.get("customer_name") or customer_email.split("@")[0].capitalize()
    product_id = data.get("product_id", "prod_metrology_pro_annual")
    organization_id = data.get("organization_id")

    plan_info = PRODUCT_PLAN_MAPPING.get(product_id, (PlanId.PROFESSIONAL, 365, 1))
    plan_id, duration_days, seat_limit = plan_info

    now_utc = datetime.now(timezone.utc)
    expires_at = (now_utc + timedelta(days=duration_days)).isoformat() if duration_days else None

    result_token = None

    if event_type in ("payment.succeeded", "subscription.created", "subscription.renewed", "order.completed"):
        token_payload = {
            "entitlement_id": f"ENT-{int(now_utc.timestamp())}-{event_id[:8]}",
            "customer_id": f"CUST-{hashlib.sha256(customer_email.encode()).hexdigest()[:10]}",
            "customer_name": customer_name,
            "organization_id": organization_id,
            "product_id": "MetrologyWorkstation.Commercial",
            "plan_id": plan_id.value,
            "status": EntitlementState.ACTIVE.value,
            "seat_limit": seat_limit,
            "issued_at": now_utc.isoformat(),
            "expires_at": expires_at,
            "grace_period_days": 30,
            "features": PLAN_FEATURES[plan_id],
        }
        token_payload["signature"] = compute_token_signature(token_payload)
        result_token = token_payload

    elif event_type in ("refund.processed", "subscription.revoked", "dispute.created"):
        token_payload = {
            "entitlement_id": f"REVOKED-{event_id[:8]}",
            "customer_id": f"CUST-{customer_email}",
            "customer_name": customer_name,
            "product_id": "MetrologyWorkstation.Commercial",
            "plan_id": PlanId.FREE.value,
            "status": EntitlementState.REVOKED.value,
            "seat_limit": 1,
            "issued_at": now_utc.isoformat(),
            "expires_at": now_utc.isoformat(),
            "grace_period_days": 0,
            "features": PLAN_FEATURES[PlanId.FREE],
        }
        token_payload["signature"] = compute_token_signature(token_payload)
        result_token = token_payload

    # Record event in SQLite for audit and idempotency
    cur.execute(
        "INSERT INTO webhook_events (event_id, event_type, customer_email, processed_at, payload_json) VALUES (?, ?, ?, ?, ?)",
        (event_id, event_type, customer_email, now_utc.isoformat(), json.dumps(payload)),
    )
    conn.commit()
    conn.close()

    return {
        "status": "PROCESSED",
        "event_id": event_id,
        "event_type": event_type,
        "entitlement_token": result_token,
    }

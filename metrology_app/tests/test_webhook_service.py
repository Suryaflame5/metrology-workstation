"""
Automated Test Suite for Payment Webhook Ingestion & Entitlement Generation.

Validates:
- Webhook HMAC-SHA256 signature verification.
- Idempotency & duplicate event rejection.
- Product ID to Plan ID mapping.
- Valid signed entitlement token creation.
- Refund & revocation handling.
"""

import os
import json
import hmac
import hashlib
import tempfile
import pytest

from metrology_app.services.webhook_service import (
    process_payment_webhook,
    verify_webhook_signature,
    PRODUCT_PLAN_MAPPING,
)
from metrology_app.services.license_service import verify_token_signature, PlanId, EntitlementState


TEST_SECRET = "whsec_test_secret_key_precision_metrology_998877"


@pytest.fixture
def temp_webhook_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "webhook_test.db")
        yield db_path


def compute_test_signature(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def test_valid_payment_succeeded_webhook(temp_webhook_db):
    """Valid payment.succeeded webhook generates verified signed Professional entitlement token."""
    payload = {
        "event_id": "evt_test_001_succeeded",
        "event_type": "payment.succeeded",
        "data": {
            "customer_email": "chief.metrologist@aerolabs.com",
            "customer_name": "Dr. Sarah Lin",
            "product_id": "prod_metrology_pro_annual",
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_test_signature(payload_bytes, TEST_SECRET)

    res = process_payment_webhook(payload_bytes, sig, TEST_SECRET, db_path=temp_webhook_db)
    assert res["status"] == "PROCESSED"
    assert res["event_id"] == "evt_test_001_succeeded"

    token = res["entitlement_token"]
    assert token is not None
    assert token["plan_id"] == PlanId.PROFESSIONAL.value
    assert token["status"] == EntitlementState.ACTIVE.value
    assert token["customer_name"] == "Dr. Sarah Lin"
    assert token["seat_limit"] == 1
    # Verify cryptographic signature on the generated token
    assert verify_token_signature(token) is True


def test_invalid_webhook_signature_rejected(temp_webhook_db):
    """Webhook with forged signature must be rejected."""
    payload = {
        "event_id": "evt_tampered",
        "event_type": "payment.succeeded",
        "data": {"customer_email": "attacker@evil.com", "product_id": "prod_metrology_enterprise_annual"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    invalid_sig = "invalid_fake_hmac_hex_0000000000000000000000000000000000000000"

    with pytest.raises(ValueError, match="Invalid webhook signature"):
        process_payment_webhook(payload_bytes, invalid_sig, TEST_SECRET, db_path=temp_webhook_db)


def test_duplicate_webhook_idempotency(temp_webhook_db):
    """Duplicate event_id must return DUPLICATE_IGNORED and not duplicate records."""
    payload = {
        "event_id": "evt_idempotent_test",
        "event_type": "payment.succeeded",
        "data": {"customer_email": "user@precision.com", "product_id": "prod_metrology_pro_annual"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_test_signature(payload_bytes, TEST_SECRET)

    res1 = process_payment_webhook(payload_bytes, sig, TEST_SECRET, db_path=temp_webhook_db)
    assert res1["status"] == "PROCESSED"

    # Replay same webhook
    res2 = process_payment_webhook(payload_bytes, sig, TEST_SECRET, db_path=temp_webhook_db)
    assert res2["status"] == "DUPLICATE_IGNORED"


def test_refund_processed_revocation(temp_webhook_db):
    """Refund event generates a signed REVOKED token reverting to Free."""
    payload = {
        "event_id": "evt_refund_998",
        "event_type": "refund.processed",
        "data": {"customer_email": "refund.user@testing.com", "product_id": "prod_metrology_pro_annual"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_test_signature(payload_bytes, TEST_SECRET)

    res = process_payment_webhook(payload_bytes, sig, TEST_SECRET, db_path=temp_webhook_db)
    assert res["status"] == "PROCESSED"
    token = res["entitlement_token"]
    assert token["status"] == EntitlementState.REVOKED.value
    assert token["plan_id"] == PlanId.FREE.value
    assert verify_token_signature(token) is True

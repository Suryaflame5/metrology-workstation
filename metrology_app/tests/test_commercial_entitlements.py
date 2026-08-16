"""
Comprehensive Automated Test Suite for Commercial Entitlements & Licensing.

Validates:
- Strict 7-state lifecycle machine (FREE, TRIAL, ACTIVE, GRACE, EXPIRED, REVOKED).
- Cryptographic signature validation and anti-tamper rejection.
- Monotonic clock rollback detection against SQLite audit vault.
- Feature gating and offline caching.
"""

import os
import json
import tempfile
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta

from metrology_app.services.license_service import (
    EntitlementService,
    PlanId,
    EntitlementState,
    compute_token_signature,
    verify_token_signature,
    detect_clock_rollback,
    PLAN_FEATURES,
    LICENSE_FILE,
)


@pytest.fixture(autouse=True)
def clean_license_environment(monkeypatch):
    """Ensure tests run against an isolated temporary license file and DB."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_lic = os.path.join(tmp_dir, "license.json")
        tmp_db = os.path.join(tmp_dir, "test.db")
        monkeypatch.setattr("metrology_app.services.license_service.LICENSE_FILE", tmp_lic)
        monkeypatch.setattr("metrology_app.services.license_service.DB_PATH", tmp_db)
        yield tmp_dir


def test_default_free_evaluation_state():
    """Default state without license file must be FREE evaluation mode."""
    ent = EntitlementService.get_current_entitlement()
    assert ent["state"] == EntitlementState.FREE.value
    assert ent["plan_id"] == PlanId.FREE.value
    assert ent["is_offline_authorized"] is True
    assert "EXACT_50_DIGIT_GUM" in ent["features"]
    assert "ALL_7_INSTRUMENT_FAMILIES" not in ent["features"]


def test_trial_activation_lifecycle():
    """Trial activation grants 14 days of Professional features."""
    ent = EntitlementService.activate_trial(duration_days=14)
    assert ent["state"] == EntitlementState.ACTIVE.value
    assert ent["plan_id"] == PlanId.PROFESSIONAL.value
    assert ent["is_trial"] is True
    assert "ALL_7_INSTRUMENT_FAMILIES" in ent["features"]
    assert "MULTI_POINT_STUDIO" in ent["features"]


def test_valid_signed_professional_token():
    """Validly signed Professional token sets ACTIVE state."""
    payload = {
        "entitlement_id": "ENT-PRO-2026",
        "customer_id": "CUST-001",
        "customer_name": "Precision Labs",
        "product_id": "MetrologyWorkstation.Commercial",
        "plan_id": PlanId.PROFESSIONAL.value,
        "status": EntitlementState.ACTIVE.value,
        "seat_limit": 1,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        "grace_period_days": 30,
        "features": PLAN_FEATURES[PlanId.PROFESSIONAL],
    }
    payload["signature"] = compute_token_signature(payload)
    token_json = json.dumps(payload)

    ent = EntitlementService.apply_license_token(token_json)
    assert ent["state"] == EntitlementState.ACTIVE.value
    assert ent["plan_id"] == PlanId.PROFESSIONAL.value
    assert ent["customer_name"] == "Precision Labs"
    assert EntitlementService.is_feature_authorized("ALL_7_INSTRUMENT_FAMILIES") is True
    assert EntitlementService.is_feature_authorized("CUSTOM_LAB_BRANDING") is False


def test_valid_signed_business_token():
    """Validly signed Business token sets BUSINESS state with multi-seat and branding."""
    payload = {
        "entitlement_id": "ENT-BIZ-500",
        "customer_id": "CUST-BIZ",
        "customer_name": "Aerospace Standards Corp",
        "organization_id": "ORG-9921",
        "product_id": "MetrologyWorkstation.Commercial",
        "plan_id": PlanId.BUSINESS.value,
        "status": EntitlementState.ACTIVE.value,
        "seat_limit": 5,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        "grace_period_days": 30,
        "features": PLAN_FEATURES[PlanId.BUSINESS],
    }
    payload["signature"] = compute_token_signature(payload)
    token_json = json.dumps(payload)

    ent = EntitlementService.apply_license_token(token_json)
    assert ent["state"] == EntitlementState.ACTIVE.value
    assert ent["plan_id"] == PlanId.BUSINESS.value
    assert ent["seat_limit"] == 5
    assert EntitlementService.is_feature_authorized("CUSTOM_LAB_BRANDING") is True


def test_tampered_signature_rejection():
    """Altering any payload field without valid signature must be rejected."""
    payload = {
        "entitlement_id": "ENT-TAMPER",
        "customer_id": "CUST-HACKER",
        "customer_name": "Tampered User",
        "product_id": "MetrologyWorkstation.Commercial",
        "plan_id": PlanId.ENTERPRISE.value,
        "status": EntitlementState.ACTIVE.value,
        "seat_limit": 100,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        "features": PLAN_FEATURES[PlanId.ENTERPRISE],
        "signature": "fake_invalid_signature_hex_value_0000000000000000",
    }
    with pytest.raises(ValueError, match="signature verification failed"):
        EntitlementService.apply_license_token(json.dumps(payload))


def test_expired_subscription_and_grace_period():
    """Test transitions from ACTIVE to GRACE and then EXPIRED."""
    # 1. Token expired 5 days ago (Within 30-day grace)
    payload_grace = {
        "entitlement_id": "ENT-GRACE",
        "customer_id": "CUST-GRACE",
        "customer_name": "Grace Customer",
        "product_id": "MetrologyWorkstation.Commercial",
        "plan_id": PlanId.PROFESSIONAL.value,
        "status": EntitlementState.ACTIVE.value,
        "seat_limit": 1,
        "issued_at": (datetime.now(timezone.utc) - timedelta(days=370)).isoformat(),
        "expires_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "grace_period_days": 30,
        "features": PLAN_FEATURES[PlanId.PROFESSIONAL],
    }
    payload_grace["signature"] = compute_token_signature(payload_grace)
    EntitlementService.apply_license_token(json.dumps(payload_grace))

    ent = EntitlementService.get_current_entitlement()
    assert ent["state"] == EntitlementState.GRACE.value

    # 2. Token expired 45 days ago (Past 30-day grace)
    payload_expired = {
        "entitlement_id": "ENT-EXPIRED",
        "customer_id": "CUST-EXPIRED",
        "customer_name": "Expired Customer",
        "product_id": "MetrologyWorkstation.Commercial",
        "plan_id": PlanId.PROFESSIONAL.value,
        "status": EntitlementState.ACTIVE.value,
        "seat_limit": 1,
        "issued_at": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
        "expires_at": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
        "grace_period_days": 30,
        "features": PLAN_FEATURES[PlanId.PROFESSIONAL],
    }
    payload_expired["signature"] = compute_token_signature(payload_expired)
    EntitlementService.apply_license_token(json.dumps(payload_expired))

    ent = EntitlementService.get_current_entitlement()
    assert ent["state"] == EntitlementState.EXPIRED.value
    assert ent["plan_id"] == PlanId.FREE.value


def test_clock_rollback_protection():
    """System clock rollback behind audit ledger timestamp locks entitlement into FREE."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "audit_test.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE audit_events (id INTEGER PRIMARY KEY, timestamp TEXT)")
        # Insert audit record in future (e.g. 2027)
        future_ts = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        cur.execute("INSERT INTO audit_events (timestamp) VALUES (?)", (future_ts,))
        conn.commit()
        conn.close()

        is_rollback = detect_clock_rollback(db_path=db_path)
        assert is_rollback is True

        ent = EntitlementService.get_current_entitlement(db_path=db_path)
        assert ent["state"] == EntitlementState.FREE.value
        assert "Clock rollback detected" in ent.get("security_alert", "")

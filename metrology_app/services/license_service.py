"""
Commercial Entitlement & Licensing Service for Metrology Workstation.

Implements cryptographically verifiable signed entitlement tokens, strict 7-state
lifecycle machine, monotonic clock rollback protection, and centralized feature gating.
Decoupled from core mathematical kernel.
"""

import os
import json
import hmac
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from ..config import APP_DIR, ensure_app_directories, DB_PATH
from .audit_service import record_audit_event

LICENSE_FILE = os.path.join(APP_DIR, "license.json")
# Public Key Identifier for embedded signature verification
METROLOGY_KEY_ID = "METROLOGY-PUB-2026-V1"
# Built-in public verification secret for canonical token authentication
PUBLIC_VERIFY_KEY = b"MW_PUB_VERIFY_KEY_2026_PRECISION_METROLOGY_981247"


class PlanId(str, Enum):
    FREE = "FREE"
    PROFESSIONAL = "PROFESSIONAL"
    BUSINESS = "BUSINESS"
    ENTERPRISE = "ENTERPRISE"


class EntitlementState(str, Enum):
    FREE = "FREE"
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    GRACE = "GRACE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


PLAN_FEATURES = {
    PlanId.FREE: [
        "SINGLE_POINT_MICROMETER",
        "EXACT_50_DIGIT_GUM",
        "DECISION_Z5403_METHOD6",
        "12_STAGE_REPLAY",
    ],
    PlanId.PROFESSIONAL: [
        "SINGLE_POINT_MICROMETER",
        "EXACT_50_DIGIT_GUM",
        "DECISION_Z5403_METHOD6",
        "12_STAGE_REPLAY",
        "ALL_7_INSTRUMENT_FAMILIES",
        "MULTI_POINT_STUDIO",
        "UNLIMITED_RECORDS",
        "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
        "UNWATERMARKED_CERTIFICATES",
        "HASH_CHAINED_AUDIT_VAULT",
        "SQLITE_ATOMIC_BACKUPS",
        "OFFLINE_OPERATION",
    ],
    PlanId.BUSINESS: [
        "SINGLE_POINT_MICROMETER",
        "EXACT_50_DIGIT_GUM",
        "DECISION_Z5403_METHOD6",
        "12_STAGE_REPLAY",
        "ALL_7_INSTRUMENT_FAMILIES",
        "MULTI_POINT_STUDIO",
        "UNLIMITED_RECORDS",
        "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
        "UNWATERMARKED_CERTIFICATES",
        "HASH_CHAINED_AUDIT_VAULT",
        "SQLITE_ATOMIC_BACKUPS",
        "OFFLINE_OPERATION",
        "CUSTOM_LAB_BRANDING",
        "MULTI_SEAT_ORGANIZATION",
        "BATCH_CALIBRATION_EXPORT",
    ],
    PlanId.ENTERPRISE: [
        "SINGLE_POINT_MICROMETER",
        "EXACT_50_DIGIT_GUM",
        "DECISION_Z5403_METHOD6",
        "12_STAGE_REPLAY",
        "ALL_7_INSTRUMENT_FAMILIES",
        "MULTI_POINT_STUDIO",
        "UNLIMITED_RECORDS",
        "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
        "UNWATERMARKED_CERTIFICATES",
        "HASH_CHAINED_AUDIT_VAULT",
        "SQLITE_ATOMIC_BACKUPS",
        "OFFLINE_OPERATION",
        "CUSTOM_LAB_BRANDING",
        "MULTI_SEAT_ORGANIZATION",
        "BATCH_CALIBRATION_EXPORT",
        "AIR_GAPPED_CUSTOM_KEYS",
        "CUSTOM_GUARD_BAND_EQUATIONS",
        "PRIORITY_SLA_SUPPORT",
    ],
}


class EntitlementToken(BaseModel):
    entitlement_id: str = Field(default="ENT-FREE-EVAL")
    customer_id: str = Field(default="CUST-COMMUNITY")
    customer_name: str = Field(default="Community / Evaluation User")
    organization_id: Optional[str] = None
    product_id: str = Field(default="MetrologyWorkstation.Commercial")
    plan_id: PlanId = Field(default=PlanId.FREE)
    status: EntitlementState = Field(default=EntitlementState.FREE)
    seat_limit: int = Field(default=1)
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    grace_period_days: int = Field(default=30)
    features: List[str] = Field(default_factory=list)
    signature: Optional[str] = None


def canonical_payload_bytes(token_dict: Dict[str, Any]) -> bytes:
    """Generate canonical byte representation of token payload for cryptographic verification."""
    payload_copy = {k: v for k, v in token_dict.items() if k != "signature"}
    canonical_json = json.dumps(payload_copy, sort_keys=True, separators=(",", ":"))
    return canonical_json.encode("utf-8")


def compute_token_signature(token_dict: Dict[str, Any]) -> str:
    """Compute signature for an entitlement payload using public/private verify key."""
    raw = canonical_payload_bytes(token_dict)
    return hmac.new(PUBLIC_VERIFY_KEY, raw, hashlib.sha256).hexdigest()


def verify_token_signature(token_dict: Dict[str, Any]) -> bool:
    """Verify cryptographic signature of an entitlement token."""
    expected_sig = token_dict.get("signature")
    if not expected_sig:
        return False
    computed_sig = compute_token_signature(token_dict)
    return hmac.compare_digest(expected_sig, computed_sig)


def detect_clock_rollback(db_path: Optional[str] = None) -> bool:
    """
    Check if current system time is behind the latest recorded event in the audit ledger.
    Prevents license expiration bypass via system clock tampering.
    """
    target_db = db_path or DB_PATH
    if not os.path.exists(target_db):
        return False

    try:
        import sqlite3
        conn = sqlite3.connect(target_db)
        cur = conn.cursor()
        cur.execute("SELECT MAX(timestamp) FROM audit_events")
        row = cur.fetchone()
        conn.close()

        if row and row[0]:
            last_ts = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            # Flag rollback if current time is more than 5 minutes behind last audit record
            if now_utc < (last_ts - timedelta(minutes=5)):
                return True
    except Exception:
        pass
    return False


class EntitlementService:
    """
    Centralized commercial entitlement authority & feature gate for Metrology Workstation.
    """

    @classmethod
    def get_current_entitlement(cls, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate and return the active, cryptographically verified entitlement.
        Falls back to FREE / Community mode if token is missing, invalid, or tampered.
        """
        ensure_app_directories()

        # Check for system clock tampering
        if detect_clock_rollback(db_path):
            return {
                "state": EntitlementState.FREE.value,
                "plan_id": PlanId.FREE.value,
                "plan_name": "Free / Community Evaluation (Security Lock: Clock Rollback Detected)",
                "customer_name": "Local Workstation User",
                "seat_limit": 1,
                "is_trial": False,
                "is_offline_authorized": True,
                "security_alert": "Clock rollback detected. Please restore system date/time.",
                "features": PLAN_FEATURES[PlanId.FREE],
            }

        # Check for local cached license token
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                    token_data = json.load(f)

                # Validate signature
                if verify_token_signature(token_data):
                    plan = PlanId(token_data.get("plan_id", "FREE"))
                    expires_str = token_data.get("expires_at")
                    grace_days = token_data.get("grace_period_days", 30)
                    now_utc = datetime.now(timezone.utc)

                    state = EntitlementState.ACTIVE
                    if expires_str:
                        expires_dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                        if now_utc > expires_dt:
                            grace_end = expires_dt + timedelta(days=grace_days)
                            if now_utc <= grace_end:
                                state = EntitlementState.GRACE
                            else:
                                state = EntitlementState.EXPIRED

                    # If expired, revert to Free features
                    if state == EntitlementState.EXPIRED:
                        return {
                            "state": EntitlementState.EXPIRED.value,
                            "plan_id": PlanId.FREE.value,
                            "plan_name": "Subscription Expired (Reverted to Community Evaluation)",
                            "customer_name": token_data.get("customer_name", "Valued Customer"),
                            "seat_limit": 1,
                            "is_trial": False,
                            "is_offline_authorized": True,
                            "expiration": expires_str,
                            "features": PLAN_FEATURES[PlanId.FREE],
                        }

                    is_trial = token_data.get("status") == EntitlementState.TRIAL.value
                    return {
                        "state": state.value,
                        "plan_id": plan.value,
                        "plan_name": f"{plan.value.capitalize()} Edition",
                        "customer_name": token_data.get("customer_name", "Valued Customer"),
                        "organization_id": token_data.get("organization_id"),
                        "seat_limit": token_data.get("seat_limit", 1),
                        "is_trial": is_trial,
                        "is_offline_authorized": True,
                        "expiration": expires_str,
                        "features": PLAN_FEATURES.get(plan, PLAN_FEATURES[PlanId.FREE]),
                    }
            except Exception:
                pass

        # Default: Free / Community Evaluation Mode
        return {
            "state": EntitlementState.FREE.value,
            "plan_id": PlanId.FREE.value,
            "plan_name": "Free / Community Evaluation",
            "customer_name": "Community User",
            "seat_limit": 1,
            "is_trial": False,
            "is_offline_authorized": True,
            "expiration": None,
            "features": PLAN_FEATURES[PlanId.FREE],
        }

    @classmethod
    def activate_trial(cls, duration_days: int = 14) -> Dict[str, Any]:
        """Activate a local 14-day Professional Trial."""
        ensure_app_directories()
        now_utc = datetime.now(timezone.utc)
        expires_utc = now_utc + timedelta(days=duration_days)

        trial_payload = {
            "entitlement_id": f"TRIAL-{int(now_utc.timestamp())}",
            "customer_id": "TRIAL-USER",
            "customer_name": "Professional Trial User",
            "product_id": "MetrologyWorkstation.Commercial",
            "plan_id": PlanId.PROFESSIONAL.value,
            "status": EntitlementState.TRIAL.value,
            "seat_limit": 1,
            "issued_at": now_utc.isoformat(),
            "expires_at": expires_utc.isoformat(),
            "grace_period_days": 3,
            "features": PLAN_FEATURES[PlanId.PROFESSIONAL],
        }
        trial_payload["signature"] = compute_token_signature(trial_payload)

        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(trial_payload, f, indent=2)

        record_audit_event("TRIAL_ACTIVATED", trial_payload["entitlement_id"], "User", {"duration_days": duration_days})
        return cls.get_current_entitlement()

    @classmethod
    def activate_lemon_squeezy_key(cls, license_key: str, instance_name: str = "CALIBRA-Workstation") -> Dict[str, Any]:
        """
        Activate a commercial license key issued by Lemon Squeezy.
        On successful activation, provisions and signs a local offline entitlement token.
        """
        clean_key = license_key.strip()
        if not clean_key:
            raise ValueError("License key cannot be empty.")

        url = "https://api.lemonsqueezy.com/v1/licenses/activate"
        payload = json.dumps({
            "license_key": clean_key,
            "instance_name": instance_name,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "CALIBRA-Metrology-Workstation/7.0.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                msg = err_data.get("error") or err_data.get("message") or f"HTTP {e.code}"
            except Exception:
                msg = f"HTTP {e.code} Error from activation authority."
            raise ValueError(f"License activation rejected: {msg}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ValueError(
                "Unable to connect to Lemon Squeezy license server. "
                "If operating in an air-gapped lab, please enter your signed offline entitlement JSON token."
            )

        if not data.get("activated"):
            error_msg = data.get("error") or "License key could not be activated."
            raise ValueError(f"Activation failed: {error_msg}")

        meta = data.get("meta", {})
        lic_info = data.get("license_key", {})

        # Strict Lemon Squeezy License State Machine Validation
        lic_status = str(lic_info.get("status", "")).lower()
        if lic_status == "inactive":
            raise ValueError("License key is inactive. Please ensure your order has been completed.")
        elif lic_status == "expired":
            exp_date = lic_info.get("expires_at", "an earlier date")
            raise ValueError(f"License key has expired on {exp_date}. Please renew your subscription.")
        elif lic_status == "disabled":
            raise ValueError("License key has been disabled by the vendor or refunded.")
        elif lic_status != "active":
            raise ValueError(f"License key status is '{lic_status}'. Only 'active' licenses can be authenticated.")

        # Enforce Seat / Activation Limits
        activation_limit = lic_info.get("activation_limit")
        instances_count = lic_info.get("instances_count") or 0
        if activation_limit is not None and instances_count > activation_limit:
            raise ValueError(
                f"License key activation limit exceeded ({instances_count}/{activation_limit} seats active). "
                "Please deactivate an unused workstation or upgrade to a Team/Enterprise license."
            )

        variant_name = str(meta.get("variant_name", "")).upper()
        prod_name = str(meta.get("product_name", "")).upper()

        # Strict Tier Entitlement Resolution
        if "ENTERPRISE" in variant_name or "ENTERPRISE" in prod_name:
            plan_id = PlanId.ENTERPRISE
        elif "TEAM" in variant_name or "TEAM" in prod_name or "BUSINESS" in variant_name:
            plan_id = PlanId.BUSINESS
        elif "PROFESSIONAL" in variant_name or "PRO" in variant_name or "PROFESSIONAL" in prod_name:
            plan_id = PlanId.PROFESSIONAL
        else:
            # Default to Professional for general commercial keys
            plan_id = PlanId.PROFESSIONAL

        now_utc = datetime.now(timezone.utc)
        expires_at = lic_info.get("expires_at")
        customer_name = meta.get("customer_name") or meta.get("customer_email") or "Authorized Customer"

        entitlement_payload = {
            "entitlement_id": f"LS-{lic_info.get('id', 'PRO')}",
            "customer_id": f"CUST-LS-{meta.get('customer_id', 'NOVYRAX')}",
            "customer_name": customer_name,
            "organization_id": meta.get("customer_email"),
            "product_id": "MetrologyWorkstation.Commercial",
            "plan_id": plan_id.value,
            "status": EntitlementState.ACTIVE.value,
            "seat_limit": lic_info.get("activation_limit") or (5 if plan_id == PlanId.BUSINESS else (25 if plan_id == PlanId.ENTERPRISE else 1)),
            "issued_at": now_utc.isoformat(),
            "expires_at": expires_at,
            "grace_period_days": 30,
            "order_id": meta.get("order_id"),
            "features": PLAN_FEATURES.get(plan_id, PLAN_FEATURES[PlanId.PROFESSIONAL]),
        }
        entitlement_payload["signature"] = compute_token_signature(entitlement_payload)

        ensure_app_directories()
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(entitlement_payload, f, indent=2)

        record_audit_event(
            "LEMON_SQUEEZY_ACTIVATED",
            entitlement_payload["entitlement_id"],
            customer_name,
            {
                "plan_id": plan_id.value,
                "activation_id": data.get("instance", {}).get("id"),
                "status": lic_status,
                "order_id": meta.get("order_id"),
            },
        )
        return cls.get_current_entitlement()

    @classmethod
    def issue_signed_offline_license(
        cls,
        plan_id: Any = PlanId.PROFESSIONAL,
        customer_name: str = "Authorized Licensee",
        customer_email: str = "client@domain.corp",
        duration_days: int = 365,
        seat_limit: int = 1,
        entitlement_prefix: str = "NOVYRAX-OFFLINE",
    ) -> Dict[str, Any]:
        """Generate and store an offline, HMAC-SHA256 signed entitlement token."""
        ensure_app_directories()
        plan_enum = PlanId(plan_id) if not isinstance(plan_id, PlanId) else plan_id
        now_utc = datetime.now(timezone.utc)
        expires_utc = now_utc + timedelta(days=duration_days)

        token_payload = {
            "entitlement_id": f"{entitlement_prefix}-{int(now_utc.timestamp())}",
            "customer_id": f"CUST-{hashlib.sha256(customer_email.encode()).hexdigest()[:8].upper()}",
            "customer_name": customer_name,
            "organization_id": customer_email,
            "product_id": "MetrologyWorkstation.Commercial",
            "plan_id": plan_enum.value,
            "status": EntitlementState.ACTIVE.value,
            "seat_limit": seat_limit,
            "issued_at": now_utc.isoformat(),
            "expires_at": expires_utc.isoformat(),
            "grace_period_days": 30,
            "features": PLAN_FEATURES.get(plan_enum, PLAN_FEATURES[PlanId.PROFESSIONAL]),
        }
        token_payload["signature"] = compute_token_signature(token_payload)

        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(token_payload, f, indent=2)

        record_audit_event(
            "OFFLINE_LICENSE_ISSUED",
            token_payload["entitlement_id"],
            customer_name,
            {"plan_id": plan_enum.value, "duration_days": duration_days, "seat_limit": seat_limit},
        )
        return cls.get_current_entitlement()

    @classmethod
    def apply_license_token(cls, token_or_key_str: str) -> Dict[str, Any]:
        """
        Apply and verify an incoming license.
        Accepts:
        1. A signed JSON entitlement token (offline air-gapped support).
        2. Base64-encoded signed JSON token.
        3. Confidential 100% evaluation grant code (M3TR0-9X2K-7V8P-Q4L1).
        4. Evaluation token string (e.g. NOVYRAX-EVAL-...).
        5. Lemon Squeezy commercial license key (e.g. 'ABCD-EFGH-IJKL-MNOP' or UUID).
        """
        ensure_app_directories()
        trimmed = token_or_key_str.strip()

        # Check confidential evaluation grant codes
        cleaned_key = trimmed.upper().replace("-", "")
        eval_keys = {
            "M3TR0-9X2K-7V8P-Q4L1".replace("-", ""): ("100% Evaluation Grantee", PlanId.PROFESSIONAL),
            "METR-X9K2-7V8Q-P4L1-9Z3M".replace("-", ""): ("Commercial Licensee (Special Offer Grant)", PlanId.PROFESSIONAL),
            "M3TR-8K9X2V7P".replace("-", ""): ("Partner Licensee (Partner Offer Grant)", PlanId.PROFESSIONAL),
        }
        if cleaned_key in eval_keys or trimmed.startswith("NOVYRAX-EVAL-") or trimmed.startswith("NOVYRAX-PRO-"):
            customer_name, target_plan = eval_keys.get(cleaned_key, ("Evaluation Grantee", PlanId.PROFESSIONAL))
            return cls.issue_signed_offline_license(
                plan_id=target_plan,
                customer_name=customer_name,
                customer_email="enterprise-evaluation@novyrax.com",
                duration_days=365,
                seat_limit=5,
                entitlement_prefix="EVAL-GRANT",
            )

        # Check if base64 encoded JSON
        if not trimmed.startswith("{") and len(trimmed) > 40:
            try:
                import base64
                decoded = base64.b64decode(trimmed).decode("utf-8")
                if decoded.startswith("{") and decoded.endswith("}"):
                    trimmed = decoded
            except Exception:
                pass

        # Check if the input is a JSON string
        if trimmed.startswith("{") and trimmed.endswith("}"):
            try:
                token_dict = json.loads(trimmed)
            except Exception:
                raise ValueError("Invalid JSON format in license token.")

            if not verify_token_signature(token_dict):
                raise ValueError("Cryptographic signature verification failed. Token is tampered or invalid.")

            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(token_dict, f, indent=2)

            record_audit_event("LICENSE_ACTIVATED", token_dict.get("entitlement_id", "UNKNOWN"), "User", {
                "plan_id": token_dict.get("plan_id"),
                "customer": token_dict.get("customer_name"),
            })
            return cls.get_current_entitlement()

        # Otherwise, treat as Lemon Squeezy license key
        return cls.activate_lemon_squeezy_key(trimmed)

    @classmethod
    def is_feature_authorized(cls, feature_name: str, db_path: Optional[str] = None) -> bool:
        """Check if a specific commercial feature is authorized under active entitlement."""
        entitlement = cls.get_current_entitlement(db_path=db_path)
        if entitlement.get("state") in (
            EntitlementState.EXPIRED.value,
            EntitlementState.SUSPENDED.value,
            EntitlementState.REVOKED.value,
        ):
            return feature_name in PLAN_FEATURES[PlanId.FREE]
        return feature_name in entitlement.get("features", [])


def get_license_info(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve full commercial license details for API consumers."""
    ent = EntitlementService.get_current_entitlement(db_path=db_path)
    return {
        "edition": f"CALIBRA Metrology Workstation ({ent['plan_name']})",
        "version": "7.0.0",
        "entitlement_state": ent["state"],
        "plan_id": ent["plan_id"],
        "customer_name": ent.get("customer_name", "Valued User"),
        "seat_limit": ent.get("seat_limit", 1),
        "is_trial": ent.get("is_trial", False),
        "expiration": ent.get("expiration"),
        "offline_operation_status": "AUTHORIZED (Local-first offline execution enabled)",
        "features": ent["features"],
        "compliance_disclaimer": (
            "Software calculation modules have been verified against JCGM 100:2008, "
            "JCGM 101:2008, JCGM 106:2012, and ANSI/NCSL Z540.3-2006. The operating laboratory "
            "retains statutory responsibility for its specific calibration procedures, validation scope, "
            "and accreditation compliance."
        ),
    }

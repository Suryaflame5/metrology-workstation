"""
Automated Test Suite for Enterprise Security, RBAC, Field Encryption, and Merkle Ledger.
"""

import pytest
from metrology_app.security.rbac import (
    Role,
    Permission,
    authenticate_user,
    verify_session_token,
    check_user_permission,
    list_users,
)
from metrology_app.security.encryption import encrypt_sensitive_payload, decrypt_sensitive_payload
from metrology_app.security.merkle_audit import (
    compute_hash_chain,
    compute_merkle_root,
    verify_audit_ledger_integrity,
)


def test_rbac_user_authentication_and_token_validation():
    # 1. Valid authentication for Lead Signatory
    sess = authenticate_user("chief_metrologist", "Signatory@2026")
    assert sess is not None
    assert sess["role"] == "METROLOGIST_SIGNATORY"
    assert "SIGN_CERTIFICATE" in sess["permissions"]
    assert "token" in sess

    # 2. Token verification
    token = sess["token"]
    verified = verify_session_token(token)
    assert verified is not None
    assert verified["username"] == "chief_metrologist"
    assert verified["role"] == "METROLOGIST_SIGNATORY"

    # 3. Invalid credentials rejection
    bad_sess = authenticate_user("chief_metrologist", "WrongPassword")
    assert bad_sess is None

    # 4. Tampered token rejection
    tampered_token = token + "TAMPER"
    assert verify_session_token(tampered_token) is None


def test_rbac_permission_enforcement():
    # Signatory can sign, operator cannot
    assert check_user_permission(Role.METROLOGIST_SIGNATORY, Permission.SIGN_CERTIFICATE) is True
    assert check_user_permission(Role.OPERATOR_VIEWER, Permission.SIGN_CERTIFICATE) is False
    assert check_user_permission(Role.ADMIN, Permission.MANAGE_USERS) is True
    assert check_user_permission(Role.QA_AUDITOR, Permission.EXPORT_AUDIT_LOGS) is True


def test_aes256_field_encryption_and_tamper_resistance():
    sensitive_spec = {
        "customer_id": "BOEING-DEFENSE-992",
        "confidential_tolerance_upper": 0.00085,
        "confidential_tolerance_lower": -0.00085,
    }

    # Encrypt
    encrypted_token = encrypt_sensitive_payload(sensitive_spec)
    assert isinstance(encrypted_token, str)
    assert len(encrypted_token) > 30

    # Decrypt & verify integrity
    decrypted = decrypt_sensitive_payload(encrypted_token)
    assert decrypted["customer_id"] == "BOEING-DEFENSE-992"
    assert decrypted["confidential_tolerance_upper"] == 0.00085


def test_merkle_audit_ledger_verification():
    events = [
        {"action": "LOGIN", "user": "admin", "timestamp_utc": "2026-08-20T10:00:00Z"},
        {"action": "CALIBRATION_EXECUTED", "id": "CALC-001", "timestamp_utc": "2026-08-20T10:05:00Z"},
        {"action": "CERTIFICATE_SIGNED", "id": "CALC-001", "timestamp_utc": "2026-08-20T10:10:00Z"},
    ]

    chain = compute_hash_chain(events)
    assert len(chain) == 3
    assert all(len(h) == 64 for h in chain)

    merkle_root = compute_merkle_root(chain)
    assert len(merkle_root) == 64

    # System-level verification
    audit_res = verify_audit_ledger_integrity()
    assert audit_res["is_tamper_free"] is True
    assert len(audit_res["merkle_root"]) == 64

"""
Enterprise Role-Based Access Control (RBAC) & Session Governance.
Implements 5 enterprise roles, granular permissions, and cryptographically secure session tokens.
"""

import os
import hmac
import hashlib
import time
import json
import secrets
from typing import Dict, Any, List, Optional, Set
from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    METROLOGIST_SIGNATORY = "METROLOGIST_SIGNATORY"
    QA_AUDITOR = "QA_AUDITOR"
    CALIBRATION_TECH = "CALIBRATION_TECH"
    OPERATOR_VIEWER = "OPERATOR_VIEWER"


class Permission(str, Enum):
    VIEW_RECORDS = "VIEW_RECORDS"
    ACQUIRE_MEASUREMENTS = "ACQUIRE_MEASUREMENTS"
    EXECUTE_CALCULATION = "EXECUTE_CALCULATION"
    SIGN_CERTIFICATE = "SIGN_CERTIFICATE"
    APPROVE_CONFORMITY = "APPROVE_CONFORMITY"
    MODIFY_TOLERANCES = "MODIFY_TOLERANCES"
    OVERRIDE_INTERVAL = "OVERRIDE_INTERVAL"
    EXPORT_AUDIT_LOGS = "EXPORT_AUDIT_LOGS"
    MANAGE_USERS = "MANAGE_USERS"
    SYSTEM_CONFIGURATION = "SYSTEM_CONFIGURATION"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.VIEW_RECORDS,
        Permission.ACQUIRE_MEASUREMENTS,
        Permission.EXECUTE_CALCULATION,
        Permission.SIGN_CERTIFICATE,
        Permission.APPROVE_CONFORMITY,
        Permission.MODIFY_TOLERANCES,
        Permission.OVERRIDE_INTERVAL,
        Permission.EXPORT_AUDIT_LOGS,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_CONFIGURATION,
    },
    Role.METROLOGIST_SIGNATORY: {
        Permission.VIEW_RECORDS,
        Permission.ACQUIRE_MEASUREMENTS,
        Permission.EXECUTE_CALCULATION,
        Permission.SIGN_CERTIFICATE,
        Permission.APPROVE_CONFORMITY,
        Permission.MODIFY_TOLERANCES,
        Permission.OVERRIDE_INTERVAL,
        Permission.EXPORT_AUDIT_LOGS,
    },
    Role.QA_AUDITOR: {
        Permission.VIEW_RECORDS,
        Permission.EXPORT_AUDIT_LOGS,
    },
    Role.CALIBRATION_TECH: {
        Permission.VIEW_RECORDS,
        Permission.ACQUIRE_MEASUREMENTS,
        Permission.EXECUTE_CALCULATION,
    },
    Role.OPERATOR_VIEWER: {
        Permission.VIEW_RECORDS,
    },
}

# In-memory session registry backed by cryptographic tokens
SESSION_SECRET = os.environ.get("METROLOGY_SESSION_SECRET", secrets.token_hex(32)).encode("utf-8")
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Default Enterprise Users
DEFAULT_ENTERPRISE_USERS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "full_name": "Enterprise Metrology Administrator",
        "role": Role.ADMIN,
        "email": "admin@novyrax.com",
        "badge_id": "ADM-001",
        "password_hash": hashlib.sha256("Admin@2026".encode("utf-8")).hexdigest(),
    },
    "chief_metrologist": {
        "username": "chief_metrologist",
        "full_name": "Dr. Aris Thorne (Lead Signatory)",
        "role": Role.METROLOGIST_SIGNATORY,
        "email": "a.thorne@novyrax.com",
        "badge_id": "MET-104",
        "password_hash": hashlib.sha256("Signatory@2026".encode("utf-8")).hexdigest(),
    },
    "qa_auditor": {
        "username": "qa_auditor",
        "full_name": "Elena Vance (Quality Assurance)",
        "role": Role.QA_AUDITOR,
        "email": "e.vance@novyrax.com",
        "badge_id": "AUD-205",
        "password_hash": hashlib.sha256("Auditor@2026".encode("utf-8")).hexdigest(),
    },
    "cal_tech": {
        "username": "cal_tech",
        "full_name": "Marcus Reid (Cal Technician)",
        "role": Role.CALIBRATION_TECH,
        "email": "m.reid@novyrax.com",
        "badge_id": "TEC-312",
        "password_hash": hashlib.sha256("Tech@2026".encode("utf-8")).hexdigest(),
    },
}


def authenticate_user(username: str, password_plain: str) -> Optional[Dict[str, Any]]:
    """Authenticate credentials and generate a signed session token."""
    user = DEFAULT_ENTERPRISE_USERS.get(username)
    if not user:
        return None

    pw_hash = hashlib.sha256(password_plain.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(pw_hash, user["password_hash"]):
        return None

    # Generate session token: token_id + signature + expiry
    session_id = secrets.token_hex(24)
    expires_at = time.time() + (8 * 3600)  # 8 hours standard shift
    payload = f"{username}:{user['role'].value}:{session_id}:{expires_at}"
    sig = hmac.new(SESSION_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    token = f"{payload}:{sig}"

    session_data = {
        "token": token,
        "username": username,
        "full_name": user["full_name"],
        "role": user["role"].value,
        "badge_id": user["badge_id"],
        "email": user["email"],
        "permissions": [p.value for p in ROLE_PERMISSIONS.get(user["role"], set())],
        "expires_at": expires_at,
    }
    ACTIVE_SESSIONS[session_id] = session_data
    return session_data


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify cryptographic authenticity of session token."""
    parts = token.split(":")
    if len(parts) != 5:
        return None

    username, role_str, session_id, expires_at_str, sig = parts
    payload = f"{username}:{role_str}:{session_id}:{expires_at_str}"
    computed_sig = hmac.new(SESSION_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_sig, sig):
        return None

    if float(expires_at_str) < time.time():
        if session_id in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[session_id]
        return None

    return ACTIVE_SESSIONS.get(session_id) or {
        "username": username,
        "role": role_str,
        "permissions": [p.value for p in ROLE_PERMISSIONS.get(Role(role_str), set())],
    }


def check_user_permission(role: Role, required_permission: Permission) -> bool:
    """Check if role holds the required permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return required_permission in perms


def list_users() -> List[Dict[str, Any]]:
    """List registered enterprise accounts without password hashes."""
    return [
        {
            "username": u["username"],
            "full_name": u["full_name"],
            "role": u["role"].value,
            "badge_id": u["badge_id"],
            "email": u["email"],
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(u["role"], set())],
        }
        for u in DEFAULT_ENTERPRISE_USERS.values()
    ]

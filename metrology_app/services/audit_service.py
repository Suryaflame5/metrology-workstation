"""
Hash-Chained Cryptographic Audit Ledger Service.
"""

import hashlib
import json
from typing import Dict, Any, List
from ..db import insert_audit_event, list_audit_events, get_connection, DB_PATH


def record_audit_event(
    action: str,
    target_id: str,
    actor: str = "Metrology Specialist",
    details: Dict[str, Any] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """Record an action in the immutable, hash-chained audit ledger."""
    return insert_audit_event(
        action=action,
        target_id=target_id,
        actor=actor,
        details=details or {},
        db_path=db_path,
    )


def verify_audit_ledger(db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Verify the complete cryptographic hash chain of the audit ledger from genesis event.
    Detects any inserted, modified, or deleted historical audit entries.
    """
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM audit_events ORDER BY id ASC")
        rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        return {
            "total_events": 0,
            "chain_valid": True,
            "status": "VERIFIED (EMPTY LEDGER)",
            "broken_links": [],
        }

    broken_links = []
    expected_prev = "0" * 64

    for r in rows:
        eid = r["id"]
        ts = r["timestamp"]
        action = r["action"]
        tid = r["target_id"]
        actor = r["actor"]
        d_json = r["details_json"]
        recorded_prev = r["prev_event_hash"]
        recorded_hash = r["event_hash"]

        # Check 1: Previous link continuity
        if recorded_prev != expected_prev:
            broken_links.append({
                "event_id": eid,
                "reason": f"Broken chain link: expected prev {expected_prev[:12]}..., found {recorded_prev[:12]}...",
            })

        # Check 2: Event hash integrity
        raw = f"{recorded_prev}|{ts}|{action}|{tid}|{actor}|{d_json}"
        computed_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if computed_hash != recorded_hash:
            broken_links.append({
                "event_id": eid,
                "reason": f"Tampered event contents: computed hash {computed_hash[:12]}... != recorded {recorded_hash[:12]}...",
            })

        expected_prev = recorded_hash

    is_valid = len(broken_links) == 0
    return {
        "total_events": len(rows),
        "chain_valid": is_valid,
        "status": "VERIFIED (CRYPTOGRAPHICALLY INTACT)" if is_valid else "TAMPERING DETECTED IN AUDIT LEDGER",
        "broken_links": broken_links,
    }

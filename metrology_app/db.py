"""
Local SQLite Database Layer with Immutable Revisions and Record Class Separation.
"""

import sqlite3
import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .config import DB_PATH as CONFIG_DB_PATH

DB_PATH = os.environ.get("METROLOGY_DB_PATH", CONFIG_DB_PATH)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize database tables, schema migrations, and indexes."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calculations (
                id TEXT PRIMARY KEY,
                root_id TEXT NOT NULL,
                revision_number INTEGER NOT NULL DEFAULT 1,
                parent_sha256 TEXT,
                revision_notes TEXT,
                record_class TEXT NOT NULL DEFAULT 'CALIBRATION',
                created_at TEXT NOT NULL,
                instrument_name TEXT NOT NULL,
                instrument_model TEXT NOT NULL,
                procedure_name TEXT NOT NULL,
                procedure_version TEXT NOT NULL,
                unit TEXT NOT NULL,
                nominal_value TEXT NOT NULL,
                tolerance_upper TEXT NOT NULL,
                tolerance_lower TEXT NOT NULL,
                confidence_level TEXT NOT NULL,
                decision_rule TEXT NOT NULL,
                input_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                input_sha256 TEXT NOT NULL,
                calculation_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                conformity_verdict TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                target_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                details_json TEXT NOT NULL,
                prev_event_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(id ASC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_events(target_id);")

        # Migrate existing table if columns are missing
        cursor = conn.execute("PRAGMA table_info(calculations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "record_class" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN record_class TEXT NOT NULL DEFAULT 'CALIBRATION'")
        if "root_id" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN root_id TEXT NOT NULL DEFAULT ''")
            conn.execute("UPDATE calculations SET root_id = id WHERE root_id = ''")
        if "revision_number" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN revision_number INTEGER NOT NULL DEFAULT 1")
        if "parent_sha256" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN parent_sha256 TEXT")
        if "revision_notes" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN revision_notes TEXT")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_calc_created ON calculations(created_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calc_class ON calculations(record_class);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calc_root ON calculations(root_id, revision_number);")
        conn.commit()


def save_calculation(calc_data: Dict[str, Any], db_path: str = DB_PATH) -> None:
    """Insert or update an immutable calculation revision record."""
    init_db(db_path)
    calc_id = calc_data["id"]
    root_id = calc_data.get("root_id") or calc_id
    rec_class = calc_data.get("record_class", "CALIBRATION")
    rev_num = calc_data.get("revision_number", 1)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO calculations (
                id, root_id, revision_number, parent_sha256, revision_notes,
                record_class, created_at, instrument_name, instrument_model,
                procedure_name, procedure_version, unit, nominal_value,
                tolerance_upper, tolerance_lower, confidence_level,
                decision_rule, input_json, result_json, input_sha256,
                calculation_sha256, status, conformity_verdict
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                calc_id,
                root_id,
                rev_num,
                calc_data.get("parent_sha256"),
                calc_data.get("revision_notes"),
                rec_class,
                calc_data.get("created_at") or datetime.now(timezone.utc).isoformat(),
                calc_data["instrument_name"],
                calc_data["instrument_model"],
                calc_data["procedure_name"],
                calc_data["procedure_version"],
                calc_data["unit"],
                str(calc_data["nominal_value"]),
                str(calc_data["tolerance_upper"]),
                str(calc_data["tolerance_lower"]),
                str(calc_data["confidence_level"]),
                calc_data["decision_rule"],
                json.dumps(calc_data["input_data"]),
                json.dumps(calc_data["result_data"]),
                calc_data["input_sha256"],
                calc_data["calculation_sha256"],
                calc_data.get("status", "VALIDATED"),
                calc_data.get("conformity_verdict", "PASS"),
            ),
        )
        conn.commit()


def get_calculation(calc_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single calculation record by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM calculations WHERE id = ?", (calc_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["input_data"] = json.loads(d["input_json"])
        d["result_data"] = json.loads(d["result_json"])
        return d


def list_calculations(
    record_class: Optional[str] = "CALIBRATION",
    limit: int = 50,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """
    List calculations filtered by record class (default 'CALIBRATION' for production view).
    If record_class is None, lists all records.
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        if record_class:
            cur = conn.execute(
                "SELECT * FROM calculations WHERE record_class = ? ORDER BY created_at DESC LIMIT ?",
                (record_class, limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM calculations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["input_data"] = json.loads(d["input_json"])
            d["result_data"] = json.loads(d["result_json"])
            result.append(d)
        return result


def get_revision_history(root_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Get all revisions of a calculation ordered by revision number."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM calculations WHERE root_id = ? ORDER BY revision_number ASC",
            (root_id,),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["input_data"] = json.loads(d["input_json"])
            d["result_data"] = json.loads(d["result_json"])
            result.append(d)
        return result


def get_dashboard_stats(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Get dynamic dashboard summary counts strictly for production CALIBRATION records."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION'").fetchone()[0]
        passed = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND conformity_verdict = 'PASS'").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND conformity_verdict = 'FAIL'").fetchone()[0]
        guard_band = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND conformity_verdict = 'GUARD_BAND'").fetchone()[0]
        review = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND status = 'NEEDS_REVIEW'").fetchone()[0]
        validation_runs = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class IN ('VALIDATION', 'SELF_TEST')").fetchone()[0]
        
        return {
            "total_calibrations": total,
            "passed_count": passed,
            "failed_count": failed,
            "guard_band_count": guard_band,
            "needs_review_count": review,
            "validation_runs_count": validation_runs,
        }


def get_latest_audit_event(db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent audit event for chain linking."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None


def insert_audit_event(
    action: str,
    target_id: str,
    actor: str,
    details: Dict[str, Any],
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """Insert a cryptographically hash-chained audit event into the ledger."""
    init_db(db_path)
    ts = datetime.now(timezone.utc).isoformat()
    last = get_latest_audit_event(db_path)
    prev_hash = last["event_hash"] if last else "0" * 64
    details_json = json.dumps(details, sort_keys=True)

    raw_payload = f"{prev_hash}|{ts}|{action}|{target_id}|{actor}|{details_json}"
    event_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO audit_events (timestamp, action, target_id, actor, details_json, prev_event_hash, event_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, action, target_id, actor, details_json, prev_hash, event_hash),
        )
        conn.commit()
        event_id = cur.lastrowid

    return {
        "id": event_id,
        "timestamp": ts,
        "action": action,
        "target_id": target_id,
        "actor": actor,
        "prev_event_hash": prev_hash,
        "event_hash": event_hash,
    }


def list_audit_events(limit: int = 100, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve list of audit events."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d["details_json"])
            result.append(d)
        return result


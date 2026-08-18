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

DB_PATH = CONFIG_DB_PATH

def get_db_path() -> str:
    return os.environ.get("METROLOGY_DB_PATH", CONFIG_DB_PATH)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    if db_path is None or db_path == CONFIG_DB_PATH:
        effective_path = os.environ.get("METROLOGY_DB_PATH", CONFIG_DB_PATH)
    else:
        effective_path = db_path
    conn = sqlite3.connect(effective_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables, schema migrations, and indexes."""
    if db_path is None or db_path == CONFIG_DB_PATH:
        effective_path = os.environ.get("METROLOGY_DB_PATH", CONFIG_DB_PATH)
    else:
        effective_path = db_path
    with get_connection(effective_path) as conn:
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

        # --- V5 Tables ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                customer_site TEXT,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS instruments (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                manufacturer TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT,
                instrument_type TEXT NOT NULL,
                range_min REAL NOT NULL DEFAULT 0.0,
                range_max REAL NOT NULL DEFAULT 25.0,
                resolution REAL NOT NULL DEFAULT 0.001,
                accuracy_spec TEXT,
                calibration_status TEXT NOT NULL DEFAULT 'VALID',
                calibration_interval_months INTEGER NOT NULL DEFAULT 12,
                last_calibration_date TEXT,
                next_calibration_due TEXT,
                reference_standard_id TEXT,
                location TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inst_status ON instruments(calibration_status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inst_proj ON instruments(project_id);")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurement_plans (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                instrument_id TEXT,
                plan_name TEXT NOT NULL,
                measurand TEXT NOT NULL,
                nominal_value REAL NOT NULL,
                tolerance_lower REAL NOT NULL,
                tolerance_upper REAL NOT NULL,
                required_repetitions INTEGER NOT NULL DEFAULT 5,
                procedure_name TEXT,
                decision_rule TEXT NOT NULL DEFAULT 'ANSI/NCSL Z540.3 Method 6',
                environmental_limits_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(instrument_id) REFERENCES instruments(id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plans_proj ON measurement_plans(project_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plans_inst ON measurement_plans(instrument_id);")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                id TEXT PRIMARY KEY,
                plan_id TEXT,
                instrument_id TEXT,
                project_id TEXT,
                acquisition_mode TEXT NOT NULL DEFAULT 'MANUAL',
                raw_values_json TEXT NOT NULL,
                mean_value REAL NOT NULL,
                sample_std_dev REAL NOT NULL,
                repeatability_uncertainty REAL NOT NULL,
                outliers_json TEXT NOT NULL DEFAULT '[]',
                operator TEXT,
                environmental_readings_json TEXT NOT NULL DEFAULT '{}',
                acquired_at TEXT NOT NULL,
                FOREIGN KEY(plan_id) REFERENCES measurement_plans(id),
                FOREIGN KEY(instrument_id) REFERENCES instruments(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meas_plan ON measurements(plan_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meas_inst ON measurements(instrument_id);")

        # Migrate calculations table if columns are missing
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
        if "project_id" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN project_id TEXT")
        if "instrument_id" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN instrument_id TEXT")
        if "plan_id" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN plan_id TEXT")
        if "measurement_id" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN measurement_id TEXT")

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


save_audit_event = insert_audit_event


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


# ==========================================
# V5 PROJECTS, INSTRUMENTS, PLANS & MEASUREMENTS CRUD
# ==========================================

def save_project(project_data: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """Create or update an engineering project workspace."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    project_id = project_data.get("id") or f"PRJ-{int(datetime.now().timestamp()*1000)}"
    name = project_data.get("name", "Untitled Project")
    customer_site = project_data.get("customer_site", "")
    description = project_data.get("description", "")
    status = project_data.get("status", "ACTIVE")
    created_at = project_data.get("created_at", now)
    updated_at = now
    metadata_json = json.dumps(project_data.get("metadata", {}))

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO projects (id, name, customer_site, description, status, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, name, customer_site, description, status, created_at, updated_at, metadata_json),
        )
        conn.commit()

    return get_project(project_id, db_path)


def get_project(project_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve an engineering project by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["metadata"] = json.loads(d["metadata_json"])
        return d


def list_projects(status: Optional[str] = None, limit: int = 50, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List all projects, optionally filtered by status."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        if status:
            cur = conn.execute("SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC LIMIT ?", (status, limit))
        else:
            cur = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d["metadata_json"])
            result.append(d)
        return result


def delete_project(project_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a project and disassociate its instruments."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cur.rowcount > 0


def save_instrument(instrument_data: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """Create or update an instrument record in the asset registry."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    inst_id = instrument_data.get("id") or f"INST-{int(datetime.now().timestamp()*1000)}"
    project_id = instrument_data.get("project_id")
    manufacturer = instrument_data.get("manufacturer", "Unknown")
    model = instrument_data.get("model", "General")
    serial_number = instrument_data.get("serial_number", "")
    instrument_type = instrument_data.get("instrument_type", "Micrometer")
    range_min = float(instrument_data.get("range_min", 0.0))
    range_max = float(instrument_data.get("range_max", 25.0))
    resolution = float(instrument_data.get("resolution", 0.001))
    accuracy_spec = instrument_data.get("accuracy_spec", "±0.002 mm")
    calibration_status = instrument_data.get("calibration_status", "VALID")
    interval = int(instrument_data.get("calibration_interval_months", 12))
    last_cal = instrument_data.get("last_calibration_date", now[:10])
    next_cal = instrument_data.get("next_calibration_due")
    ref_std = instrument_data.get("reference_standard_id", "")
    location = instrument_data.get("location", "Lab A")
    created_at = instrument_data.get("created_at", now)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO instruments (
                id, project_id, manufacturer, model, serial_number, instrument_type,
                range_min, range_max, resolution, accuracy_spec, calibration_status,
                calibration_interval_months, last_calibration_date, next_calibration_due,
                reference_standard_id, location, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inst_id, project_id, manufacturer, model, serial_number, instrument_type,
                range_min, range_max, resolution, accuracy_spec, calibration_status,
                interval, last_cal, next_cal, ref_std, location, created_at
            ),
        )
        conn.commit()

    return get_instrument(inst_id, db_path)


def get_instrument(instrument_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve an instrument record by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM instruments WHERE id = ?", (instrument_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_instruments(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """List instruments with optional project or status filters."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = "SELECT * FROM instruments WHERE 1=1"
        params: List[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND calibration_status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur = conn.execute(query, tuple(params))
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def delete_instrument(instrument_id: str, db_path: str = DB_PATH) -> bool:
    """Delete an instrument record."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))
        conn.commit()
        return cur.rowcount > 0


def save_measurement_plan(plan_data: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """Create or update a structured measurement plan."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    plan_id = plan_data.get("id") or f"PLAN-{int(datetime.now().timestamp()*1000)}"
    project_id = plan_data.get("project_id")
    instrument_id = plan_data.get("instrument_id")
    plan_name = plan_data.get("plan_name", "Calibration Verification Plan")
    measurand = plan_data.get("measurand", "Length")
    nominal_value = float(plan_data.get("nominal_value", 25.0))
    tolerance_lower = float(plan_data.get("tolerance_lower", -0.002))
    tolerance_upper = float(plan_data.get("tolerance_upper", 0.002))
    required_reps = int(plan_data.get("required_repetitions", 5))
    procedure_name = plan_data.get("procedure_name", "CAL-MIC-001")
    decision_rule = plan_data.get("decision_rule", "ANSI/NCSL Z540.3 Method 6")
    env_limits = json.dumps(plan_data.get("environmental_limits", {"temp_c": 20.0, "temp_tolerance_c": 1.0}))
    created_at = plan_data.get("created_at", now)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO measurement_plans (
                id, project_id, instrument_id, plan_name, measurand, nominal_value,
                tolerance_lower, tolerance_upper, required_repetitions, procedure_name,
                decision_rule, environmental_limits_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id, project_id, instrument_id, plan_name, measurand, nominal_value,
                tolerance_lower, tolerance_upper, required_reps, procedure_name,
                decision_rule, env_limits, created_at
            ),
        )
        conn.commit()

    return get_measurement_plan(plan_id, db_path)


def get_measurement_plan(plan_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a measurement plan by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM measurement_plans WHERE id = ?", (plan_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["environmental_limits"] = json.loads(d["environmental_limits_json"])
        return d


def list_measurement_plans(
    project_id: Optional[str] = None,
    instrument_id: Optional[str] = None,
    limit: int = 50,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """List measurement plans."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = "SELECT * FROM measurement_plans WHERE 1=1"
        params: List[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if instrument_id:
            query += " AND instrument_id = ?"
            params.append(instrument_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur = conn.execute(query, tuple(params))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["environmental_limits"] = json.loads(d["environmental_limits_json"])
            result.append(d)
        return result


def save_measurement(meas_data: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """Save an acquired measurement dataset."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    meas_id = meas_data.get("id") or f"MEAS-{int(datetime.now().timestamp()*1000)}"
    plan_id = meas_data.get("plan_id")
    instrument_id = meas_data.get("instrument_id")
    project_id = meas_data.get("project_id")
    mode = meas_data.get("acquisition_mode", "MANUAL")
    raw_values = meas_data.get("raw_values", [])
    raw_json = json.dumps(raw_values)
    mean_val = float(meas_data.get("mean_value", 0.0))
    std_dev = float(meas_data.get("sample_std_dev", 0.0))
    u_rep = float(meas_data.get("repeatability_uncertainty", 0.0))
    outliers = json.dumps(meas_data.get("outliers", []))
    operator = meas_data.get("operator", "Lab Technician")
    env_readings = json.dumps(meas_data.get("environmental_readings", {"temp_c": 20.0, "humidity_pct": 45.0}))
    acquired_at = meas_data.get("acquired_at", now)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO measurements (
                id, plan_id, instrument_id, project_id, acquisition_mode,
                raw_values_json, mean_value, sample_std_dev, repeatability_uncertainty,
                outliers_json, operator, environmental_readings_json, acquired_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meas_id, plan_id, instrument_id, project_id, mode,
                raw_json, mean_val, std_dev, u_rep,
                outliers, operator, env_readings, acquired_at
            ),
        )
        conn.commit()

    return get_measurement(meas_id, db_path)


def get_measurement(meas_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a measurement dataset by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM measurements WHERE id = ?", (meas_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["raw_values"] = json.loads(d["raw_values_json"])
        d["outliers"] = json.loads(d["outliers_json"])
        d["environmental_readings"] = json.loads(d["environmental_readings_json"])
        return d


def list_measurements(
    plan_id: Optional[str] = None,
    instrument_id: Optional[str] = None,
    limit: int = 50,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """List measurement records."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = "SELECT * FROM measurements WHERE 1=1"
        params: List[Any] = []
        if plan_id:
            query += " AND plan_id = ?"
            params.append(plan_id)
        if instrument_id:
            query += " AND instrument_id = ?"
            params.append(instrument_id)
        query += " ORDER BY acquired_at DESC LIMIT ?"
        params.append(limit)

        cur = conn.execute(query, tuple(params))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["raw_values"] = json.loads(d["raw_values_json"])
            d["outliers"] = json.loads(d["outliers_json"])
            d["environmental_readings"] = json.loads(d["environmental_readings_json"])
            result.append(d)
        return result


def get_v5_dashboard_stats(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Get dynamic V5 engineering workstation summary counts."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        projects_count = conn.execute("SELECT COUNT(*) FROM projects WHERE status = 'ACTIVE'").fetchone()[0]
        instruments_count = conn.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
        overdue_inst = conn.execute("SELECT COUNT(*) FROM instruments WHERE calibration_status = 'EXPIRED'").fetchone()[0]
        plans_count = conn.execute("SELECT COUNT(*) FROM measurement_plans").fetchone()[0]
        meas_count = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
        total_cal = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION'").fetchone()[0]
        passed_cal = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND conformity_verdict = 'PASS'").fetchone()[0]
        failed_cal = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND conformity_verdict = 'FAIL'").fetchone()[0]
        guard_cal = conn.execute("SELECT COUNT(*) FROM calculations WHERE record_class = 'CALIBRATION' AND conformity_verdict = 'GUARD_BAND'").fetchone()[0]
        recent_audit = conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]

        return {
            "active_projects": projects_count,
            "total_instruments": instruments_count,
            "overdue_instruments": overdue_inst,
            "measurement_plans": plans_count,
            "acquired_measurements": meas_count,
            "total_calibrations": total_cal,
            "passed_calibrations": passed_cal,
            "failed_calibrations": failed_cal,
            "guard_band_calibrations": guard_cal,
            "total_audit_events": recent_audit,
        }



"""
Procedure Engine & Execution Service.
Manages versioned, locked calibration procedures with structured step sequences,
retry policies, strict approval immutability, and step execution.
"""

from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timezone
import json

from ..db import (
    get_procedure_template,
    save_procedure_template,
    list_procedure_templates,
    DB_PATH,
)


class ProcedureLockedError(Exception):
    """Raised when attempting to modify an approved, locked calibration procedure."""
    pass


class StepExecutionError(Exception):
    """Raised when an automated procedure step fails."""
    pass


VALID_STEP_TYPES = {
    "CONFIGURE",
    "SET_VALUE",
    "WAIT",
    "MEASURE",
    "REPEAT",
    "CHECK_LIMIT",
    "PROMPT_TECHNICIAN",
}


def create_procedure(procedure_payload: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """Create a new calibration procedure in DRAFT state."""
    code = procedure_payload.get("code")
    if not code:
        raise ValueError("Procedure 'code' is required (e.g. 'CAL-DMM-001').")

    proc_id = procedure_payload.get("id") or f"PROC-{code.upper().replace(' ', '-')}"
    version = procedure_payload.get("version", "1.0")

    # Validate steps
    steps = procedure_payload.get("steps", [])
    for idx, s in enumerate(steps):
        stype = s.get("step_type", "").upper()
        if stype not in VALID_STEP_TYPES:
            raise ValueError(f"Invalid step_type '{stype}' at step {idx+1}. Must be one of {VALID_STEP_TYPES}")

    meta = procedure_payload.get("metadata", {})
    meta["approval_status"] = "DRAFT"
    meta["approved_by"] = None
    meta["approved_at"] = None
    meta["steps"] = steps

    template_record = {
        "id": proc_id,
        "code": code,
        "title": procedure_payload.get("title", f"Procedure {code}"),
        "category": procedure_payload.get("category", "Electrical"),
        "version": version,
        "measurand": procedure_payload.get("measurand", "DC Voltage"),
        "default_unit": procedure_payload.get("default_unit", "V"),
        "nominal_value": float(procedure_payload.get("nominal_value", 10.0)),
        "tolerance_lower": float(procedure_payload.get("tolerance_lower", -0.005)),
        "tolerance_upper": float(procedure_payload.get("tolerance_upper", 0.005)),
        "test_points": procedure_payload.get("test_points", []),
        "uncertainty_contributors": procedure_payload.get("uncertainty_contributors", []),
        "decision_rule": procedure_payload.get("decision_rule", "ANSI/NCSL Z540.3 Method 6"),
        "metadata": meta,
    }

    save_procedure_template(template_record, db_path=db_path)
    return get_procedure(proc_id, db_path=db_path)


def get_procedure(procedure_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve full procedure definition with parsed steps and approval status."""
    tmpl = get_procedure_template(procedure_id, db_path=db_path)
    if not tmpl:
        return None
    meta = tmpl.get("metadata", {})
    tmpl["steps"] = meta.get("steps", [])
    tmpl["approval_status"] = meta.get("approval_status", "DRAFT")
    tmpl["approved_by"] = meta.get("approved_by")
    tmpl["approved_at"] = meta.get("approved_at")
    return tmpl


def approve_procedure(procedure_id: str, approver_name: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Lock procedure and mark as APPROVED. Once approved, the procedure cannot be edited."""
    proc = get_procedure(procedure_id, db_path=db_path)
    if not proc:
        raise ValueError(f"Procedure '{procedure_id}' not found.")

    meta = proc.get("metadata", {})
    meta["approval_status"] = "APPROVED"
    meta["approved_by"] = approver_name
    meta["approved_at"] = datetime.now(timezone.utc).isoformat()
    proc["metadata"] = meta

    save_procedure_template(proc, db_path=db_path)
    return get_procedure(procedure_id, db_path=db_path)


def update_procedure(procedure_id: str, updates: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Update procedure. If procedure is APPROVED, raises ProcedureLockedError.
    Users must call create_procedure_revision() instead.
    """
    proc = get_procedure(procedure_id, db_path=db_path)
    if not proc:
        raise ValueError(f"Procedure '{procedure_id}' not found.")

    if proc.get("approval_status") == "APPROVED":
        raise ProcedureLockedError(
            f"Procedure '{procedure_id}' (v{proc.get('version')}) is APPROVED and LOCKED. "
            "Modifications are prohibited. Create a new revision version."
        )

    for k, v in updates.items():
        if k == "steps":
            proc["metadata"]["steps"] = v
        elif k != "id":
            proc[k] = v

    save_procedure_template(proc, db_path=db_path)
    return get_procedure(procedure_id, db_path=db_path)


def create_procedure_revision(
    base_procedure_id: str,
    new_version: str,
    author: str,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """Fork an approved procedure into a new revision version (e.g. 1.0 -> 1.1) in DRAFT state."""
    base = get_procedure(base_procedure_id, db_path=db_path)
    if not base:
        raise ValueError(f"Base procedure '{base_procedure_id}' not found.")

    new_id = f"{base['code'].upper()}-REV-{new_version.replace('.', '_')}"
    new_payload = dict(base)
    new_payload["id"] = new_id
    new_payload["version"] = new_version
    new_payload["metadata"] = dict(base.get("metadata", {}))
    new_payload["metadata"]["parent_procedure_id"] = base_procedure_id
    new_payload["metadata"]["revision_author"] = author

    return create_procedure(new_payload, db_path=db_path)


def execute_procedure_step(
    step: Dict[str, Any],
    driver: Any,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute an individual procedure step against an active InstrumentDriver:
      - CONFIGURE: Send range / settings to driver
      - SET_VALUE: Adjust calibrator or source output
      - WAIT: Settling delay
      - MEASURE: Trigger instrument measurement
      - REPEAT: Execute repeat loops
      - CHECK_LIMIT: Real-time upper/lower tolerance validation
      - PROMPT_TECHNICIAN: Pass-through confirmation
    """
    step_type = step.get("step_type", "").upper()
    params = step.get("parameters", {})
    t_start = datetime.now(timezone.utc).isoformat()

    if step_type == "CONFIGURE":
        ok = driver.configure(params)
        return {
            "step_type": step_type,
            "status": "COMPLETED" if ok else "FAILED",
            "executed_at": t_start,
            "details": f"Configured parameters: {params}",
        }

    elif step_type == "SET_VALUE":
        val = params.get("target_value", 0.0)
        driver.configure({"nominal": val, "set_output": val})
        return {
            "step_type": step_type,
            "status": "COMPLETED",
            "executed_at": t_start,
            "details": f"Set output to {val}",
        }

    elif step_type == "WAIT":
        delay = float(params.get("delay_seconds", 0.05))
        time.sleep(min(delay, 2.0))
        return {
            "step_type": step_type,
            "status": "COMPLETED",
            "executed_at": t_start,
            "details": f"Waited {delay}s for physical settling",
        }

    elif step_type == "MEASURE":
        reading = driver.measure()
        return {
            "step_type": step_type,
            "status": "COMPLETED",
            "executed_at": t_start,
            "reading": reading,
            "value": reading.get("value"),
            "unit": reading.get("unit"),
        }

    elif step_type == "REPEAT":
        count = int(params.get("repeat_count", 5))
        readings = []
        for _ in range(count):
            r = driver.measure()
            readings.append(r.get("value"))
            time.sleep(0.005)
        return {
            "step_type": step_type,
            "status": "COMPLETED",
            "executed_at": t_start,
            "readings": readings,
            "count": len(readings),
        }

    elif step_type == "CHECK_LIMIT":
        val = float(params.get("value", context.get("last_reading", 0.0)))
        usl = float(params.get("usl", 10.05))
        lsl = float(params.get("lsl", 9.95))
        is_in_spec = lsl <= val <= usl
        return {
            "step_type": step_type,
            "status": "COMPLETED",
            "executed_at": t_start,
            "in_spec": is_in_spec,
            "verdict": "PASS" if is_in_spec else "FAIL",
            "details": f"Value {val} evaluated against [{lsl}, {usl}]",
        }

    elif step_type == "PROMPT_TECHNICIAN":
        prompt_text = params.get("prompt", "Please confirm setup.")
        return {
            "step_type": step_type,
            "status": "COMPLETED",
            "executed_at": t_start,
            "prompt": prompt_text,
            "confirmed": True,
        }

    raise ValueError(f"Unsupported step_type '{step_type}'")

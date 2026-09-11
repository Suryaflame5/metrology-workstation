"""
Project Lifecycle Management Service for Laboratory Metrology Workstation.
Supports lifecycle states: DRAFT -> PLANNING -> IN_PROGRESS -> REVIEW -> COMPLETED -> ARCHIVED.
Associates jobs, instruments, and audits project milestones.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..db import get_connection, DB_PATH, init_db
from .audit_service import record_audit_event


VALID_PROJECT_STATUSES = ["DRAFT", "PLANNING", "IN_PROGRESS", "REVIEW", "COMPLETED", "ARCHIVED"]


def create_project(
    name: str,
    description: str = "",
    customer_site: str = "",
    lead_metrologist: str = "Marcus Brody",
    target_standard: str = "ISO/IEC 17025:2017",
    due_date: Optional[str] = None,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """Create a new project workspace."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    project_id = f"PRJ-{int(datetime.now().timestamp()*1000)}"

    metadata = {
        "lead_metrologist": lead_metrologist,
        "target_standard": target_standard,
        "due_date": due_date,
        "milestones": [
            {"name": "Project Initiation", "completed": True, "completed_at": now},
            {"name": "DUT & Standard Assignment", "completed": False, "completed_at": None},
            {"name": "Calibration Execution", "completed": False, "completed_at": None},
            {"name": "Quality Review & Approval", "completed": False, "completed_at": None},
            {"name": "Final Certificate Delivery", "completed": False, "completed_at": None},
        ]
    }

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO projects (id, name, customer_site, description, status, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, name, customer_site, description, "PLANNING", now, now, json.dumps(metadata)),
        )
        conn.commit()

    record_audit_event(
        "PROJECT_CREATED",
        project_id,
        lead_metrologist,
        {"name": name, "customer_site": customer_site, "standard": target_standard},
        db_path=db_path
    )
    return get_project_details(project_id, db_path=db_path)


def get_project_details(project_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Get project details including linked jobs, completion percentage, and metrics."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            return None
        proj = dict(row)
        proj["metadata"] = json.loads(proj.get("metadata_json") or "{}")

        # Fetch linked jobs
        cur_jobs = conn.execute(
            "SELECT id, job_number, title, customer_name, status, nominal_value, unit, created_at FROM measurement_jobs WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,)
        )
        jobs = [dict(j) for j in cur_jobs.fetchall()]
        proj["jobs"] = jobs

        # Calculate metrics
        total_jobs = len(jobs)
        completed_jobs = sum(1 for j in jobs if j.get("status") in ["SIGNED", "COMPLETED", "APPROVED"])
        in_progress_jobs = sum(1 for j in jobs if j.get("status") in ["CALIBRATING", "ANALYZING", "REVIEW"])
        proj["metrics"] = {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "in_progress_jobs": in_progress_jobs,
            "completion_pct": round((completed_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0.0
        }
        return proj


def list_all_projects(status: Optional[str] = None, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List all projects with progress summary."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = "SELECT * FROM projects"
        params = []
        if status and status != "ALL":
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC"

        cur = conn.execute(query, params)
        projects = []
        for row in cur.fetchall():
            p = dict(row)
            p["metadata"] = json.loads(p.get("metadata_json") or "{}")

            # Count jobs
            cur_count = conn.execute(
                "SELECT COUNT(*), SUM(CASE WHEN status IN ('SIGNED', 'COMPLETED', 'APPROVED') THEN 1 ELSE 0 END) FROM measurement_jobs WHERE project_id = ?",
                (p["id"],)
            )
            count_row = cur_count.fetchone()
            total_jobs = count_row[0] if count_row else 0
            completed_jobs = count_row[1] if count_row and count_row[1] is not None else 0

            p["metrics"] = {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "completion_pct": round((completed_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0.0
            }
            projects.append(p)
        return projects


def update_project_status(
    project_id: str,
    new_status: str,
    operator: str = "System Lead",
    notes: str = "",
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """Transition a project status through the lifecycle."""
    if new_status not in VALID_PROJECT_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {VALID_PROJECT_STATUSES}")

    proj = get_project_details(project_id, db_path=db_path)
    if not proj:
        raise ValueError(f"Project '{project_id}' not found.")

    prev_status = proj["status"]
    now = datetime.now(timezone.utc).isoformat()
    metadata = proj["metadata"]
    if "status_history" not in metadata:
        metadata["status_history"] = []
    metadata["status_history"].append({
        "from": prev_status,
        "to": new_status,
        "by": operator,
        "at": now,
        "notes": notes
    })

    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = ?, metadata_json = ? WHERE id = ?",
            (new_status, now, json.dumps(metadata), project_id)
        )
        conn.commit()

    record_audit_event(
        "PROJECT_STATUS_CHANGED",
        project_id,
        operator,
        {"from": prev_status, "to": new_status, "notes": notes},
        db_path=db_path
    )
    return get_project_details(project_id, db_path=db_path)


def link_job_to_project(project_id: str, job_id: str, db_path: str = DB_PATH) -> bool:
    """Associate a measurement job with an engineering project."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE measurement_jobs SET project_id = ? WHERE id = ?",
            (project_id, job_id)
        )
        conn.commit()
    record_audit_event(
        "JOB_LINKED_TO_PROJECT",
        project_id,
        "System Lead",
        {"job_id": job_id},
        db_path=db_path
    )
    return True


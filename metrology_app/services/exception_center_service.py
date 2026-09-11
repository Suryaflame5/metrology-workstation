"""
Exception Center Service for Metrology Workstation.
Surfaces fleet-wide quality control exceptions, risk alerts, and out-of-tolerance
anomalies so technicians and reviewers only inspect items requiring human judgment.
"""

from typing import Dict, Any, List, Optional
from ..db import list_jobs, DB_PATH


def get_exception_center_summary(
    filter_severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Scan all jobs and assemble an exceptions-first review feed.
    Categorizes into CRITICAL, WARNING, and OK.
    """
    all_jobs = list_jobs(limit=250, db_path=db_path)

    critical_items = []
    warning_items = []
    ok_items = []

    for j in all_jobs:
        job_id = j.get("id")
        job_num = j.get("job_number")
        title = j.get("title")
        customer = j.get("customer_name")
        instrument = f"{j.get('instrument_name')} ({j.get('instrument_serial')})"
        status = j.get("status")
        verdict = j.get("conformity", {}).get("conformance_verdict")
        tur = j.get("conformity", {}).get("tur")
        exceptions = j.get("exceptions", [])

        # Check search match
        if search:
            s_lower = search.lower()
            text_haystack = f"{job_id} {job_num} {title} {customer} {instrument}".lower()
            if s_lower not in text_haystack:
                continue

        # Evaluate criticality
        is_crit = False
        is_warn = False
        reasons = []

        if verdict == "FAIL":
            is_crit = True
            reasons.append("Out of tolerance: UUT failed conformity assessment.")

        for exc in exceptions:
            msg = exc if isinstance(exc, str) else exc.get("message", "")
            sev = (exc.get("severity") if isinstance(exc, dict) else "WARNING").upper()
            if sev == "CRITICAL" or "EXPIRED" in msg.upper() or "OUT OF TOLERANCE" in msg.upper():
                is_crit = True
                reasons.append(msg)
            else:
                is_warn = True
                reasons.append(msg)

        if tur is not None and tur < 4.0:
            if tur < 3.0:
                is_crit = True
                reasons.append(f"Substandard Test Uncertainty Ratio (TUR = {tur:.2f} < 3.00). High consumer risk.")
            else:
                is_warn = True
                reasons.append(f"Borderline Test Uncertainty Ratio (TUR = {tur:.2f} < 4.00). Root guardband applied.")

        # Assign category
        item = {
            "job_id": job_id,
            "job_number": job_num,
            "title": title,
            "customer_name": customer,
            "instrument": instrument,
            "status": status,
            "verdict": verdict,
            "tur": tur,
            "reasons": reasons,
            "primary_reason": reasons[0] if reasons else "Conforming calibration.",
            "action_required": "Root Cause Investigation Required" if is_crit else ("Reviewer Concurrence Recommended" if is_warn else "None (Routine Release)"),
            "created_at": j.get("created_at"),
        }

        if is_crit:
            item["severity"] = "CRITICAL"
            critical_items.append(item)
        elif is_warn:
            item["severity"] = "WARNING"
            warning_items.append(item)
        else:
            item["severity"] = "OK"
            ok_items.append(item)

    total_count = len(critical_items) + len(warning_items) + len(ok_items)

    # Filter by severity if requested
    if filter_severity:
        f_up = filter_severity.upper()
        if f_up == "CRITICAL":
            feed = critical_items
        elif f_up in ("WARNING", "WARNINGS"):
            feed = warning_items
        elif f_up == "OK":
            feed = ok_items
        else:
            feed = critical_items + warning_items + ok_items
    else:
        # Default sort: Critical first, then Warnings, then OK
        feed = critical_items + warning_items + ok_items

    feed = feed[:limit]

    return {
        "total_jobs_scanned": total_count,
        "critical_count": len(critical_items),
        "warning_count": len(warning_items),
        "ok_count": len(ok_items),
        "feed": feed,
    }


def log_automated_exception(exc_data: Dict[str, Any], db_path: str = DB_PATH) -> bool:
    """Log an automated exception to a job."""
    from ..db import get_job, save_job
    job_id = exc_data.get("job_id")
    if not job_id:
        return False
    job = get_job(job_id, db_path=db_path)
    if not job:
        return False
    exceptions = job.get("exceptions", [])
    exceptions.append(exc_data)
    job["exceptions"] = exceptions
    save_job(job, db_path=db_path)
    return True

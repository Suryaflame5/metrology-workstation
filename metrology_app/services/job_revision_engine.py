"""
Job Revision Control & Diff Engine for Metrology Workstation.
Tracks multi-revision calibrations (Rev 1, Rev 2) and provides
side-by-side delta comparisons for quality audits and investigation.
"""

from typing import Dict, Any, List, Optional
from ..db import get_job, create_job_revision, list_jobs, DB_PATH


def create_revision_for_job(
    job_id: str,
    notes: str = "",
    operator: str = "Metrology Specialist",
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """Create a new incremented revision for a calibration job."""
    return create_job_revision(job_id, revision_notes=notes, operator=operator, db_path=db_path)


def compare_job_revisions(
    job_id_a: str,
    job_id_b: str,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Compare two job revisions side-by-side.
    Separates changed parameters (measurements, temperature, uncertainty, verdict)
    from controlled invariant parameters (procedure, tolerance, decision rule, reference standard).
    """
    job_a = get_job(job_id_a, db_path=db_path)
    job_b = get_job(job_id_b, db_path=db_path)

    if not job_a or not job_b:
        raise ValueError(f"One or both jobs not found ('{job_id_a}', '{job_id_b}').")

    changed_items = []
    unchanged_items = []

    def check_diff(field_name: str, label: str, val_a: Any, val_b: Any):
        if val_a != val_b:
            changed_items.append({
                "field": field_name,
                "label": label,
                "rev_a_value": str(val_a),
                "rev_b_value": str(val_b),
            })
        else:
            unchanged_items.append({
                "field": field_name,
                "label": label,
                "value": str(val_a),
            })

    # Compare core fields
    check_diff("status", "Job Status", job_a.get("status"), job_b.get("status"))
    check_diff("revision_number", "Revision Number", job_a.get("revision_number"), job_b.get("revision_number"))
    check_diff("operator", "Operator", job_a.get("operator"), job_b.get("operator"))
    check_diff("raw_measurements", "Raw Measurements Count", len(job_a.get("raw_measurements", [])), len(job_b.get("raw_measurements", [])))

    mean_a = job_a.get("statistics", {}).get("mean")
    mean_b = job_b.get("statistics", {}).get("mean")
    check_diff("mean_value", "Sample Mean", f"{mean_a:.5f}" if mean_a else "N/A", f"{mean_b:.5f}" if mean_b else "N/A")

    s_a = job_a.get("statistics", {}).get("sample_std_dev")
    s_b = job_b.get("statistics", {}).get("sample_std_dev")
    check_diff("sample_std_dev", "Sample Std Dev (s)", f"{s_a:.6f}" if s_a else "N/A", f"{s_b:.6f}" if s_b else "N/A")

    u95_a = job_a.get("uncertainty_budget", {}).get("expanded_uncertainty_U95")
    u95_b = job_b.get("uncertainty_budget", {}).get("expanded_uncertainty_U95")
    check_diff("expanded_uncertainty", "Expanded Uncertainty (U95)", f"{u95_a:.6f}" if u95_a else "N/A", f"{u95_b:.6f}" if u95_b else "N/A")

    verdict_a = job_a.get("conformity", {}).get("conformance_verdict", "N/A")
    verdict_b = job_b.get("conformity", {}).get("conformance_verdict", "N/A")
    check_diff("verdict", "Conformity Verdict", verdict_a, verdict_b)

    temp_a = job_a.get("environment", {}).get("ambient_temperature_c")
    temp_b = job_b.get("environment", {}).get("ambient_temperature_c")
    check_diff("ambient_temp", "Ambient Temperature (°C)", temp_a, temp_b)

    rh_a = job_a.get("environment", {}).get("relative_humidity_pct")
    rh_b = job_b.get("environment", {}).get("relative_humidity_pct")
    check_diff("relative_humidity", "Relative Humidity (%)", rh_a, rh_b)

    # Invariants
    check_diff("procedure_name", "Procedure Name", job_a.get("procedure_name"), job_b.get("procedure_name"))
    check_diff("nominal_value", "Nominal Value", job_a.get("nominal_value"), job_b.get("nominal_value"))
    check_diff("tolerance_upper", "Upper Tolerance", job_a.get("tolerance_upper"), job_b.get("tolerance_upper"))
    check_diff("tolerance_lower", "Lower Tolerance", job_a.get("tolerance_lower"), job_b.get("tolerance_lower"))
    check_diff("reference_standard_name", "Reference Standard", job_a.get("reference_standard_name"), job_b.get("reference_standard_name"))

    return {
        "job_a": {
            "id": job_a.get("id"),
            "job_number": job_a.get("job_number"),
            "revision": job_a.get("revision_number"),
            "status": job_a.get("status"),
        },
        "job_b": {
            "id": job_b.get("id"),
            "job_number": job_b.get("job_number"),
            "revision": job_b.get("revision_number"),
            "status": job_b.get("status"),
        },
        "total_changed": len(changed_items),
        "total_unchanged": len(unchanged_items),
        "changed": changed_items,
        "unchanged": unchanged_items,
    }

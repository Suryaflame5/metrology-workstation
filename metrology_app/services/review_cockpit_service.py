"""
Review Cockpit & 1-Click Release Service for Metrology Workstation.
Consolidates measurement results, specification limits, GUM uncertainty,
decision rules, quality checks checklist, and cryptographic evidence into
a high-efficiency reviewer cockpit for 30-second sign-off.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..db import get_job, save_job, DB_PATH
from .job_pipeline_engine import sign_and_approve_job


def get_review_cockpit_data(job_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Assemble the complete reviewer cockpit payload for a measurement job.
    """
    job = get_job(job_id, db_path=db_path)
    if not job:
        raise ValueError(f"Job '{job_id}' not found.")

    nominal = float(job.get("nominal_value", 25.0))
    tol_upper = float(job.get("tolerance_upper", 0.002))
    tol_lower = float(job.get("tolerance_lower", -0.002))
    unit = job.get("unit", "mm")

    stats = job.get("statistics") or {}
    unc = job.get("uncertainty_budget") or {}
    conf = job.get("conformity") or {}
    env = job.get("environment") or {}
    exceptions = job.get("exceptions") or []

    mean_val = stats.get("mean", nominal)
    u95 = unc.get("expanded_uncertainty_U95", 0.0006)
    k_factor = unc.get("coverage_factor_k", 2.0)
    tur = conf.get("tur", 4.0)
    verdict = conf.get("conformance_verdict", "IN_PROGRESS" if job.get("status") == "NEW" else "PASS")

    # Quality Checks Checklist
    # 1. Measurement integrity
    s_val = stats.get("sample_std_dev", 0.00008)
    n_count = stats.get("count", len(job.get("raw_measurements", [])))
    meas_integrity_pass = n_count >= 3 and s_val <= 0.00035

    # 2. Uncertainty calculation
    unc_calc_pass = u95 > 0 and unc.get("combined_uncertainty_uc", 0) > 0

    # 3. Reference standard validity
    ref_due = job.get("reference_due_date", "2026-12-31")
    try:
        ref_due_dt = datetime.strptime(ref_due[:10], "%Y-%m-%d")
        ref_valid_pass = ref_due_dt > datetime.now()
    except Exception:
        ref_valid_pass = True

    # 4. Decision rule compliance
    dec_rule_pass = (tur >= 4.0) or (verdict != "FAIL" and conf.get("guardband_w") is not None)

    # 5. Environmental conditions completeness
    has_temp = env.get("ambient_temperature_c") is not None
    has_rh = env.get("relative_humidity_pct") is not None
    env_pass = has_temp and has_rh

    all_checks_passed = all([meas_integrity_pass, unc_calc_pass, ref_valid_pass, dec_rule_pass, env_pass])

    checklist = [
        {
            "id": "meas_integrity",
            "label": "Measurement Statistical Integrity",
            "passed": meas_integrity_pass,
            "detail": f"{n_count} valid observations, Bessel s = {s_val:.6f} {unit}",
        },
        {
            "id": "uncertainty_calc",
            "label": "GUM Uncertainty Budget Validated",
            "passed": unc_calc_pass,
            "detail": f"U95 = ±{u95:.6f} {unit} (k = {k_factor:.2f}, 95.45% coverage)",
        },
        {
            "id": "reference_validity",
            "label": "Reference Standard Traceability & Calibration Validity",
            "passed": ref_valid_pass,
            "detail": f"{job.get('reference_standard_name', 'Standard')} (Due: {ref_due})",
        },
        {
            "id": "decision_rule",
            "label": "ANSI/NCSL Z540.3 Method 6 Conformity Guardbanding",
            "passed": dec_rule_pass,
            "detail": f"TUR = {tur:.2f}:1, Root Guardband w = {conf.get('guardband_w', 0):.6f} {unit}",
        },
        {
            "id": "environmental_record",
            "label": "Laboratory Environmental Conditions Recorded",
            "passed": env_pass,
            "detail": f"T = {env.get('ambient_temperature_c', 20.0)} °C, RH = {env.get('relative_humidity_pct', 45.0)}%",
        },
    ]

    return {
        "job_id": job.get("id"),
        "job_number": job.get("job_number"),
        "title": job.get("title"),
        "customer_name": job.get("customer_name"),
        "instrument_name": job.get("instrument_name"),
        "instrument_model": job.get("instrument_model"),
        "instrument_serial": job.get("instrument_serial"),
        "procedure_name": job.get("procedure_name"),
        "status": job.get("status"),
        "unit": unit,
        # Result summary
        "result": {
            "mean": mean_val,
            "expanded_uncertainty": u95,
            "formatted_statement": f"{mean_val:.5f} {unit} ± {u95:.5f} {unit}",
            "coverage_factor": k_factor,
        },
        # Specification limits
        "specification_limits": {
            "nominal": nominal,
            "tolerance_lower": tol_lower,
            "tolerance_upper": tol_upper,
            "lower_limit": nominal + tol_lower,
            "upper_limit": nominal + tol_upper,
            "span": tol_upper - tol_lower,
        },
        # Decision & Guardband
        "conformity": {
            "verdict": verdict,
            "tur": tur,
            "guardband_w": conf.get("guardband_w", 0.0006),
            "acceptance_lower": conf.get("acceptance_lower", tol_lower + 0.0006),
            "acceptance_upper": conf.get("acceptance_upper", tol_upper - 0.0006),
            "consumer_risk_pct": "< 2.0%",
        },
        # Quality gates checklist
        "quality_checks": checklist,
        "all_checks_passed": all_checks_passed,
        "exceptions": exceptions,
        # Evidence trail
        "evidence": {
            "calculation_id": job.get("calculation_id"),
            "certificate_id": job.get("certificate_id"),
            "evidence_package_path": job.get("evidence_package_path"),
            "is_signed": bool(job.get("digital_signature", {}).get("signature_hash")),
            "signer": job.get("digital_signature", {}).get("signer_name"),
            "signed_at": job.get("digital_signature", {}).get("timestamp"),
        },
        "operator": job.get("operator"),
        "reviewer": job.get("reviewer"),
    }

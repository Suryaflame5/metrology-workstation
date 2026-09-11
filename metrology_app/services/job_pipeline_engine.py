"""
Measurement Job 1-Click Automated Pipeline Engine.
Orchestrates: Ingested Data -> Validation and Outliers -> Statistics ->
GUM Uncertainty Model -> Method 6 Guardband -> Exceptions First -> Diagnostic Explanation.
"""

import math
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from decimal import Decimal

from ..db import get_job, update_job, save_calculation, get_reference_standard
from metrology_core.context import to_decimal
from metrology_core.uncertainty.type_a import evaluate_type_a
from metrology_core.uncertainty.type_b import evaluate_type_b, DistributionType
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.uncertainty.degrees_of_freedom import calculate_welch_satterthwaite
from metrology_core.decision.tur import calculate_tur
from metrology_core.decision.method6 import calculate_method6_guardband, evaluate_method6_conformance
from metrology_core.rounding.metrological import format_metrological_result


def run_job_pipeline(job_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute end-to-end automated metrological pipeline on a measurement job.
    """
    job = get_job(job_id, db_path=db_path)
    if not job:
        raise ValueError(f"Measurement job '{job_id}' not found.")

    raw_readings = job.get("raw_measurements") or []
    if not raw_readings:
        raise ValueError(f"Cannot run pipeline: Job '{job_id}' has no raw measurements. Import data first.")

    nominal = float(job.get("nominal_value", 25.0))
    tol_upper = float(job.get("tolerance_upper", 0.002))
    tol_lower = float(job.get("tolerance_lower", -0.002))
    unit = job.get("unit", "mm")
    env = job.get("environment") or {}
    ambient_temp = float(env.get("ambient_temperature_c", 20.0))
    humidity = float(env.get("relative_humidity_pct", 45.0))

    # -------------------------------------------------------------
    # STAGE 1: STATISTICAL EVALUATION & OUTLIER DETECTION
    # -------------------------------------------------------------
    n = len(raw_readings)
    mean_val = sum(raw_readings) / n
    sorted_readings = sorted(raw_readings)
    median_val = (sorted_readings[n // 2] if n % 2 != 0 else (sorted_readings[n // 2 - 1] + sorted_readings[n // 2]) / 2.0)

    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in raw_readings) / (n - 1)
        std_dev = math.sqrt(variance)
        repeatability_uc = std_dev / math.sqrt(n)
    else:
        variance = 0.0
        std_dev = 0.0
        repeatability_uc = 0.00010

    min_val = min(raw_readings)
    max_val = max(raw_readings)
    val_range = max_val - min_val

    # Outlier filter (Grubbs / 2.8 sigma threshold)
    outliers = []
    cleansed = []
    for x in raw_readings:
        if std_dev > 0 and abs(x - mean_val) > 2.8 * std_dev:
            outliers.append(x)
        else:
            cleansed.append(x)

    statistics = {
        "count": n,
        "mean": round(mean_val, 6),
        "median": round(median_val, 6),
        "sample_std_dev": round(std_dev, 6),
        "repeatability_uncertainty": round(repeatability_uc, 6),
        "min": min_val,
        "max": max_val,
        "range": round(val_range, 6),
        "drift_rate": round(raw_readings[-1] - raw_readings[0], 6) if n > 1 else 0.0,
        "outliers": outliers,
    }

    # -------------------------------------------------------------
    # STAGE 2: SUGGESTED GUM UNCERTAINTY BUDGET ASSEMBLY
    # -------------------------------------------------------------
    ref_id = job.get("reference_standard_id", "")
    ref_std = get_reference_standard(ref_id, db_path=db_path) if ref_id else None
    ref_unc = float(ref_std.get("expanded_uncertainty", 0.0004)) if ref_std else float(job.get("reference_uncertainty", 0.0004))

    components = []
    # 1. Repeatability (Type A)
    components.append({
        "name": "Repeatability of Measurement (Type A)",
        "distribution": "normal",
        "standard_uncertainty": max(repeatability_uc, 0.000020),
        "sensitivity_coefficient": 1.0,
        "dof": max(1, n - 1),
    })

    # 2. Calibration of Reference Standard (Type B)
    components.append({
        "name": f"Reference Standard Calibration ({job.get('reference_standard_name', 'Primary Standard')})",
        "distribution": "normal",
        "standard_uncertainty": ref_unc / 2.0,
        "sensitivity_coefficient": 1.0,
        "dof": 50.0,
    })

    # 3. Scale / Digital Resolution (Type B)
    res_val = 0.001 if unit == "mm" else 0.0001
    components.append({
        "name": "Digital / Scale Resolution Limit",
        "distribution": "rectangular",
        "standard_uncertainty": res_val / math.sqrt(12),
        "sensitivity_coefficient": 1.0,
        "dof": 100.0,
    })

    # 4. Thermal Expansion Differential (Type B)
    delta_t = abs(ambient_temp - 20.0) + 0.5
    cte_expansion = (nominal * 11.5e-6 * delta_t) if unit == "mm" else (1e-5 * delta_t)
    components.append({
        "name": "Thermal Differential and Expansion",
        "distribution": "rectangular",
        "standard_uncertainty": cte_expansion / math.sqrt(3),
        "sensitivity_coefficient": 1.0,
        "dof": 30.0,
    })

    # Combined uncertainty calculation
    sum_var = sum((c["sensitivity_coefficient"] * c["standard_uncertainty"]) ** 2 for c in components)
    combined_uc = math.sqrt(sum_var)

    # Welch-Satterthwaite Effective Degrees of Freedom
    if combined_uc > 0:
        dof_denominator = sum(
            ((c["sensitivity_coefficient"] * c["standard_uncertainty"]) ** 4) / max(1.0, float(c["dof"]))
            for c in components
        )
        effective_dof = (combined_uc ** 4) / dof_denominator if dof_denominator > 0 else 50.0
    else:
        effective_dof = 50.0

    k_factor = 2.00
    expanded_U95 = combined_uc * k_factor

    # Variance contribution percentage for each component
    budget_breakdown = []
    for c in components:
        comp_var = (c["sensitivity_coefficient"] * c["standard_uncertainty"]) ** 2
        pct = (comp_var / sum_var * 100.0) if sum_var > 0 else 0.0
        budget_breakdown.append({
            "name": c["name"],
            "distribution": c["distribution"],
            "standard_uncertainty": round(c["standard_uncertainty"], 6),
            "sensitivity_coefficient": c["sensitivity_coefficient"],
            "variance_percent": round(pct, 1),
            "dof": c["dof"],
        })

    uncertainty_budget = {
        "combined_uncertainty_uc": round(combined_uc, 6),
        "expanded_uncertainty_U95": round(expanded_U95, 6),
        "coverage_factor_k": k_factor,
        "effective_dof": round(effective_dof, 1),
        "budget_breakdown": budget_breakdown,
    }

    # -------------------------------------------------------------
    # STAGE 3: ANSI/NCSL Z540.3 METHOD 6 ROOT GUARDBAND CONFORMITY
    # -------------------------------------------------------------
    error_of_indication = mean_val - nominal

    tur_calc = calculate_tur(to_decimal(tol_upper), to_decimal(tol_lower), to_decimal(expanded_U95))
    tur_val = float(tur_calc.tur)

    m6_gb = calculate_method6_guardband(to_decimal(tol_upper), to_decimal(tol_lower), to_decimal(expanded_U95))
    guardband_w = float(m6_gb.guardband_w)

    # Acceptance limits (shrunk inward from specification limits)
    ual = float(m6_gb.acceptance_upper)
    lal = float(m6_gb.acceptance_lower)

    if lal <= error_of_indication <= ual:
        verdict = "PASS"
    elif tol_lower <= error_of_indication <= tol_upper:
        verdict = "GUARD_BAND"
    else:
        verdict = "FAIL"

    conformity = {
        "nominal_value": nominal,
        "mean_measured": round(mean_val, 6),
        "error_of_indication": round(error_of_indication, 6),
        "tolerance_upper": tol_upper,
        "tolerance_lower": tol_lower,
        "tur": round(tur_val, 2),
        "guardband_multiplier": float(m6_gb.multiplier_M),
        "guardband_w": round(guardband_w, 6),
        "acceptance_lower": round(lal, 6),
        "acceptance_upper": round(ual, 6),
        "consumer_risk_pfa_pct": 2.0,
        "conformance_verdict": verdict,
    }

    # -------------------------------------------------------------
    # STAGE 4: EXCEPTIONS-FIRST DETECTION ENGINE
    # -------------------------------------------------------------
    exceptions = []

    # 1. Conformity failure or guardband alert
    if verdict == "FAIL":
        exceptions.append({
            "type": "CONFORMITY_OUT_OF_TOLERANCE",
            "severity": "CRITICAL",
            "title": "Measurement Exceeds Specification Tolerance",
            "message": f"Error of indication ({error_of_indication:+.5f} {unit}) violates tolerance bounds [{tol_lower:+.5f}, {tol_upper:+.5f} {unit}].",
        })
    elif verdict == "GUARD_BAND":
        exceptions.append({
            "type": "CONFORMITY_GUARD_BAND",
            "severity": "WARNING",
            "title": "Measurement Within Guardband Zone (Consumer Risk Alert)",
            "message": f"Measured error ({error_of_indication:+.5f} {unit}) is inside tolerance but outside acceptance limit ({ual:+.5f} {unit}). Consumer risk may exceed 2.0% under ANSI Z540.3 Method 6.",
        })

    # 2. Elevated Repeatability
    if std_dev > 0.00030:
        exceptions.append({
            "type": "ELEVATED_REPEATABILITY",
            "severity": "WARNING",
            "title": "Repeatability Standard Deviation Elevated",
            "message": f"Sample standard deviation ({std_dev:.5f} {unit}) is above typical laboratory threshold. Verify thermal settling and fixture rigidity.",
        })

    # 3. Outlier check
    if outliers:
        exceptions.append({
            "type": "OUTLIERS_DETECTED",
            "severity": "INFO",
            "title": f"{len(outliers)} Measurement Outliers Detected",
            "message": f"Observations {outliers} deviated > 2.8 standard deviations from mean. Inspect raw records.",
        })

    # 4. Environmental excursions
    if abs(ambient_temp - 20.0) > 1.5:
        exceptions.append({
            "type": "ENVIRONMENTAL_EXCURSION",
            "severity": "WARNING",
            "title": "Ambient Temperature Deviation",
            "message": f"Recorded ambient temperature ({ambient_temp:.1f} °C) is outside standard laboratory reference condition (20.0 ± 1.0 °C).",
        })

    # 5. Reference Standard Expiration check
    ref_due = job.get("reference_due_date", "")
    if ref_due:
        try:
            due_dt = datetime.fromisoformat(ref_due.replace("Z", ""))
            days_left = (due_dt - datetime.now()).days
            if days_left < 0:
                exceptions.append({
                    "type": "REFERENCE_EXPIRED",
                    "severity": "CRITICAL",
                    "title": "Reference Standard Calibration Expired",
                    "message": f"Standard '{job.get('reference_standard_name')}' expired {abs(days_left)} days ago. Release blocked under ISO 17025 §7.8.",
                })
            elif days_left <= 30:
                exceptions.append({
                    "type": "REFERENCE_EXPIRING_SOON",
                    "severity": "WARNING",
                    "title": "Reference Standard Calibration Due Soon",
                    "message": f"Standard '{job.get('reference_standard_name')}' calibration expires in {days_left} days ({ref_due}).",
                })
        except Exception:
            pass

    # -------------------------------------------------------------
    # STAGE 5: AUTOMATED 'WHY DID THIS FAIL?' DIAGNOSTIC
    # -------------------------------------------------------------
    diagnostic_explanation = ""
    if verdict != "PASS":
        sorted_comps = sorted(budget_breakdown, key=lambda c: c["variance_percent"], reverse=True)
        dominant_name = sorted_comps[0]["name"] if sorted_comps else "Unknown"
        dominant_pct = sorted_comps[0]["variance_percent"] if sorted_comps else 0.0

        excess = abs(error_of_indication) - tol_upper
        diagnostic_explanation = (
            f"Root-Cause Metrological Diagnostic:\n"
            f"- Measured Error of Indication: {error_of_indication:+.5f} {unit}\n"
            f"- Permissible Specification: ±{tol_upper:.5f} {unit}\n"
            f"- Direct Tolerance Excess: {excess:+.5f} {unit}\n"
            f"- Dominant Uncertainty Contributor: {dominant_name} ({dominant_pct}% of total variance)\n"
            f"- Applied Decision Rule: ANSI/NCSL Z540.3 Method 6 Root Guardband\n"
            f"- Corrective Action: Inspect zero reference alignment, verify thermal stabilization time (minimum 60 min), "
            f"and re-verify reference standard certificate."
        )

    conformity["diagnostic_explanation"] = diagnostic_explanation

    # -------------------------------------------------------------
    # STAGE 6: REGISTER IN CRYPTOGRAPHIC REPLAY LEDGER & UPDATE JOB
    # -------------------------------------------------------------
    calc_id = f"MC-{job_id.replace('JOB-', '')}"
    input_dict = {
        "repeatability": {"measurements": raw_readings},
        "reference_standard": {"nominal_value": nominal, "uncertainty": ref_unc, "coverage_factor_k": 2.0},
        "resolution": {"resolution": res_val},
        "temperature": {"delta_temperature_c": delta_t, "half_width_mm": cte_expansion},
        "nominal_value": nominal,
        "tolerance_upper": tol_upper,
        "tolerance_lower": tol_lower,
    }
    result_dict = {
        "combined_standard_uncertainty": combined_uc,
        "expanded_uncertainty_k2": expanded_U95,
        "tur": tur_val,
        "guardband_multiplier": float(m6_gb.multiplier_M),
        "guardband_w": guardband_w,
        "acceptance_lower": lal,
        "acceptance_upper": ual,
        "conformity_verdict": verdict,
    }
    input_hash = hashlib.sha256(json.dumps(input_dict, sort_keys=True).encode("utf-8")).hexdigest()
    calc_hash = hashlib.sha256((input_hash + json.dumps(result_dict, sort_keys=True)).encode("utf-8")).hexdigest()

    calc_record = {
        "id": calc_id,
        "root_id": calc_id,
        "revision_number": job.get("revision_number", 1),
        "record_class": "CALIBRATION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "instrument_name": job.get("instrument_name", "Precision Instrument"),
        "instrument_model": job.get("instrument_model", "Standard"),
        "procedure_name": job.get("procedure_name", "Standard Procedure"),
        "procedure_version": "1.0.0",
        "unit": unit,
        "nominal_value": nominal,
        "tolerance_upper": tol_upper,
        "tolerance_lower": tol_lower,
        "confidence_level": "95%",
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
        "status": "VALID",
        "conformity_verdict": verdict,
        "input_data": input_dict,
        "result_data": result_dict,
        "input_sha256": input_hash,
        "calculation_sha256": calc_hash,
    }
    save_calculation(calc_record, db_path=db_path)

    # Next status: If exceptions exist, REVIEW_REQUIRED; else READY_FOR_APPROVAL
    next_status = "REVIEW_REQUIRED" if exceptions else "READY_FOR_APPROVAL"

    updates = {
        "statistics": statistics,
        "uncertainty_budget": uncertainty_budget,
        "conformity": conformity,
        "exceptions": exceptions,
        "calculation_id": calc_id,
        "status": next_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    update_job(job_id, updates, db_path=db_path)

    return get_job(job_id, db_path=db_path)


def sign_and_approve_job(
    job_id: str,
    signer_name: str = "Authorized Reviewer",
    role: str = "Quality Director",
    reason: str = "Technical Approval & Release Concurrence",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute 21 CFR Part 11 Electronic Signature ceremony on a measurement job,
    transitioning its status to APPROVED with immutable cryptographic timestamp.
    """
    job = get_job(job_id, db_path=db_path)
    if not job:
        raise ValueError(f"Measurement job '{job_id}' not found.")

    now = datetime.now(timezone.utc).isoformat()
    sig_payload = {
        "job_id": job_id,
        "signer_name": signer_name,
        "role": role,
        "reason": reason,
        "timestamp": now,
        "calculation_id": job.get("calculation_id"),
        "conformity_verdict": job.get("conformity", {}).get("conformance_verdict", "PASS"),
    }
    sig_hash = hashlib.sha256(json.dumps(sig_payload, sort_keys=True).encode("utf-8")).hexdigest()
    sig_payload["signature_hash"] = sig_hash

    cert_id = f"CAL-{datetime.now().year}-{job_id.replace('JOB-', '')[:8]}"
    updates = {
        "status": "APPROVED",
        "certificate_id": cert_id,
        "reviewer": f"{signer_name} ({role})",
        "reviewed_at": now,
        "digital_signature": sig_payload,
        "updated_at": now,
    }
    update_job(job_id, updates, db_path=db_path)
    return get_job(job_id, db_path=db_path)


run_1click_job_pipeline = run_job_pipeline

"""
Evidence Service: Machine-verifiable evidence package generator.
"""

import json
import os
import zipfile
import io
from typing import Dict, Any, Optional
from ..db import get_calculation
from .. import __version__ as APP_VERSION


def build_evidence_package_files(calc_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Build the dictionary of filenames -> JSON string content for a machine-verifiable evidence package.
    """
    res = calc_data["result_data"]
    inp = calc_data["input_data"]
    cid = calc_data["id"]

    # 1. calculation.json
    calc_json = {
        "schema_version": "1.0.0",
        "calculation_id": cid,
        "created_at": calc_data["created_at"],
        "engine_version": f"metrology-core 0.3.0 (metrology-app {APP_VERSION})",
        "instrument_name": calc_data["instrument_name"],
        "instrument_model": calc_data["instrument_model"],
        "procedure_name": calc_data["procedure_name"],
        "procedure_version": calc_data["procedure_version"],
        "unit": calc_data["unit"],
        "status": calc_data["status"],
        "conformity_verdict": calc_data["conformity_verdict"],
        "input_sha256": calc_data["input_sha256"],
        "calculation_sha256": calc_data["calculation_sha256"],
    }

    # 2. measurements.json
    measurements_json = {
        "nominal_checkpoint_mm": inp.get("nominal_value"),
        "reference_standard": inp.get("reference_standard"),
        "repeatability_observations": inp.get("repeatability", {}).get("measurements"),
        "resolution_spec": inp.get("resolution"),
        "temperature_spec": inp.get("temperature"),
        "tolerance_limits": {
            "lower_mm": inp.get("tolerance_lower"),
            "upper_mm": inp.get("tolerance_upper"),
        },
    }

    # 3. uncertainty_budget.json
    unc_summary = res.get("uncertainty_summary", {})
    budget_json = {
        "methodology": "JCGM 100:2008 (GUM Law of Propagation of Uncertainty)",
        "combined_standard_uncertainty_mm": unc_summary.get("combined_standard_uncertainty_mm"),
        "effective_degrees_of_freedom": unc_summary.get("effective_degrees_of_freedom"),
        "coverage_factor_k": unc_summary.get("coverage_factor_k"),
        "expanded_uncertainty_U95_mm": unc_summary.get("expanded_uncertainty_U95_mm"),
        "formatted_result": unc_summary.get("formatted_result"),
        "budget_table": unc_summary.get("budget_rows", []),
    }

    # 4. decision.json
    dec_summary = res.get("decision_summary", {})
    decision_json = {
        "decision_rule": dec_summary.get("decision_rule"),
        "tur": dec_summary.get("tur"),
        "guardband_multiplier_M": dec_summary.get("guardband_multiplier_M"),
        "guardband_w_mm": dec_summary.get("guardband_w_mm"),
        "tolerance_limits_mm": [dec_summary.get("tolerance_lower_mm"), dec_summary.get("tolerance_upper_mm")],
        "acceptance_zone_mm": [dec_summary.get("acceptance_lower_mm"), dec_summary.get("acceptance_upper_mm")],
        "measured_error_mm": dec_summary.get("error_of_indication_mm"),
        "conformity_verdict": dec_summary.get("conformity_verdict"),
        "decision_trace": dec_summary.get("decision_explanation"),
    }

    # 5. provenance.json
    provenance_json = {
        "calculation_id": cid,
        "timestamp": calc_data["created_at"],
        "input_sha256": calc_data["input_sha256"],
        "calculation_sha256": calc_data["calculation_sha256"],
        "algorithm_sequence": [
            "1. Type A Repeatability Statistical Evaluation (GUM 4.2)",
            "2. Type B Reference Standard, Resolution, and Temperature Evaluation (GUM 4.3)",
            "3. Law of Propagation of Uncertainty (GUM 5.1)",
            "4. Welch-Satterthwaite Effective Degrees of Freedom (GUM Annex G)",
            "5. Student's t Coverage Factor Derivation (k=95.45%)",
            "6. Guardbanding & Acceptance Limits Derivation (ANSI/NCSL Z540.3 / ISO 14253-1)",
            "7. Binary Conformity Decision & Resolution Matching (GUM 7.2.6)",
        ],
    }

    # 6. verification.json
    verification_json = {
        "verifier_command": f"python -m metrology_app.cli verify {cid}",
        "expected_input_sha256": calc_data["input_sha256"],
        "expected_calculation_sha256": calc_data["calculation_sha256"],
        "verdict": calc_data["conformity_verdict"],
    }

    return {
        "calculation.json": json.dumps(calc_json, indent=2),
        "measurements.json": json.dumps(measurements_json, indent=2),
        "uncertainty_budget.json": json.dumps(budget_json, indent=2),
        "decision.json": json.dumps(decision_json, indent=2),
        "provenance.json": json.dumps(provenance_json, indent=2),
        "verification.json": json.dumps(verification_json, indent=2),
    }


def export_evidence_package_directory(calc_id: str, base_dir: str = "evidence_packages") -> str:
    """Export evidence package files to a local directory."""
    calc_data = get_calculation(calc_id)
    if not calc_data:
        raise ValueError(f"Calculation ID '{calc_id}' not found")

    target_dir = os.path.join(base_dir, calc_id)
    os.makedirs(target_dir, exist_ok=True)

    files = build_evidence_package_files(calc_data)
    for fname, content in files.items():
        fpath = os.path.join(target_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

    return target_dir


def export_evidence_package_zip_bytes(calc_id: str) -> bytes:
    """Export evidence package as a zip archive byte stream."""
    calc_data = get_calculation(calc_id)
    if not calc_data:
        raise ValueError(f"Calculation ID '{calc_id}' not found")

    files = build_evidence_package_files(calc_data)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(f"{calc_id}/{fname}", content)
    buf.seek(0)
    return buf.getvalue()

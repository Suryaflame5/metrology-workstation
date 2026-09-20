"""
Test Suite for Metrology Evidence & Impact Platform:
Validates OOT reverse impact tracing, 60-second audit evidence defense package,
financial exposure bounds, and root-cause quality investigations.
"""

import os
import io
import zipfile
import json
import pytest
from fastapi.testclient import TestClient

from metrology_app.server import app
from metrology_app.services.impact_service import (
    trace_out_of_tolerance_impact,
    calculate_financial_exposure,
    build_60s_audit_defense_package,
)
from metrology_app.db import (
    init_db,
    save_job,
    save_inspection_job,
    save_investigation,
    get_investigation,
    save_corrective_action,
    DB_PATH,
)


@pytest.fixture
def client(tmp_path):
    db_file = str(tmp_path / "test_impact.db")
    init_db(db_file)
    old_env = os.environ.get("METROLOGY_DB_PATH")
    os.environ["METROLOGY_DB_PATH"] = db_file

    with TestClient(app) as test_client:
        yield test_client

    if old_env is not None:
        os.environ["METROLOGY_DB_PATH"] = old_env
    else:
        os.environ.pop("METROLOGY_DB_PATH", None)


def test_calculate_financial_exposure_bounds():
    """Verify transparent mathematical formulas and bounding intervals for financial exposure."""
    res = calculate_financial_exposure(
        affected_units=1000,
        unit_cost_usd=50.0,
        scrap_rate_pct=10.0,
        rework_rate_pct=20.0,
        rework_cost_usd=15.0,
        inspection_hours=10.0,
        labor_rate_usd=60.0,
        blanket_recall_units=5000,
    )

    # Scrap: 1000 * 10% * 50 = $5,000
    assert res["exposure_breakdown"]["scrap_loss_usd"] == 5000.0
    # Rework: 1000 * 20% * 15 = $3,000
    assert res["exposure_breakdown"]["rework_loss_usd"] == 3000.0
    # Reinspection: 10 * 60 = $600
    assert res["exposure_breakdown"]["reinspection_labor_usd"] == 600.0
    # Total: 5000 + 3000 + 600 = $8,600
    assert res["exposure_breakdown"]["total_targeted_exposure_usd"] == 8600.0

    # Bounds: 95% confidence interval
    assert res["calculation_bounds_95pct"]["lower_bound_usd"] < 8600.0
    assert res["calculation_bounds_95pct"]["upper_bound_usd"] > 8600.0

    # Blanket recall comparison
    assert res["containment_comparison"]["blanket_recall_cost_usd"] > res["containment_comparison"]["targeted_window_cost_usd"]
    assert res["containment_comparison"]["potential_recoverable_savings_usd"] > 0
    assert "28,800" in res["containment_comparison"]["case_study_metric"]


def test_trace_out_of_tolerance_impact():
    """Verify OOT reverse impact tracing identifies affected jobs, batches, and containment plan."""
    # Seed a job with specific instrument
    test_inst_id = "MTR-TEST-99"
    save_job({
        "job_number": "JOB-OOT-991",
        "title": "Precision Gauge Block Verification",
        "customer_name": "Apex Aerospace Plant 2",
        "instrument_id": test_inst_id,
        "instrument_name": "Digital Micrometer",
        "instrument_model": "Mitutoyo 293",
        "instrument_serial": test_inst_id,
        "nominal_value": 25.0,
        "tolerance_upper": 0.002,
        "tolerance_lower": -0.002,
        "conformity": {"verdict": "PASS", "tur": 5.0},
    })

    impact = trace_out_of_tolerance_impact(
        instrument_id=test_inst_id,
        failure_date="2026-09-20",
        last_valid_date="2026-08-20",
        tolerance_breach_magnitude=0.008,
    )

    assert impact["instrument_id"] == test_inst_id
    assert impact["exposure_window"]["exposure_duration_days"] == 31
    assert len(impact["lineage_jobs"]) >= 1
    assert len(impact["affected_batches"]) >= 1

    containment = impact["containment_recommendation"]
    assert containment["immediate_action"] == "QUARANTINE_AFFECTED_BATCHES"
    assert len(containment["recommended_steps"]) == 5
    assert "ISO/IEC 17025" in containment["investigation_protocol"]


def test_60s_audit_defense_package_zip():
    """Verify single-click 60-Second Audit Evidence Defense Package contains all 6 defense artifacts."""
    job_id = "AUDIT-JOB-TEST-42"
    zip_bytes = build_60s_audit_defense_package(job_id)

    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 500

    # Verify ZIP contents
    buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buf, "r") as zf:
        namelist = zf.namelist()
        expected_files = [
            "AUDIT_SUMMARY.md",
            "CALIBRATION_CERTIFICATE.json",
            "GUM_UNCERTAINTY_BUDGET.json",
            "REFERENCE_STANDARDS_TRACEABILITY.json",
            "RAW_MEASUREMENTS_AUDIT.csv",
            "CRYPTOGRAPHIC_PROOF.json",
        ]
        for exp in expected_files:
            match = any(exp in name for name in namelist)
            assert match, f"Missing {exp} in audit defense package: {namelist}"

        # Verify cryptographic proof structure
        proof_filename = [n for n in namelist if "CRYPTOGRAPHIC_PROOF.json" in n][0]
        proof_data = json.loads(zf.read(proof_filename).decode("utf-8"))
        assert proof_data["signature_verified"] is True
        assert proof_data["tamper_detected"] is False
        assert "sha256_hash" in proof_data
        assert "merkle_root_anchor" in proof_data


def test_api_impact_and_investigation_routes(client):
    """Verify REST API endpoints for impact tracing, financial exposure, and investigation lifecycle."""
    # 1. POST /api/v1/impact/trace-oot
    res_trace = client.post(
        "/api/v1/impact/trace-oot",
        json={"instrument_id": "CALIPER-007", "tolerance_breach_magnitude": 0.006}
    )
    assert res_trace.status_code == 200
    trace_data = res_trace.json()
    assert trace_data["instrument_id"] == "CALIPER-007"
    assert "containment_recommendation" in trace_data
    assert "financial_exposure" in trace_data

    # 2. POST /api/v1/impact/financial-exposure
    res_exp = client.post(
        "/api/v1/impact/financial-exposure",
        json={"affected_units": 500, "unit_cost_usd": 60.0, "scrap_rate_pct": 10.0}
    )
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    assert exp_data["affected_production_units"] == 500
    assert exp_data["exposure_breakdown"]["scrap_loss_usd"] == 3000.0

    # 3. GET /api/v1/evidence/audit-package/{job_id}
    res_pkg = client.get("/api/v1/evidence/audit-package/JOB-DEMO-01")
    assert res_pkg.status_code == 200
    assert res_pkg.headers["content-type"] == "application/zip"
    assert "attachment" in res_pkg.headers["content-disposition"]
    assert len(res_pkg.content) > 500

    # 4. POST & GET /api/v1/investigations
    res_inv = client.post(
        "/api/v1/investigations",
        json={
            "title": "Thermal Drift in Cylindrical Grinding Cell",
            "lead_engineer": "Senior Quality Metrologist",
            "findings": "Coolant temperature fluctuation exceeded ±2°C limit.",
            "status": "IN_PROGRESS",
        }
    )
    assert res_inv.status_code == 200
    inv_id = res_inv.json()["id"]

    res_get_inv = client.get(f"/api/v1/investigations/{inv_id}")
    assert res_get_inv.status_code == 200
    inv_detail = res_get_inv.json()
    assert inv_detail["title"] == "Thermal Drift in Cylindrical Grinding Cell"

    # 5. POST /api/v1/investigations/{inv_id}/actions (CAPA)
    res_act = client.post(
        f"/api/v1/investigations/{inv_id}/actions",
        json={
            "action_title": "Install Proportional Chiller Thermostat",
            "description": "Lock coolant tank to 20.0 ± 0.5°C with dual RTD feedback.",
            "assigned_to": "Facilities Engineering",
            "status": "SCHEDULED",
        }
    )
    assert res_act.status_code == 200
    assert res_act.json()["status"] == "SUCCESS"

"""
End-to-End Workflow Integration Tests for metrology_app.
"""

import pytest
import os
from decimal import Decimal
from fastapi.testclient import TestClient

from metrology_app.server import app
from metrology_app.models import CalculationCreateRequest
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.evidence_service import build_evidence_package_files, export_evidence_package_zip_bytes
from metrology_app.services.report_service import generate_html_report
from metrology_app.db import get_calculation, init_db

client = TestClient(app)


def test_micrometer_calculation_service():
    req = CalculationCreateRequest(
        nominal_value=25.00000,
        tolerance_upper=0.00200,
        tolerance_lower=-0.00200,
        decision_rule="ANSI/NCSL Z540.3 Method 6",
        record_class="VALIDATION",
    )
    res = compute_micrometer_calibration(req, calc_id="TEST-MC-001")

    assert res.id == "TEST-MC-001"
    assert res.conformity_verdict in ("PASS", "GUARD_BAND", "FAIL")
    assert len(res.uncertainty_summary.budget_rows) == 4
    assert res.uncertainty_summary.combined_standard_uncertainty_mm is not None
    assert res.decision_summary.tur is not None
    assert len(res.input_sha256) == 64
    assert len(res.calculation_sha256) == 64

    # Verify saved in DB
    db_rec = get_calculation("TEST-MC-001")
    assert db_rec is not None
    assert db_rec["id"] == "TEST-MC-001"


def test_evidence_package_generation():
    req = CalculationCreateRequest(record_class="VALIDATION")
    res = compute_micrometer_calibration(req, calc_id="TEST-MC-PKG")

    db_rec = get_calculation("TEST-MC-PKG")
    files = build_evidence_package_files(db_rec)

    expected_files = [
        "calculation.json",
        "measurements.json",
        "uncertainty_budget.json",
        "decision.json",
        "provenance.json",
        "verification.json",
    ]
    for ef in expected_files:
        assert ef in files
        assert len(files[ef]) > 20

    zip_bytes = export_evidence_package_zip_bytes("TEST-MC-PKG")
    assert len(zip_bytes) > 500


def test_html_report_generation():
    req = CalculationCreateRequest(record_class="VALIDATION")
    res = compute_micrometer_calibration(req, calc_id="TEST-MC-REPORT")

    html = generate_html_report("TEST-MC-REPORT")
    assert "<!DOCTYPE html>" in html
    assert "TEST-MC-REPORT" in html
    assert "Uncertainty Budget" in html
    assert "Conformity Assessment" in html
    assert res.input_sha256 in html


def test_fastapi_rest_endpoints():
    # 1. Stats
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_calibrations" in data

    # 2. Procedures
    resp = client.get("/api/procedures")
    assert resp.status_code == 200
    procs = resp.json()
    assert len(procs) >= 1

    # 3. Create Calculation via POST
    payload = {
        "instrument_name": "Micrometer",
        "instrument_model": "0–25 mm Outside Micrometer",
        "nominal_value": 25.0,
        "tolerance_upper": 0.002,
        "tolerance_lower": -0.002,
    }
    resp = client.post("/api/calculations", json=payload)
    assert resp.status_code == 200
    calc = resp.json()
    assert "id" in calc
    assert calc["status"] == "VALIDATED"

    # 4. Get Calculation
    cid = calc["id"]
    resp = client.get(f"/api/calculations/{cid}")
    assert resp.status_code == 200

    # 5. Export ZIP
    resp = client.get(f"/api/calculations/{cid}/export/zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    # 6. Report HTML
    resp = client.get(f"/api/calculations/{cid}/report")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]

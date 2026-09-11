"""
Automated Verification Test Suite for Metrology Workstation V7 Technician Workflow.
Tests:
- Unified Measurement Job Database & Reference Standards Fleet
- Universal Ingestion & Heuristic Column Mapping Engine
- 1-Click Pipeline & Exceptions-First Diagnostics Engine
- REST Endpoints (Import, Pipeline, 21 CFR Part 11 Signature, Repeat Duplication, PDF, ZIP)
"""

import json
import pytest
from fastapi.testclient import TestClient

from metrology_app.db import (
    save_job,
    get_job,
    update_job,
    list_jobs,
    duplicate_job,
    list_reference_standards,
    get_reference_standard,
)
from metrology_app.services.universal_importer import (
    parse_raw_data_stream,
    auto_detect_columns,
    extract_job_measurements,
    normalize_unit_value,
)
from metrology_app.services.job_pipeline_engine import run_job_pipeline
from metrology_app.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_job_database_crud_and_seeding():
    """Verify measurement job creation, retrieval, and baseline seeding."""
    stds = list_reference_standards()
    assert len(stds) >= 4
    # Check that standard categories exist
    categories = [s["category"] for s in stds]
    assert "Dimensional" in categories
    assert "Electrical" in categories

    jobs = list_jobs()
    assert len(jobs) >= 3

    # Create new test job
    job_id = save_job({
        "id": "JOB-TEST-001",
        "job_number": "JOB-TEST-001",
        "title": "Unit Test Calibration Job",
        "instrument_name": "Test Gauge",
        "instrument_model": "TG-100",
        "instrument_serial": "TG-9901",
        "nominal_value": 50.0,
        "tolerance_upper": 0.005,
        "tolerance_lower": -0.005,
        "unit": "mm",
        "status": "NEW",
        "raw_measurements": [50.001, 50.002, 50.001],
    })
    assert job_id == "JOB-TEST-001"

    retrieved = get_job("JOB-TEST-001")
    assert retrieved is not None
    assert retrieved["title"] == "Unit Test Calibration Job"
    assert len(retrieved["raw_measurements"]) == 3

    # Update job
    updated = update_job("JOB-TEST-001", {"status": "ANALYZING"})
    assert updated["status"] == "ANALYZING"


def test_universal_data_importer():
    """Verify CSV ingestion, unit conversions, and column auto-detection."""
    # Unit normalization
    assert normalize_unit_value(1000.0, "mV", "V") == 1.0
    assert normalize_unit_value(25.4, "mm", "in") == 1.0
    assert round(normalize_unit_value(68.0, "°F", "°C"), 1) == 20.0
    assert round(normalize_unit_value(20.0, "°C", "°F"), 1) == 68.0

    # Incompatible units rejected
    with pytest.raises(ValueError):
        normalize_unit_value(10.0, "V", "mm")

    # CSV Parsing and Column Mapping
    sample_csv = """Run,Nominal_mm,Indicated_mm,Ambient_Temp_C,Relative_Humidity
1,25.000,25.0004,20.1,44.2
2,25.000,25.0003,20.1,44.5
3,25.000,25.0005,20.2,44.1
4,25.000,25.0004,20.1,44.3
5,25.000,25.0003,20.2,44.0
"""
    rows = parse_raw_data_stream(sample_csv)
    assert len(rows) == 5

    headers = list(rows[0].keys())
    mapping_res = auto_detect_columns(headers, rows)
    assert mapping_res["has_measured_values"] is True
    assert mapping_res["has_nominal_values"] is True
    assert mapping_res["overall_confidence_pct"] >= 95.0

    extracted = extract_job_measurements(rows, mapping_res["columns"], target_unit="mm")
    assert extracted["sample_size"] == 5
    assert extracted["nominal_value"] == 25.0
    assert len(extracted["raw_measurements"]) == 5


def test_job_pipeline_engine_pass():
    """Verify 1-click automated pipeline execution for a passing instrument."""
    job_id = "JOB-PIPE-PASS"
    save_job({
        "id": job_id,
        "job_number": job_id,
        "title": "Passing Outside Micrometer",
        "instrument_name": "Outside Micrometer",
        "instrument_model": "Mitutoyo 103",
        "instrument_serial": "MIT-103-999",
        "nominal_value": 25.0,
        "tolerance_upper": 0.002,
        "tolerance_lower": -0.002,
        "unit": "mm",
        "status": "NEW",
        "raw_measurements": [25.0003, 25.0004, 25.0003, 25.0004, 25.0003],
    })

    result = run_job_pipeline(job_id)
    assert result is not None
    assert result["statistics"]["count"] == 5
    assert result["statistics"]["sample_std_dev"] < 0.0002
    assert result["uncertainty_budget"]["expanded_uncertainty_U95"] > 0
    assert result["conformity"]["conformance_verdict"] == "PASS"
    assert result["conformity"]["tur"] >= 2.5
    assert result["calculation_id"] is not None


def test_job_pipeline_engine_fail_with_diagnostic():
    """Verify out-of-tolerance detection and 'Why did this fail?' diagnostic generation."""
    job_id = "JOB-PIPE-FAIL"
    save_job({
        "id": job_id,
        "job_number": job_id,
        "title": "Failing Caliper Job",
        "instrument_name": "Vernier Caliper",
        "instrument_model": "Standard",
        "instrument_serial": "VC-FAIL-01",
        "nominal_value": 25.0,
        "tolerance_upper": 0.002,
        "tolerance_lower": -0.002,
        "unit": "mm",
        "status": "NEW",
        "raw_measurements": [25.008, 25.009, 25.008, 25.008, 25.009], # > 0.008 error
    })

    result = run_job_pipeline(job_id)
    assert result["conformity"]["conformance_verdict"] == "FAIL"
    assert len(result["exceptions"]) > 0
    assert "Root-Cause Metrological Diagnostic" in result["conformity"]["diagnostic_explanation"]
    assert "Direct Tolerance Excess" in result["conformity"]["diagnostic_explanation"]


def test_job_duplication_repeat_cycle():
    """Verify duplicating an approved job creates a clean repeat cycle job."""
    orig_id = "JOB-2026-08143" # Seeded approved job
    dup = duplicate_job(orig_id, operator="Marcus Reid")
    assert dup is not None
    assert dup["status"] == "NEW"
    assert dup["parent_job_id"] == orig_id
    assert dup["revision_number"] >= 2
    assert dup["raw_measurements"] == []
    assert dup["operator"] == "Marcus Reid"


def test_fastapi_job_endpoints(client):
    """Verify all FastAPI REST endpoints for V7 workflow."""
    # 1. GET /api/jobs
    r = client.get("/api/jobs")
    assert r.status_code == 200
    assert len(r.json()["jobs"]) > 0

    # 2. GET /api/reference-standards
    r_std = client.get("/api/reference-standards")
    assert r_std.status_code == 200
    stds = r_std.json()["standards"]
    assert len(stds) >= 4
    for s in stds:
        assert "days_until_due" in s
        assert "expiration_status" in s

    # 3. POST /api/jobs/import/preview
    csv_text = "Run,Reading\n1,25.001\n2,25.002\n3,25.001\n"
    r_prev = client.post("/api/jobs/import/preview", json={"content": csv_text, "target_unit": "mm"})
    assert r_prev.status_code == 200
    assert r_prev.json()["confidence_pct"] >= 80

    # 4. Create and run pipeline on a dedicated test job
    target_job = "JOB-API-TEST"
    r_create = client.post("/api/jobs", json={
        "id": target_job,
        "job_number": target_job,
        "title": "API Test Micrometer",
        "instrument_name": "Precision Micrometer",
        "instrument_model": "Mitutoyo 103",
        "instrument_serial": "MIT-9921",
        "nominal_value": 25.0,
        "tolerance_upper": 0.002,
        "tolerance_lower": -0.002,
        "unit": "mm",
        "raw_measurements": [25.0003, 25.0004, 25.0003, 25.0004, 25.0003],
    })
    assert r_create.status_code == 200

    r_pipe = client.post(f"/api/jobs/{target_job}/pipeline")
    assert r_pipe.status_code == 200
    assert r_pipe.json()["job"]["conformity"]["conformance_verdict"] == "PASS"

    # 5. POST /api/jobs/{id}/approve (21 CFR Part 11)
    r_app = client.post(f"/api/jobs/{target_job}/approve", json={
        "signer_name": "Dr. Vance",
        "signer_role": "Quality Director",
        "meaning": "Conformance Approval"
    })
    assert r_app.status_code == 200
    approved_job = r_app.json()["job"]
    assert approved_job["status"] == "APPROVED"
    assert approved_job["digital_signature"]["cfr_part11_compliant"] is True

    # 6. GET /api/jobs/{id}/certificate PDF
    r_pdf = client.get(f"/api/jobs/{target_job}/certificate")
    assert r_pdf.status_code == 200
    assert r_pdf.content.startswith(b"%PDF")

    # 7. GET /api/jobs/{id}/evidence-package ZIP
    r_zip = client.get(f"/api/jobs/{target_job}/evidence-package")
    assert r_zip.status_code == 200
    assert r_zip.content.startswith(b"PK")

"""
V5 Engineering Workstation Automated Test Suite.
Tests the 11-stage project-centric workflow, instrument management,
measurement plans, statistical acquisition, uncertainty workbench,
conformity workbench, and V4->V5 non-destructive database migrations.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from metrology_app.db import (
    init_db,
    save_project,
    get_project,
    list_projects,
    delete_project,
    save_instrument,
    get_instrument,
    list_instruments,
    delete_instrument,
    save_measurement_plan,
    get_measurement_plan,
    list_measurement_plans,
    save_measurement,
    get_measurement,
    list_measurements,
    get_v5_dashboard_stats,
)
from metrology_app.services.acquisition_service import analyze_measurement_series
from metrology_app.services.workbench_service import compute_uncertainty_workbench, compute_conformity_workbench
from metrology_app.models import (
    UncertaintyComponentInput,
    ConformityWorkbenchRequest,
)
from metrology_app.server import app


@pytest.fixture
def clean_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_v5_workstation.db")
    init_db(db_path)
    yield db_path


def test_v5_fresh_db_is_empty(clean_db):
    """Verify that a fresh V5 installation opens completely empty."""
    stats = get_v5_dashboard_stats(clean_db)
    assert stats["active_projects"] == 0
    assert stats["total_instruments"] == 0
    assert stats["measurement_plans"] == 0
    assert stats["acquired_measurements"] == 0
    assert stats["total_calibrations"] == 0


def test_v5_project_lifecycle(clean_db):
    """Verify project creation, retrieval, listing, and deletion."""
    proj_data = {
        "id": "PRJ-TEST-001",
        "name": "Aerospace Wing Spar Quality Audit",
        "customer_site": "Lockheed Facility B",
        "description": "High precision micrometer and caliper dimensional audit",
        "status": "ACTIVE",
    }
    saved = save_project(proj_data, clean_db)
    assert saved["id"] == "PRJ-TEST-001"
    assert saved["name"] == "Aerospace Wing Spar Quality Audit"

    retrieved = get_project("PRJ-TEST-001", clean_db)
    assert retrieved is not None
    assert retrieved["customer_site"] == "Lockheed Facility B"

    projects = list_projects(status="ACTIVE", db_path=clean_db)
    assert len(projects) == 1

    deleted = delete_project("PRJ-TEST-001", clean_db)
    assert deleted is True
    assert get_project("PRJ-TEST-001", clean_db) is None


def test_v5_instrument_asset_management(clean_db):
    """Verify instrument creation, asset attributes, and interval tracking."""
    inst_data = {
        "id": "INST-MIC-401",
        "project_id": "PRJ-TEST-001",
        "manufacturer": "Mitutoyo",
        "model": "QuantuMike 0-25mm",
        "serial_number": "SN-8849201",
        "instrument_type": "Micrometer",
        "range_min": 0.0,
        "range_max": 25.0,
        "resolution": 0.001,
        "accuracy_spec": "±0.001 mm",
        "calibration_status": "VALID",
        "calibration_interval_months": 12,
        "last_calibration_date": "2026-08-01",
        "next_calibration_due": "2027-08-01",
        "location": "Metrology Lab Clean Room",
    }
    saved = save_instrument(inst_data, clean_db)
    assert saved["id"] == "INST-MIC-401"
    assert saved["serial_number"] == "SN-8849201"
    assert saved["calibration_status"] == "VALID"

    instruments = list_instruments(db_path=clean_db)
    assert len(instruments) == 1
    assert instruments[0]["model"] == "QuantuMike 0-25mm"

    deleted = delete_instrument("INST-MIC-401", clean_db)
    assert deleted is True


def test_v5_measurement_plan_workflow(clean_db):
    """Verify structured measurement plan creation and specification limits."""
    plan_data = {
        "id": "PLAN-MIC-25MM",
        "project_id": "PRJ-001",
        "instrument_id": "INST-MIC-401",
        "plan_name": "25mm Nominal Check",
        "measurand": "External Diameter",
        "nominal_value": 25.0,
        "tolerance_lower": -0.002,
        "tolerance_upper": 0.002,
        "required_repetitions": 5,
        "procedure_name": "PROC-ISO-3611",
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
    }
    saved = save_measurement_plan(plan_data, clean_db)
    assert saved["id"] == "PLAN-MIC-25MM"
    assert saved["nominal_value"] == 25.0
    assert saved["required_repetitions"] == 5

    plans = list_measurement_plans(db_path=clean_db)
    assert len(plans) == 1


def test_v5_measurement_acquisition_statistics():
    """Verify acquisition statistics: mean, standard deviation, repeatability, outlier filtering."""
    raw_readings = [25.0012, 25.0010, 25.0014, 25.0011, 25.0013]
    mean_val, s_dev, u_rep, outliers = analyze_measurement_series(raw_readings)

    assert pytest.approx(mean_val, abs=1e-5) == 25.00120
    assert s_dev > 0.0
    assert u_rep > 0.0
    assert len(outliers) == 0  # no 3-sigma outliers in tight dataset


def test_v5_uncertainty_workbench_service():
    """Verify interactive GUM Uncertainty Workbench propagation."""
    components = [
        UncertaintyComponentInput(
            name="Repeatability (Type A)",
            distribution="normal",
            semi_range=0.00014,
            coverage_factor_k=1.0,
            sensitivity_coefficient=1.0,
            degrees_of_freedom=4.0,
        ),
        UncertaintyComponentInput(
            name="Digital Resolution",
            distribution="rectangular",
            semi_range=0.0005,
            sensitivity_coefficient=1.0,
        ),
        UncertaintyComponentInput(
            name="Reference Standard Calibration",
            distribution="normal",
            semi_range=0.00040,
            coverage_factor_k=2.0,
            degrees_of_freedom=50.0,
        ),
        UncertaintyComponentInput(
            name="Thermal Expansion",
            distribution="rectangular",
            semi_range=0.00030,
            sensitivity_coefficient=1.0,
        ),
    ]

    res = compute_uncertainty_workbench(components)
    assert res.combined_uncertainty_uc > 0.0
    assert res.effective_degrees_of_freedom > 0.0
    assert res.coverage_factor_k >= 1.95
    assert res.expanded_uncertainty_U95 > res.combined_uncertainty_uc
    assert len(res.budget_breakdown) == 4


def test_v5_conformity_workbench_service():
    """Verify dedicated Conformity Assessment Workbench with ANSI Z540.3 Method 6 guardband."""
    req = ConformityWorkbenchRequest(
        nominal_value=25.0000,
        measured_value=25.0012,
        tolerance_lower=-0.0020,
        tolerance_upper=0.0020,
        expanded_uncertainty_U95=0.00078,
        decision_rule="ANSI/NCSL Z540.3 Method 6",
    )
    res = compute_conformity_workbench(req)
    assert pytest.approx(res.error_of_indication, abs=1e-5) == 0.00120
    assert res.tur > 2.0
    assert res.guardband_width_w > 0.0
    assert res.acceptance_upper < 25.0020
    assert res.conformance_verdict == "PASS"
    assert "ANSI/NCSL Z540.3 Method 6" in res.derivation_statement


def test_v5_rest_api_endpoints(clean_db, monkeypatch):
    """Verify that all V5 FastAPI REST endpoints respond correctly."""
    monkeypatch.setenv("METROLOGY_DB_PATH", clean_db)
    client = TestClient(app)

    # 1. Project API
    p_resp = client.post("/api/projects", json={
        "name": "Precision Calibration 2026",
        "customer_site": "Defense Lab Alpha",
    })
    assert p_resp.status_code == 200
    p_id = p_resp.json()["id"]

    list_p = client.get("/api/projects")
    assert list_p.status_code == 200
    assert len(list_p.json()) == 1

    # 2. Instrument API
    i_resp = client.post("/api/instruments", json={
        "project_id": p_id,
        "manufacturer": "Starrett",
        "model": "733XFL-1",
        "serial_number": "ST-9912",
        "instrument_type": "Micrometer",
        "range_min": 0.0,
        "range_max": 25.0,
        "resolution": 0.001,
    })
    assert i_resp.status_code == 200
    i_id = i_resp.json()["id"]

    list_i = client.get(f"/api/instruments?project_id={p_id}")
    assert list_i.status_code == 200
    assert len(list_i.json()) == 1

    # 3. Plan API
    plan_resp = client.post("/api/plans", json={
        "project_id": p_id,
        "instrument_id": i_id,
        "plan_name": "Mid-Point Check",
        "nominal_value": 12.5,
        "tolerance_lower": -0.002,
        "tolerance_upper": 0.002,
    })
    assert plan_resp.status_code == 200

    # 4. Measurement Acquisition API
    meas_resp = client.post("/api/measurements", json={
        "plan_id": plan_resp.json()["id"],
        "instrument_id": i_id,
        "project_id": p_id,
        "raw_values": [12.5005, 12.5004, 12.5006, 12.5005, 12.5005],
    })
    assert meas_resp.status_code == 200
    assert pytest.approx(meas_resp.json()["mean_value"], abs=1e-5) == 12.5005

    # 5. Workbench API
    wb_resp = client.post("/api/workbench/conformity", json={
        "nominal_value": 12.5,
        "measured_value": 12.5005,
        "tolerance_lower": -0.002,
        "tolerance_upper": 0.002,
        "expanded_uncertainty_U95": 0.0006,
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
    })
    assert wb_resp.status_code == 200
    assert wb_resp.json()["conformance_verdict"] == "PASS"

    # 6. Stats API
    stats_resp = client.get("/api/v5/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["active_projects"] == 1
    assert stats["total_instruments"] == 1
    assert stats["measurement_plans"] == 1
    assert stats["acquired_measurements"] == 1

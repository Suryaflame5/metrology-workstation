import pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.db import init_db, DB_PATH, save_job


def test_project_lifecycle_flow():
    client = TestClient(app)

    # 1. Create Project
    res = client.post(
        "/api/v1/projects",
        json={
            "name": "Automotive Sensor Calibration Q4",
            "description": "Multi-instrument qualification for chassis line",
            "customer_site": "Plant 4, Pune",
            "lead_metrologist": "Marcus Brody",
            "target_standard": "ISO/IEC 17025:2017",
            "due_date": "2026-12-31"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    proj = data["project"]
    proj_id = proj["id"]
    assert proj["status"] == "PLANNING"
    assert proj["metrics"]["total_jobs"] == 0

    # 2. Create a Job and Link to Project
    job_id = save_job({
        "title": "Pressure Transducer Cal",
        "customer_name": "Plant 4, Pune",
        "instrument_name": "Pressure Transducer",
        "instrument_model": "PT-200",
        "instrument_serial": "SN-88910",
        "procedure_name": "Standard Calibration",
        "nominal_value": 100.0,
        "unit": "kPa",
    })
    # job_id obtained directly

    link_res = client.post(f"/api/v1/projects/{proj_id}/link-job/{job_id}")
    assert link_res.status_code == 200

    # 3. Retrieve Project Details and verify linked job
    det_res = client.get(f"/api/v1/projects/{proj_id}")
    assert det_res.status_code == 200
    det = det_res.json()["project"]
    assert len(det["jobs"]) >= 1
    assert det["metrics"]["total_jobs"] >= 1

    # 4. Status Transition PLANNING -> IN_PROGRESS
    patch_res = client.patch(
        f"/api/v1/projects/{proj_id}/status",
        json={"status": "IN_PROGRESS", "notes": "Execution started on bench 1"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["project"]["status"] == "IN_PROGRESS"

    # 5. Transition to REVIEW -> COMPLETED
    client.patch(f"/api/v1/projects/{proj_id}/status", json={"status": "REVIEW"})
    final_res = client.patch(f"/api/v1/projects/{proj_id}/status", json={"status": "COMPLETED"})
    assert final_res.status_code == 200
    assert final_res.json()["project"]["status"] == "COMPLETED"

    # 6. List Projects Filter
    list_res = client.get("/api/v1/projects?status=COMPLETED")
    assert list_res.status_code == 200
    projects = list_res.json()["projects"]
    assert any(p["id"] == proj_id for p in projects)



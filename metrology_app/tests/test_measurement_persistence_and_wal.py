import pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.db import save_job, get_job, DB_PATH

client = TestClient(app)

@pytest.fixture
def test_job():
    job_data = {
        "job_number": "JOB-PERSIST-TEST",
        "title": "Data Loss Prevention Test Job",
        "instrument_name": "Keysight 3458A",
        "instrument_serial": "MY5501",
        "status": "RUNNING",
        "nominal_value": 10.0,
        "unit": "V",
        "tolerance_upper": 0.005,
        "tolerance_lower": -0.005,
        "raw_measurements": [10.001, 10.002]
    }
    job_id = save_job(job_data, db_path=DB_PATH)
    yield job_id


def test_append_single_and_batch_measurements(test_job):
    job_id = test_job
    
    # 1. Append single measurement
    res1 = client.post(f"/api/jobs/{job_id}/measurements", json={"value": 10.0015, "operator": "Tech A"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "success"
    assert len(data1["raw_measurements"]) == 3
    assert data1["statistics"]["count"] == 3
    assert abs(data1["statistics"]["mean"] - 10.0015) < 1e-4

    # Verify persistence in database
    persisted_job = get_job(job_id)
    assert len(persisted_job["raw_measurements"]) == 3

    # 2. Append batch measurements
    res2 = client.post(f"/api/jobs/{job_id}/measurements", json={"values": [10.0018, 10.0022], "operator": "Tech B"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["raw_measurements"]) == 5
    assert data2["statistics"]["count"] == 5

    persisted_job2 = get_job(job_id)
    assert len(persisted_job2["raw_measurements"]) == 5


def test_delete_measurement_and_recalc_stats(test_job):
    job_id = test_job

    # Delete index 0
    res = client.delete(f"/api/jobs/{job_id}/measurements/0")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["raw_measurements"]) >= 1

    # Attempt to delete out of bounds index
    bad_res = client.delete(f"/api/jobs/{job_id}/measurements/999")
    assert bad_res.status_code == 400


def test_replace_all_measurements(test_job):
    job_id = test_job

    res = client.put(f"/api/jobs/{job_id}/measurements", json={"raw_measurements": [10.0001, 10.0002, 10.0003, 10.0004]})
    assert res.status_code == 200
    data = res.json()
    assert len(data["raw_measurements"]) == 4
    assert data["statistics"]["count"] == 4
    assert abs(data["statistics"]["mean"] - 10.00025) < 1e-5

import pytest
import tempfile
import os
import zipfile
import io
from metrology_app.db import init_db, save_job, get_job
from metrology_app.services.evidence_service import export_evidence_package_zip_bytes
from metrology_app.services.job_pipeline_engine import run_job_pipeline

@pytest.fixture
def test_env():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    job_data = {
        "job_number": "JOB-DYN-EV-01",
        "title": "Dynamic Evidence Test Job",
        "instrument_name": "Agilent 34401A",
        "instrument_serial": "US3601",
        "status": "RUNNING",
        "nominal_value": 10.0,
        "unit": "V",
        "tolerance_upper": 0.005,
        "tolerance_lower": -0.005,
        "raw_measurements": [10.0002, 10.0003, 10.0001, 10.0004, 10.0002]
    }
    job_id = save_job(job_data, db_path=path)
    yield path, job_id
    if os.path.exists(path):
        os.remove(path)


def test_export_evidence_using_job_id(test_env):
    path, job_id = test_env

    # Directly export evidence ZIP using job_id (without prior calculation)
    # The dynamic resolver should automatically run the pipeline and generate calculation
    zip_bytes = export_evidence_package_zip_bytes(job_id, db_path=path)
    assert len(zip_bytes) > 0

    # Verify contents of zip
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    filenames = zf.namelist()
    assert any("calculation.json" in fn for fn in filenames)
    assert any("measurements.json" in fn for fn in filenames)
    assert any("uncertainty_budget.json" in fn for fn in filenames)
    assert any("decision.json" in fn for fn in filenames)


def test_export_evidence_using_calc_id(test_env):
    path, job_id = test_env

    # Run pipeline first to obtain calculation_id
    job = run_job_pipeline(job_id, db_path=path)
    calc_id = job["calculation_id"]
    assert calc_id is not None

    # Export using calc_id
    zip_bytes = export_evidence_package_zip_bytes(calc_id, db_path=path)
    assert len(zip_bytes) > 0

    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    filenames = zf.namelist()
    assert any("calculation.json" in fn for fn in filenames)


def test_export_evidence_path_traversal_rejection(test_env):
    path, _ = test_env

    with pytest.raises(ValueError, match="path traversal"):
        export_evidence_package_zip_bytes("../etc/passwd", db_path=path)

    with pytest.raises(ValueError, match="path traversal"):
        export_evidence_package_zip_bytes("..\\boot.ini", db_path=path)

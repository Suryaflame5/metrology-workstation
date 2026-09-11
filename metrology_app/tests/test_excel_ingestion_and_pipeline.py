import os
import io
import pytest
import openpyxl
from metrology_app.services.universal_importer import (
    parse_excel_workbook,
    parse_raw_data_stream,
    auto_detect_columns,
    extract_job_measurements,
)
from metrology_app.services.job_pipeline_engine import (
    run_job_pipeline,
    sign_and_approve_job,
)
from metrology_app.services.job_revision_engine import (
    create_revision_for_job,
    compare_job_revisions,
)
from metrology_app.services.evidence_service import (
    export_evidence_package_zip_bytes,
    verify_evidence_package,
)
from metrology_app.db import (
    init_db,
    save_job,
    get_job,
)


@pytest.fixture
def test_db_path(tmp_path):
    db_file = str(tmp_path / "test_metrology.db")
    init_db(db_file)
    return db_file


def test_excel_binary_creation_and_ingestion(test_db_path):
    # 1. Create a binary Excel workbook with openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DMM_Calibration"
    
    # Headers
    ws.append(["Run", "Nominal_V", "Measured_V", "Std_Deviation", "Temperature_C", "Humidity_Pct"])
    
    # 10 test measurement rows
    for i in range(1, 11):
        ws.append([i, 10.0000, 10.0000 + (i * 0.0002), 0.00008, 23.0 + (i * 0.05), 45.0])
    
    buf = io.BytesIO()
    wb.save(buf)
    excel_bytes = buf.getvalue()

    # 2. Test parse_excel_workbook directly
    sheets, rows, headers = parse_excel_workbook(excel_bytes)
    assert "DMM_Calibration" in sheets
    assert len(rows) == 10
    assert "Measured_V" in headers

    # 3. Test parse_raw_data_stream with binary Excel
    stream_rows = parse_raw_data_stream(excel_bytes, filename="calibration_run.xlsx")
    assert len(stream_rows) == 10
    assert float(stream_rows[0]["Measured_V"]) == pytest.approx(10.0002, abs=1e-5)

    # 4. Auto-detect columns
    col_mapping = auto_detect_columns(headers, stream_rows)
    assert col_mapping["has_measured_values"] is True
    assert col_mapping["overall_confidence_pct"] >= 80

    # 5. Extract job measurements
    extracted = extract_job_measurements(stream_rows, col_mapping["columns"], target_unit="V")
    assert extracted["sample_size"] == 10
    assert len(extracted["raw_measurements"]) == 10
    assert extracted["nominal_value"] == pytest.approx(10.0, abs=1e-3)


def test_end_to_end_job_pipeline_with_excel_data(test_db_path):
    # 1. Prepare raw measurements
    raw_readings = [10.0001, 10.0002, 10.0003, 10.0001, 10.0002, 10.0004, 10.0002, 10.0001, 10.0003, 10.0002]
    
    # 2. Save job to test database
    job_payload = {
        "title": "Precision 10V DMM Verification",
        "job_number": "JOB-2026-TEST",
        "instrument_name": "Fluke 8508A Multimeter",
        "instrument_serial": "SN-TEST-8508A",
        "instrument_model": "8508A",
        "customer_name": "Apex Metrology Labs",
        "procedure_standard": "ISO/IEC 17025:2017",
        "measurand": "DC Voltage",
        "nominal_value": 10.0,
        "unit": "V",
        "tolerance_lower": -0.01,
        "tolerance_upper": 0.01,
        "raw_measurements": raw_readings,
        "operator": "Senior Cal Specialist",
        "status": "DRAFT",
    }
    job_id = save_job(job_payload, db_path=test_db_path)
    assert job_id is not None

    # 3. Execute 1-Click Metrology Pipeline
    pipeline_res = run_job_pipeline(job_id, db_path=test_db_path)
    assert pipeline_res["status"] in ("READY_FOR_APPROVAL", "REVIEW_REQUIRED", "CALCULATED")
    assert "uncertainty_budget" in pipeline_res
    assert "conformity" in pipeline_res
    assert pipeline_res["conformity"]["conformance_verdict"] == "PASS"
    assert pipeline_res["conformity"]["consumer_risk_pfa_pct"] <= 2.0

    # 4. Verify job statistics in DB
    updated_job = get_job(job_id, db_path=test_db_path)
    assert updated_job["statistics"]["count"] == 10

    # 5. Sign and approve job (21 CFR Part 11)
    approved_job = sign_and_approve_job(
        job_id,
        signer_name="Dr. Aris Thorne",
        role="Technical Director",
        reason="Technical Approval & Release Concurrence",
        db_path=test_db_path,
    )
    assert approved_job["status"] in ("APPROVED", "LOCKED")
    assert approved_job["certificate_id"] is not None

    # 6. Test Revision creation
    rev_res = create_revision_for_job(
        job_id,
        notes="Annual Quality Audit Review",
        operator="Lead Auditor",
        db_path=test_db_path,
    )
    assert rev_res["revision_number"] == 2

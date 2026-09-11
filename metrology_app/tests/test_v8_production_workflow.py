"""
Comprehensive Automated Test Suite for V8 Production Workstation,
Batch Processing Engine, Exception Center, Review Cockpit, and Lab Fleet.
"""

import pytest
import tempfile
import os
import json
import base64

from metrology_app.db import (
    init_db,
    save_job,
    get_job,
    list_jobs,
    list_customers,
    save_customer,
    list_procedure_templates,
    get_procedure_template,
    list_connected_devices,
)
from metrology_app.services.universal_importer import (
    validate_imported_data,
    build_suggested_measurement_model,
)
from metrology_app.services.procedure_template_service import (
    get_all_templates,
    instantiate_job_from_template,
)
from metrology_app.services.job_pipeline_engine import (
    run_1click_job_pipeline,
    sign_and_approve_job,
)
from metrology_app.services.batch_pipeline_engine import execute_batch_run
from metrology_app.services.exception_center_service import get_exception_center_summary
from metrology_app.services.review_cockpit_service import get_review_cockpit_data
from metrology_app.services.job_revision_engine import (
    create_revision_for_job,
    compare_job_revisions,
)
from metrology_app.services.hardware_device_adapter import (
    discover_available_devices,
    send_scpi_command,
    stream_instrument_measurements,
)
from metrology_app.services.evidence_service import (
    export_evidence_package_zip_bytes,
    verify_evidence_package,
)


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    from metrology_app.db import seed_default_jobs_and_standards
    seed_default_jobs_and_standards(db_path)
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_procedure_templates_and_instantiation(test_db):
    templates = get_all_templates(db_path=test_db)
    assert len(templates) >= 5
    codes = [t["code"] for t in templates]
    assert "EURAMET-cg-15" in codes
    assert "ISO-3611" in codes

    job = instantiate_job_from_template(
        template_id="PROC-EURAMET-CG-15",
        customer_name="Apex Aerospace Systems",
        instrument_name="Multimeter 8.5 Digits",
        instrument_model="Fluke 8508A",
        instrument_serial="SN-TEST-998",
        operator="Marcus Tech",
        db_path=test_db,
    )
    assert job is not None
    assert job["nominal_value"] == 10.0
    assert job["unit"] == "V"
    assert job["customer_name"] == "Apex Aerospace Systems"


def test_smart_data_validation_and_modeling():
    # Normal readings with 1 Grubbs outlier
    raw_readings = [10.0018, 10.0019, 10.0020, 10.0021, 10.0150]
    rows = [{"Val": r} for r in raw_readings]
    mapping = {"Val": {"role": "measured"}}

    val = validate_imported_data(
        rows=rows,
        column_mapping=mapping,
        nominal=10.0,
        tolerance_lower=-0.005,
        tolerance_upper=0.005,
        target_unit="V",
    )
    assert val["valid_rows_count"] == 5
    assert len(val["outliers"]) >= 1  # 10.0150 is > 2.8 sigma
    assert len(val["range_breaches"]) >= 1  # 10.0150 > 10.005

    model = build_suggested_measurement_model("DC Voltage", 10.0, "V", raw_readings)
    assert model["suggested_model_status"] == "READY"
    assert len(model["contributors"]) >= 4
    assert model["combined_uncertainty_uc"] > 0
    assert model["expanded_uncertainty_U95"] > model["combined_uncertainty_uc"]


def test_1click_pipeline_and_review_cockpit(test_db):
    job = instantiate_job_from_template(
        template_id="PROC-EURAMET-CG-15",
        customer_name="Northrop Grumman",
        instrument_name="Digital Multimeter",
        instrument_model="Keysight 34461A",
        instrument_serial="SN-KEY-4421",
        db_path=test_db,
    )
    # Populate readings
    job["raw_measurements"] = [10.0018, 10.0021, 10.0019, 10.0022, 10.0020]
    save_job(job, db_path=test_db)

    # Run 1-Click Pipeline
    processed = run_1click_job_pipeline(job["id"], db_path=test_db)
    assert processed["status"] in ("READY_FOR_APPROVAL", "REVIEW_REQUIRED")
    assert processed["conformity"]["conformance_verdict"] == "PASS"

    # Review Cockpit
    cockpit = get_review_cockpit_data(job["id"], db_path=test_db)
    assert cockpit["result"]["mean"] > 10.0
    assert len(cockpit["quality_checks"]) == 5

    # 21 CFR Part 11 Electronic Signature
    signed = sign_and_approve_job(
        job["id"],
        signer_name="Marcus Brody",
        role="Lead Metrologist",
        reason="Quality approval",
        db_path=test_db,
    )
    assert signed["status"] == "APPROVED"
    assert signed["digital_signature"]["signature_hash"] is not None


def test_job_revision_and_diff(test_db):
    job = instantiate_job_from_template(
        template_id="PROC-ISO-3611",
        customer_name="Lockheed Precision",
        instrument_name="Outside Micrometer",
        instrument_model="Mitutoyo 293-240",
        instrument_serial="SN-MIT-0129",
        db_path=test_db,
    )
    job["raw_measurements"] = [25.0004, 25.0006, 25.0003, 25.0007, 25.0005]
    save_job(job, db_path=test_db)
    run_1click_job_pipeline(job["id"], db_path=test_db)

    # Create Revision 2
    rev2 = create_revision_for_job(job["id"], notes="Zero adjustment after cleaning", db_path=test_db)
    assert rev2["revision_number"] == 2
    assert rev2["parent_job_id"] == job["id"]

    # Compare Diff
    diff = compare_job_revisions(job["id"], rev2["id"], db_path=test_db)
    assert diff["job_a"]["revision"] == 1
    assert diff["job_b"]["revision"] == 2
    assert diff["total_unchanged"] > 0


def test_batch_processing_and_exceptions(test_db):
    instruments = [
        {"serial": f"BAT-SN-{i:02d}", "model": "Fluke 87V", "customer": "Tesla Energy"}
        for i in range(10)
    ]
    batch = execute_batch_run(
        batch_title="Test Fleet Batch",
        procedure_template_id="PROC-EURAMET-CG-15",
        instruments=instruments,
        operator="Marcus Tech",
        fail_rate_simulation=0.10,
        db_path=test_db,
    )
    assert batch["total_instruments"] == 10
    assert batch["completed_count"] == 10
    assert batch["status"] == "COMPLETED"

    # Exception center summary
    exc_summary = get_exception_center_summary(db_path=test_db)
    assert exc_summary["total_jobs_scanned"] >= 10
    assert len(exc_summary["feed"]) > 0


def test_hardware_adapter_simulation(test_db):
    devs = discover_available_devices(db_path=test_db)
    assert len(devs) >= 4

    # Test SCPI *IDN?
    idn_res = send_scpi_command("DEV-FLK-8508A", "*IDN?", db_path=test_db)
    assert "FLUKE" in idn_res["response"]

    # Test live stream
    stream = stream_instrument_measurements("DEV-FLK-8508A", count=5, interval_sec=0.01, db_path=test_db)
    assert stream["count"] == 5
    assert len(stream["readings"]) == 5
    assert stream["unit"] == "V"


def test_evidence_package_and_verification(test_db):
    job = instantiate_job_from_template(
        template_id="PROC-EURAMET-CG-15",
        customer_name="Apex Aero",
        instrument_name="DMM",
        instrument_model="Fluke 8508A",
        instrument_serial="SN-EV-001",
        db_path=test_db,
    )
    job["raw_measurements"] = [10.0019, 10.0020, 10.0018, 10.0021, 10.0019]
    save_job(job, db_path=test_db)
    processed = run_1click_job_pipeline(job["id"], db_path=test_db)

    calc_id = processed["calculation_id"]
    zip_bytes = export_evidence_package_zip_bytes(calc_id, db_path=test_db)
    assert len(zip_bytes) > 500

    ver = verify_evidence_package(zip_bytes)
    assert ver["is_valid"] is True
    assert ver["tamper_detected"] is False
    assert ver["total_files_verified"] >= 6

"""
Comprehensive Automated Test Suite for the Laboratory Calibration & Metrology Execution Platform.
Verifies the end-to-end master pipeline:
  Job -> Asset Registry -> Instrument Registry -> Unified InstrumentDriver ->
  Procedure Execution -> Automated Measurement -> Environmental Telemetry ->
  Deterministic GUM -> Conformity -> Electronic Signatures -> PDF & DCC JSON/XML ->
  Evidence Vault.
"""

import pytest
import tempfile
import os
import json
import xml.etree.ElementTree as ET

from metrology_app.db import (
    init_db,
    save_job,
    get_job,
    seed_default_jobs_and_standards,
)
from metrology_app.services.asset_service import (
    register_asset,
    get_asset_details,
    scan_and_identify_asset,
    list_all_assets,
    update_asset_after_calibration,
)
from metrology_app.industrial.instrument_driver import (
    create_instrument_driver,
    MockSimulatorDriver,
    SCPITCPDriver,
    HardwareCommunicationError,
)
from metrology_app.services.hardware_acquisition_service import (
    execute_instrument_acquisition,
    get_hardware_audit_log,
    clear_hardware_audit_log,
)
from metrology_app.services.procedure_execution_service import (
    create_procedure,
    get_procedure,
    update_procedure,
    approve_procedure,
    create_procedure_revision,
    ProcedureLockedError,
)
from metrology_app.services.automated_calibration_engine import (
    run_automated_calibration,
)
from metrology_app.services.canonical_certificate_service import (
    build_canonical_result_model,
    export_dcc_json,
    export_dcc_xml,
    generate_canonical_pdf,
)
from metrology_app.services.job_pipeline_engine import (
    sign_and_approve_job,
)


@pytest.fixture
def lab_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    seed_default_jobs_and_standards(db_path)
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


# =============================================================================
# 1. ASSET REGISTRY & BARCODE TRACKING
# =============================================================================

def test_asset_registry_lifecycle_and_scanning(lab_db):
    asset_data = {
        "id": "ASSET-FLUKE-8508A-01",
        "asset_tag": "TAG-LAB-8508",
        "serial_number": "FLK-9920148",
        "manufacturer": "Fluke Calibration",
        "model": "8508A Reference Multimeter",
        "instrument_type": "Digital Multimeter 8.5 Digits",
        "range_min": 0.0,
        "range_max": 1000.0,
        "resolution": 0.0000001,
        "accuracy_spec": "±0.65 ppm of reading",
        "calibration_interval_days": 365,
        "location": "Primary Standards Bay 1",
        "owner_customer_name": "Lockheed Advanced Labs",
    }

    registered = register_asset(asset_data, db_path=lab_db)
    assert registered["id"] == "ASSET-FLUKE-8508A-01"
    assert registered["next_calibration_due"] is not None

    # Scan by exact tag
    scan_tag = scan_and_identify_asset("TAG-LAB-8508", db_path=lab_db)
    assert scan_tag["found"] is True
    assert scan_tag["asset"]["serial_number"] == "FLK-9920148"
    assert scan_tag["asset"]["calibration_health"] in ("COMPLIANT", "EXPIRING_SOON")

    # Scan by QR code string
    qr_code = "METRO:ASSET:ASSET-FLUKE-8508A-01:FLK-9920148"
    scan_qr = scan_and_identify_asset(qr_code, db_path=lab_db)
    assert scan_qr["found"] is True
    assert scan_qr["asset"]["id"] == "ASSET-FLUKE-8508A-01"

    # Scan non-existent
    scan_missing = scan_and_identify_asset("UNKNOWN-9999", db_path=lab_db)
    assert scan_missing["found"] is False

    # Update after calibration
    updated = update_asset_after_calibration(
        asset_id="ASSET-FLUKE-8508A-01",
        calibration_date="2026-09-01T10:00:00Z",
        certificate_id="CERT-2026-0099",
        conformance_status="PASS",
        db_path=lab_db,
    )
    assert updated["status"] == "IN_SERVICE"
    assert updated["last_calibration_date"] == "2026-09-01"
    assert len(updated["metadata"]["calibration_history"]) == 1


# =============================================================================
# 2. UNIFIED INSTRUMENT DRIVER HIERARCHY
# =============================================================================

def test_unified_instrument_driver_hierarchy():
    # 1. Explicit Simulator Driver
    driver = create_instrument_driver({
        "bus": "VIRTUAL",
        "driver_profile": "KEYSIGHT_34461A",
    })
    assert isinstance(driver, MockSimulatorDriver)

    conn = driver.connect()
    assert conn["status"] == "CONNECTED_SIMULATOR"
    assert "Keysight" in driver.identify()

    # Measure default 10.0 V nominal
    m1 = driver.measure()
    assert m1["status"] == "VALID"
    assert abs(m1["value"] - 10.0) < 0.001
    assert m1["unit"] == "V"

    # Configure new nominal
    driver.configure({"nominal": 5.0, "unit": "V"})
    m2 = driver.measure()
    assert abs(m2["value"] - 5.0) < 0.001

    # Status and error queue
    st = driver.status()
    assert st["is_connected"] is True
    errs = driver.get_errors()
    assert errs == ['+0,"No error"']

    driver.reset()
    driver.disconnect()
    assert driver.is_connected is False

    # 2. Strict Physical Hardware Honesty (No Fake Connection)
    unreachable_driver = SCPITCPDriver("TCPIP::127.0.0.1::59999::SOCKET", timeout_sec=0.2)
    with pytest.raises(HardwareCommunicationError):
        unreachable_driver.connect()
    assert unreachable_driver.is_connected is False


# =============================================================================
# 3. HARDWARE ACQUISITION & AUDIT LOGGER
# =============================================================================

def test_hardware_acquisition_and_command_audit():
    clear_hardware_audit_log()

    dev_config = {
        "id": "BENCH-DMM-01",
        "bus": "VIRTUAL",
        "driver_profile": "KEYSIGHT_34461A",
    }

    result = execute_instrument_acquisition(
        device_config=dev_config,
        count=5,
        configure_params={"nominal": 10.0, "unit": "V"},
        job_id="JOB-CAL-TEST-01",
    )

    assert result["status"] == "SUCCESS"
    assert result["readings_count"] == 5
    assert len(result["raw_values"]) == 5
    assert len(result["hardware_evidence_sha256"]) == 64

    # Audit log validation
    audit_events = get_hardware_audit_log("JOB-CAL-TEST-01")
    assert len(audit_events) >= 7  # Connect, IDN, Configure, 5x Measure, Disconnect
    commands = [e["command_sent"] for e in audit_events]
    assert "CONNECT" in commands
    assert "*IDN?" in commands
    assert "MEASURE" in commands
    assert "DISCONNECT" in commands


# =============================================================================
# 4. PROCEDURE ENGINE VERSIONING & IMMUTABILITY LOCKING
# =============================================================================

def test_procedure_engine_versioning_and_locking(lab_db):
    steps = [
        {"step_number": 1, "step_type": "CONFIGURE", "parameters": {"function": "VOLT:DC"}},
        {"step_number": 2, "step_type": "WAIT", "parameters": {"delay_seconds": 0.01}},
        {"step_number": 3, "step_type": "REPEAT", "parameters": {"repeat_count": 5}},
        {"step_number": 4, "step_type": "CHECK_LIMIT", "parameters": {"usl": 10.005, "lsl": 9.995}},
    ]

    proc_data = {
        "code": "SOP-VOLT-10V",
        "title": "Precision DC Voltage 10V Verification",
        "category": "Electrical",
        "version": "1.0",
        "measurand": "DC Voltage",
        "nominal_value": 10.0,
        "tolerance_lower": -0.005,
        "tolerance_upper": 0.005,
        "steps": steps,
    }

    # 1. Create in DRAFT
    proc = create_procedure(proc_data, db_path=lab_db)
    assert proc["approval_status"] == "DRAFT"
    assert len(proc["steps"]) == 4

    # 2. Update while in DRAFT (permitted)
    updated = update_procedure(proc["id"], {"title": "Updated Title in Draft"}, db_path=lab_db)
    assert updated["title"] == "Updated Title in Draft"

    # 3. Approve and Lock
    approved = approve_procedure(proc["id"], approver_name="Dr. Katherine Stone", db_path=lab_db)
    assert approved["approval_status"] == "APPROVED"
    assert approved["approved_by"] == "Dr. Katherine Stone"

    # 4. Attempt to modify locked procedure (must fail)
    with pytest.raises(ProcedureLockedError):
        update_procedure(proc["id"], {"title": "Illegal Modification"}, db_path=lab_db)

    # 5. Fork new revision version
    rev = create_procedure_revision(
        base_procedure_id=proc["id"],
        new_version="1.1",
        author="Marcus Brody",
        db_path=lab_db,
    )
    assert rev["version"] == "1.1"
    assert rev["approval_status"] == "DRAFT"
    assert rev["metadata"]["parent_procedure_id"] == proc["id"]


# =============================================================================
# 5. AUTOMATED EXECUTION & CANONICAL DIGITAL CALIBRATION CERTIFICATE (DCC)
# =============================================================================

def test_end_to_end_automated_calibration_and_dcc(lab_db):
    from metrology_app.services.procedure_template_service import instantiate_job_from_template

    # 1. Instantiate Job
    job = instantiate_job_from_template(
        template_id="PROC-EURAMET-CG-15",
        customer_name="Northrop Grumman Mission Systems",
        instrument_name="Reference Multimeter",
        instrument_model="Keysight 34461A",
        instrument_serial="SN-KEY-88124",
        operator="Marcus Tech",
        db_path=lab_db,
    )
    job_id = job["id"]

    # 2. Run Automated Calibration Execution
    exec_res = run_automated_calibration(
        job_id=job_id,
        ambient_environment={
            "ambient_temperature_c": 20.05,
            "relative_humidity_pct": 45.8,
            "atmospheric_pressure_hpa": 1013.25,
        },
        db_path=lab_db,
    )

    assert exec_res["measurements_acquired"] >= 5
    assert exec_res["conformity_verdict"] == "PASS"
    assert exec_res["expanded_uncertainty_U95"] is not None
    assert exec_res["hardware_trace_events"] >= 3

    # 3. Dual-Sign 21 CFR Part 11 Electronic Signature
    signed = sign_and_approve_job(
        job_id,
        signer_name="Marcus Brody",
        role="Lead Metrologist",
        reason="Automated execution verified against ISO 17025 standard",
        db_path=lab_db,
    )
    assert signed["status"] == "APPROVED"
    assert signed["digital_signature"]["signature_hash"] is not None

    # 4. Canonical DCC JSON Export
    dcc_json_str = export_dcc_json(job_id, db_path=lab_db)
    dcc_dict = json.loads(dcc_json_str)
    assert dcc_dict["dcc_version"] == "3.2.0"
    assert dcc_dict["item_under_test"]["serial_number"] == "SN-KEY-88124"
    assert dcc_dict["conformity_statement"]["verdict"] == "PASS"
    assert dcc_dict["calibration_results"]["expanded_uncertainty_U95"] > 0
    assert dcc_dict["calibration_results"]["coverage_factor_k"] == 2.0

    # 5. Canonical DCC XML Export
    dcc_xml_str = export_dcc_xml(job_id, db_path=lab_db)
    root = ET.fromstring(dcc_xml_str)
    assert "digitalCalibrationCertificate" in root.tag
    assert root.attrib.get("schemaVersion") == "3.2.0"

    # 6. Canonical PDF Generation
    pdf_bytes = generate_canonical_pdf(job_id, db_path=lab_db)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


# =============================================================================
# 6. REST API ENDPOINTS INTEGRATION
# =============================================================================

def test_laboratory_platform_rest_api():
    from fastapi.testclient import TestClient
    from metrology_app.server import app

    client = TestClient(app)

    # 1. Register Asset via API
    asset_payload = {
        "asset_tag": "TAG-API-TEST-01",
        "serial_number": "SN-API-7711",
        "manufacturer": "Keysight",
        "model": "3458A 8.5 Digit DMM",
        "instrument_type": "Digital Multimeter",
        "calibration_interval_days": 365,
    }
    r_reg = client.post("/api/v1/assets", json=asset_payload)
    assert r_reg.status_code == 200
    asset_id = r_reg.json()["id"]

    # 2. List & Scan Asset
    r_list = client.get("/api/v1/assets")
    assert r_list.status_code == 200
    assert any(a["id"] == asset_id for a in r_list.json()["assets"])

    r_scan = client.get(f"/api/v1/assets/scan/{asset_payload['asset_tag']}")
    assert r_scan.status_code == 200
    assert r_scan.json()["found"] is True
    assert r_scan.json()["asset"]["serial_number"] == "SN-API-7711"

    # 3. Hardware Acquisition API
    r_acq = client.post("/api/v1/hardware/acquire", json={
        "device": {"bus": "VIRTUAL", "driver_profile": "KEYSIGHT_34461A"},
        "count": 3,
        "job_id": "JOB-API-ACQ-01",
    })
    assert r_acq.status_code == 200
    assert r_acq.json()["status"] == "SUCCESS"
    assert r_acq.json()["readings_count"] == 3

    # Audit log API
    r_log = client.get("/api/v1/hardware/audit-log?job_id=JOB-API-ACQ-01")
    assert r_log.status_code == 200
    assert len(r_log.json()["events"]) >= 3

    # 4. Procedure API
    proc_payload = {
        "code": "SOP-API-TEST",
        "title": "API Test Procedure",
        "category": "Electrical",
        "nominal_value": 10.0,
        "steps": [
            {"step_number": 1, "step_type": "CONFIGURE", "parameters": {"nominal": 10.0}},
            {"step_number": 2, "step_type": "MEASURE", "parameters": {}},
        ],
    }
    r_proc = client.post("/api/v1/procedures", json=proc_payload)
    assert r_proc.status_code == 200
    proc_id = r_proc.json()["id"]

    r_appr = client.post(f"/api/v1/procedures/{proc_id}/approve", json={"approver": "Chief Metrologist"})
    assert r_appr.status_code == 200
    assert r_appr.json()["approval_status"] == "APPROVED"

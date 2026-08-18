"""
Automated Test Suite for Metrology Workstation V5.1 — Reproducible Measurement Intelligence.
Covers:
  1. Audit chain continuous cryptographic verification
  2. Tampered audit block detection
  3. Evidence 12-stage exact mathematical reproduction
  4. HTML calibration certificate generation
  5. Pre-built engineering sandbox scenarios
"""

import os
import pytest
import sqlite3
import hashlib
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.db import init_db, save_audit_event
from metrology_app.services.verifier_service import verify_entire_audit_chain, verify_calculation_by_id


@pytest.fixture
def clean_v5_1_client(tmp_path):
    db_file = str(tmp_path / "v5_1_test.db")
    os.environ["METROLOGY_DB_PATH"] = db_file
    init_db(db_file)
    client = TestClient(app)
    yield client
    if os.path.exists(db_file):
        os.remove(db_file)


def test_audit_chain_verification_on_empty_and_populated_ledger(clean_v5_1_client, tmp_path):
    db_file = str(tmp_path / "v5_1_test.db")
    
    # 1. Empty audit ledger
    res_empty = verify_entire_audit_chain(db_path=db_file)
    assert res_empty["is_valid"] is True
    assert res_empty["status"] == "VALID"
    assert res_empty["total_events"] == 0

    # 2. Add sequential audit events
    ev1 = save_audit_event("CREATE_PROJECT", "PRJ-001", "OPERATOR", {"name": "Test Project 1"}, db_path=db_file)
    ev2 = save_audit_event("CREATE_INSTRUMENT", "INST-001", "OPERATOR", {"model": "QuantuMike"}, db_path=db_file)
    ev3 = save_audit_event("CALCULATE", "CALC-001", "ENGINE", {"tur": 2.56}, db_path=db_file)

    res_pop = verify_entire_audit_chain(db_path=db_file)
    assert res_pop["is_valid"] is True
    assert res_pop["status"] == "VERIFIED"
    assert res_pop["total_events"] == 3


def test_tampered_audit_ledger_detection(clean_v5_1_client, tmp_path):
    db_file = str(tmp_path / "v5_1_test.db")
    
    save_audit_event("CREATE_PROJECT", "PRJ-101", "OPERATOR", {"site": "Lab A"}, db_path=db_file)
    save_audit_event("CREATE_PROJECT", "PRJ-102", "OPERATOR", {"site": "Lab B"}, db_path=db_file)
    
    # Tamper with the second record directly in SQLite
    conn = sqlite3.connect(db_file)
    conn.execute("UPDATE audit_events SET prev_event_hash = 'TAMPERED_PREV_HASH' WHERE id = 2")
    conn.commit()
    conn.close()

    res_tampered = verify_entire_audit_chain(db_path=db_file)
    assert res_tampered["is_valid"] is False
    assert res_tampered["status"] == "BROKEN_LINK"
    assert res_tampered["failed_block_id"] == 2


def test_sandbox_scenarios_endpoint(clean_v5_1_client):
    response = clean_v5_1_client.get("/api/sandbox/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 5
    ids = [s["id"] for s in scenarios]
    assert "scenario-micrometer" in ids
    assert "scenario-caliper" in ids
    assert "scenario-guardband-compare" in ids


def test_calculation_reproduction_and_html_certificate(clean_v5_1_client):
    # 1. Execute a single-point calibration
    calc_req = {
        "instrument_name": "Precision Micrometer 0-25mm",
        "procedure_name": "PROC-MIC-01",
        "nominal_value": 25.0,
        "tolerance_limit_mm": 0.002,
        "readings_mm": [25.0012, 25.0010, 25.0014, 25.0011, 25.0013],
        "ambient_temp_c": 20.0,
        "relative_humidity_pct": 45.0,
        "operator": "Lead Metrologist",
    }
    create_res = clean_v5_1_client.post("/api/calculations", json=calc_req)
    assert create_res.status_code == 200
    calc_id = create_res.json()["id"]

    # 2. Reproduce evidence via endpoint
    rep_res = clean_v5_1_client.post(f"/api/evidence/reproduce/{calc_id}")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["is_valid"] is True
    assert rep_data["reproduced_successfully"] is True
    assert rep_data["overall_status"] == "VERIFIED"

    # 3. Request HTML calibration certificate
    cert_res = clean_v5_1_client.get(f"/api/reports/html/{calc_id}")
    assert cert_res.status_code == 200
    assert "OFFICIAL CALIBRATION CERTIFICATE" in cert_res.text
    assert "ISO/IEC 17025:2017" in cert_res.text
    assert calc_id in cert_res.text


def test_api_verify_audit_chain_endpoint(clean_v5_1_client):
    res = clean_v5_1_client.post("/api/audit/verify-chain")
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True

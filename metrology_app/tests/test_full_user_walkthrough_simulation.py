"""
Full End-to-End User Persona Simulation Test Suite.
Simulates a real Quality Engineer / Metrology Specialist interacting with
every button, workspace, calculation feature, report, and regulatory mechanism.
"""

import os
import io
import base64
import json
import pytest
from fastapi.testclient import TestClient

from metrology_app.server import app
from metrology_app.db import init_db


@pytest.fixture
def client(tmp_path):
    """Create isolated test client with a fresh temporary SQLite database."""
    db_file = str(tmp_path / "test_user_sim.db")
    init_db(db_file)
    
    # Override DB_PATH in server & db modules
    import metrology_app.db as db_mod
    import metrology_app.services.loss_engine as loss_mod
    import metrology_app.services.investigation_engine as inv_mod
    import metrology_app.services.recovery_engine as rec_mod
    import metrology_app.services.demo_factory_data as demo_mod
    import metrology_app.services.watchfolder_service as watch_mod
    import metrology_app.services.production_report_service as rep_mod
    
    old_db = db_mod.DB_PATH
    old_env_db = os.environ.get("METROLOGY_DB_PATH")
    os.environ["METROLOGY_DB_PATH"] = db_file
    db_mod.DB_PATH = db_file
    loss_mod.DB_PATH = db_file
    inv_mod.DB_PATH = db_file
    rec_mod.DB_PATH = db_file
    demo_mod.DB_PATH = db_file
    watch_mod.DB_PATH = db_file
    rep_mod.DB_PATH = db_file

    with TestClient(app) as test_client:
        yield test_client

    if old_env_db is not None:
        os.environ["METROLOGY_DB_PATH"] = old_env_db
    else:
        os.environ.pop("METROLOGY_DB_PATH", None)
    db_mod.DB_PATH = old_db
    loss_mod.DB_PATH = old_db
    inv_mod.DB_PATH = old_db
    rec_mod.DB_PATH = old_db
    demo_mod.DB_PATH = old_db
    watch_mod.DB_PATH = old_db
    rep_mod.DB_PATH = old_db


def test_complete_user_workflow_simulation(client):
    """
    Simulate full operator journey:
    1. Check Overview -> 2. Seed Demo -> 3. Ingest Custom CSV -> 4. Analyze Losses ->
    5. Trigger Investigation -> 6. Log Action -> 7. Verify Recovery ROI ->
    8. Generate Reports & PDFs -> 9. Run GUM Pipeline & 21 CFR Part 11 Approval ->
    10. Replay 12-Stage Math -> 11. Export & Verify Evidence Bundle.
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: User opens application and views empty factory overview
    # -------------------------------------------------------------------------
    resp = client.get("/api/v1/factory/overview")
    assert resp.status_code == 200
    overview_data = resp.json()
    assert overview_data["factory_status"] == "OPERATIONAL"
    assert "metrics" in overview_data

    # -------------------------------------------------------------------------
    # STEP 2: User clicks "Load Demo Scenario" button
    # -------------------------------------------------------------------------
    resp = client.post("/api/v1/factory/demo/seed")
    assert resp.status_code == 200
    seed_result = resp.json()
    assert seed_result["status"] == "SUCCESS"
    assert seed_result["seeded_entities"]["recovered_value_per_month"] == 28800.0

    # User re-checks overview: KPIs should now reflect the live demo scenario
    resp = client.get("/api/v1/factory/overview")
    assert resp.status_code == 200
    overview_data = resp.json()
    assert overview_data["metrics"]["parts_inspected_today"] >= 200
    assert overview_data["metrics"]["monitored_machines_count"] >= 3
    assert overview_data["metrics"]["total_loss_exposure"] >= 36000.0
    assert overview_data["metrics"]["verified_monthly_recovered_roi"] >= 28800.0

    # -------------------------------------------------------------------------
    # STEP 3: User inspects Parts & Characteristics workspace
    # -------------------------------------------------------------------------
    resp = client.get("/api/v1/factory/parts")
    assert resp.status_code == 200
    parts = resp.json()
    assert len(parts) >= 1
    part_a = parts[0]
    assert "PART-A-10MM" in part_a["part_number"]
    assert len(part_a["revisions"]) >= 1
    assert len(part_a["revisions"][0]["characteristics"]) >= 1

    # -------------------------------------------------------------------------
    # STEP 4: User uploads a new custom 20-part CSV inspection dataset
    # -------------------------------------------------------------------------
    csv_content = "PartSeq,Nominal,MeasuredValue,Tool\n"
    for i in range(1, 21):
        # 20 parts with stable 10.001 mm readings
        csv_content += f"{i},10.0000,{10.0000 + (i * 0.0001):.4f},Tool #1\n"
    
    b64_csv = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    
    resp = client.post(
        "/api/v1/factory/inspections/ingest",
        json={
            "file_base64": b64_csv,
            "filename": "custom_batch_01.csv",
            "part_id": part_a["id"],
            "machine_id": "Machine #4",
            "operator": "Senior Metrologist",
        },
    )
    assert resp.status_code == 200
    ingest_res = resp.json()
    assert ingest_res["status"] == "SUCCESS"
    assert ingest_res["total_parts"] == 20
    assert ingest_res["passed_parts"] == 20
    assert ingest_res["failed_parts"] == 0

    # -------------------------------------------------------------------------
    # STEP 5: User updates Factory Cost Settings
    # -------------------------------------------------------------------------
    resp = client.get("/api/v1/factory/cost-config")
    assert resp.status_code == 200
    cost_cfg = resp.json()

    # User modifies scrap cost and hourly downtime
    cost_cfg["scrap_cost_per_part"] = 1500.0
    cost_cfg["downtime_cost_per_hr"] = 2000.0
    resp = client.put("/api/v1/factory/cost-config", json=cost_cfg)
    assert resp.status_code == 200
    updated_cfg = resp.json()
    assert updated_cfg["scrap_cost_per_part"] == 1500.0

    # -------------------------------------------------------------------------
    # STEP 6: User navigates to Root-Cause Investigations
    # -------------------------------------------------------------------------
    resp = client.get("/api/v1/factory/investigations")
    assert resp.status_code == 200
    invs = resp.json()
    assert len(invs) >= 1
    inv_0 = invs[0]
    assert "Tool #17" in str(inv_0["correlation_matrix"])

    # User views investigation details
    resp = client.get(f"/api/v1/factory/investigations/{inv_0['id']}")
    assert resp.status_code == 200
    inv_details = resp.json()
    assert len(inv_details["actions"]) >= 1

    # User adds a new preventive action note
    resp = client.post(
        "/api/v1/factory/actions",
        json={
            "investigation_id": inv_0["id"],
            "action_title": "Install High-Pressure Coolant Nozzle",
            "description": "Improve chip evacuation on Okuma LB3000.",
            "assigned_to": "Tooling Engineer",
            "status": "RESOLVED",
        },
    )
    assert resp.status_code == 200
    action_res = resp.json()
    assert action_res["status"] == "SUCCESS"

    # -------------------------------------------------------------------------
    # STEP 7: User executes Before vs After Recovery Comparison
    # -------------------------------------------------------------------------
    resp = client.post(
        "/api/v1/factory/recovery/compare",
        json={
            "baseline_job_id": "INSP-DEMO-001",
            "verification_job_id": "INSP-DEMO-002",
            "verified_by": "Quality Director",
        },
    )
    assert resp.status_code == 200
    rec_compare = resp.json()
    assert rec_compare["status"] == "VERIFIED_ROI_PROOF"
    assert rec_compare["comparison"]["defect_rate_reduction_pct"] == 12.0
    assert rec_compare["comparison"]["monthly_recovered_value"] > 0

    # -------------------------------------------------------------------------
    # STEP 8: User generates and downloads HTML & ReportLab PDF Reports
    # -------------------------------------------------------------------------
    # 1. Inspection Report HTML
    resp = client.get("/api/v1/factory/reports/inspection/INSP-DEMO-001/html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "NovyraX Quality Operations Workstation" in resp.text

    # 2. Inspection Report PDF
    resp = client.get("/api/v1/factory/reports/inspection/INSP-DEMO-001/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 1000  # Valid binary PDF bytes

    # 3. Loss & Recovery ROI HTML
    resp = client.get("/api/v1/factory/reports/recovery/html")
    assert resp.status_code == 200
    assert "Total Verified Monthly Recovery Value" in resp.text

    # 4. Loss & Recovery ROI PDF
    resp = client.get("/api/v1/factory/reports/recovery/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 1000

    # -------------------------------------------------------------------------
    # STEP 9: User runs GUM 1-Click Metrology Pipeline on Calibration Job
    # -------------------------------------------------------------------------
    # Create a calibration job
    job_payload = {
        "id": "JOB-USER-SIM-01",
        "job_number": "JOB-2026-SIM-01",
        "title": "Digital Micrometer Precision Calibration",
        "customer_name": "Apex Aerospace Corp",
        "instrument_name": "Digital Outside Micrometer",
        "instrument_model": "Mitutoyo 293-140-30",
        "instrument_serial": "SN-MTR-9042",
        "procedure_name": "Micrometer ISO 17025 Standard Calibration",
        "nominal_value": 25.0000,
        "tolerance_upper": 0.0020,
        "tolerance_lower": -0.0020,
        "unit": "mm",
        "raw_measurements": [25.0012, 25.0011, 25.0013, 25.0012, 25.0012],
    }
    resp = client.post("/api/jobs", json=job_payload)
    assert resp.status_code == 200

    # Execute 1-Click pipeline (Statistics -> GUM Uncertainty Budget -> Method 6 Guardband)
    resp = client.post("/api/jobs/JOB-USER-SIM-01/pipeline")
    assert resp.status_code == 200
    pipe_res = resp.json()
    assert pipe_res["status"] == "success"
    job_updated = pipe_res["job"]
    assert job_updated["conformity"]["conformance_verdict"] == "PASS"
    assert "expanded_uncertainty_U95" in job_updated["uncertainty_budget"]

    # -------------------------------------------------------------------------
    # STEP 10: User signs & approves job (21 CFR Part 11 Electronic Signature)
    # -------------------------------------------------------------------------
    resp = client.post(
        "/api/jobs/JOB-USER-SIM-01/approve",
        json={
            "signer_name": "Dr. Aris Thorne",
            "signer_role": "Lead Quality Architect",
            "meaning": "Technical Conformity & ISO/IEC 17025:2017 Approval",
        },
    )
    assert resp.status_code == 200
    appr_res = resp.json()
    assert appr_res["status"] == "success"
    assert appr_res["job"]["status"] == "APPROVED"
    assert "digital_signature" in appr_res["job"]
    assert "signature_hash" in appr_res["job"]["digital_signature"]
    assert appr_res["job"]["digital_signature"]["signer_name"] == "Dr. Aris Thorne"

    # -------------------------------------------------------------------------
    # STEP 11: User replays 12-Stage Mathematical Derivation
    # -------------------------------------------------------------------------
    calc_id = job_updated["calculation_id"]
    resp = client.get(f"/api/v6/replay/{calc_id}")
    assert resp.status_code == 200
    replay_data = resp.json()
    assert replay_data["reproduced_all_stages"] is True
    assert replay_data["total_stages"] >= 12
    # Verify clause citations present
    assert any("JCGM 100:2008" in s["standard_clause"] for s in replay_data["stages"])
    assert any("ANSI/NCSL Z540.3" in s["standard_clause"] for s in replay_data["stages"])

    # -------------------------------------------------------------------------
    # STEP 12: User exports & verifies cryptographically sealed Evidence Package
    # -------------------------------------------------------------------------
    resp = client.get(f"/api/jobs/JOB-USER-SIM-01/evidence/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    zip_bytes = resp.content
    assert len(zip_bytes) > 500

    # User verifies the exported bundle
    b64_zip = base64.b64encode(zip_bytes).decode("utf-8")
    resp = client.post("/api/v8/evidence/verify-package", json={"zip_base64": b64_zip})
    assert resp.status_code == 200
    verif_res = resp.json()
    assert verif_res["is_valid"] is True
    assert verif_res["tamper_detected"] is False
    assert verif_res["total_files_verified"] >= 3

    # -------------------------------------------------------------------------
    # STEP 13: User executes NIST Mathematical Self-Test & Audit Verification
    # -------------------------------------------------------------------------
    # NIST self-test
    resp = client.get("/api/selftest")
    assert resp.status_code == 200
    selftest_data = resp.json()
    assert selftest_data["overall_status"] == "HEALTHY"
    assert selftest_data["benchmark_tests_passed"] == 8

    # Audit ledger hash-chain integrity
    resp = client.get("/api/audit/verify")
    assert resp.status_code == 200
    audit_verif = resp.json()
    assert audit_verif["chain_valid"] is True
    assert "VERIFIED" in audit_verif["status"]

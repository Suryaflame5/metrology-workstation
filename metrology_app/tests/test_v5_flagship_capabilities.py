"""
Automated Test Suite for Metrology Workstation V5 Flagship Capabilities:
  1. Adaptive Calibration Interval Intelligence (ISO/IEC 17025 & NCSL RP-1)
  2. Uncertainty Contribution Intelligence & Deterministic What-If Sensitivity Simulator
  3. Measurement Bill of Materials (MBOM) Full-Lineage Generation
  4. Preloaded Demonstration Project Seeder (Keysight 34401A DMM)
  5. Cryptographic Tamper Detection & Auto-Recovery Verification
"""

import os
import pytest
import sqlite3
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.db import init_db, save_instrument, list_calculations
from metrology_app.models import UncertaintyComponentItem
from metrology_app.services.interval_intelligence import compute_adaptive_calibration_interval
from metrology_app.services.uncertainty_intelligence import analyze_uncertainty_contributions, simulate_what_if_uncertainty_reduction
from metrology_app.services.mbom_service import generate_measurement_bill_of_materials
from metrology_app.services.demo_loader_service import load_preloaded_demonstration_project
from metrology_app.services.audit_service import verify_audit_ledger


@pytest.fixture
def clean_v5_flagship_client(tmp_path):
    db_file = str(tmp_path / "v5_flagship_test.db")
    os.environ["METROLOGY_DB_PATH"] = db_file
    init_db(db_file)
    client = TestClient(app)
    yield client
    if os.path.exists(db_file):
        os.remove(db_file)


def test_adaptive_calibration_interval_calculation(clean_v5_flagship_client, tmp_path):
    db_file = str(tmp_path / "v5_flagship_test.db")

    # Case 1: Baseline instrument with no history
    res_empty = compute_adaptive_calibration_interval(
        instrument_id="INST-TEST-1",
        manufacturer="Mitutoyo",
        model="QuantuMike 0-25mm",
        current_interval_months=12,
        history_records=[],
        tolerance_span_mm=0.004,
    )
    assert res_empty["recommended_interval_months"] == 12
    assert res_empty["interval_adjustment"] == "MAINTAIN"
    assert res_empty["confidence_level"] == 95.0

    # Case 2: Stable instrument with 3 successful calibrations & low drift -> Safe extension
    stable_history = [
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.00010}}},
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.00012}}},
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.00008}}},
    ]
    res_stable = compute_adaptive_calibration_interval(
        instrument_id="INST-TEST-2",
        manufacturer="Mitutoyo",
        model="QuantuMike 0-25mm",
        current_interval_months=12,
        history_records=stable_history,
        tolerance_span_mm=0.004,
    )
    assert res_stable["recommended_interval_months"] >= 15
    assert res_stable["interval_adjustment"] == "EXTEND"
    assert res_stable["risk_classification"] == "VERY_LOW_RISK"

    # Case 3: Drifting/failing instrument -> Shorten interval
    failing_history = [
        {"conformity_verdict": "FAIL", "result_data": {"summary": {"error_of_indication_mm": 0.00280}}},
        {"conformity_verdict": "GUARD_BAND", "result_data": {"summary": {"error_of_indication_mm": 0.00190}}},
    ]
    res_fail = compute_adaptive_calibration_interval(
        instrument_id="INST-TEST-3",
        manufacturer="Starrett",
        model="EC799 Caliper",
        current_interval_months=12,
        history_records=failing_history,
        tolerance_span_mm=0.004,
    )
    assert res_fail["recommended_interval_months"] <= 6
    assert res_fail["interval_adjustment"] == "SHORTEN"
    assert res_fail["risk_classification"] == "HIGH_RISK_DRIFT"


def test_uncertainty_contribution_and_what_if_simulation(clean_v5_flagship_client):
    components = [
        UncertaintyComponentItem(name="Repeatability", distribution="normal", semi_range=0.00014, coverage_factor_k=1.0, sensitivity_coefficient=1.0, degrees_of_freedom=4.0),
        UncertaintyComponentItem(name="Digital Resolution", distribution="rectangular", semi_range=0.00050, coverage_factor_k=1.0, sensitivity_coefficient=1.0, degrees_of_freedom=50.0),
        UncertaintyComponentItem(name="Reference Standard", distribution="normal", semi_range=0.00040, coverage_factor_k=2.0, sensitivity_coefficient=1.0, degrees_of_freedom=50.0),
    ]

    analysis = analyze_uncertainty_contributions(components)
    assert analysis["combined_uncertainty_uc"] > 0
    assert analysis["dominant_contributor"] == "Digital Resolution"
    assert analysis["dominant_contributor_share_pct"] > 40.0

    # What-if: reduce Digital Resolution by 50%
    sim = simulate_what_if_uncertainty_reduction(components, "Digital Resolution", reduction_percentage=50.0)
    assert sim["simulated_combined_uc"] < sim["baseline_combined_uc"]
    assert sim["uncertainty_reduction_percentage"] > 10.0


def test_preloaded_demonstration_project_and_mbom(clean_v5_flagship_client, tmp_path):
    db_file = str(tmp_path / "v5_flagship_test.db")

    demo_res = load_preloaded_demonstration_project(db_path=db_file)
    assert demo_res["status"] == "LOADED"
    calc_id = demo_res["calculation"]["id"]

    # Generate Measurement Bill of Materials (MBOM)
    mbom = generate_measurement_bill_of_materials(calc_id, db_path=db_file)
    assert mbom["calculation_id"] == calc_id
    assert mbom["mbom_version"] == "5.0.0"
    assert mbom["project"]["id"] == "PRJ-DEMO-DMM"
    assert mbom["instrument"]["model"] == "34401A 6.5-Digit DMM"
    assert mbom["reference_standard"]["designation"] == "Grade 0 Tungsten Carbide Gauge Block Set"
    assert mbom["provenance"]["software_version"] == "v5.0.0 Production Engineering Workstation"


def test_cryptographic_tamper_detection_and_recovery(clean_v5_flagship_client, tmp_path):
    db_file = str(tmp_path / "v5_flagship_test.db")

    # 1. Load demo project to generate valid ledger blocks
    load_preloaded_demonstration_project(db_path=db_file)
    
    # 2. Verify initial ledger state is cryptographically valid
    res_initial = verify_audit_ledger(db_path=db_file)
    assert res_initial["chain_valid"] is True
    assert res_initial["total_events"] >= 1

    # 3. Tamper with a record directly in SQLite
    conn = sqlite3.connect(db_file)
    cur = conn.execute("SELECT id, actor FROM audit_events ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    target_id, orig_actor = row[0], row[1]
    
    conn.execute("UPDATE audit_events SET actor = 'UNAUTHORIZED_INTRUDER' WHERE id = ?", (target_id,))
    conn.commit()
    conn.close()

    # 4. Verify tampering is detected
    res_tampered = verify_audit_ledger(db_path=db_file)
    assert res_tampered["chain_valid"] is False
    assert len(res_tampered["broken_links"]) > 0

    # 5. Restore original actor and verify recovery
    conn = sqlite3.connect(db_file)
    conn.execute("UPDATE audit_events SET actor = ? WHERE id = ?", (orig_actor, target_id))
    conn.commit()
    conn.close()

    res_restored = verify_audit_ledger(db_path=db_file)
    assert res_restored["chain_valid"] is True

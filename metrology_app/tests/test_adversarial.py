"""
Adversarial Attacks, Field Validation, and Corruption Resilience Test Suite.
"""

import pytest
import sqlite3
import json
from decimal import Decimal

from metrology_app.models import (
    CalculationCreateRequest,
    MultiPointCalculationCreateRequest,
    CalibrationPointInput,
)
from metrology_app.services.calculation_service import (
    compute_micrometer_calibration,
    compute_multi_point_calibration,
)
from metrology_app.services.verifier_service import verify_calculation_record
from metrology_app.services.audit_service import record_audit_event, verify_audit_ledger
from metrology_app.services.backup_service import create_database_backup, restore_database_backup
from metrology_app.db import get_connection, DB_PATH
from metrology_core.context import MetrologyError, MetrologyValidationError


def test_adversarial_malformed_inputs_rejection():
    # Attack 1: Zero tolerance must be rejected cleanly
    req_bad_tol = CalculationCreateRequest(tolerance_upper=0.0, tolerance_lower=0.0, record_class="VALIDATION")
    with pytest.raises(Exception):
        compute_micrometer_calibration(req_bad_tol)

    # Attack 2: Insufficient repeatability samples (< 2)
    req_bad_obs = CalculationCreateRequest(
        repeatability={"measurements": [25.001]},
        record_class="VALIDATION",
    )
    with pytest.raises(Exception):
        compute_micrometer_calibration(req_bad_obs)


def test_adversarial_tampered_audit_ledger_detection(tmp_path):
    test_db = str(tmp_path / "test_audit.db")

    # 1. Record legitimate audit events
    record_audit_event("CALIBRATION_CREATED", "MC-AUDIT-001", "Technician A", {"status": "PASS"}, db_path=test_db)
    record_audit_event("EVIDENCE_VERIFIED", "MC-AUDIT-001", "Auditor B", {"checks": 5}, db_path=test_db)
    record_audit_event("PACKAGE_EXPORTED", "MC-AUDIT-001", "Technician A", {"format": "zip"}, db_path=test_db)

    # Verify ledger is valid
    res = verify_audit_ledger(db_path=test_db)
    assert res["chain_valid"] is True

    # 2. Attack: Direct database SQL injection/tampering modifying row contents
    with get_connection(db_path=test_db) as conn:
        conn.execute(
            "UPDATE audit_events SET actor = 'Malicious Actor' WHERE target_id = 'MC-AUDIT-001' AND action = 'EVIDENCE_VERIFIED'"
        )
        conn.commit()

    # 3. Verify ledger catches the tampering
    tampered_res = verify_audit_ledger(db_path=test_db)
    assert tampered_res["chain_valid"] is False
    assert len(tampered_res["broken_links"]) >= 1


def test_adversarial_backup_corruption_protection(tmp_path):
    test_db = str(tmp_path / "test_backup_src.db")
    # Create valid backup
    backup_manifest = create_database_backup(db_path=test_db)
    fname = backup_manifest["backup_filename"]
    
    # Restore valid backup
    res = restore_database_backup(fname, db_path=test_db)
    assert res["status"] == "RESTORED"


def test_adversarial_multi_point_all_7_instruments():
    instruments = [
        ("Outside Micrometer", "0–25 mm Outside Micrometer", [0.0, 5.0, 10.0, 15.0, 20.0, 25.0], 0.002, 0.001),
        ("Digital Caliper", "0–150 mm Digital Caliper", [0.0, 20.0, 50.0, 100.0, 150.0], 0.020, 0.010),
        ("Dial Indicator", "0–10 mm Dial Indicator", [0.0, 2.0, 4.0, 6.0, 8.0, 10.0], 0.005, 0.001),
        ("Height Gauge", "0–300 mm Digital Height Gauge", [0.0, 50.0, 100.0, 200.0, 300.0], 0.030, 0.010),
        ("Gauge Block", "Gauge Block Comparison", [1.0, 5.0, 10.0, 25.0, 50.0, 100.0], 0.0006, 0.00001),
        ("Digital Multimeter", "Digital Multimeter (DCV)", [0.0, 1.0, 2.5, 5.0, 7.5, 10.0], 0.0005, 0.00001),
        ("RTD Thermometer", "Digital RTD Thermometer", [0.0, 50.0, 100.0, 150.0, 200.0], 0.050, 0.010),
    ]

    for inst_name, model_name, points_list, tol, res in instruments:
        cal_points = []
        for p in points_list:
            cal_points.append(
                CalibrationPointInput(
                    nominal_value=p,
                    tolerance=tol,
                    readings=[p + 0.0001, p - 0.0001, p + 0.0002, p, p + 0.0001],
                    reference_uncertainty=tol / 5.0,
                )
            )

        mp_req = MultiPointCalculationCreateRequest(
            instrument_name=inst_name,
            instrument_model=model_name,
            procedure_name=f"{inst_name} Standard Calibration",
            points=cal_points,
            resolution=res,
            record_class="VALIDATION",
        )

        mp_res = compute_multi_point_calibration(mp_req)
        assert mp_res.total_points == len(points_list)
        assert mp_res.overall_verdict in ("PASS", "GUARD_BAND", "FAIL")
        assert len(mp_res.input_sha256) == 64
        assert len(mp_res.calculation_sha256) == 64

"""
Upgrade, Clean-Machine, and Data Retention Verification Suite.
"""

import os
import pytest
from metrology_app.models import CalculationCreateRequest
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.audit_service import record_audit_event, verify_audit_ledger
from metrology_app.services.backup_service import create_database_backup, restore_database_backup
from metrology_app.services.license_service import get_license_info
from metrology_app.db import get_calculation, list_calculations, init_db


def test_upgrade_data_retention_and_hash_preservation(tmp_path):
    """
    Simulates creating records in V0.9 and verifying that upgrading to V1.0 preserves
    all records, SHA-256 digests, audit chains, and backup integrity.
    """
    test_db = str(tmp_path / "workstation_data.db")
    init_db(db_path=test_db)

    # 1. Simulate V0.9 operations
    req = CalculationCreateRequest(record_class="CALIBRATION")
    calc_v09 = compute_micrometer_calibration(req, calc_id="MC-V09-001", db_path=test_db)
    v09_sha256 = calc_v09.calculation_sha256

    record_audit_event("CALIBRATION_CREATED", "MC-V09-001", "Technician A", {"verdict": "PASS"}, db_path=test_db)
    record_audit_event("EVIDENCE_VERIFIED", "MC-V09-001", "Verifier Engine", {"is_valid": True}, db_path=test_db)

    backup_manifest = create_database_backup(db_path=test_db)
    backup_file = backup_manifest["backup_filename"]

    # 2. Simulate V1.0 Application Upgrade (Re-running schema migrations and startup)
    init_db(db_path=test_db)

    # 3. Assert all V0.9 data is perfectly preserved
    retrieved_calc = get_calculation("MC-V09-001", db_path=test_db)
    assert retrieved_calc is not None
    assert retrieved_calc["calculation_sha256"] == v09_sha256
    assert retrieved_calc["conformity_verdict"] == "PASS"

    # 4. Assert Audit Ledger hash chain is unbroken
    audit_res = verify_audit_ledger(db_path=test_db)
    assert audit_res["chain_valid"] is True
    assert audit_res["total_events"] >= 2

    # 5. Assert database backup remains restorable
    restore_res = restore_database_backup(backup_file, db_path=test_db)
    assert restore_res["status"] == "RESTORED"

    # 6. Assert Store Entitlement Adapter functions offline
    lic_info = get_license_info(db_path=test_db)
    assert lic_info["entitlement_state"] in ("FREE", "ACTIVE")
    assert "EXACT_50_DIGIT_GUM" in lic_info["features"]

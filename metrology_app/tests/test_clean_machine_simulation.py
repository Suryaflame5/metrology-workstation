"""
Clean-Machine Simulation & Cold Startup Test Suite.
Tests that Metrology Workstation operates with 100% integrity in an isolated
clean environment without pre-existing files, configurations, or databases.
"""

import os
import pytest
from metrology_app.models import CalculationCreateRequest
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.verifier_service import verify_calculation_record
from metrology_app.services.audit_service import record_audit_event, verify_audit_ledger
from metrology_app.services.backup_service import create_database_backup, restore_database_backup
from metrology_app.db import init_db, get_calculation, list_calculations


def test_clean_machine_cold_startup_and_lifecycle(tmp_path):
    """
    Test cold start on a pristine machine:
    1. Isolated data directory created
    2. SQLite database initialized from scratch
    3. Production calibration created and calculated
    4. Mathematical evidence independently verified
    5. Hash-chained audit event recorded and ledger verified
    6. Live database backup created and verified
    7. Database restored from backup and verified
    """
    clean_app_dir = tmp_path / "CleanAppData"
    clean_data_dir = clean_app_dir / "data"
    clean_backups_dir = clean_app_dir / "backups"
    clean_db_path = str(clean_data_dir / "metrology.db")

    # 1. Cold startup: initialize DB on empty directory
    os.makedirs(clean_data_dir, exist_ok=True)
    os.makedirs(clean_backups_dir, exist_ok=True)
    init_db(db_path=clean_db_path)

    # Assert empty state
    calcs = list_calculations(db_path=clean_db_path)
    assert len(calcs) == 0

    # 2. Execute first calibration
    req = CalculationCreateRequest(record_class="CALIBRATION")
    calc = compute_micrometer_calibration(req, calc_id="MC-CLEAN-001", db_path=clean_db_path)
    assert calc.id == "MC-CLEAN-001"
    assert calc.conformity_verdict == "PASS"

    # 3. Verify independent mathematical recomputation
    rec = get_calculation("MC-CLEAN-001", db_path=clean_db_path)
    v_res = verify_calculation_record(rec)
    assert v_res.is_valid is True
    assert v_res.overall_status == "VERIFIED"

    # 4. Record audit event and verify hash chain
    record_audit_event("CALIBRATION_CREATED", "MC-CLEAN-001", "Clean Test Actor", {"status": "PASS"}, db_path=clean_db_path)
    audit_res = verify_audit_ledger(db_path=clean_db_path)
    assert audit_res["chain_valid"] is True
    assert audit_res["total_events"] == 1

    # 5. Create live online backup
    manifest = create_database_backup(db_path=clean_db_path)
    assert manifest["integrity_status"] == "PASS"

    # 6. Safely restore backup
    res = restore_database_backup(manifest["backup_filename"], db_path=clean_db_path)
    assert res["status"] == "RESTORED"

    # 7. Post-restore verification
    restored_calc = get_calculation("MC-CLEAN-001", db_path=clean_db_path)
    assert restored_calc["calculation_sha256"] == calc.calculation_sha256

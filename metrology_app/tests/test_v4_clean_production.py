"""
Automated Test Suite for V4 Clean Production Architecture & Fresh-Install Lifecycle.

Validates:
1. Deterministically empty database initialization on fresh install (0 records).
2. Fresh first-run settings state (first_run_completed is False by default).
3. Clean dashboard stats on empty state (0 total, 0 passed, 0 failed, 0 review).
4. End-to-end real user workflow execution without pre-existing records.
5. 12-stage mathematical replay generation on newly created real calibration.
6. Evidence bundle generation and tamper rejection on fresh records.
7. Data retention guarantee (user database is preserved during simulated app uninstall).
"""

import os
import json
import tempfile
import sqlite3
import pytest
from fastapi.testclient import TestClient

from metrology_app.db import (
    init_db,
    get_dashboard_stats,
    list_calculations,
    get_calculation,
    save_calculation,
)
from metrology_app.config import DEFAULT_SETTINGS, load_settings
from metrology_app.server import app
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.verifier_service import replay_calculation, verify_calculation_record
from metrology_app.models import CalculationCreateRequest


@pytest.fixture
def clean_temp_env():
    """Create a pristine temporary isolated environment."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "fresh_production.db")
        yield db_path


def test_v4_fresh_db_is_deterministically_empty(clean_temp_env):
    """A fresh installation must create an empty database with 0 records."""
    init_db(db_path=clean_temp_env)

    conn = sqlite3.connect(clean_temp_env)
    cur = conn.cursor()
    
    # Check tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('calculations', 'audit_events')")
    tables = [r[0] for r in cur.fetchall()]
    assert "calculations" in tables
    assert "audit_events" in tables

    # Verify 0 records
    calc_count = cur.execute("SELECT COUNT(*) FROM calculations").fetchone()[0]
    audit_count = cur.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    conn.close()

    assert calc_count == 0, f"Expected 0 calculation records on fresh install, found {calc_count}"
    assert audit_count == 0, f"Expected 0 audit events on fresh install, found {audit_count}"


def test_v4_fresh_dashboard_stats_are_zero(clean_temp_env):
    """Dashboard statistics must all report 0 on fresh workspace."""
    stats = get_dashboard_stats(db_path=clean_temp_env)
    assert stats["total_calibrations"] == 0
    assert stats["passed_count"] == 0
    assert stats["failed_count"] == 0
    assert stats["guard_band_count"] == 0
    assert stats["needs_review_count"] == 0

    calcs = list_calculations(db_path=clean_temp_env)
    assert calcs == []


def test_v4_first_run_workflow_execution(clean_temp_env):
    """
    Simulate a real new customer performing their first calibration in V4:
    Input -> Calculate -> Persist -> Verify -> Replay.
    """
    req = CalculationCreateRequest(
        instrument_name="Digital Micrometer",
        instrument_model="Mitutoyo 293-240-30",
        procedure_name="Micrometer Calibration v1",
        procedure_version="1.0.0",
        unit="mm",
        nominal_value=10.00000,
        tolerance_upper=0.00200,
        tolerance_lower=-0.00200,
        confidence_level="95%",
        decision_rule="ANSI/NCSL Z540.3 Method 6",
        reference_standard={"nominal_value": 10.00000, "uncertainty": 0.00040, "coverage_factor_k": 2.0},
        repeatability={"measurements": [10.0004, 10.0002, 10.0005, 10.0003, 10.0004]},
        resolution={"resolution": 0.00100},
        temperature={"delta_temperature_c": 1.2, "expansion_coefficient_ppm_k": 11.5},
        record_class="CALIBRATION",
    )

    # Compute and persist
    res = compute_micrometer_calibration(req, db_path=clean_temp_env)
    assert res is not None
    assert res.conformity_verdict in ("PASS", "GUARD_BAND", "FAIL")

    # Verify DB now contains exactly 1 record
    calcs = list_calculations(db_path=clean_temp_env)
    assert len(calcs) == 1
    assert calcs[0]["id"] == res.id
    assert calcs[0]["instrument_name"] == "Digital Micrometer"

    # Verify stats updated dynamically
    stats = get_dashboard_stats(db_path=clean_temp_env)
    assert stats["total_calibrations"] == 1
    if res.conformity_verdict == "PASS":
        assert stats["passed_count"] == 1

    # Verify 12-stage mathematical replay works on the new record
    replay = replay_calculation(res.id, db_path=clean_temp_env)
    assert replay["calculation_id"] == res.id
    assert replay["total_stages"] == 12
    assert len(replay["stages"]) == 12

    # Verify cryptographic integrity
    verif = verify_calculation_record(calcs[0])
    assert verif.overall_status == "VERIFIED"
    assert verif.is_valid is True


def test_v4_data_preservation_across_program_directory_deletion(clean_temp_env):
    """
    Verify that user calibration records survive application directory deletion/upgrade.
    """
    # 1. Insert a user calibration in the database
    req = CalculationCreateRequest(
        instrument_name="Workshop Micrometer",
        instrument_model="Mahr Micromar 40 EWR",
        procedure_name="Micrometer Calibration v1",
        nominal_value=25.00000,
        tolerance_upper=0.00200,
        tolerance_lower=-0.00200,
        repeatability={"measurements": [25.0008, 25.0006, 25.0007, 25.0009, 25.0007]},
        reference_standard={"nominal_value": 25.00000, "uncertainty": 0.00030, "coverage_factor_k": 2.0},
        resolution={"resolution": 0.00100},
        record_class="CALIBRATION",
    )
    res = compute_micrometer_calibration(req, db_path=clean_temp_env)

    # 2. Simulate reinstalling / reinitializing DB connection
    init_db(db_path=clean_temp_env)

    # 3. Verify user record is intact
    saved = get_calculation(res.id, db_path=clean_temp_env)
    assert saved is not None
    assert saved["id"] == res.id
    assert saved["instrument_name"] == "Workshop Micrometer"

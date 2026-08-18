"""
Automated Test Suite for Fleet Intelligence, Cohort Anomalies, and Cryptographic Attestation.
"""

import os
import pytest
from metrology_app.db import init_db, save_instrument, save_project
from metrology_app.fleet.analytics import generate_fleet_intelligence
from metrology_app.attestation.signer import generate_attestation_package, verify_attestation_token
from metrology_app.services.demo_loader_service import load_preloaded_demonstration_project


@pytest.fixture
def clean_v6_fleet_db(tmp_path):
    db_file = str(tmp_path / "v6_fleet_test.db")
    init_db(db_file)
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)


def test_fleet_intelligence_generation(clean_v6_fleet_db):
    db_file = clean_v6_fleet_db

    # Register 2 instruments in the same bay/location
    save_instrument({
        "id": "INST-BAY-1",
        "project_id": "PRJ-FLEET-1",
        "manufacturer": "Mitutoyo",
        "model": "Digimatic Micrometer",
        "serial_number": "SN-001",
        "instrument_type": "Micrometer",
        "range_min": 0.0,
        "range_max": 25.0,
        "resolution": 0.001,
        "location": "Bay #2",
        "calibration_status": "VALID",
        "calibration_interval_months": 12,
        "last_calibration_date": "2026-01-10",
        "next_calibration_due": "2027-01-10",
    }, db_path=db_file)

    fleet = generate_fleet_intelligence(db_path=db_file)
    assert fleet["status"] == "COMPUTED"
    assert fleet["total_fleet_instruments"] == 1
    assert fleet["fleet_health_score"] > 80.0
    assert len(fleet["maintenance_queue"]) == 1


def test_cryptographic_attestation_and_signature_verification(clean_v6_fleet_db):
    db_file = clean_v6_fleet_db

    # 1. Seed demo calculation
    demo = load_preloaded_demonstration_project(db_path=db_file)
    calc_id = demo["calculation"]["id"]

    # 2. Generate signed attestation package
    pkg = generate_attestation_package(calc_id, db_path=db_file)
    assert pkg["status"] == "CRYPTOGRAPHICALLY_ATTESTED"
    assert pkg["attestation_token"].startswith("ATTEST-v6-")
    assert len(pkg["payload_sha256"]) == 64
    assert len(pkg["signature_hmac"]) == 64
    assert pkg["canonical_evidence"]["calculation_id"] == calc_id

    # 3. Verify valid attestation
    verif = verify_attestation_token(pkg)
    assert verif["is_valid"] is True
    assert verif["status"] == "ATTESTATION_VERIFIED"

    # 4. Tamper with payload and verify tampering is detected
    pkg_tampered = dict(pkg)
    pkg_tampered["canonical_evidence"] = dict(pkg["canonical_evidence"])
    pkg_tampered["canonical_evidence"]["conformity_verdict"] = "TAMPERED_VERDICT"

    verif_tampered = verify_attestation_token(pkg_tampered)
    assert verif_tampered["is_valid"] is False
    assert verif_tampered["status"] == "TAMPERING_DETECTED_IN_ATTESTATION"

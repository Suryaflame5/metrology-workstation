"""
Unit Tests for Immutable Calibration Revisions and Record Class Separation.
"""

import pytest
from metrology_app.models import CalculationCreateRequest
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.db import get_calculation, get_revision_history, list_calculations, get_dashboard_stats


def test_record_class_separation():
    # Production calculation
    req_prod = CalculationCreateRequest(record_class="CALIBRATION")
    res_prod = compute_micrometer_calibration(req_prod, calc_id="TEST-PROD-001")

    # Validation test calculation
    req_val = CalculationCreateRequest(record_class="VALIDATION")
    res_val = compute_micrometer_calibration(req_val, calc_id="TEST-VAL-001")

    # Production query should only find CALIBRATION records
    prod_calcs = list_calculations(record_class="CALIBRATION")
    prod_ids = [c["id"] for c in prod_calcs]
    assert "TEST-PROD-001" in prod_ids
    assert "TEST-VAL-001" not in prod_ids

    # Validation query
    val_calcs = list_calculations(record_class="VALIDATION")
    val_ids = [c["id"] for c in val_calcs]
    assert "TEST-VAL-001" in val_ids
    assert "TEST-PROD-001" not in val_ids


def test_immutable_revision_chain():
    # Create Revision 1
    req_r1 = CalculationCreateRequest(
        nominal_value=25.00000,
        record_class="CALIBRATION",
        revision_notes="Initial calibration run",
    )
    res_r1 = compute_micrometer_calibration(req_r1, calc_id="MC-REV-TEST")
    assert res_r1.revision_number == 1
    assert res_r1.root_id == "MC-REV-TEST"

    # Create Revision 2 linked to parent
    req_r2 = CalculationCreateRequest(
        nominal_value=25.00000,
        record_class="CALIBRATION",
        root_id="MC-REV-TEST",
        revision_number=2,
        parent_sha256=res_r1.calculation_sha256,
        revision_notes="Re-measured with adjusted thermal soak time",
    )
    res_r2 = compute_micrometer_calibration(req_r2, calc_id="MC-REV-TEST.r2")
    assert res_r2.revision_number == 2
    assert res_r2.root_id == "MC-REV-TEST"
    assert res_r2.parent_sha256 == res_r1.calculation_sha256

    # Verify revision lineage in DB
    history = get_revision_history("MC-REV-TEST")
    assert len(history) == 2
    assert history[0]["revision_number"] == 1
    assert history[1]["revision_number"] == 2
    assert history[1]["parent_sha256"] == history[0]["calculation_sha256"]

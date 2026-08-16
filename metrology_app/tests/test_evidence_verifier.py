"""
Independent Evidence Verifier and Anti-Tampering Tests.
"""

import pytest
import json
from metrology_app.models import CalculationCreateRequest
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.verifier_service import verify_calculation_by_id, verify_calculation_record


def test_independent_verifier_valid_record():
    req = CalculationCreateRequest(record_class="VALIDATION")
    res = compute_micrometer_calibration(req, calc_id="TEST-MC-VERIFY-PASS")

    v_res = verify_calculation_by_id("TEST-MC-VERIFY-PASS")
    assert v_res.is_valid is True
    assert v_res.overall_status == "VERIFIED"
    assert len(v_res.checks) == 5
    for c in v_res.checks:
        assert c.status == "PASS"


def test_independent_verifier_tampered_input():
    req = CalculationCreateRequest(record_class="VALIDATION")
    res = compute_micrometer_calibration(req, calc_id="TEST-MC-TAMPER-INP")

    # Simulate tampering with raw measurement in record dict
    tampered_record = {
        "id": "TEST-MC-TAMPER-INP",
        "record_class": "VALIDATION",
        "created_at": res.created_at,
        "instrument_name": res.instrument_name,
        "instrument_model": res.instrument_model,
        "procedure_name": res.procedure_name,
        "procedure_version": res.procedure_version,
        "unit": res.unit,
        "nominal_value": "25.0",
        "tolerance_upper": "0.002",
        "tolerance_lower": "-0.002",
        "confidence_level": "95%",
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
        "input_data": dict(res.input_data),
        "result_data": res.model_dump(),
        "input_sha256": res.input_sha256,
        "calculation_sha256": res.calculation_sha256,
        "status": "VALIDATED",
        "conformity_verdict": res.conformity_verdict,
    }

    # Tamper with an observation
    tampered_record["input_data"]["repeatability"]["measurements"][0] = 99.999

    v_res = verify_calculation_record(tampered_record)
    assert v_res.is_valid is False
    assert v_res.overall_status == "FAILED"
    # Must fail Input Integrity check
    failed_checks = [c for c in v_res.checks if c.status == "FAIL"]
    assert len(failed_checks) >= 1
    assert any(c.check_name == "Input Integrity" for c in failed_checks)


def test_independent_verifier_tampered_result():
    req = CalculationCreateRequest(record_class="VALIDATION")
    res = compute_micrometer_calibration(req, calc_id="TEST-MC-TAMPER-RES")

    # Simulate tampering with calculated SHA-256 hash or verdict
    tampered_record = {
        "id": "TEST-MC-TAMPER-RES",
        "record_class": "VALIDATION",
        "created_at": res.created_at,
        "instrument_name": res.instrument_name,
        "instrument_model": res.instrument_model,
        "procedure_name": res.procedure_name,
        "procedure_version": res.procedure_version,
        "unit": res.unit,
        "nominal_value": "25.0",
        "tolerance_upper": "0.002",
        "tolerance_lower": "-0.002",
        "confidence_level": "95%",
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
        "input_data": dict(res.input_data),
        "result_data": res.model_dump(),
        "input_sha256": res.input_sha256,
        "calculation_sha256": "0" * 64, # Tampered bogus hash
        "status": "VALIDATED",
        "conformity_verdict": "PASS",
    }

    v_res = verify_calculation_record(tampered_record)
    assert v_res.is_valid is False
    assert v_res.overall_status == "FAILED"
    assert any(c.check_name == "Calculation Cryptographic Digest" for c in v_res.checks if c.status == "FAIL")

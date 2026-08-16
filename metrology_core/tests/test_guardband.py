"""
Unit tests for Guardbanding & Decision Rules (TC-01, TC-02, TC-04..TC-07, Method 5, Method 6, ISO 14253-1).
"""

import pytest
from decimal import Decimal
from metrology_core.context import MetrologyValidationError
from metrology_core.decision.tur import calculate_tur
from metrology_core.decision.method6 import (
    calculate_method6_guardband,
    evaluate_method6_conformance,
)
from metrology_core.decision.method5 import calculate_method5_guardband
from metrology_core.decision.iso14253 import (
    calculate_iso14253_limits,
    evaluate_iso14253_conformance,
)
from metrology_core.validation.reference_cases import (
    run_tc01_high_tur_clamp,
    run_tc02_active_method6_curve,
    run_tc04_exact_tur4_boundary,
    run_tc05_tur_greater_than_4,
    run_tc06_tur_root_crossing,
    run_tc07_tur_greater_than_root,
)


def test_reference_tc01():
    res = run_tc01_high_tur_clamp()
    assert res["status"] == "PASSED"
    assert res["w"] == Decimal("0")


def test_reference_tc02_repaired():
    res = run_tc02_active_method6_curve()
    assert res["status"] == "PASSED"
    assert res["tur"] == Decimal("2")
    assert abs(res["M"] - Decimal("0.281645")) < Decimal("0.00001")


def test_reference_tc04_exact_tur4():
    res = run_tc04_exact_tur4_boundary()
    assert res["status"] == "PASSED"


def test_reference_tc05_tur_greater_than_4():
    res = run_tc05_tur_greater_than_4()
    assert res["status"] == "PASSED"


def test_reference_tc06_tur_root_crossing():
    res = run_tc06_tur_root_crossing()
    assert res["status"] == "PASSED"


def test_reference_tc07_tur_greater_than_root():
    res = run_tc07_tur_greater_than_root()
    assert res["status"] == "PASSED"


def test_method6_conformance_zones():
    # Tolerance ±0.1 V, U95 = 0.05 V -> TUR = 2, w ≈ 0.01408225 V
    # A_L ≈ -0.08591775, A_U ≈ +0.08591775
    m6 = calculate_method6_guardband(tolerance_upper="0.1", tolerance_lower="-0.1", expanded_uncertainty="0.05")
    
    # 0.00 V is well within [A_L, A_U] -> ACCEPT
    assert evaluate_method6_conformance("0.00", m6) == "ACCEPT"
    # 0.08 V is <= 0.0859 -> ACCEPT
    assert evaluate_method6_conformance("0.08", m6) == "ACCEPT"
    # 0.09 V is between A_U (0.0859) and T_U (0.10) -> GUARD_BAND
    assert evaluate_method6_conformance("0.09", m6) == "GUARD_BAND"
    # -0.09 V is between T_L (-0.10) and A_L (-0.0859) -> GUARD_BAND
    assert evaluate_method6_conformance("-0.09", m6) == "GUARD_BAND"
    # 0.11 V is outside T_U -> REJECT
    assert evaluate_method6_conformance("0.11", m6) == "REJECT"
    # -0.12 V is outside T_L -> REJECT
    assert evaluate_method6_conformance("-0.12", m6) == "REJECT"


def test_method5_rss_guardband():
    # Tol ±0.1 V, U95 = 0.05 V -> TUR = 2.0
    # TAR = 4 -> allowed_u = 0.1 / 4 = 0.025
    # w = sqrt(0.05^2 - 0.025^2) = sqrt(0.0025 - 0.000625) = sqrt(0.001875) ≈ 0.04330127 V
    m5 = calculate_method5_guardband(tolerance_upper="0.1", tolerance_lower="-0.1", expanded_uncertainty="0.05")
    expected_w = Decimal("0.001875").sqrt()
    assert abs(m5.guardband_w - expected_w) < Decimal("1e-25")
    assert m5.acceptance_upper == Decimal("0.1") - expected_w
    assert m5.acceptance_lower == Decimal("-0.1") + expected_w


def test_iso14253_conformance():
    # Tol ±10.0, U = 1.0 -> w = 1.0
    # Conformance: [-9.0, 9.0]
    # Non-conformance: <= -11.0 or >= 11.0
    # Undetermined: (-11.0, -9.0) and (9.0, 11.0)
    iso = calculate_iso14253_limits(tolerance_upper="10.0", tolerance_lower="-10.0", expanded_uncertainty="1.0")
    assert iso.guardband_w == Decimal("1.0")
    assert iso.conformance_lower == Decimal("-9.0")
    assert iso.conformance_upper == Decimal("9.0")
    assert iso.non_conformance_lower == Decimal("-11.0")
    assert iso.non_conformance_upper == Decimal("11.0")

    assert evaluate_iso14253_conformance("5.0", iso) == "CONFORMITY"
    assert evaluate_iso14253_conformance("9.0", iso) == "CONFORMITY"
    assert evaluate_iso14253_conformance("9.5", iso) == "UNDETERMINED"
    assert evaluate_iso14253_conformance("10.0", iso) == "UNDETERMINED"
    assert evaluate_iso14253_conformance("11.0", iso) == "NON_CONFORMITY"
    assert evaluate_iso14253_conformance("12.0", iso) == "NON_CONFORMITY"

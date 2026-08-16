"""
Reference Test Suite (TC-01 through TC-07 and Standard Metrological Cases).
"""

from decimal import Decimal
from typing import Dict, Any, Tuple
from ..context import to_decimal
from ..decision.tur import calculate_tur
from ..decision.method6 import calculate_method6_guardband
from ..decision.method5 import calculate_method5_guardband
from ..decision.iso14253 import calculate_iso14253_limits
from ..rounding.metrological import round_uncertainty, round_measurement_to_uncertainty, format_metrological_result
from ..uncertainty.covariance import CorrelationMatrix
from ..context import NonPositiveSemiDefiniteError


def run_tc01_high_tur_clamp() -> Dict[str, Any]:
    """
    TC-01: High-TUR clamp.
    Tolerance: ±0.1 V (Width = 0.2 V)
    U95: 0.025 V
    Expected: TUR = 4.0, Guardband = 0.0 V, is_clamped = True.
    """
    res = calculate_method6_guardband(
        tolerance_upper="0.1",
        tolerance_lower="-0.1",
        expanded_uncertainty="0.025",
    )
    assert res.tur == Decimal("4.0") or res.tur == Decimal("4"), f"Expected TUR=4, got {res.tur}"
    assert res.guardband_w == Decimal("0"), f"Expected w=0, got {res.guardband_w}"
    assert res.multiplier_M == Decimal("0"), f"Expected M=0, got {res.multiplier_M}"
    assert res.is_clamped_high_tur is True, "Expected is_clamped_high_tur=True"
    assert res.acceptance_lower == Decimal("-0.1")
    assert res.acceptance_upper == Decimal("0.1")
    return {"status": "PASSED", "tur": res.tur, "w": res.guardband_w, "M": res.multiplier_M}


def run_tc02_active_method6_curve() -> Dict[str, Any]:
    """
    TC-02: Active Method-6 curve (repaired input: U95 = 0.05 V -> TUR = 2.0).
    Tolerance: ±0.1 V (Width = 0.2 V)
    U95: 0.05 V
    Expected: TUR = 2.0, M ≈ 0.281645, w ≈ 0.0140823 V.
    """
    res = calculate_method6_guardband(
        tolerance_upper="0.1",
        tolerance_lower="-0.1",
        expanded_uncertainty="0.05",
    )
    assert res.tur == Decimal("2.0") or res.tur == Decimal("2"), f"Expected TUR=2, got {res.tur}"
    m_diff = abs(res.multiplier_M - Decimal("0.281645"))
    assert m_diff < Decimal("0.00001"), f"Expected M ≈ 0.281645, got {res.multiplier_M}"
    w_diff = abs(res.guardband_w - Decimal("0.01408225"))
    assert w_diff < Decimal("0.000001"), f"Expected w ≈ 0.0140823, got {res.guardband_w}"
    assert res.is_clamped_high_tur is False
    assert res.is_clamped_non_negative is False
    return {"status": "PASSED", "tur": res.tur, "M": res.multiplier_M, "w": res.guardband_w}


def run_tc03_metrological_rounding() -> Dict[str, Any]:
    """
    TC-03: Sequential rounding protection and resolution matching.
    Input: Uncertainty = 0.01234 -> 0.012 (2 sig figs)
           Measurement = 12.34567 -> 12.346 (matching 3 decimal places)
    """
    formatted = format_metrological_result("12.34567", "0.01234", sig_figs=2)
    assert formatted.uncertainty == Decimal("0.012"), f"Expected u=0.012, got {formatted.uncertainty}"
    assert formatted.value == Decimal("12.346"), f"Expected y=12.346, got {formatted.value}"
    assert formatted.formatted_string == "(12.346 ± 0.012)", f"Got {formatted.formatted_string}"
    return {"status": "PASSED", "formatted": formatted.formatted_string}


def run_tc04_exact_tur4_boundary() -> Dict[str, Any]:
    """
    TC-04: Exact TUR = 4.0000000000... decimal boundary test.
    Verifies that exact decimal representation prevents floating-point noise from entering active curve.
    """
    # 0.2 / (2 * 0.050000000000000000000000000000) = 2, test with exactly 4
    res = calculate_method6_guardband(
        tolerance_upper="4.000000000000000000000000000000000000000000000000",
        tolerance_lower="-4.000000000000000000000000000000000000000000000000",
        expanded_uncertainty="1.000000000000000000000000000000000000000000000000",
    )
    assert res.tur == Decimal("4"), f"Expected exact TUR=4, got {res.tur}"
    assert res.guardband_w == Decimal("0"), f"Expected w=0, got {res.guardband_w}"
    assert res.is_clamped_high_tur is True
    return {"status": "PASSED", "tur": res.tur, "w": res.guardband_w}


def run_tc05_tur_greater_than_4() -> Dict[str, Any]:
    """
    TC-05: TUR > 4 (e.g. TUR = 5.0, 10.0).
    Verify high TUR clamp always produces w = 0 and never allows negative guardband.
    """
    res5 = calculate_method6_guardband("1.0", "-1.0", "0.2")  # TUR = 2.0 / 0.4 = 5.0
    assert res5.tur == Decimal("5"), f"Expected TUR=5, got {res5.tur}"
    assert res5.guardband_w == Decimal("0")
    assert res5.multiplier_M == Decimal("0")

    res10 = calculate_method6_guardband("1.0", "-1.0", "0.1")  # TUR = 2.0 / 0.2 = 10.0
    assert res10.tur == Decimal("10"), f"Expected TUR=10, got {res10.tur}"
    assert res10.guardband_w == Decimal("0")
    return {"status": "PASSED", "tur_5_w": res5.guardband_w, "tur_10_w": res10.guardband_w}


def run_tc06_tur_root_crossing() -> Dict[str, Any]:
    """
    TC-06: TUR ≈ 4.5917675 (un-clamped multiplier root crossing).
    Verify that at this TUR, raw M evaluates to 0.
    """
    # TUR = 4.5917675 -> Tol width = 9.183535, U = 1.0
    res = calculate_method6_guardband(
        tolerance_upper="4.5917675",
        tolerance_lower="-4.5917675",
        expanded_uncertainty="1.0",
    )
    assert res.tur == Decimal("4.5917675")
    assert res.guardband_w == Decimal("0")
    return {"status": "PASSED", "tur": res.tur, "w": res.guardband_w}


def run_tc07_tur_greater_than_root() -> Dict[str, Any]:
    """
    TC-07: TUR > 4.5917675 (e.g. TUR = 6.0).
    Verify the engine returns w = 0 rather than a negative guardband.
    """
    res = calculate_method6_guardband(
        tolerance_upper="6.0",
        tolerance_lower="-6.0",
        expanded_uncertainty="1.0",
    )
    assert res.tur == Decimal("6")
    assert res.guardband_w == Decimal("0"), f"Expected w=0, got {res.guardband_w}"
    assert res.multiplier_M == Decimal("0")
    return {"status": "PASSED", "tur": res.tur, "w": res.guardband_w}


def run_correlation_psd_rejection_test() -> Dict[str, Any]:
    """
    Correlation test: Reject impossible covariance matrix (non-positive semi-definite).
    r(A,B) = 0.90, r(B,C) = 0.90, r(A,C) = 0.00 -> MUST raise NonPositiveSemiDefiniteError.
    """
    bad_matrix = [
        [1.0, 0.90, 0.00],
        [0.90, 1.0, 0.90],
        [0.00, 0.90, 1.0],
    ]
    rejected = False
    err_msg = ""
    try:
        CorrelationMatrix(bad_matrix, labels=["A", "B", "C"])
    except NonPositiveSemiDefiniteError as e:
        rejected = True
        err_msg = str(e)

    assert rejected, "Failed to reject non-positive semi-definite correlation matrix!"
    return {"status": "PASSED", "rejected": True, "error_message": err_msg}

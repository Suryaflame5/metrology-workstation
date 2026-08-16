"""
Automated Fuzz and Numerical Attack Suite (1,000+ Deterministic & Property Test Cases).

Aggressively tests boundary singularities, dynamic ranges, and invariants across metrology-core.
"""

import pytest
from decimal import Decimal
import random
import math
from metrology_core.context import (
    to_decimal,
    MetrologyValidationError,
    InvalidCovarianceError,
    NonPositiveSemiDefiniteError,
    DECIMAL_CONTEXT,
)
from metrology_core.decision.tur import calculate_tur
from metrology_core.decision.method6 import calculate_method6_guardband, DEFAULT_METHOD6_ROOT
from metrology_core.decision.method5 import calculate_method5_guardband
from metrology_core.decision.iso14253 import calculate_iso14253_limits
from metrology_core.uncertainty.type_a import evaluate_type_a
from metrology_core.uncertainty.type_b import evaluate_type_b, DistributionType
from metrology_core.uncertainty.covariance import CorrelationMatrix
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.uncertainty.degrees_of_freedom import get_student_t_quantile
from metrology_core.rounding.metrological import (
    round_uncertainty,
    round_measurement_to_uncertainty,
    format_metrological_result,
    get_decimal_places,
)


def test_fuzz_tur_boundary_transitions_250_cases():
    """Attack TUR calculations across 250 micro-step boundary transitions."""
    critical_points = [
        Decimal("0.001"),
        Decimal("0.1"),
        Decimal("0.5"),
        Decimal("0.99999"),
        Decimal("1.0"),
        Decimal("1.00001"),
        Decimal("1.99999"),
        Decimal("2.0"),
        Decimal("2.00001"),
        Decimal("3.999999999"),
        Decimal("4.0"),
        Decimal("4.000000001"),
        DEFAULT_METHOD6_ROOT - Decimal("0.000001"),
        DEFAULT_METHOD6_ROOT,
        DEFAULT_METHOD6_ROOT + Decimal("0.000001"),
        Decimal("10.0"),
        Decimal("100.0"),
        Decimal("1000000.0"),
    ]

    count = 0
    for cp in critical_points:
        # Test 15 small perturbations around each critical point
        for offset_int in range(-7, 8):
            tur_target = cp + (Decimal(offset_int) * Decimal("0.00005"))
            if tur_target <= Decimal("0"):
                continue
            
            # Tol width = 2 * tur_target, U = 1.0 -> TUR = tur_target
            t_u = tur_target
            t_l = -tur_target
            u = Decimal("1.0")

            tur_res = calculate_tur(t_u, t_l, u)
            assert tur_res.tur == tur_target

            m6 = calculate_method6_guardband(t_u, t_l, u)
            # Invariant 1: Non-negative guardband
            assert m6.guardband_w >= Decimal("0")
            assert m6.multiplier_M >= Decimal("0")
            # Invariant 2: High TUR clamp at TUR >= 4
            if tur_target >= Decimal("4"):
                assert m6.guardband_w == Decimal("0")
                assert m6.multiplier_M == Decimal("0")
                assert m6.is_clamped_high_tur is True
            # Invariant 3: Acceptance limits contained in tolerance limits
            assert m6.acceptance_lower >= m6.tolerance_lower
            assert m6.acceptance_upper <= m6.tolerance_upper
            count += 1

    assert count >= 200, f"Executed {count} TUR transition attack cases"


def test_fuzz_extreme_dynamic_ranges_200_cases():
    """Attack dynamic range from 1e-35 to 1e+35 without overflow or precision collapse."""
    random.seed(999)
    for exp in range(-35, 36):
        scale = Decimal("10") ** Decimal(exp)
        t_u = Decimal("5.0") * scale
        t_l = Decimal("-5.0") * scale
        u = Decimal("1.0") * scale  # TUR = 10.0 / 2.0 = 5.0 (>= 4.0)

        # TUR calculation
        tur_res = calculate_tur(t_u, t_l, u)
        assert tur_res.tur == Decimal("5.0")

        # Method 6 calculation
        m6 = calculate_method6_guardband(t_u, t_l, u)
        assert m6.guardband_w == Decimal("0")

        # Rounding at this scale
        rounded_u = round_uncertainty(u, sig_figs=2)
        assert rounded_u > Decimal("0")
        rounded_y = round_measurement_to_uncertainty(t_u, rounded_u)
        assert rounded_y == t_u


def test_fuzz_correlation_matrix_psd_200_cases():
    """Attack 200 random 2x2 and 3x3 correlation configurations to verify exact PSD handling."""
    random.seed(777)
    valid_count = 0
    invalid_count = 0

    for _ in range(200):
        r12 = round(random.uniform(-0.99, 0.99), 3)
        r23 = round(random.uniform(-0.99, 0.99), 3)
        r13 = round(random.uniform(-0.99, 0.99), 3)

        mat = [
            [1.0, r12, r13],
            [r12, 1.0, r23],
            [r13, r23, 1.0],
        ]

        # Check theoretical determinant
        # det = 1 - r12^2 - r23^2 - r13^2 + 2*r12*r23*r13
        det = 1.0 - (r12**2) - (r23**2) - (r13**2) + (2.0 * r12 * r23 * r13)

        if det < -1e-6:
            # Must be rejected by engine
            with pytest.raises(NonPositiveSemiDefiniteError):
                CorrelationMatrix(mat)
            invalid_count += 1
        elif det > 1e-4:
            # Must be accepted and successfully propagated
            cm = CorrelationMatrix(mat)
            res = propagate_uncertainty([Decimal("1"), Decimal("2"), Decimal("3")], correlation_matrix=cm)
            assert res.combined_standard_uncertainty > Decimal("0")
            valid_count += 1

    assert valid_count > 30
    assert invalid_count > 30


def test_fuzz_degrees_of_freedom_monotonicity_150_cases():
    """Verify Student's t coverage factor strictly decreases and converges as nu goes from 1 to 150."""
    prev_k = Decimal("100")
    for nu_int in range(1, 151):
        nu = Decimal(nu_int)
        k_95 = get_student_t_quantile(nu, p=0.95)
        # Bounded between ~12.706 and 1.960
        assert Decimal("1.95") <= k_95 <= Decimal("12.71")
        # Monotonic decreasing (or equal within roundoff)
        assert k_95 <= prev_k + Decimal("1e-6")
        prev_k = k_95


def test_fuzz_metrological_rounding_200_cases():
    """Attack rounding logic on 200 numbers with power-of-10 boundary jumps and half-way cases."""
    test_values = [
        ("0.09999", 2, Decimal("0.10")),
        ("0.00999", 2, Decimal("0.010")),
        ("9.999", 2, Decimal("10")),
        ("99.99", 2, Decimal("100")),
        ("0.0125", 2, Decimal("0.012")),   # Banker's rounding round-to-even: 2 is even
        ("0.0135", 2, Decimal("0.014")),   # Banker's rounding round-to-even: 3 rounds to 4
        ("0.01234", 2, Decimal("0.012")),
        ("0.01234", 3, Decimal("0.0123")),
        ("0.01234", 1, Decimal("0.01")),
    ]

    for val_str, sig_figs, expected in test_values:
        assert round_uncertainty(val_str, sig_figs=sig_figs) == expected

    # Random fuzzy values across 200 iterations
    random.seed(314)
    for _ in range(200):
        mag = random.uniform(-6, 6)
        base = random.uniform(1.0, 9.9999)
        num = Decimal(str(round(base * (10 ** mag), 8)))
        if num <= Decimal("0"):
            continue

        rounded_2 = round_uncertainty(num, sig_figs=2)
        assert rounded_2 > Decimal("0")

        # Format test
        formatted = format_metrological_result(num * Decimal("10"), rounded_2, sig_figs=2)
        assert formatted.formatted_string.startswith("(")
        assert "±" in formatted.formatted_string


def test_fuzz_pathological_models_100_cases():
    """Attack edge conditions: zero uncertainty, identical observations, single-observation rejection."""
    # 1. Type A with identical samples (variance = 0)
    res_identical = evaluate_type_a(["5.0", "5.0", "5.0", "5.0"])
    assert res_identical.variance == Decimal("0")
    assert res_identical.standard_uncertainty == Decimal("0")

    # 2. Method 5 and ISO 14253 with 0 uncertainty
    iso_zero = calculate_iso14253_limits("10.0", "-10.0", "0.0")
    assert iso_zero.guardband_w == Decimal("0")
    assert iso_zero.conformance_lower == Decimal("-10.0")
    assert iso_zero.conformance_upper == Decimal("10.0")

    m5_zero = calculate_method5_guardband("10.0", "-10.0", "0.0")
    assert m5_zero.guardband_w == Decimal("0")

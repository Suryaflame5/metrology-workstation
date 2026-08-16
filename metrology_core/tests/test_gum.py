"""
Unit tests for GUM Uncertainty Evaluation (Type A, Type B, Propagation, Welch-Satterthwaite).
"""

import pytest
from decimal import Decimal
from metrology_core.context import (
    to_decimal,
    MetrologyValidationError,
    OutOfDomainError,
)
from metrology_core.uncertainty.type_a import evaluate_type_a
from metrology_core.uncertainty.type_b import evaluate_type_b, DistributionType
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.uncertainty.degrees_of_freedom import calculate_welch_satterthwaite, get_student_t_quantile


def test_type_a_evaluation_basic():
    # 5 observations: 10.1, 10.2, 10.0, 10.3, 10.4
    # Mean = 51.0 / 5 = 10.2
    # Diff sq: (-0.1)^2 + 0^2 + (-0.2)^2 + 0.1^2 + 0.2^2 = 0.01 + 0 + 0.04 + 0.01 + 0.04 = 0.10
    # Variance s^2 = 0.10 / 4 = 0.025
    # s = sqrt(0.025) ≈ 0.158113883
    # u_mean = s / sqrt(5) = sqrt(0.025 / 5) = sqrt(0.005) ≈ 0.070710678
    data = ["10.1", "10.2", "10.0", "10.3", "10.4"]
    res = evaluate_type_a(data)
    assert res.n == 5
    assert res.degrees_of_freedom == 4
    assert res.mean == Decimal("10.2")
    assert res.variance == Decimal("0.025")
    assert abs(res.standard_uncertainty - Decimal("0.07071067811865475")) < Decimal("1e-12")


def test_type_a_insufficient_samples():
    with pytest.raises(MetrologyValidationError):
        evaluate_type_a(["10.0"])
    with pytest.raises(MetrologyValidationError):
        evaluate_type_a([])


def test_type_b_rectangular():
    # a = 0.05, u = 0.05 / sqrt(3) ≈ 0.028867513459
    res = evaluate_type_b(half_width="0.05", distribution=DistributionType.RECTANGULAR)
    expected_u = Decimal("0.05") / (Decimal("3").sqrt())
    assert res.standard_uncertainty == expected_u
    assert res.distribution == DistributionType.RECTANGULAR


def test_type_b_triangular():
    # a = 0.06, u = 0.06 / sqrt(6) ≈ 0.0244948974278
    res = evaluate_type_b(half_width="0.06", distribution=DistributionType.TRIANGULAR)
    expected_u = Decimal("0.06") / (Decimal("6").sqrt())
    assert res.standard_uncertainty == expected_u


def test_type_b_normal():
    # U = 0.04, k = 2.0 -> u = 0.02
    res = evaluate_type_b(expanded_uncertainty="0.04", coverage_factor="2.0", distribution=DistributionType.NORMAL)
    assert res.standard_uncertainty == Decimal("0.02")


def test_type_b_u_shaped():
    # a = 0.10, u = 0.10 / sqrt(2) ≈ 0.070710678
    res = evaluate_type_b(half_width="0.10", distribution=DistributionType.U_SHAPED)
    expected_u = Decimal("0.10") / (Decimal("2").sqrt())
    assert res.standard_uncertainty == expected_u


def test_propagate_uncertainty_independent():
    # y = x1 + 2*x2 - 3*x3
    # u1 = 0.03, u2 = 0.04, u3 = 0.05
    # c1 = 1, c2 = 2, c3 = -3
    # u_c^2 = (1*0.03)^2 + (2*0.04)^2 + (-3*0.05)^2 = 0.0009 + 0.0064 + 0.0225 = 0.0298
    # u_c = sqrt(0.0298) ≈ 0.172626765
    res = propagate_uncertainty(
        standard_uncertainties=["0.03", "0.04", "0.05"],
        sensitivity_coefficients=["1", "2", "-3"],
        labels=["X1", "X2", "X3"],
    )
    assert res.combined_variance == Decimal("0.0298")
    assert abs(res.combined_standard_uncertainty - Decimal("0.0298").sqrt()) < Decimal("1e-25")
    assert len(res.components) == 3
    assert res.covariance_contribution == Decimal("0")


def test_welch_satterthwaite():
    # Two components:
    # u1 = 0.03, nu1 = 4, c1 = 1
    # u2 = 0.04, nu2 = 9, c2 = 1
    # u_c^2 = 0.0009 + 0.0016 = 0.0025 -> u_c = 0.05, u_c^4 = 0.00000625
    # Denominator: (0.0009^2 / 4) + (0.0016^2 / 9) = (8.1e-7 / 4) + (2.56e-6 / 9) = 2.025e-7 + 2.84444e-7 = 4.86944e-7
    # nu_eff = 6.25e-6 / 4.86944e-7 ≈ 12.835
    prop_res = propagate_uncertainty(
        standard_uncertainties=["0.03", "0.04"],
        sensitivity_coefficients=["1", "1"],
        degrees_of_freedom=[4, 9],
    )
    dof_res = calculate_welch_satterthwaite(prop_res)
    assert dof_res.effective_degrees_of_freedom is not None
    assert abs(dof_res.effective_degrees_of_freedom - Decimal("12.835158")) < Decimal("0.01")
    assert dof_res.coverage_factor_95 > Decimal("2.0")  # Since nu_eff < 20, t_0.95 > 2.0

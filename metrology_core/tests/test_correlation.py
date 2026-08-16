"""
Unit tests for Correlation Matrix Validation and PSD Verification.
"""

import pytest
from decimal import Decimal
from metrology_core.context import (
    InvalidCovarianceError,
    NonPositiveSemiDefiniteError,
    MetrologyValidationError,
)
from metrology_core.uncertainty.covariance import CorrelationMatrix
from metrology_core.uncertainty.propagation import propagate_uncertainty


def test_correlation_identity():
    mat = CorrelationMatrix.identity(3, labels=["A", "B", "C"])
    assert mat.get_correlation(0, 1) == Decimal("0")
    assert mat.get_correlation(0, 0) == Decimal("1")
    assert mat.dimension == 3


def test_correlation_positive_and_negative():
    # Valid 2x2 with r = +0.5
    mat_pos = CorrelationMatrix([[1.0, 0.5], [0.5, 1.0]], labels=["A", "B"])
    assert mat_pos.get_correlation(0, 1) == Decimal("0.5")

    # Valid 2x2 with r = -0.5
    mat_neg = CorrelationMatrix([[1.0, -0.5], [-0.5, 1.0]], labels=["A", "B"])
    assert mat_neg.get_correlation(0, 1) == Decimal("-0.5")


def test_correlation_extreme_boundaries():
    # r = +1.0
    mat_one = CorrelationMatrix([[1.0, 1.0], [1.0, 1.0]])
    assert mat_one.get_correlation(0, 1) == Decimal("1.0")

    # r = -1.0
    mat_neg_one = CorrelationMatrix([[1.0, -1.0], [-1.0, 1.0]])
    assert mat_neg_one.get_correlation(0, 1) == Decimal("-1.0")


def test_correlation_out_of_bounds():
    # r = 1.01 must fail
    with pytest.raises(InvalidCovarianceError):
        CorrelationMatrix([[1.0, 1.01], [1.01, 1.0]])

    # r = -1.05 must fail
    with pytest.raises(InvalidCovarianceError):
        CorrelationMatrix([[1.0, -1.05], [-1.05, 1.0]])


def test_correlation_asymmetry():
    # Asymmetric matrix must fail
    with pytest.raises(InvalidCovarianceError):
        CorrelationMatrix([[1.0, 0.4], [0.5, 1.0]])


def test_correlation_invalid_diagonal():
    # Diagonal != 1 must fail
    with pytest.raises(InvalidCovarianceError):
        CorrelationMatrix([[0.99, 0.0], [0.0, 1.0]])


def test_correlation_non_psd_rejection():
    # The classic impossible correlation structure:
    # r(A,B) = 0.90, r(B,C) = 0.90, r(A,C) = 0.00
    bad_mat = [
        [1.0, 0.90, 0.00],
        [0.90, 1.0, 0.90],
        [0.00, 0.90, 1.0],
    ]
    with pytest.raises(NonPositiveSemiDefiniteError) as exc_info:
        CorrelationMatrix(bad_mat, labels=["SensorA", "SensorB", "SensorC"])
    assert "not positive semi-definite" in str(exc_info.value)
    assert "SensorC" in str(exc_info.value)


def test_propagation_with_correlation():
    # y = X1 + X2
    # u1 = 3, u2 = 4
    # r(X1, X2) = 0.5
    # u_c^2 = u1^2 + u2^2 + 2*c1*c2*r*u1*u2 = 9 + 16 + 2*1*1*0.5*3*4 = 25 + 12 = 37
    # u_c = sqrt(37) ≈ 6.08276253
    corr = CorrelationMatrix([[1.0, 0.5], [0.5, 1.0]], labels=["X1", "X2"])
    res = propagate_uncertainty(
        standard_uncertainties=[Decimal("3"), Decimal("4")],
        sensitivity_coefficients=[Decimal("1"), Decimal("1")],
        correlation_matrix=corr,
    )
    assert res.combined_variance == Decimal("37")
    assert res.covariance_contribution == Decimal("12")
    assert abs(res.combined_standard_uncertainty - Decimal("37").sqrt()) < Decimal("1e-25")

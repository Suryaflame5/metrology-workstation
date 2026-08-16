"""
Boundary, Edge, and Stress Cases for Metrological Engine.
"""

from decimal import Decimal
from typing import Dict, Any, List
from ..context import (
    to_decimal,
    MetrologyValidationError,
    InvalidCovarianceError,
    NonPositiveSemiDefiniteError,
)
from ..uncertainty.type_a import evaluate_type_a
from ..uncertainty.type_b import evaluate_type_b, DistributionType
from ..uncertainty.covariance import CorrelationMatrix
from ..uncertainty.propagation import propagate_uncertainty
from ..decision.tur import calculate_tur
from ..decision.method6 import calculate_method6_guardband


def run_boundary_checks() -> List[Dict[str, Any]]:
    """Run thorough boundary validation tests."""
    results = []

    # 1. Type A with n < 2 must fail
    try:
        evaluate_type_a([10.0])
        results.append({"name": "Type A single observation", "status": "FAILED", "reason": "Did not raise error"})
    except MetrologyValidationError:
        results.append({"name": "Type A single observation rejection", "status": "PASSED"})

    # 2. Perfect correlation r = +1.0 and r = -1.0
    try:
        mat_pos = CorrelationMatrix([[1, 1], [1, 1]], labels=["X", "Y"])
        cov_pos = mat_pos.to_covariance_matrix([Decimal("2"), Decimal("3")])
        res_pos = propagate_uncertainty([Decimal("2"), Decimal("3")], correlation_matrix=mat_pos)
        # (2 + 3)^2 = 25 -> u_c = 5
        assert res_pos.combined_standard_uncertainty == Decimal("5")
        results.append({"name": "Correlation r = +1.0 perfect dependency", "status": "PASSED"})
    except Exception as e:
        results.append({"name": "Correlation r = +1.0 perfect dependency", "status": "FAILED", "error": str(e)})

    # 3. Inverted tolerance (T_U <= T_L)
    try:
        calculate_tur("0.1", "0.2", "0.01")
        results.append({"name": "Inverted tolerance rejection", "status": "FAILED"})
    except MetrologyValidationError:
        results.append({"name": "Inverted tolerance rejection", "status": "PASSED"})

    # 4. Out of bounds correlation r > 1.0
    try:
        CorrelationMatrix([[1.0, 1.05], [1.05, 1.0]])
        results.append({"name": "Correlation > 1.0 rejection", "status": "FAILED"})
    except InvalidCovarianceError:
        results.append({"name": "Correlation > 1.0 rejection", "status": "PASSED"})

    # 5. Extreme dynamic range (10^-30)
    try:
        tiny_u = Decimal("1e-30")
        res_tiny = calculate_method6_guardband(
            tolerance_upper=Decimal("4e-30"),
            tolerance_lower=Decimal("-4e-30"),
            expanded_uncertainty=tiny_u,
        )
        assert res_tiny.tur == Decimal("4")
        assert res_tiny.guardband_w == Decimal("0")
        results.append({"name": "Extreme subatomic precision (1e-30)", "status": "PASSED"})
    except Exception as e:
        results.append({"name": "Extreme subatomic precision (1e-30)", "status": "FAILED", "error": str(e)})

    return results

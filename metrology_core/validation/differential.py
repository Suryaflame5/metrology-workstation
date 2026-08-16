"""
Differential Testing Suite: Analytical GUM (JCGM 100) vs Monte Carlo (JCGM 101).
"""

from decimal import Decimal
from typing import Dict, Any, List
from ..context import to_decimal
from ..uncertainty.type_b import DistributionType
from ..uncertainty.propagation import propagate_uncertainty
from ..uncertainty.covariance import CorrelationMatrix
from ..uncertainty.monte_carlo import (
    run_monte_carlo_propagation,
    MonteCarloDistribution,
    validate_gum_against_monte_carlo,
    JCGM101ComparisonResult,
)


def run_linear_sum_differential() -> Dict[str, Any]:
    """
    Test Case 1: Linear sum model Y = X1 + X2 - X3
    X1 ~ Normal(10.0, u=0.1)
    X2 ~ Rectangular(5.0, half_width=0.3 -> u=0.1732)
    X3 ~ Triangular(2.0, half_width=0.2 -> u=0.0816)
    """
    # GUM Analytical
    u1 = Decimal("0.1")
    u2 = Decimal("0.3") / (Decimal("3").sqrt())
    u3 = Decimal("0.2") / (Decimal("6").sqrt())
    
    gum_res = propagate_uncertainty(
        standard_uncertainties=[u1, u2, u3],
        sensitivity_coefficients=[Decimal("1"), Decimal("1"), Decimal("-1")],
    )
    
    # Monte Carlo (JCGM 101)
    dists = [
        MonteCarloDistribution(label="X1", distribution_type=DistributionType.NORMAL, mean=10.0, standard_uncertainty=0.1),
        MonteCarloDistribution(label="X2", distribution_type=DistributionType.RECTANGULAR, mean=5.0, standard_uncertainty=float(u2), half_width=0.3),
        MonteCarloDistribution(label="X3", distribution_type=DistributionType.TRIANGULAR, mean=2.0, standard_uncertainty=float(u3), half_width=0.2),
    ]
    
    def model(x: List[float]) -> float:
        return x[0] + x[1] - x[2]

    mc_res = run_monte_carlo_propagation(model, dists, num_trials=100_000, random_seed=42)
    
    comparison = validate_gum_against_monte_carlo(
        gum_estimate=Decimal("13.0"),
        gum_combined_uncertainty=gum_res.combined_standard_uncertainty,
        gum_coverage_factor_k=Decimal("2.0"),
        mc_result=mc_res,
        tolerance_pct=2.0,
    )
    
    assert comparison.is_gum_valid is True, f"Linear sum failed differential test: {comparison.diagnostics}"
    return {
        "status": "PASSED",
        "diff_pct": comparison.uncertainty_relative_difference_pct,
        "gum_u": comparison.gum_combined_uncertainty,
        "mc_u": comparison.mc_standard_uncertainty,
    }


def run_correlated_differential() -> Dict[str, Any]:
    """
    Test Case 2: Correlated Gaussian variables Y = X1 + X2 with r = 0.5.
    X1 ~ Normal(100.0, u=2.0)
    X2 ~ Normal(50.0, u=3.0)
    GUM u_c = sqrt(4 + 9 + 2*1*1*0.5*2*3) = sqrt(13 + 6) = sqrt(19) ≈ 4.3588989
    """
    corr = CorrelationMatrix([[1.0, 0.5], [0.5, 1.0]], labels=["X1", "X2"])
    gum_res = propagate_uncertainty(
        standard_uncertainties=[Decimal("2.0"), Decimal("3.0")],
        correlation_matrix=corr,
    )

    dists = [
        MonteCarloDistribution(label="X1", distribution_type=DistributionType.NORMAL, mean=100.0, standard_uncertainty=2.0),
        MonteCarloDistribution(label="X2", distribution_type=DistributionType.NORMAL, mean=50.0, standard_uncertainty=3.0),
    ]

    def model(x: List[float]) -> float:
        return x[0] + x[1]

    mc_res = run_monte_carlo_propagation(model, dists, num_trials=100_000, correlation_matrix=corr, random_seed=123)

    comparison = validate_gum_against_monte_carlo(
        gum_estimate=Decimal("150.0"),
        gum_combined_uncertainty=gum_res.combined_standard_uncertainty,
        gum_coverage_factor_k=Decimal("2.0"),
        mc_result=mc_res,
        tolerance_pct=2.0,
    )

    assert comparison.is_gum_valid is True, f"Correlated model failed differential: {comparison.diagnostics}"
    return {
        "status": "PASSED",
        "diff_pct": comparison.uncertainty_relative_difference_pct,
        "gum_u": comparison.gum_combined_uncertainty,
        "mc_u": comparison.mc_standard_uncertainty,
    }


def run_ohms_law_nonlinear_differential() -> Dict[str, Any]:
    """
    Test Case 3: Ohm's Law Resistance R = V / I.
    V = 100.0 V, u(V) = 0.5 V (0.5%)
    I = 5.0 A, u(I) = 0.05 A (1.0%)
    R_nominal = 20.0 Ohm
    GUM: c_V = 1/I = 0.2, c_I = -V/I^2 = -4.0
    u_c(R) = sqrt((0.2*0.5)^2 + (-4.0*0.05)^2) = sqrt(0.01 + 0.04) = sqrt(0.05) ≈ 0.2236068 Ohm (1.118%)
    """
    c_v = Decimal("1") / Decimal("5.0")
    c_i = Decimal("-100.0") / (Decimal("5.0") ** 2)
    gum_res = propagate_uncertainty(
        standard_uncertainties=[Decimal("0.5"), Decimal("0.05")],
        sensitivity_coefficients=[c_v, c_i],
    )

    dists = [
        MonteCarloDistribution(label="V", distribution_type=DistributionType.NORMAL, mean=100.0, standard_uncertainty=0.5),
        MonteCarloDistribution(label="I", distribution_type=DistributionType.NORMAL, mean=5.0, standard_uncertainty=0.05),
    ]

    def model(x: List[float]) -> float:
        return x[0] / x[1]

    mc_res = run_monte_carlo_propagation(model, dists, num_trials=100_000, random_seed=999)

    comparison = validate_gum_against_monte_carlo(
        gum_estimate=Decimal("20.0"),
        gum_combined_uncertainty=gum_res.combined_standard_uncertainty,
        gum_coverage_factor_k=Decimal("2.0"),
        mc_result=mc_res,
        tolerance_pct=2.0,
    )

    assert comparison.is_gum_valid is True, f"Ohm's Law failed differential test: {comparison.diagnostics}"
    return {
        "status": "PASSED",
        "diff_pct": comparison.uncertainty_relative_difference_pct,
        "gum_u": comparison.gum_combined_uncertainty,
        "mc_u": comparison.mc_standard_uncertainty,
    }


def run_all_differential_tests() -> List[Dict[str, Any]]:
    """Run all differential test cases."""
    results = [
        {"name": "Linear Sum (Normal + Rectangular + Triangular)", **run_linear_sum_differential()},
        {"name": "Correlated Gaussian Sum (r = 0.5)", **run_correlated_differential()},
        {"name": "Nonlinear Division Model (Ohm's Law V/I)", **run_ohms_law_nonlinear_differential()},
    ]
    return results


if __name__ == "__main__":
    tests = run_all_differential_tests()
    for t in tests:
        print(f"Differential Test '{t['name']}': {t['status']} (Diff = {t['diff_pct']}%)")

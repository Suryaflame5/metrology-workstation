"""
Unit tests for JCGM 101:2008 Monte Carlo propagation and GUM validation.
"""

import pytest
from decimal import Decimal
from metrology_core.uncertainty.type_b import DistributionType
from metrology_core.uncertainty.monte_carlo import (
    run_monte_carlo_propagation,
    MonteCarloDistribution,
    validate_gum_against_monte_carlo,
)
from metrology_core.validation.differential import (
    run_linear_sum_differential,
    run_correlated_differential,
    run_ohms_law_nonlinear_differential,
)


def test_mc_single_gaussian():
    # Mean = 10.0, u = 1.0 -> MC should yield mean ~ 10.0, std ~ 1.0, 95% coverage ~ [8.04, 11.96]
    dists = [
        MonteCarloDistribution(label="X", distribution_type=DistributionType.NORMAL, mean=10.0, standard_uncertainty=1.0)
    ]
    res = run_monte_carlo_propagation(lambda x: x[0], dists, num_trials=50_000, random_seed=42)
    assert abs(res.mean - Decimal("10.0")) < Decimal("0.05")
    assert abs(res.standard_uncertainty - Decimal("1.0")) < Decimal("0.05")
    assert res.is_normal_like is True


def test_mc_rectangular_distribution():
    # Mean = 0, half_width = 1.0 -> variance = 1/3 ≈ 0.3333 -> std = 1/sqrt(3) ≈ 0.57735
    dists = [
        MonteCarloDistribution(label="X", distribution_type=DistributionType.RECTANGULAR, mean=0.0, standard_uncertainty=0.57735, half_width=1.0)
    ]
    res = run_monte_carlo_propagation(lambda x: x[0], dists, num_trials=50_000, random_seed=42)
    assert abs(res.mean - Decimal("0.0")) < Decimal("0.05")
    assert abs(res.standard_uncertainty - Decimal("0.57735")) < Decimal("0.02")


def test_differential_linear_sum():
    res = run_linear_sum_differential()
    assert res["status"] == "PASSED"
    assert res["diff_pct"] < Decimal("1.0")


def test_differential_correlated():
    res = run_correlated_differential()
    assert res["status"] == "PASSED"
    assert res["diff_pct"] < Decimal("1.0")


def test_differential_ohms_law():
    res = run_ohms_law_nonlinear_differential()
    assert res["status"] == "PASSED"
    assert res["diff_pct"] < Decimal("1.0")

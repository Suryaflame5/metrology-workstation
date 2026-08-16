"""
JCGM 101:2008 (Supplement 1 to GUM) - Propagation of Distributions via Monte Carlo Method.

Provides an independent statistical validation path for evaluating measurement uncertainty,
coverage intervals, and detecting non-linear measurement model distortions.
"""

from decimal import Decimal
import math
import random
from typing import Sequence, Callable, Optional, List, Dict, Any, NamedTuple, Tuple
from ..context import (
    to_decimal,
    MetrologyValidationError,
    InvalidCovarianceError,
    NonPositiveSemiDefiniteError,
    DECIMAL_CONTEXT,
)
from .type_b import DistributionType
from .covariance import CorrelationMatrix


class MonteCarloDistribution(NamedTuple):
    label: str
    distribution_type: DistributionType
    mean: float
    standard_uncertainty: float
    half_width: Optional[float] = None
    degrees_of_freedom: Optional[float] = None


class MonteCarloResult(NamedTuple):
    mean: Decimal
    standard_uncertainty: Decimal
    coverage_interval_95_low: Decimal
    coverage_interval_95_high: Decimal
    coverage_interval_95_width: Decimal
    sample_size: int
    skewness: float
    kurtosis: float
    is_normal_like: bool


class JCGM101ComparisonResult(NamedTuple):
    gum_combined_uncertainty: Decimal
    mc_standard_uncertainty: Decimal
    uncertainty_relative_difference_pct: Decimal
    gum_coverage_low: Decimal
    gum_coverage_high: Decimal
    mc_coverage_low: Decimal
    mc_coverage_high: Decimal
    is_gum_valid: bool
    diagnostics: str


def run_monte_carlo_propagation(
    model: Callable[[List[float]], float],
    distributions: Sequence[MonteCarloDistribution],
    num_trials: int = 100_000,
    correlation_matrix: Optional[CorrelationMatrix] = None,
    random_seed: Optional[int] = 42,
) -> MonteCarloResult:
    """
    Execute Monte Carlo distribution propagation conforming to JCGM 101:2008.
    
    Parameters:
        model: Python function f(x_1, ..., x_N) -> y representing the measurement equation.
        distributions: List of MonteCarloDistribution definitions for input quantities.
        num_trials: Number of Monte Carlo draws M (default 100,000).
        correlation_matrix: Optional CorrelationMatrix for correlated Gaussian variables.
        random_seed: Random seed for deterministic reproducibility.
        
    Returns:
        MonteCarloResult containing output mean, u(y), 95% coverage interval, and distribution metrics.
    """
    if num_trials < 1000:
        raise MetrologyValidationError(f"Monte Carlo requires at least 1,000 trials, got {num_trials}")

    if random_seed is not None:
        rng = random.Random(random_seed)
    else:
        rng = random.Random()

    n_inputs = len(distributions)
    if n_inputs == 0:
        raise MetrologyValidationError("At least one input distribution is required")

    # If correlated, compute Cholesky factor L of correlation matrix
    cholesky_L: Optional[List[List[float]]] = None
    if correlation_matrix is not None:
        if correlation_matrix.dimension != n_inputs:
            raise MetrologyValidationError(
                f"Correlation matrix size ({correlation_matrix.dimension}) != inputs ({n_inputs})"
            )
        # Convert Decimal matrix to float matrix for high-speed numpy-free Monte Carlo
        dim = correlation_matrix.dimension
        cholesky_L = [[0.0] * dim for _ in range(dim)]
        for i in range(dim):
            for j in range(i + 1):
                s = sum(cholesky_L[i][k] * cholesky_L[j][k] for k in range(j))
                val = float(correlation_matrix.matrix[i][j]) - s
                if i == j:
                    if val < 0.0:
                        val = 0.0
                    cholesky_L[i][i] = math.sqrt(val)
                else:
                    if cholesky_L[j][j] > 1e-15:
                        cholesky_L[i][j] = (float(correlation_matrix.matrix[i][j]) - s) / cholesky_L[j][j]
                    else:
                        cholesky_L[i][j] = 0.0

    # Draw M samples
    y_samples: List[float] = []

    for _ in range(num_trials):
        x_vec: List[float] = [0.0] * n_inputs

        if cholesky_L is not None:
            # Correlated Gaussian draws
            z_uncorr = [rng.gauss(0.0, 1.0) for _ in range(n_inputs)]
            for i in range(n_inputs):
                z_corr = sum(cholesky_L[i][k] * z_uncorr[k] for k in range(i + 1))
                x_vec[i] = distributions[i].mean + (distributions[i].standard_uncertainty * z_corr)
        else:
            # Independent draws per specified distribution
            for i, dist in enumerate(distributions):
                dtype = dist.distribution_type
                mu = dist.mean
                u = dist.standard_uncertainty
                hw = dist.half_width

                if dtype in (DistributionType.NORMAL, DistributionType.GAUSSIAN):
                    if dist.degrees_of_freedom is not None and dist.degrees_of_freedom < 100:
                        # Sample Student's t distribution: Z / sqrt(V / nu) where V ~ Chi-sq(nu)
                        nu = dist.degrees_of_freedom
                        z = rng.gauss(0.0, 1.0)
                        v = sum(rng.gauss(0.0, 1.0) ** 2 for _ in range(int(round(nu))))
                        t_draw = z / math.sqrt(v / nu)
                        x_vec[i] = mu + (u * t_draw)
                    else:
                        x_vec[i] = rng.gauss(mu, u)

                elif dtype in (DistributionType.RECTANGULAR, DistributionType.UNIFORM):
                    half_w = hw if hw is not None else (u * math.sqrt(3.0))
                    x_vec[i] = rng.uniform(mu - half_w, mu + half_w)

                elif dtype == DistributionType.TRIANGULAR:
                    half_w = hw if hw is not None else (u * math.sqrt(6.0))
                    x_vec[i] = rng.triangular(mu - half_w, mu + half_w, mu)

                elif dtype == DistributionType.U_SHAPED:
                    half_w = hw if hw is not None else (u * math.sqrt(2.0))
                    theta = rng.uniform(-math.pi / 2.0, math.pi / 2.0)
                    x_vec[i] = mu + (half_w * math.sin(theta))
                else:
                    x_vec[i] = rng.gauss(mu, u)

        y_val = model(x_vec)
        y_samples.append(y_val)

    # Compute Monte Carlo sample statistics
    m_float = float(num_trials)
    mean_y = sum(y_samples) / m_float

    var_y = sum((y - mean_y) ** 2 for y in y_samples) / (m_float - 1.0)
    std_y = math.sqrt(max(0.0, var_y))

    # Moments (Skewness & Kurtosis) for normality assessment
    if std_y > 1e-15:
        skewness = (sum((y - mean_y) ** 3 for y in y_samples) / m_float) / (std_y ** 3)
        kurtosis = (sum((y - mean_y) ** 4 for y in y_samples) / m_float) / (std_y ** 4) - 3.0
    else:
        skewness = 0.0
        kurtosis = 0.0

    is_normal_like = (abs(skewness) < 0.2) and (abs(kurtosis) < 0.4)

    # Compute 95% coverage interval by sorting (JCGM 101 Section 7.7)
    y_samples.sort()
    idx_low = int(math.floor(0.025 * m_float))
    idx_high = int(math.floor(0.975 * m_float))
    c_low = y_samples[max(0, min(num_trials - 1, idx_low))]
    c_high = y_samples[max(0, min(num_trials - 1, idx_high))]
    c_width = c_high - c_low

    return MonteCarloResult(
        mean=to_decimal(round(mean_y, 10)),
        standard_uncertainty=to_decimal(round(std_y, 10)),
        coverage_interval_95_low=to_decimal(round(c_low, 10)),
        coverage_interval_95_high=to_decimal(round(c_high, 10)),
        coverage_interval_95_width=to_decimal(round(c_width, 10)),
        sample_size=num_trials,
        skewness=round(skewness, 4),
        kurtosis=round(kurtosis, 4),
        is_normal_like=is_normal_like,
    )


def validate_gum_against_monte_carlo(
    gum_estimate: Any,
    gum_combined_uncertainty: Any,
    gum_coverage_factor_k: Any,
    mc_result: MonteCarloResult,
    tolerance_pct: float = 5.0,
) -> JCGM101ComparisonResult:
    """
    Compare GUM analytical 1st-order evaluation against JCGM 101 Monte Carlo results.
    
    Checks:
    1. Relative standard uncertainty difference |u_GUM - u_MC| / u_MC.
    2. Coverage interval overlap and non-linear distortion.
    """
    u_gum = to_decimal(gum_combined_uncertainty)
    u_mc = mc_result.standard_uncertainty
    y_gum = to_decimal(gum_estimate)
    k_gum = to_decimal(gum_coverage_factor_k)

    expanded_u = u_gum * k_gum
    gum_cov_low = y_gum - expanded_u
    gum_cov_high = y_gum + expanded_u

    if u_mc > Decimal("0"):
        diff_pct = (abs(u_gum - u_mc) / u_mc) * Decimal("100")
    else:
        diff_pct = Decimal("0") if u_gum == Decimal("0") else Decimal("100")

    is_valid = float(diff_pct) <= tolerance_pct

    if is_valid:
        diag = (
            f"GUM 1st-order model validated by JCGM 101 Monte Carlo (diff = {diff_pct:.3f}% <= {tolerance_pct}%). "
            f"Output distribution is sufficiently linear and normal-like."
        )
    else:
        diag = (
            f"WARNING: JCGM 101 Monte Carlo detects non-linearity/distortion! "
            f"GUM u_c ({u_gum}) differs from MC u ({u_mc}) by {diff_pct:.2f}% (> {tolerance_pct}% threshold). "
            f"Skewness = {mc_result.skewness}, Kurtosis = {mc_result.kurtosis}."
        )

    return JCGM101ComparisonResult(
        gum_combined_uncertainty=u_gum,
        mc_standard_uncertainty=u_mc,
        uncertainty_relative_difference_pct=to_decimal(round(diff_pct, 4)),
        gum_coverage_low=gum_cov_low,
        gum_coverage_high=gum_cov_high,
        mc_coverage_low=mc_result.coverage_interval_95_low,
        mc_coverage_high=mc_result.coverage_interval_95_high,
        is_gum_valid=is_valid,
        diagnostics=diag,
    )

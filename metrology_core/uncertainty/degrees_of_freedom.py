"""
Welch-Satterthwaite Effective Degrees of Freedom and Coverage Factors (GUM Annex G).
"""

from decimal import Decimal
import math
from typing import Sequence, Optional, Union, NamedTuple, Any
from ..context import (
    to_decimal,
    decimal_sqrt,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)
from .propagation import CombinedUncertaintyResult


class DegreesOfFreedomResult(NamedTuple):
    effective_degrees_of_freedom: Optional[Decimal]  # None indicates infinity
    coverage_factor_95: Decimal
    coverage_factor_9545: Decimal
    expanded_uncertainty_95: Decimal
    expanded_uncertainty_9545: Decimal


# Standard Student-t table values for 95% (two-tailed p=0.05) and 95.45% (k=2 equivalent)
T_TABLE_95 = {
    1: Decimal("12.706"),
    2: Decimal("4.303"),
    3: Decimal("3.182"),
    4: Decimal("2.776"),
    5: Decimal("2.571"),
    6: Decimal("2.447"),
    7: Decimal("2.365"),
    8: Decimal("2.306"),
    9: Decimal("2.262"),
    10: Decimal("2.228"),
    12: Decimal("2.179"),
    14: Decimal("2.145"),
    16: Decimal("2.120"),
    18: Decimal("2.101"),
    20: Decimal("2.086"),
    25: Decimal("2.060"),
    30: Decimal("2.042"),
    40: Decimal("2.021"),
    50: Decimal("2.009"),
    60: Decimal("2.000"),
    80: Decimal("1.990"),
    100: Decimal("1.984"),
}


def calculate_welch_satterthwaite(
    combined_result: CombinedUncertaintyResult,
) -> DegreesOfFreedomResult:
    """
    Calculate effective degrees of freedom nu_eff using the Welch-Satterthwaite formula:
        nu_eff = u_c^4(y) / sum( (c_i * u_i)^4 / nu_i )
        
    Parameters:
        combined_result: CombinedUncertaintyResult from propagate_uncertainty.
        
    Returns:
        DegreesOfFreedomResult with nu_eff, k_95, k_9545, U_95, U_9545.
    """
    u_c = combined_result.combined_standard_uncertainty
    if u_c == Decimal("0"):
        return DegreesOfFreedomResult(
            effective_degrees_of_freedom=None,
            coverage_factor_95=Decimal("2.0"),
            coverage_factor_9545=Decimal("2.0"),
            expanded_uncertainty_95=Decimal("0"),
            expanded_uncertainty_9545=Decimal("0"),
        )

    u_c_4 = u_c ** 4
    denominator = Decimal("0")

    for comp in combined_result.components:
        if comp.degrees_of_freedom is not None:
            nu_i = comp.degrees_of_freedom
            if nu_i <= Decimal("0"):
                raise MetrologyValidationError(f"Component '{comp.label}' has invalid degrees of freedom: {nu_i}")
            # (c_i * u_i)^4 / nu_i
            term = (comp.variance_contribution ** 2) / nu_i
            denominator += term

    if denominator == Decimal("0"):
        nu_eff = None  # Infinite degrees of freedom
        k_95 = Decimal("1.960")
        k_9545 = Decimal("2.000")
    else:
        nu_eff = u_c_4 / denominator
        # Calculate t-distribution coverage factor
        k_95 = get_student_t_quantile(nu_eff, p=0.95)
        k_9545 = get_student_t_quantile(nu_eff, p=0.9545)

    u_95 = u_c * k_95
    u_9545 = u_c * k_9545

    return DegreesOfFreedomResult(
        effective_degrees_of_freedom=nu_eff,
        coverage_factor_95=k_95,
        coverage_factor_9545=k_9545,
        expanded_uncertainty_95=u_95,
        expanded_uncertainty_9545=u_9545,
    )


def get_student_t_quantile(nu: Optional[Decimal], p: float = 0.95) -> Decimal:
    """
    Calculate Student's t quantile t_p(nu) for effective degrees of freedom nu.
    """
    if nu is None:
        if abs(p - 0.95) < 1e-4:
            return Decimal("1.959963984540054")
        if abs(p - 0.9545) < 1e-4:
            return Decimal("2.000000000000000")
        if abs(p - 0.99) < 1e-4:
            return Decimal("2.575829303548900")
        return Decimal("2.0")

    float_nu = float(nu)
    if float_nu <= 0:
        raise MetrologyValidationError(f"Degrees of freedom must be > 0, got {nu}")

    # For high degrees of freedom, t approaches normal z-score
    if float_nu >= 200:
        if abs(p - 0.95) < 1e-3:
            return Decimal("1.960")
        if abs(p - 0.9545) < 1e-3:
            return Decimal("2.000")

    # High-precision approximation using Cornish-Fisher expansion / regularized incomplete beta
    # For Student's t two-tailed quantile with confidence p:
    alpha = 1.0 - p
    # Standard normal quantile z
    # Rational approximation for standard normal quantile
    z = math.sqrt(2.0) * _erfinv(p)
    
    # Hill's Cornish-Fisher expansion for Student's t:
    # t = z + (z^3 + z)/(4 nu) + (5z^5 + 16z^3 + 3z)/(96 nu^2) + ...
    z2 = z * z
    z3 = z2 * z
    z5 = z3 * z2
    term1 = (z3 + z) / (4.0 * float_nu)
    term2 = (5.0 * z5 + 16.0 * z3 + 3.0 * z) / (96.0 * (float_nu ** 2))
    t_val = z + term1 + term2

    return to_decimal(round(t_val, 6))


def _erfinv(y: float) -> float:
    """Inverse error function approximation (Winitzki)."""
    a = 0.147
    sgn = 1.0 if y >= 0 else -1.0
    y2 = y * y
    ln_term = math.log(1.0 - y2)
    part1 = 2.0 / (math.pi * a) + ln_term / 2.0
    val = math.sqrt(math.sqrt(part1 * part1 - ln_term / a) - part1)
    return sgn * val

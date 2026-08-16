"""
Type A Standard Uncertainty Evaluation (GUM / JCGM 100 Section 4.2).
"""

from decimal import Decimal
from typing import Sequence, Any, NamedTuple
from ..context import (
    to_decimal,
    decimal_sqrt,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)


class TypeAResult(NamedTuple):
    """Result of Type A statistical evaluation."""
    n: int
    mean: Decimal
    variance: Decimal
    standard_deviation: Decimal
    standard_uncertainty: Decimal
    degrees_of_freedom: int


def evaluate_type_a(observations: Sequence[Any]) -> TypeAResult:
    """
    Evaluate Type A uncertainty from a sequence of repeated observations.
    
    Parameters:
        observations: Sequence of numeric or string values representing repeated measurements.
        
    Returns:
        TypeAResult containing n, mean, variance s^2(x), sample std dev s(x),
        standard uncertainty u(mean) = s(x) / sqrt(n), and degrees of freedom nu = n - 1.
        
    Raises:
        MetrologyValidationError: If fewer than 2 observations are provided.
    """
    if len(observations) < 2:
        raise MetrologyValidationError(
            f"Type A evaluation requires at least n=2 observations, got {len(observations)}"
        )
    
    obs = [to_decimal(x) for x in observations]
    n = len(obs)
    dec_n = Decimal(n)
    
    # Arithmetic mean: x_bar = (1/n) * sum(x_k)
    total = sum(obs, Decimal("0"))
    mean = total / dec_n
    
    # Sample variance: s^2 = (1 / (n-1)) * sum((x_k - x_bar)^2)
    sum_sq_diff = sum(((x - mean) ** 2 for x in obs), Decimal("0"))
    variance = sum_sq_diff / Decimal(n - 1)
    
    # Sample standard deviation: s = sqrt(s^2)
    std_dev = decimal_sqrt(variance)
    
    # Standard uncertainty of the mean: u(x_bar) = s / sqrt(n)
    std_uncertainty = std_dev / decimal_sqrt(dec_n)
    
    dof = n - 1
    
    return TypeAResult(
        n=n,
        mean=mean,
        variance=variance,
        standard_deviation=std_dev,
        standard_uncertainty=std_uncertainty,
        degrees_of_freedom=dof,
    )

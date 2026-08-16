"""
Type B Standard Uncertainty Evaluation (GUM / JCGM 100 Section 4.3).
"""

from decimal import Decimal
from enum import Enum
from typing import Any, Optional, NamedTuple, Union
from ..context import (
    to_decimal,
    decimal_sqrt,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)


class DistributionType(str, Enum):
    RECTANGULAR = "rectangular"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    NORMAL = "normal"
    GAUSSIAN = "gaussian"
    U_SHAPED = "u_shaped"


class TypeBResult(NamedTuple):
    """Result of Type B evaluation."""
    distribution: DistributionType
    half_width: Optional[Decimal]
    divisor: Decimal
    standard_uncertainty: Decimal
    degrees_of_freedom: Optional[Decimal]  # None or Decimal('inf') for infinite


def evaluate_type_b(
    half_width: Optional[Any] = None,
    distribution: Union[DistributionType, str] = DistributionType.RECTANGULAR,
    expanded_uncertainty: Optional[Any] = None,
    coverage_factor: Optional[Any] = None,
    degrees_of_freedom: Optional[Any] = None,
) -> TypeBResult:
    """
    Evaluate Type B standard uncertainty from specified distribution model.
    
    Parameters:
        half_width: Semi-range / half-width 'a' of the distribution (for rectangular, triangular, U-shaped).
        distribution: Distribution type (DistributionType or str).
        expanded_uncertainty: Expanded uncertainty U (for normal distribution).
        coverage_factor: Coverage factor k (for normal distribution, default 2.0).
        degrees_of_freedom: Degrees of freedom (default infinity).
        
    Returns:
        TypeBResult with standard_uncertainty = half_width / divisor or U / k.
    """
    if isinstance(distribution, str):
        dist_str = distribution.lower().replace("-", "_")
        try:
            dist = DistributionType(dist_str)
        except ValueError:
            raise MetrologyValidationError(
                f"Unknown distribution: '{distribution}'. Valid choices: "
                f"{[d.value for d in DistributionType]}"
            )
    else:
        dist = distribution

    dof: Optional[Decimal] = None
    if degrees_of_freedom is not None and str(degrees_of_freedom).lower() not in ("inf", "infinity"):
        dof = to_decimal(degrees_of_freedom)
        if dof <= Decimal("0"):
            raise MetrologyValidationError(f"Degrees of freedom must be positive, got {dof}")

    if dist in (DistributionType.RECTANGULAR, DistributionType.UNIFORM):
        if half_width is None:
            raise MetrologyValidationError("half_width is required for rectangular/uniform distribution")
        a = to_decimal(half_width)
        if a < Decimal("0"):
            raise MetrologyValidationError(f"half_width cannot be negative, got {a}")
        # u = a / sqrt(3)
        divisor = decimal_sqrt(Decimal("3"))
        u = a / divisor
        return TypeBResult(
            distribution=DistributionType.RECTANGULAR,
            half_width=a,
            divisor=divisor,
            standard_uncertainty=u,
            degrees_of_freedom=dof,
        )

    elif dist == DistributionType.TRIANGULAR:
        if half_width is None:
            raise MetrologyValidationError("half_width is required for triangular distribution")
        a = to_decimal(half_width)
        if a < Decimal("0"):
            raise MetrologyValidationError(f"half_width cannot be negative, got {a}")
        # u = a / sqrt(6)
        divisor = decimal_sqrt(Decimal("6"))
        u = a / divisor
        return TypeBResult(
            distribution=DistributionType.TRIANGULAR,
            half_width=a,
            divisor=divisor,
            standard_uncertainty=u,
            degrees_of_freedom=dof,
        )

    elif dist == DistributionType.U_SHAPED:
        if half_width is None:
            raise MetrologyValidationError("half_width is required for U-shaped distribution")
        a = to_decimal(half_width)
        if a < Decimal("0"):
            raise MetrologyValidationError(f"half_width cannot be negative, got {a}")
        # u = a / sqrt(2)
        divisor = decimal_sqrt(Decimal("2"))
        u = a / divisor
        return TypeBResult(
            distribution=DistributionType.U_SHAPED,
            half_width=a,
            divisor=divisor,
            standard_uncertainty=u,
            degrees_of_freedom=dof,
        )

    elif dist in (DistributionType.NORMAL, DistributionType.GAUSSIAN):
        if expanded_uncertainty is not None:
            U = to_decimal(expanded_uncertainty)
            k = to_decimal(coverage_factor if coverage_factor is not None else Decimal("2"))
            if k <= Decimal("0"):
                raise MetrologyValidationError(f"Coverage factor k must be positive, got {k}")
            if U < Decimal("0"):
                raise MetrologyValidationError(f"Expanded uncertainty U cannot be negative, got {U}")
            u = U / k
            return TypeBResult(
                distribution=DistributionType.NORMAL,
                half_width=U,
                divisor=k,
                standard_uncertainty=u,
                degrees_of_freedom=dof,
            )
        elif half_width is not None:
            # If half_width is given with normal distribution, treat half-width as expanded uncertainty with k
            a = to_decimal(half_width)
            k = to_decimal(coverage_factor if coverage_factor is not None else Decimal("2"))
            if k <= Decimal("0"):
                raise MetrologyValidationError(f"Coverage factor k must be positive, got {k}")
            if a < Decimal("0"):
                raise MetrologyValidationError(f"half_width cannot be negative, got {a}")
            u = a / k
            return TypeBResult(
                distribution=DistributionType.NORMAL,
                half_width=a,
                divisor=k,
                standard_uncertainty=u,
                degrees_of_freedom=dof,
            )
        else:
            raise MetrologyValidationError("Either expanded_uncertainty or half_width must be provided for normal distribution")

    raise MetrologyValidationError(f"Unhandled distribution type: {dist}")

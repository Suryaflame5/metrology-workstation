"""
Law of Propagation of Uncertainty (GUM / JCGM 100 Section 5).
"""

from decimal import Decimal
from typing import Sequence, Optional, List, NamedTuple, Any
from ..context import (
    to_decimal,
    decimal_sqrt,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)
from .covariance import CovarianceMatrix, CorrelationMatrix


class UncertaintyComponent(NamedTuple):
    label: str
    standard_uncertainty: Decimal
    sensitivity_coefficient: Decimal
    variance_contribution: Decimal
    percentage_contribution: Decimal
    degrees_of_freedom: Optional[Decimal]


class CombinedUncertaintyResult(NamedTuple):
    combined_standard_uncertainty: Decimal
    combined_variance: Decimal
    components: List[UncertaintyComponent]
    covariance_contribution: Decimal
    covariance_matrix: Optional[CovarianceMatrix]


def propagate_uncertainty(
    standard_uncertainties: Sequence[Any],
    sensitivity_coefficients: Optional[Sequence[Any]] = None,
    covariance_matrix: Optional[CovarianceMatrix] = None,
    correlation_matrix: Optional[CorrelationMatrix] = None,
    labels: Optional[Sequence[str]] = None,
    degrees_of_freedom: Optional[Sequence[Optional[Any]]] = None,
) -> CombinedUncertaintyResult:
    """
    Calculate combined standard uncertainty u_c(y) using the GUM law of propagation.
    
    Formula:
        u_c^2(y) = sum(c_i^2 * u^2(x_i)) + 2 * sum_{i < j}(c_i * c_j * u(x_i, x_j))
        u_c(y) = sqrt(u_c^2(y))
        
    Parameters:
        standard_uncertainties: List of u(x_i) standard uncertainties.
        sensitivity_coefficients: List of partial derivatives c_i = df/dx_i (default 1.0 for all).
        covariance_matrix: Full CovarianceMatrix instance (optional).
        correlation_matrix: Full CorrelationMatrix instance (optional).
        labels: Variable names/labels (optional).
        degrees_of_freedom: Individual degrees of freedom nu_i for Welch-Satterthwaite (optional).
        
    Returns:
        CombinedUncertaintyResult with combined u_c, variance, component breakdown, and covariance contribution.
    """
    n = len(standard_uncertainties)
    if n == 0:
        raise MetrologyValidationError("At least one uncertainty component is required")

    u_list = [to_decimal(u) for u in standard_uncertainties]
    for i, u in enumerate(u_list):
        if u < Decimal("0"):
            raise MetrologyValidationError(f"Standard uncertainty u[{i}] cannot be negative: {u}")

    if sensitivity_coefficients is not None:
        c_list = [to_decimal(c) for c in sensitivity_coefficients]
        if len(c_list) != n:
            raise MetrologyValidationError(
                f"Number of sensitivity coefficients ({len(c_list)}) must match components ({n})"
            )
    else:
        c_list = [Decimal("1") for _ in range(n)]

    component_labels = (
        [str(l) for l in labels] if labels is not None else [f"X{i+1}" for i in range(n)]
    )
    if len(component_labels) != n:
        raise MetrologyValidationError(f"Number of labels ({len(component_labels)}) must match components ({n})")

    dof_list: List[Optional[Decimal]] = []
    if degrees_of_freedom is not None:
        if len(degrees_of_freedom) != n:
            raise MetrologyValidationError(
                f"Number of degrees of freedom entries ({len(degrees_of_freedom)}) must match components ({n})"
            )
        for d in degrees_of_freedom:
            if d is None or str(d).lower() in ("inf", "infinity"):
                dof_list.append(None)
            else:
                dec_d = to_decimal(d)
                if dec_d <= Decimal("0"):
                    raise MetrologyValidationError(f"Degrees of freedom must be positive, got {dec_d}")
                dof_list.append(dec_d)
    else:
        dof_list = [None] * n

    # Covariance resolution
    cov_mat: Optional[CovarianceMatrix] = None
    if covariance_matrix is not None:
        if covariance_matrix.dimension != n:
            raise MetrologyValidationError(
                f"Covariance matrix dimension ({covariance_matrix.dimension}) must match components ({n})"
            )
        cov_mat = covariance_matrix
    elif correlation_matrix is not None:
        if correlation_matrix.dimension != n:
            raise MetrologyValidationError(
                f"Correlation matrix dimension ({correlation_matrix.dimension}) must match components ({n})"
            )
        cov_mat = correlation_matrix.to_covariance_matrix(u_list)

    # 1. Independent sum of squares: sum(c_i^2 * u_i^2)
    uncorrelated_variance_terms: List[Decimal] = []
    for i in range(n):
        var_i = (c_list[i] ** 2) * (u_list[i] ** 2)
        uncorrelated_variance_terms.append(var_i)

    uncorrelated_variance = sum(uncorrelated_variance_terms, Decimal("0"))

    # 2. Covariance cross-terms: 2 * sum_{i < j}(c_i * c_j * cov(x_i, x_j))
    covariance_contribution = Decimal("0")
    if cov_mat is not None:
        for i in range(n):
            for j in range(i + 1, n):
                c_i_j = Decimal("2") * c_list[i] * c_list[j] * cov_mat.get_covariance(i, j)
                covariance_contribution += c_i_j

    combined_variance = uncorrelated_variance + covariance_contribution
    if combined_variance < Decimal("0"):
        # Could happen only if covariance is invalid, but caught by PSD. Guard anyway.
        raise MetrologyValidationError(
            f"Calculated combined variance is negative: {combined_variance}. Verify correlation matrix."
        )

    combined_std_uncertainty = decimal_sqrt(combined_variance)

    # Component budget breakdown
    components: List[UncertaintyComponent] = []
    for i in range(n):
        var_contrib = uncorrelated_variance_terms[i]
        pct = (
            (var_contrib / combined_variance * Decimal("100"))
            if combined_variance > Decimal("0")
            else Decimal("0")
        )
        components.append(
            UncertaintyComponent(
                label=component_labels[i],
                standard_uncertainty=u_list[i],
                sensitivity_coefficient=c_list[i],
                variance_contribution=var_contrib,
                percentage_contribution=pct,
                degrees_of_freedom=dof_list[i],
            )
        )

    return CombinedUncertaintyResult(
        combined_standard_uncertainty=combined_std_uncertainty,
        combined_variance=combined_variance,
        components=components,
        covariance_contribution=covariance_contribution,
        covariance_matrix=cov_mat,
    )

"""
Covariance and Correlation Matrix Validation with Exact Decimal PSD Verification.
"""

from decimal import Decimal
from typing import Sequence, List, Optional, Union, Tuple, Any
from ..context import (
    to_decimal,
    decimal_sqrt,
    MetrologyValidationError,
    InvalidCovarianceError,
    NonPositiveSemiDefiniteError,
    DECIMAL_CONTEXT,
)


class CorrelationMatrix:
    """
    Validated Correlation Matrix with exact Decimal positive semi-definiteness (PSD) checks.
    """

    def __init__(
        self,
        matrix: Sequence[Sequence[Union[Decimal, float, int, str]]],
        labels: Optional[Sequence[str]] = None,
    ) -> None:
        self.dimension = len(matrix)
        if self.dimension == 0:
            raise MetrologyValidationError("Correlation matrix cannot be empty")

        self.labels = [str(l) for l in labels] if labels is not None else [f"X{i+1}" for i in range(self.dimension)]
        if len(self.labels) != self.dimension:
            raise MetrologyValidationError(
                f"Number of labels ({len(self.labels)}) must match matrix dimension ({self.dimension})"
            )

        self.matrix: List[List[Decimal]] = []
        for i, row in enumerate(matrix):
            if len(row) != self.dimension:
                raise MetrologyValidationError(
                    f"Row {i} has {len(row)} elements; expected square matrix of size {self.dimension}x{self.dimension}"
                )
            self.matrix.append([to_decimal(val) for val in row])

        self._validate()

    def _validate(self) -> None:
        """Validate symmetry, bounds [-1, 1], diagonal unity, and positive semi-definiteness."""
        n = self.dimension
        one = Decimal("1")
        minus_one = Decimal("-1")
        zero = Decimal("0")
        eps = Decimal("1e-40")

        for i in range(n):
            # Diagonal check
            if abs(self.matrix[i][i] - one) > eps:
                raise InvalidCovarianceError(
                    f"Diagonal element R[{i}][{i}] for '{self.labels[i]}' must be exactly 1.0, got {self.matrix[i][i]}"
                )
            for j in range(i + 1, n):
                r_ij = self.matrix[i][j]
                r_ji = self.matrix[j][i]

                # Bounds check
                if r_ij < minus_one or r_ij > one:
                    raise InvalidCovarianceError(
                        f"Correlation r({self.labels[i]}, {self.labels[j]}) = {r_ij} is out of bounds [-1, 1]"
                    )

                # Symmetry check
                if abs(r_ij - r_ji) > eps:
                    raise InvalidCovarianceError(
                        f"Correlation matrix must be symmetric: r({self.labels[i]}, {self.labels[j]}) = {r_ij} "
                        f"!= r({self.labels[j]}, {self.labels[i]}) = {r_ji}"
                    )

        # Positive semi-definiteness check via Decimal Cholesky decomposition
        self._verify_positive_semi_definite()

    def _verify_positive_semi_definite(self) -> None:
        """
        Verify positive semi-definiteness via Decimal Cholesky-Banachiewicz decomposition.
        Raises NonPositiveSemiDefiniteError if matrix fails PSD condition.
        """
        n = self.dimension
        zero = Decimal("0")
        neg_tol = Decimal("-1e-35")
        L = [[zero] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1):
                sum_k = sum((L[i][k] * L[j][k] for k in range(j)), zero)
                if i == j:
                    val = self.matrix[i][i] - sum_k
                    if val < neg_tol:
                        # Build explanatory error message
                        context_pairs = []
                        for row_idx in range(i + 1):
                            for col_idx in range(row_idx + 1, i + 1):
                                context_pairs.append(
                                    f"r({self.labels[row_idx]}, {self.labels[col_idx]}) = {self.matrix[row_idx][col_idx]}"
                                )
                        raise NonPositiveSemiDefiniteError(
                            f"Correlation matrix is not positive semi-definite (failed at variable '{self.labels[i]}', "
                            f"pivot residual = {val}).\n"
                            f"Correlations: {', '.join(context_pairs) if context_pairs else 'N/A'}"
                        )
                    pivot_val = max(zero, val)
                    L[i][i] = decimal_sqrt(pivot_val)
                else:
                    if L[j][j] == zero:
                        remainder = self.matrix[i][j] - sum_k
                        if abs(remainder) > Decimal("1e-35"):
                            raise NonPositiveSemiDefiniteError(
                                f"Correlation matrix is singular and inconsistent at ({self.labels[i]}, {self.labels[j]})"
                            )
                        L[i][j] = zero
                    else:
                        L[i][j] = (self.matrix[i][j] - sum_k) / L[j][j]

    def get_correlation(self, i: int, j: int) -> Decimal:
        """Get correlation coefficient r_ij between component i and j."""
        return self.matrix[i][j]

    def to_covariance_matrix(self, standard_uncertainties: Sequence[Any]) -> "CovarianceMatrix":
        """Generate CovarianceMatrix V_ij = r_ij * u_i * u_j."""
        u_list = [to_decimal(u) for u in standard_uncertainties]
        if len(u_list) != self.dimension:
            raise MetrologyValidationError(
                f"Number of standard uncertainties ({len(u_list)}) must match matrix dimension ({self.dimension})"
            )
        for i, u in enumerate(u_list):
            if u < Decimal("0"):
                raise MetrologyValidationError(f"Standard uncertainty for '{self.labels[i]}' cannot be negative: {u}")

        cov_matrix: List[List[Decimal]] = []
        for i in range(self.dimension):
            row = []
            for j in range(self.dimension):
                cov = self.matrix[i][j] * u_list[i] * u_list[j]
                row.append(cov)
            cov_matrix.append(row)

        return CovarianceMatrix(cov_matrix, self.labels, standard_uncertainties=u_list, correlation_matrix=self)

    @classmethod
    def identity(cls, dimension: int, labels: Optional[Sequence[str]] = None) -> "CorrelationMatrix":
        """Create identity correlation matrix (all correlations r_ij = 0 for i != j)."""
        if dimension < 1:
            raise MetrologyValidationError(f"Dimension must be positive integer, got {dimension}")
        one = Decimal("1")
        zero = Decimal("0")
        mat = [[one if i == j else zero for j in range(dimension)] for i in range(dimension)]
        return cls(mat, labels=labels)


class CovarianceMatrix:
    """
    Covariance Matrix holding pairwise covariances V_ij = u(x_i, x_j).
    """

    def __init__(
        self,
        matrix: Sequence[Sequence[Union[Decimal, float, int, str]]],
        labels: Optional[Sequence[str]] = None,
        standard_uncertainties: Optional[Sequence[Decimal]] = None,
        correlation_matrix: Optional[CorrelationMatrix] = None,
    ) -> None:
        self.dimension = len(matrix)
        if self.dimension == 0:
            raise MetrologyValidationError("Covariance matrix cannot be empty")

        self.labels = [str(l) for l in labels] if labels is not None else [f"X{i+1}" for i in range(self.dimension)]
        self.matrix: List[List[Decimal]] = [
            [to_decimal(val) for val in row] for row in matrix
        ]
        self.standard_uncertainties = (
            [to_decimal(u) for u in standard_uncertainties]
            if standard_uncertainties is not None
            else [decimal_sqrt(self.matrix[i][i]) for i in range(self.dimension)]
        )
        self.correlation_matrix = correlation_matrix

    def get_covariance(self, i: int, j: int) -> Decimal:
        """Get covariance V_ij = u(x_i, x_j)."""
        return self.matrix[i][j]

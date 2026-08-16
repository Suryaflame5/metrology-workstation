"""
Metrology Context and Exact Decimal Math Utilities.

Configures high-precision decimal context and domain-specific exception hierarchy.
"""

from decimal import Decimal, Context, ROUND_HALF_EVEN, getcontext, setcontext, localcontext
from typing import Any, Union

# Global high-precision metrological context (50 decimal digits)
DEFAULT_METROLOGY_PRECISION = 50
DECIMAL_CONTEXT = Context(prec=DEFAULT_METROLOGY_PRECISION, rounding=ROUND_HALF_EVEN)
setcontext(DECIMAL_CONTEXT)


class MetrologyError(Exception):
    """Base exception for all metrology-core domain errors."""
    pass


class MetrologyValidationError(MetrologyError):
    """Raised when calculation inputs or constraints violate physical or metrological rules."""
    pass


class InvalidCovarianceError(MetrologyValidationError):
    """Raised when covariance or correlation matrices are mathematically or physically invalid."""
    pass


class NonPositiveSemiDefiniteError(InvalidCovarianceError):
    """Raised when a correlation or covariance matrix is not positive semi-definite."""
    pass


class OutOfDomainError(MetrologyValidationError):
    """Raised when an operation is attempted outside its valid metrological domain."""
    pass


class DecisionRuleError(MetrologyError):
    """Raised when a decision rule fails or cannot be computed."""
    pass


def set_precision(prec: int) -> None:
    """Set global calculation precision in decimal places."""
    if prec < 1:
        raise MetrologyValidationError(f"Precision must be positive integer, got {prec}")
    DECIMAL_CONTEXT.prec = prec
    setcontext(DECIMAL_CONTEXT)


def get_precision() -> int:
    """Get current global calculation precision."""
    return DECIMAL_CONTEXT.prec


def to_decimal(value: Any) -> Decimal:
    """
    Safely convert an input to Decimal within the metrology context.
    
    Accepts Decimal, str, int, float. Converts str and int directly.
    For float, converts via str(float) representation to prevent binary IEEE 754 precision artifacts.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        try:
            return Decimal(str(value), DECIMAL_CONTEXT)
        except Exception as e:
            raise MetrologyValidationError(f"Cannot convert '{value}' to Decimal: {e}")
    if isinstance(value, float):
        # Convert via string representation to preserve the exact decimal representation written by user
        return Decimal(str(value), DECIMAL_CONTEXT)
    try:
        return Decimal(str(value), DECIMAL_CONTEXT)
    except Exception as e:
        raise MetrologyValidationError(f"Unsupported type {type(value)} for to_decimal: {e}")


def decimal_sqrt(x: Any) -> Decimal:
    """Compute exact square root of x using Decimal context."""
    dx = to_decimal(x)
    if dx < Decimal("0"):
        raise OutOfDomainError(f"Cannot compute square root of negative value: {dx}")
    if dx == Decimal("0"):
        return Decimal("0")
    with localcontext(DECIMAL_CONTEXT):
        return dx.sqrt()


def decimal_ln(x: Any) -> Decimal:
    """Compute natural logarithm of x using Decimal context."""
    dx = to_decimal(x)
    if dx <= Decimal("0"):
        raise OutOfDomainError(f"Natural logarithm requires positive value, got {dx}")
    with localcontext(DECIMAL_CONTEXT):
        return dx.ln()


def decimal_exp(x: Any) -> Decimal:
    """Compute natural exponential e^x using Decimal context."""
    dx = to_decimal(x)
    with localcontext(DECIMAL_CONTEXT):
        return dx.exp()


def decimal_abs(x: Any) -> Decimal:
    """Compute absolute value of x."""
    dx = to_decimal(x)
    return abs(dx)

"""
metrology_core - High-precision exact decimal metrology reference engine.

Adheres to JCGM 100 (GUM), JCGM 106, ANSI/NCSL Z540.3, and ISO 14253-1.
"""

from .context import (
    DECIMAL_CONTEXT,
    MetrologyError,
    MetrologyValidationError,
    InvalidCovarianceError,
    NonPositiveSemiDefiniteError,
    OutOfDomainError,
    to_decimal,
    set_precision,
    get_precision,
    decimal_sqrt,
    decimal_ln,
    decimal_exp,
)

__version__ = "1.0.0"
__all__ = [
    "DECIMAL_CONTEXT",
    "MetrologyError",
    "MetrologyValidationError",
    "InvalidCovarianceError",
    "NonPositiveSemiDefiniteError",
    "OutOfDomainError",
    "to_decimal",
    "set_precision",
    "get_precision",
    "decimal_sqrt",
    "decimal_ln",
    "decimal_exp",
]

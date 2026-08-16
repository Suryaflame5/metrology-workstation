"""
Metrological Rounding and Resolution Matching (GUM Section 7.2.6 & ISO 80000-1).
"""

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
import math
from typing import Any, Tuple, NamedTuple, Optional
from ..context import (
    to_decimal,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)


class MetrologicalFormattedResult(NamedTuple):
    value: Decimal
    uncertainty: Decimal
    formatted_string: str
    decimal_places: int


def round_uncertainty(
    uncertainty: Any,
    sig_figs: int = 2,
    rounding_mode: str = ROUND_HALF_EVEN,
) -> Decimal:
    """
    Round an uncertainty value to a specified number of significant figures (default 2).
    
    Parameters:
        uncertainty: Uncertainty value (standard u or expanded U).
        sig_figs: Number of significant figures (typically 2, or 1).
        rounding_mode: Decimal rounding mode (default ROUND_HALF_EVEN / round-to-nearest-even).
        
    Returns:
        Exact Decimal rounded to sig_figs significant figures.
    """
    u = to_decimal(uncertainty)
    if u < Decimal("0"):
        raise MetrologyValidationError(f"Uncertainty cannot be negative: {u}")
    if u == Decimal("0"):
        return Decimal("0")
    if sig_figs < 1:
        raise MetrologyValidationError(f"Significant figures must be at least 1, got {sig_figs}")

    # Determine order of magnitude: floor(log10(u))
    # Using Decimal adjusted()
    magnitude = u.adjusted()
    # Number of decimal places needed: sig_figs - 1 - magnitude
    dec_places = sig_figs - 1 - magnitude

    if dec_places >= 0:
        quantizer = Decimal("1e-" + str(dec_places))
    else:
        quantizer = Decimal("1e+" + str(-dec_places))

    rounded_u = u.quantize(quantizer, rounding=rounding_mode)
    return rounded_u


def get_decimal_places(d: Decimal) -> int:
    """Get the number of fractional decimal places of a quantized Decimal."""
    # as_tuple().exponent gives negative of number of decimal places (e.g. -3 for 0.001)
    exp = d.as_tuple().exponent
    return -exp if exp < 0 else 0


def round_measurement_to_uncertainty(
    measurement_value: Any,
    rounded_uncertainty: Any,
    rounding_mode: str = ROUND_HALF_EVEN,
) -> Decimal:
    """
    Round the measurement result to match the last significant decimal digit of the uncertainty.
    
    Direct single-pass quantization is used to strictly avoid sequential rounding errors.
    
    Parameters:
        measurement_value: The unrounded measurement result or best estimate.
        rounded_uncertainty: The already-rounded uncertainty (with definite resolution).
        rounding_mode: Decimal rounding mode.
        
    Returns:
        Exact Decimal rounded to the exact resolution of the uncertainty.
    """
    y = to_decimal(measurement_value)
    u = to_decimal(rounded_uncertainty)

    if u == Decimal("0"):
        return y

    # Quantize to the exact exponent of rounded_uncertainty
    quantizer = Decimal("1e" + str(u.as_tuple().exponent))
    return y.quantize(quantizer, rounding=rounding_mode)


def format_metrological_result(
    measurement_value: Any,
    uncertainty: Any,
    sig_figs: int = 2,
    unit: str = "",
    rounding_mode: str = ROUND_HALF_EVEN,
) -> MetrologicalFormattedResult:
    """
    Format a measurement result and its uncertainty conforming to GUM 7.2.6:
    1. Uncertainty rounded to sig_figs (e.g. 0.01234 -> 0.012).
    2. Measurement value rounded to matching resolution (e.g. 12.34567 -> 12.346).
    3. Produces standard notation: '12.346 ± 0.012 [unit]'.
    """
    rounded_u = round_uncertainty(uncertainty, sig_figs=sig_figs, rounding_mode=rounding_mode)
    rounded_y = round_measurement_to_uncertainty(measurement_value, rounded_u, rounding_mode=rounding_mode)
    dec_places = get_decimal_places(rounded_u)

    unit_str = f" {unit}" if unit else ""
    formatted_str = f"({rounded_y} ± {rounded_u}){unit_str}"

    return MetrologicalFormattedResult(
        value=rounded_y,
        uncertainty=rounded_u,
        formatted_string=formatted_str,
        decimal_places=dec_places,
    )

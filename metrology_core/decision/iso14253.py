"""
ISO 14253-1 Decision Rules and Conformance Zones.
"""

from decimal import Decimal
from typing import Any, NamedTuple
from ..context import (
    to_decimal,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)


class ISO14253Result(NamedTuple):
    guardband_w: Decimal
    tolerance_lower: Decimal
    tolerance_upper: Decimal
    conformance_lower: Decimal
    conformance_upper: Decimal
    non_conformance_lower: Decimal
    non_conformance_upper: Decimal


def calculate_iso14253_limits(
    tolerance_upper: Any,
    tolerance_lower: Any,
    expanded_uncertainty: Any,
) -> ISO14253Result:
    """
    Calculate ISO 14253-1 decision zones with guardband w = U (expanded uncertainty).
    
    Zones:
    - Conformance Zone (Proving Conformance): [T_L + U, T_U - U]
    - Non-Conformance Zone (Proving Non-Conformance): (-inf, T_L - U] and [T_U + U, +inf)
    - Uncertainty / Undetermined Zone: (T_L - U, T_L + U) and (T_U - U, T_U + U)
    """
    t_u = to_decimal(tolerance_upper)
    t_l = to_decimal(tolerance_lower)
    u = to_decimal(expanded_uncertainty)

    if t_u <= t_l:
        raise MetrologyValidationError(f"T_U ({t_u}) must be > T_L ({t_l})")
    if u < Decimal("0"):
        raise MetrologyValidationError(f"Uncertainty cannot be negative: {u}")

    w = u
    conf_l = t_l + w
    conf_u = t_u - w
    non_conf_l = t_l - w
    non_conf_u = t_u + w

    return ISO14253Result(
        guardband_w=w,
        tolerance_lower=t_l,
        tolerance_upper=t_u,
        conformance_lower=conf_l,
        conformance_upper=conf_u,
        non_conformance_lower=non_conf_l,
        non_conformance_upper=non_conf_u,
    )


def evaluate_iso14253_conformance(
    measurement_value: Any,
    iso_result: ISO14253Result,
) -> str:
    """
    Evaluate conformity under ISO 14253-1:
    - 'CONFORMITY': inside [conformance_lower, conformance_upper]
    - 'NON_CONFORMITY': <= non_conformance_lower or >= non_conformance_upper
    - 'UNDETERMINED': inside the uncertainty zone around limits
    """
    y = to_decimal(measurement_value)
    r = iso_result

    if r.conformance_lower <= y <= r.conformance_upper:
        return "CONFORMITY"
    elif y <= r.non_conformance_lower or y >= r.non_conformance_upper:
        return "NON_CONFORMITY"
    else:
        return "UNDETERMINED"

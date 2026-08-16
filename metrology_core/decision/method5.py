"""
ANSI/NCSL Z540.3 Method 5 Guardbanding (Root-Sum-Square / RSS Guardband).
"""

from decimal import Decimal
from typing import Any, NamedTuple, Optional
from ..context import (
    to_decimal,
    decimal_sqrt,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)
from .tur import calculate_tur


class Method5Result(NamedTuple):
    tur: Decimal
    guardband_w: Decimal
    tolerance_lower: Decimal
    tolerance_upper: Decimal
    acceptance_lower: Decimal
    acceptance_upper: Decimal
    is_clamped_high_tur: bool


def calculate_method5_guardband(
    tolerance_upper: Any,
    tolerance_lower: Any,
    expanded_uncertainty: Any,
    target_tar: Any = Decimal("4.0"),
) -> Method5Result:
    """
    Calculate ANSI/NCSL Z540.3 Method 5 RSS Guardband.
    
    Formula:
        If TUR >= 4.0: w = 0 (high-TUR threshold)
        If TUR < 4.0: w = sqrt( max(0, U_95^2 - ((T_U - T_L) / (2 * TAR))^2) )
        
    Parameters:
        tolerance_upper: Upper tolerance limit T_U.
        tolerance_lower: Lower tolerance limit T_L.
        expanded_uncertainty: Expanded uncertainty U_95.
        target_tar: Target Test Accuracy Ratio (default 4.0).
        
    Returns:
        Method5Result with TUR, guardband w, acceptance limits.
    """
    t_u = to_decimal(tolerance_upper)
    t_l = to_decimal(tolerance_lower)
    u_95 = to_decimal(expanded_uncertainty)
    tar = to_decimal(target_tar)

    tur_assessment = calculate_tur(t_u, t_l, u_95)
    tur = tur_assessment.tur

    zero = Decimal("0")
    four = Decimal("4")

    if tur >= four:
        w = zero
        is_clamped = True
    else:
        is_clamped = False
        t_half = (t_u - t_l) / Decimal("2")
        allowed_u_at_target_tar = t_half / tar
        radicand = (u_95 ** 2) - (allowed_u_at_target_tar ** 2)
        if radicand <= zero:
            w = zero
        else:
            w = decimal_sqrt(radicand)

    a_l = t_l + w
    a_u = t_u - w

    return Method5Result(
        tur=tur,
        guardband_w=w,
        tolerance_lower=t_l,
        tolerance_upper=t_u,
        acceptance_lower=a_l,
        acceptance_upper=a_u,
        is_clamped_high_tur=is_clamped,
    )

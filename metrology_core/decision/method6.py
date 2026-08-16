"""
ANSI/NCSL Z540.3 Method 6 Guardbanding Engine (2% False Accept Risk Curve).
"""

from decimal import Decimal
from typing import Any, NamedTuple, Optional
from ..context import (
    to_decimal,
    decimal_ln,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)
from .tur import calculate_tur, TURAssessment


# Method 6 empirical curve coefficients
# M(TUR) = A - B * ln(TUR), with root at TUR = 4.5917675 and M(2) = 0.281645
DEFAULT_METHOD6_A = Decimal("0.5165351056525997637")
DEFAULT_METHOD6_B = Decimal("0.3388748057211158941")
DEFAULT_METHOD6_ROOT = Decimal("4.5917675")


class Method6Result(NamedTuple):
    tur: Decimal
    multiplier_M: Decimal
    guardband_w: Decimal
    tolerance_lower: Decimal
    tolerance_upper: Decimal
    acceptance_lower: Decimal
    acceptance_upper: Decimal
    is_clamped_high_tur: bool
    is_clamped_non_negative: bool
    is_acceptance_zone_closed: bool
    decision_zone_message: str


def calculate_method6_guardband(
    tolerance_upper: Any,
    tolerance_lower: Any,
    expanded_uncertainty: Any,
    coeff_a: Optional[Decimal] = None,
    coeff_b: Optional[Decimal] = None,
    clamp_to_half_width: bool = True,
) -> Method6Result:
    """
    Calculate ANSI/NCSL Z540.3 Method 6 Guardband with exact Decimal arithmetic and strict boundary handling.
    
    Rules:
    1. If TUR >= 4.0: Guardband is clamped to 0 (M = 0, w = 0).
    2. If TUR < 4.0: Multiplier M = A - B * ln(TUR).
    3. Multiplier M is clamped to >= 0 (never negative).
    4. Guardband w = M * U_95.
    5. Acceptance Limits: A_L = T_L + w, A_U = T_U - w.
    6. If w > (T_U - T_L)/2 (acceptance zone closes), w is clamped to half-width and acceptance zone is empty/point.
    
    Parameters:
        tolerance_upper: Upper tolerance limit T_U.
        tolerance_lower: Lower tolerance limit T_L.
        expanded_uncertainty: Expanded uncertainty U_95.
        coeff_a: Optional custom coefficient A (default 0.516535...).
        coeff_b: Optional custom coefficient B (default 0.338875...).
        clamp_to_half_width: Clamp guardband to tolerance half-width if w exceeds half-width (default True).
        
    Returns:
        Method6Result containing TUR, M, w, acceptance limits, and clamp statuses.
    """
    t_u = to_decimal(tolerance_upper)
    t_l = to_decimal(tolerance_lower)
    u_95 = to_decimal(expanded_uncertainty)

    tur_assessment = calculate_tur(t_u, t_l, u_95)
    tur = tur_assessment.tur

    a = coeff_a if coeff_a is not None else DEFAULT_METHOD6_A
    b = coeff_b if coeff_b is not None else DEFAULT_METHOD6_B

    zero = Decimal("0")
    two = Decimal("2")
    four = Decimal("4")
    t_half = (t_u - t_l) / two

    is_clamped_high_tur = False
    is_clamped_non_negative = False
    is_acceptance_zone_closed = False

    if tur >= four:
        # High TUR boundary clamp: TUR >= 4 requires no guardband in Z540.3
        m = zero
        w = zero
        is_clamped_high_tur = True
        msg = f"TUR = {tur} >= 4.0: Method 6 active curve bypassed. Zero guardband applied."
    else:
        # Active Method 6 curve
        raw_m = a - (b * decimal_ln(tur))
        if raw_m < zero:
            m = zero
            w = zero
            is_clamped_non_negative = True
            msg = f"TUR = {tur}: Raw multiplier M was negative ({raw_m}), clamped to 0."
        else:
            m = raw_m
            w = m * u_95
            if w > t_half:
                is_acceptance_zone_closed = True
                if clamp_to_half_width:
                    w = t_half
                msg = (
                    f"TUR = {tur}: Guardband w ({m * u_95:.6f}) exceeds tolerance half-width ({t_half:.6f}). "
                    f"Acceptance zone is closed (100% rejection required for <= 2% PFA)."
                )
            else:
                msg = f"TUR = {tur}: Method 6 active multiplier M = {m:.6f}, guardband w = {w:.8f}."

    a_l = t_l + w
    a_u = t_u - w

    if a_l > a_u and not clamp_to_half_width:
        raise MetrologyValidationError(
            f"Calculated acceptance limits are inverted (A_L={a_l} > A_U={a_u}). "
            f"Measurement uncertainty exceeds capability for this tolerance."
        )

    return Method6Result(
        tur=tur,
        multiplier_M=m,
        guardband_w=w,
        tolerance_lower=t_l,
        tolerance_upper=t_u,
        acceptance_lower=a_l,
        acceptance_upper=a_u,
        is_clamped_high_tur=is_clamped_high_tur,
        is_clamped_non_negative=is_clamped_non_negative,
        is_acceptance_zone_closed=is_acceptance_zone_closed,
        decision_zone_message=msg,
    )


def evaluate_method6_conformance(
    measurement_value: Any,
    method6_result: Method6Result,
) -> str:
    """
    Evaluate conformity of a measured value under Method 6 acceptance limits.
    
    Returns:
        'ACCEPT' (within [A_L, A_U])
        'GUARD_BAND' (between tolerance limit and acceptance limit)
        'REJECT' (outside tolerance limits [T_L, T_U])
    """
    y = to_decimal(measurement_value)
    r = method6_result

    if r.acceptance_lower <= y <= r.acceptance_upper:
        return "ACCEPT"
    elif r.tolerance_lower <= y <= r.tolerance_upper:
        return "GUARD_BAND"
    else:
        return "REJECT"

"""
Test Uncertainty Ratio (TUR) Calculation and Domain Validation.
"""

from decimal import Decimal
from typing import Any, NamedTuple, Optional
from ..context import (
    to_decimal,
    MetrologyValidationError,
    DECIMAL_CONTEXT,
)


class TURAssessment(NamedTuple):
    tur: Decimal
    tolerance_width: Decimal
    expanded_uncertainty: Decimal
    is_high_tur: bool          # TUR >= 4.0
    is_adequate: bool          # TUR >= 1.0
    recommendation: str


def calculate_tur(
    tolerance_upper: Any,
    tolerance_lower: Any,
    expanded_uncertainty: Any,
) -> TURAssessment:
    """
    Calculate Test Uncertainty Ratio (TUR) using exact Decimal arithmetic:
        TUR = (T_U - T_L) / (2 * U_95)
        
    Parameters:
        tolerance_upper: Upper tolerance limit T_U.
        tolerance_lower: Lower tolerance limit T_L.
        expanded_uncertainty: Expanded measurement uncertainty U_95 (k=2 or 95% confidence).
        
    Returns:
        TURAssessment containing exact TUR, tolerance width, and compliance status.
        
    Raises:
        MetrologyValidationError: If T_U <= T_L or U_95 <= 0.
    """
    t_u = to_decimal(tolerance_upper)
    t_l = to_decimal(tolerance_lower)
    u_95 = to_decimal(expanded_uncertainty)

    if t_u <= t_l:
        raise MetrologyValidationError(
            f"Upper tolerance limit T_U ({t_u}) must be strictly greater than lower tolerance limit T_L ({t_l})"
        )

    if u_95 < Decimal("0"):
        raise MetrologyValidationError(
            f"Expanded uncertainty U_95 cannot be negative, got {u_95}"
        )

    tol_width = t_u - t_l

    if u_95 == Decimal("0"):
        tur = Decimal("Infinity")
        is_high_tur = True
        is_adequate = True
        rec = "U_95 = 0 (Ideal measurement): TUR -> Infinity. Zero guardband applied."
        return TURAssessment(
            tur=tur,
            tolerance_width=tol_width,
            expanded_uncertainty=u_95,
            is_high_tur=is_high_tur,
            is_adequate=is_adequate,
            recommendation=rec,
        )

    denominator = Decimal("2") * u_95
    tur = tol_width / denominator

    is_high_tur = tur >= Decimal("4")
    is_adequate = tur >= Decimal("1")

    if is_high_tur:
        rec = "TUR >= 4.0: Standard compliance achieved. Zero guardband recommended (ANSI/NCSL Z540.3)."
    elif is_adequate:
        rec = f"TUR = {tur}: Active guardband required to control False Accept Risk (Method 5 or Method 6)."
    else:
        rec = f"TUR = {tur} < 1.0: Inadequate measurement capability. Test uncertainty exceeds tolerance."

    return TURAssessment(
        tur=tur,
        tolerance_width=tol_width,
        expanded_uncertainty=u_95,
        is_high_tur=is_high_tur,
        is_adequate=is_adequate,
        recommendation=rec,
    )

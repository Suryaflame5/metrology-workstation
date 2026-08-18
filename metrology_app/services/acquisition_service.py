"""
V5 Measurement Acquisition & Statistical Dispersion Service.
"""

from decimal import Decimal
import math
from typing import List, Dict, Any, Tuple
from metrology_core.context import to_decimal


def analyze_measurement_series(
    raw_readings: List[float],
) -> Tuple[float, float, float, List[float]]:
    """
    Computes sample mean, sample standard deviation (Bessel-corrected),
    Type A repeatability standard uncertainty (s / sqrt(n)), and identifies outliers.
    """
    if not raw_readings:
        return 0.0, 0.0, 0.0, []

    n = len(raw_readings)
    if n == 1:
        return raw_readings[0], 0.0, 0.0, []

    # 50-digit exact decimal summation
    dec_readings = [to_decimal(r) for r in raw_readings]
    mean_dec = sum(dec_readings) / Decimal(str(n))

    # Variance
    var_sum = sum((r - mean_dec) ** 2 for r in dec_readings)
    s_sq = var_sum / Decimal(str(n - 1))
    s_dec = s_sq.sqrt()
    u_rep = s_dec / Decimal(str(math.sqrt(n)))

    # Outlier detection (3-sigma criterion)
    outliers: List[float] = []
    threshold = 3.0 * float(s_dec)
    mean_float = float(mean_dec)

    if threshold > 0:
        for r in raw_readings:
            if abs(r - mean_float) > threshold:
                outliers.append(r)

    return float(mean_dec), float(s_dec), float(u_rep), outliers

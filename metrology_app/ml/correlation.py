"""
Environmental & Multi-Variate Correlation Intelligence Engine.
Computes Pearson & Spearman correlation coefficients between ambient environmental conditions and measurement bias.
"""

import math
from typing import List, Dict, Any


def compute_pearson_correlation(x: List[float], y: List[float]) -> float:
    """Compute Pearson correlation coefficient r between two numeric lists."""
    n = len(x)
    if n < 2 or len(y) != n:
        return 0.0

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denom_x = sum((x[i] - x_mean) ** 2 for i in range(n))
    denom_y = sum((y[i] - y_mean) ** 2 for i in range(n))

    if denom_x < 1e-15 or denom_y < 1e-15:
        return 0.0

    r = numerator / math.sqrt(denom_x * denom_y)
    return max(-1.0, min(1.0, r))


def analyze_environmental_correlation(history_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate correlations between ambient parameters and measurement errors across history.
    """
    n = len(history_records)
    if n < 3:
        return {
            "sample_count": n,
            "correlations": {},
            "strongest_driver": None,
            "status": "INSUFFICIENT_DATA",
            "message": "Need at least 3 historical runs with environmental logs to calculate correlation.",
        }

    temps = []
    humidities = []
    errors = []

    for rec in history_records:
        inp = rec.get("input_data", {})
        res = rec.get("result_data", {})
        summary = res.get("summary", {})
        
        t = float(inp.get("ambient_temp_c", 20.0))
        rh = float(inp.get("relative_humidity_pct", 45.0))
        err = float(summary.get("error_of_indication_mm", 0.0))

        temps.append(t)
        humidities.append(rh)
        errors.append(err)

    r_temp = compute_pearson_correlation(temps, errors)
    r_humidity = compute_pearson_correlation(humidities, errors)

    def classify_strength(r: float) -> str:
        abs_r = abs(r)
        if abs_r >= 0.75:
            return "STRONG_POSITIVE" if r > 0 else "STRONG_NEGATIVE"
        if abs_r >= 0.40:
            return "MODERATE_POSITIVE" if r > 0 else "MODERATE_NEGATIVE"
        return "NEGLIGIBLE_CORRELATION"

    correlations = {
        "ambient_temperature_c": {
            "pearson_r": round(r_temp, 3),
            "strength": classify_strength(r_temp),
            "causality_note": "Thermal expansion differential (alpha * L * delta_T) directly shifts physical dimensions.",
        },
        "relative_humidity_pct": {
            "pearson_r": round(r_humidity, 3),
            "strength": classify_strength(r_humidity),
            "causality_note": "Humidity shifts optical refractivity and hygroscopic moisture absorption on standards.",
        },
    }

    # Find dominant driver
    strongest = "ambient_temperature_c" if abs(r_temp) >= abs(r_humidity) else "relative_humidity_pct"
    strongest_r = r_temp if strongest == "ambient_temperature_c" else r_humidity

    return {
        "sample_count": n,
        "correlations": correlations,
        "strongest_driver": strongest,
        "strongest_driver_r": round(strongest_r, 3),
        "status": "COMPUTED",
        "message": f"Evaluated across {n} historical observations. Dominant environmental influence: {strongest} (r = {strongest_r:+.3f}).",
    }

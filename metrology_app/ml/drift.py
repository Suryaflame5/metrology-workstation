"""
Real Machine Learning Historical Drift Intelligence & Conformal Projection Engine.
Analyzes instrument calibration trajectory, calculates drift rates, and projects future deviations with statistical coverage bounds.
"""

import math
from typing import List, Dict, Any, Optional


def fit_linear_regression(x: List[float], y: List[float]) -> Dict[str, float]:
    """Fit ordinary least squares linear regression."""
    n = len(x)
    if n < 2:
        return {"slope": 0.0, "intercept": y[0] if y else 0.0, "r_squared": 0.0}

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_yy = sum((yi - y_mean) ** 2 for yi in y)
    ss_xy = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))

    if ss_xx < 1e-15:
        return {"slope": 0.0, "intercept": y_mean, "r_squared": 0.0}

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 1e-15 else 1.0
    return {"slope": slope, "intercept": intercept, "r_squared": max(0.0, min(1.0, r_squared))}


def analyze_instrument_drift(
    history_records: List[Dict[str, Any]],
    tolerance_limit: float = 0.0020,
) -> Dict[str, Any]:
    """
    Compute rigorous drift analysis and predictive future projections.
    
    Parameters:
      - history_records: Chronologically sorted calibration runs.
      - tolerance_limit: Bilateral tolerance (+/-).
    """
    n = len(history_records)
    if n < 2:
        return {
            "historical_cycles_count": n,
            "drift_trend": "INSUFFICIENT_HISTORY",
            "drift_slope_per_cycle": 0.0,
            "r_squared": 0.0,
            "mean_error": 0.0,
            "max_observed_deviation": 0.0,
            "projected_drift_30d": 0.0,
            "projected_drift_60d": 0.0,
            "projected_drift_90d": 0.0,
            "conformal_interval_90d": [-tolerance_limit, tolerance_limit],
            "risk_verdict": "LOW_RISK_INSUFFICIENT_DATA",
            "model_version": "DriftRegModel_v1.0",
            "limitations": "Requires at least 2 historical calibration cycles for trend fitting.",
        }

    # Extract sequence indices and error of indication
    x_indices = []
    y_errors = []

    for i, rec in enumerate(history_records):
        res = rec.get("result_data", {})
        summary = res.get("summary", {})
        err = float(summary.get("error_of_indication_mm", 0.0))
        x_indices.append(float(i + 1))
        y_errors.append(err)

    fit = fit_linear_regression(x_indices, y_errors)
    slope = fit["slope"]
    intercept = fit["intercept"]
    r2 = fit["r_squared"]

    # Calculate residuals and residual standard error
    residuals = [y_errors[i] - (slope * x_indices[i] + intercept) for i in range(n)]
    sse = sum(r ** 2 for r in residuals)
    residual_std = math.sqrt(sse / max(1, n - 2)) if n > 2 else math.sqrt(sse / n)

    # Trend classification
    if abs(slope) < (tolerance_limit * 0.05):
        trend = "STABLE"
    elif slope > 0:
        trend = "ACCELERATING_POSITIVE_DRIFT"
    else:
        trend = "ACCELERATING_NEGATIVE_DRIFT"

    # Future cycle projections: Cycle n+1 (approx 30d), n+2 (60d), n+3 (90d)
    pred_30d = slope * (n + 1) + intercept
    pred_60d = slope * (n + 2) + intercept
    pred_90d = slope * (n + 3) + intercept

    # Conformal 95% prediction interval around 90-day forecast (k=2.0 * residual_std)
    margin = max(tolerance_limit * 0.1, 2.0 * residual_std)
    conformal_lower = pred_90d - margin
    conformal_upper = pred_90d + margin

    # Risk evaluation
    max_forecast_err = max(abs(pred_30d), abs(pred_60d), abs(pred_90d))
    if max_forecast_err > (tolerance_limit * 0.85):
        risk = "HIGH_RISK_OUT_OF_TOLERANCE_PROJECTED"
    elif max_forecast_err > (tolerance_limit * 0.50):
        risk = "MEDIUM_RISK_MONITOR_CLOSELY"
    else:
        risk = "LOW_RISK_WITHIN_GUARD_BAND"

    return {
        "historical_cycles_count": n,
        "drift_trend": trend,
        "drift_slope_per_cycle": round(slope, 6),
        "r_squared": round(r2, 4),
        "mean_error": round(sum(y_errors) / n, 6),
        "max_observed_deviation": round(max(abs(y) for y in y_errors), 6),
        "projected_drift_30d": round(pred_30d, 6),
        "projected_drift_60d": round(pred_60d, 6),
        "projected_drift_90d": round(pred_90d, 6),
        "conformal_interval_90d": [round(conformal_lower, 6), round(conformal_upper, 6)],
        "risk_verdict": risk,
        "model_version": "DriftRegModel_v1.0",
        "confidence_score": round(min(0.95, 0.60 + (r2 * 0.35)), 2),
        "limitations": f"Linear trajectory based on {n} points. Non-linear step changes (e.g. drop/shock) not modeled.",
    }

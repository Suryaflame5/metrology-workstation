"""
Composite Multi-Factor Metrological Risk Engine.
Computes deterministic 0-100 Risk Score and 30/60/90-day risk progression based on transparent engineering weights.
"""

from typing import List, Dict, Any


def compute_composite_risk_score(
    history_records: List[Dict[str, Any]],
    current_tur: float = 4.0,
    tolerance_limit: float = 0.0020,
    days_since_last_cal: int = 180,
    nominal_interval_days: int = 365,
) -> Dict[str, Any]:
    """
    Compute evidence-based composite risk score and future trajectory.
    """
    n = len(history_records)

    # 1. Historical Failure Rate (Weight: 30%)
    failures = sum(1 for r in history_records if r.get("conformity_verdict") == "FAIL")
    guardbands = sum(1 for r in history_records if r.get("conformity_verdict") == "GUARD_BAND")
    fail_rate = (failures + 0.5 * guardbands) / max(1, n)
    fail_score = min(100.0, fail_rate * 150.0)

    # 2. TUR Margin Deficit (Weight: 25%)
    # Target TUR >= 4.0 (score 0), TUR <= 1.0 (score 100)
    if current_tur >= 4.0:
        tur_score = 0.0
    elif current_tur <= 1.0:
        tur_score = 100.0
    else:
        tur_score = (4.0 - current_tur) / 3.0 * 100.0

    # 3. Drift Velocity Factor (Weight: 25%)
    if n >= 2:
        errors = [float(r.get("result_data", {}).get("summary", {}).get("error_of_indication_mm", 0.0)) for r in history_records]
        max_err = max(abs(e) for e in errors)
        drift_ratio = max_err / max(1e-6, tolerance_limit)
        drift_score = min(100.0, drift_ratio * 100.0)
    else:
        drift_score = 20.0

    # 4. Calibration Interval Aging (Weight: 20%)
    age_ratio = days_since_last_cal / max(1, nominal_interval_days)
    age_score = min(100.0, age_ratio * 70.0) if age_ratio <= 1.0 else min(100.0, 70.0 + (age_ratio - 1.0) * 100.0)

    # Composite Risk Calculation (0 - 100)
    composite = (
        0.30 * fail_score +
        0.25 * tur_score +
        0.25 * drift_score +
        0.20 * age_score
    )

    # Forward Risk Trajectory: 30d, 60d, 90d
    risk_30d = min(100.0, composite + (30 / nominal_interval_days) * 10.0)
    risk_60d = min(100.0, composite + (60 / nominal_interval_days) * 20.0)
    risk_90d = min(100.0, composite + (90 / nominal_interval_days) * 35.0)

    def classify_risk(score: float) -> str:
        if score >= 70.0:
            return "HIGH_RISK"
        if score >= 35.0:
            return "MEDIUM_RISK"
        return "LOW_RISK"

    return {
        "current_risk_score": round(composite, 1),
        "current_risk_level": classify_risk(composite),
        "projected_risk_30d": round(risk_30d, 1),
        "projected_risk_60d": round(risk_60d, 1),
        "projected_risk_90d": round(risk_90d, 1),
        "contributing_factors": {
            "historical_failure_factor": {"score": round(fail_score, 1), "weight": "30%", "raw_failures": failures},
            "tur_margin_factor": {"score": round(tur_score, 1), "weight": "25%", "current_tur": round(current_tur, 2)},
            "drift_velocity_factor": {"score": round(drift_score, 1), "weight": "25%"},
            "calibration_aging_factor": {"score": round(age_score, 1), "weight": "20%", "days_elapsed": days_since_last_cal},
        },
        "reasoning": f"Current risk level is {classify_risk(composite)} ({composite:.1f}/100). TUR margin is {current_tur:.2f}, with {failures} historical OOT events.",
    }

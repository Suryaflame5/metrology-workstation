"""
Fleet Intelligence & Cross-Instrument Cohort Anomaly Engine.
Evaluates multi-instrument health, detects cohort environmental biases, and schedules predictive maintenance.
"""

from typing import List, Dict, Any, Optional
from ..db import list_instruments, list_calculations
from ..ml.drift import analyze_instrument_drift
from ..ml.risk import compute_composite_risk_score


def generate_fleet_intelligence(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate fleet-wide health scores, cohort anomaly analysis, and predictive maintenance queue.
    """
    instruments = list_instruments(db_path=db_path)
    all_calcs = list_calculations(limit=100, db_path=db_path)

    if not instruments:
        return {
            "total_fleet_instruments": 0,
            "fleet_health_score": 100.0,
            "instruments_at_risk_count": 0,
            "cohort_anomalies": [],
            "maintenance_queue": [],
            "status": "FLEET_EMPTY",
        }

    fleet_assessments = []
    total_risk = 0.0

    for inst in instruments:
        inst_id = inst.get("id")
        matching_calcs = [c for c in all_calcs if c.get("instrument_id") == inst_id or inst.get("model", "").lower() in c.get("instrument_name", "").lower()]
        
        drift_res = analyze_instrument_drift(matching_calcs)
        risk_res = compute_composite_risk_score(matching_calcs, current_tur=3.5, tolerance_limit=0.0020)
        
        risk_score = risk_res.get("current_risk_score", 15.0)
        total_risk += risk_score

        fleet_assessments.append({
            "instrument_id": inst_id,
            "name": f"{inst.get('manufacturer', '')} {inst.get('model', '')}",
            "serial_number": inst.get("serial_number", ""),
            "location": inst.get("location", "Main Lab"),
            "risk_score": risk_score,
            "risk_level": risk_res.get("current_risk_level", "LOW_RISK"),
            "drift_trend": drift_res.get("drift_trend", "STABLE"),
            "drift_slope": drift_res.get("drift_slope_per_cycle", 0.0),
            "calibrations_count": len(matching_calcs),
            "next_due": inst.get("next_calibration_due", "2027-08-18"),
        })

    avg_risk = total_risk / max(1, len(instruments))
    fleet_health = max(0.0, min(100.0, 100.0 - avg_risk))

    # Cohort Anomaly Analysis (Grouping by location)
    location_groups: Dict[str, List[Dict[str, Any]]] = {}
    for a in fleet_assessments:
        loc = a["location"]
        if loc not in location_groups:
            location_groups[loc] = []
        location_groups[loc].append(a)

    cohort_anomalies = []
    for loc, items in location_groups.items():
        if len(items) >= 2:
            positive_drifts = sum(1 for item in items if "POSITIVE" in item["drift_trend"])
            if positive_drifts >= 2:
                cohort_anomalies.append({
                    "cohort_type": "COMMON_LOCATION_THERMAL_DRIFT",
                    "location": loc,
                    "affected_instruments_count": len(items),
                    "finding": f"Multiple ({positive_drifts}) instruments in '{loc}' exhibit simultaneous positive drift.",
                    "hypothesis": "Common ambient thermal shift or uncalibrated reference standard in this bay.",
                    "recommended_action": f"Inspect environmental temperature stability and reference gauge blocks at {loc}.",
                })

    # Prioritize maintenance queue by risk descending
    maintenance_queue = sorted(fleet_assessments, key=lambda x: x["risk_score"], reverse=True)

    return {
        "total_fleet_instruments": len(instruments),
        "fleet_health_score": round(fleet_health, 1),
        "instruments_at_risk_count": sum(1 for a in fleet_assessments if a["risk_level"] != "LOW_RISK"),
        "fleet_summary": fleet_assessments,
        "cohort_anomalies": cohort_anomalies,
        "maintenance_queue": maintenance_queue,
        "status": "COMPUTED",
    }

"""
Industrial Loss Quantification & Financial Exposure Engine.
Translates dimensional deviations, scrap counts, rework cycles, machine drift,
and inspection delays into quantified financial losses and recovery opportunities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math
from ..db import (
    get_cost_configuration,
    list_inspection_jobs,
    list_loss_events,
    save_loss_event,
    DB_PATH,
)


def calculate_inspection_loss_exposure(
    job_id: str,
    total_parts: int,
    passed_parts: int,
    failed_parts: int,
    scrap_count: int,
    rework_count: int,
    inspection_hours: float = 0.5,
    machine_downtime_hours: float = 0.0,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Calculate full financial loss breakdown for an inspection batch.
    Uses factory cost configuration (Scrap cost, Rework cost, Labor, Machine downtime).
    """
    cost_cfg = get_cost_configuration(db_path=db_path)
    curr = cost_cfg.get("currency", "₹")

    part_cost = float(cost_cfg.get("default_part_cost", 1200.0))
    scrap_unit_cost = float(cost_cfg.get("scrap_cost_per_part", part_cost))
    rework_unit_cost = float(cost_cfg.get("rework_cost_per_part", 350.0))
    labor_rate = float(cost_cfg.get("inspection_labor_cost_per_hr", 400.0))
    downtime_rate = float(cost_cfg.get("downtime_cost_per_hr", 1500.0))

    # Calculations
    scrap_loss = scrap_count * scrap_unit_cost
    rework_loss = rework_count * rework_unit_cost
    inspection_labor_cost = inspection_hours * labor_rate
    downtime_loss = machine_downtime_hours * downtime_rate

    total_loss = scrap_loss + rework_loss + inspection_labor_cost + downtime_loss

    # Monthly projected exposure if drift is uncorrected (assuming 20 batches/month)
    monthly_projected_loss = (scrap_loss + rework_loss) * 20.0

    return {
        "job_id": job_id,
        "currency": curr,
        "total_parts": total_parts,
        "passed_parts": passed_parts,
        "failed_parts": failed_parts,
        "scrap_count": scrap_count,
        "rework_count": rework_count,
        "breakdown": {
            "scrap_loss": round(scrap_loss, 2),
            "rework_loss": round(rework_loss, 2),
            "inspection_labor_cost": round(inspection_labor_cost, 2),
            "downtime_loss": round(downtime_loss, 2),
        },
        "total_loss": round(total_loss, 2),
        "monthly_projected_loss": round(monthly_projected_loss, 2),
        "assumptions": {
            "part_cost": scrap_unit_cost,
            "rework_cost_per_part": rework_unit_cost,
            "labor_hourly_rate": labor_rate,
            "downtime_hourly_rate": downtime_rate,
            "projected_monthly_batches": 20,
        },
    }


def evaluate_machine_drift_loss(
    machine_code: str,
    part_name: str,
    measurements: List[float],
    nominal: float,
    tol_upper: float,
    tol_lower: float,
    db_path: str = DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Detect tool wear or thermal machine drift and calculate potential exposure
    before parts become scrap.
    """
    if len(measurements) < 10:
        return None

    cost_cfg = get_cost_configuration(db_path=db_path)
    curr = cost_cfg.get("currency", "₹")
    part_cost = float(cost_cfg.get("scrap_cost_per_part", 1200.0))

    # Evaluate trajectory (first third vs last third)
    split = len(measurements) // 3
    early_mean = sum(measurements[:split]) / split
    late_mean = sum(measurements[-split:]) / split
    drift_delta = late_mean - early_mean

    # Check % of tolerance consumed by drift
    tol_span = tol_upper - tol_lower
    pct_drift_of_tolerance = (abs(drift_delta) / tol_span) * 100.0 if tol_span > 0 else 0.0

    # Count points approaching upper/lower guardband (>= 75% tolerance consumed)
    high_risk_count = 0
    for m in measurements:
        dev = m - nominal
        consumed = (abs(dev) / (tol_upper if dev >= 0 else abs(tol_lower))) * 100.0
        if consumed >= 75.0:
            high_risk_count += 1

    if pct_drift_of_tolerance >= 25.0 or high_risk_count >= 3:
        # Potential scrap exposure for an upcoming production run of 100 parts
        potential_affected_parts = max(high_risk_count * 5, 30)
        exposure_amount = potential_affected_parts * part_cost

        return {
            "machine_code": machine_code,
            "part_name": part_name,
            "currency": curr,
            "drift_delta": round(drift_delta, 5),
            "pct_drift_of_tolerance": round(pct_drift_of_tolerance, 1),
            "high_risk_parts_detected": high_risk_count,
            "potential_scrap_exposure": round(exposure_amount, 2),
            "severity": "CRITICAL" if pct_drift_of_tolerance >= 70.0 else "WARNING",
            "recommended_action": f"Inspect tooling on {machine_code}, check thermal offsets, and reset cutter wear compensation.",
            "assumptions": f"Based on {potential_affected_parts} projected scrap parts at {curr}{part_cost:.0f}/part.",
        }
    return None


def get_factory_financial_summary(db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Aggregate all active loss events, scrap costs, and recovery opportunities
    across the entire factory floor.
    """
    cost_cfg = get_cost_configuration(db_path=db_path)
    curr = cost_cfg.get("currency", "₹")
    active_losses = list_loss_events(status="ACTIVE", db_path=db_path)

    total_exposure = sum(float(l.get("estimated_loss_amount", 0.0)) for l in active_losses)
    scrap_exposure = sum(
        float(l.get("estimated_loss_amount", 0.0))
        for l in active_losses
        if l.get("loss_category") == "EXCESSIVE_SCRAP" or "SCRAP" in l.get("loss_category", "")
    )
    rework_exposure = sum(
        float(l.get("estimated_loss_amount", 0.0))
        for l in active_losses
        if l.get("loss_category") == "REWORK_BURDEN" or "REWORK" in l.get("loss_category", "")
    )
    drift_exposure = sum(
        float(l.get("estimated_loss_amount", 0.0))
        for l in active_losses
        if "DRIFT" in l.get("loss_category", "") or "TOOL" in l.get("loss_category", "")
    )

    # Recovery potential: estimated 70-80% recoverable with corrective action
    recovery_opportunity = total_exposure * 0.75

    return {
        "currency": curr,
        "total_loss_exposure": round(total_exposure, 2),
        "recovery_opportunity": round(recovery_opportunity, 2),
        "active_loss_events_count": len(active_losses),
        "breakdown_by_category": {
            "scrap_loss": round(scrap_exposure, 2),
            "rework_loss": round(rework_exposure, 2),
            "machine_drift_exposure": round(drift_exposure, 2),
            "other_losses": round(total_exposure - (scrap_exposure + rework_exposure + drift_exposure), 2),
        },
        "top_loss_events": active_losses[:5],
    }

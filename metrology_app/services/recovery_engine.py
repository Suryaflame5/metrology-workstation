"""
Before / After Recovery Proof & ROI Verification Engine.
Compares baseline defect/scrap rates with post-action verification batches
to establish quantifiable recovered value and commercial return on investment.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ..db import (
    get_inspection_job,
    get_cost_configuration,
    save_recovery_event,
    list_recovery_events,
    DB_PATH,
)


def compare_before_after_recovery(
    baseline_job_id: str,
    verification_job_id: str,
    action_id: Optional[str] = None,
    loss_event_id: Optional[str] = None,
    verified_by: str = "Quality Assurance Lead",
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Execute rigorous Before vs After comparison between baseline and post-correction jobs.
    Calculates scrap reduction, defect rate delta, and monthly verified recovered financial value.
    """
    base_job = get_inspection_job(baseline_job_id, db_path=db_path)
    post_job = get_inspection_job(verification_job_id, db_path=db_path)

    if not base_job or not post_job:
        raise ValueError(f"One or both jobs not found ('{baseline_job_id}', '{verification_job_id}').")

    cost_cfg = get_cost_configuration(db_path=db_path)
    curr = cost_cfg.get("currency", "₹")
    scrap_cost_unit = float(cost_cfg.get("scrap_cost_per_part", 1200.0))
    rework_cost_unit = float(cost_cfg.get("rework_cost_per_part", 350.0))

    # Baseline metrics
    base_total = max(int(base_job.get("total_parts", 100)), 1)
    base_scrap = int(base_job.get("scrap_count", 0))
    base_rework = int(base_job.get("rework_count", 0))
    base_failed = int(base_job.get("failed_parts", base_scrap + base_rework))
    base_defect_rate_pct = (base_failed / base_total) * 100.0
    base_loss_per_batch = (base_scrap * scrap_cost_unit) + (base_rework * rework_cost_unit)

    # Post-action metrics
    post_total = max(int(post_job.get("total_parts", 100)), 1)
    post_scrap = int(post_job.get("scrap_count", 0))
    post_rework = int(post_job.get("rework_count", 0))
    post_failed = int(post_job.get("failed_parts", post_scrap + post_rework))
    post_defect_rate_pct = (post_failed / post_total) * 100.0
    post_loss_per_batch = (post_scrap * scrap_cost_unit) + (post_rework * rework_cost_unit)

    # Recovery Calculations
    defect_rate_reduction_pct = max(base_defect_rate_pct - post_defect_rate_pct, 0.0)
    batch_savings = max(base_loss_per_batch - post_loss_per_batch, 0.0)
    monthly_recovered_value = batch_savings * 20.0  # 20 production batches per month
    recovery_efficiency_pct = (batch_savings / base_loss_per_batch * 100.0) if base_loss_per_batch > 0 else 100.0

    # Evidence payload
    evidence_payload = {
        "baseline_job": {
            "id": baseline_job_id,
            "job_number": base_job.get("job_number"),
            "total_parts": base_total,
            "failed_parts": base_failed,
            "scrap_count": base_scrap,
            "defect_rate_pct": round(base_defect_rate_pct, 2),
            "loss_per_batch": round(base_loss_per_batch, 2),
        },
        "post_correction_job": {
            "id": verification_job_id,
            "job_number": post_job.get("job_number"),
            "total_parts": post_total,
            "failed_parts": post_failed,
            "scrap_count": post_scrap,
            "defect_rate_pct": round(post_defect_rate_pct, 2),
            "loss_per_batch": round(post_loss_per_batch, 2),
        },
        "defect_rate_reduction_pct": round(defect_rate_reduction_pct, 2),
        "batch_savings": round(batch_savings, 2),
        "monthly_recovered_value": round(monthly_recovered_value, 2),
        "recovery_efficiency_pct": round(recovery_efficiency_pct, 1),
    }

    # Record persistent recovery proof
    rec_id = save_recovery_event(
        {
            "loss_event_id": loss_event_id,
            "action_id": action_id,
            "baseline_period": f"Job {base_job.get('job_number')}",
            "baseline_loss_rate": base_loss_per_batch,
            "post_action_loss_rate": post_loss_per_batch,
            "actual_recovered_amount": monthly_recovered_value,
            "recovery_percentage": recovery_efficiency_pct,
            "verification_evidence": evidence_payload,
            "verified_by": verified_by,
        },
        db_path=db_path,
    )

    return {
        "recovery_event_id": rec_id,
        "status": "VERIFIED_ROI_PROOF",
        "currency": curr,
        "comparison": evidence_payload,
        "summary_statement": (
            f"Defect rate reduced by {defect_rate_reduction_pct:.1f}% (from {base_defect_rate_pct:.1f}% down to {post_defect_rate_pct:.1f}%). "
            f"Verified monthly recovered value: {curr}{monthly_recovered_value:,.0f}/month."
        ),
    }

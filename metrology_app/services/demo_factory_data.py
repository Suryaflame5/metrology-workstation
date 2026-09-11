"""
Sample Factory Dataset & End-to-End Acceptance Scenario Seeder.
Demonstrates the complete value loop:
Capture -> Understand -> Detect -> Quantify -> Investigate -> Recover -> Prove.
"""

from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import math
from ..db import (
    init_db,
    save_part,
    save_part_revision,
    save_characteristic,
    save_machine,
    save_watch_folder,
    save_inspection_job,
    save_inspection_measurements,
    save_cost_configuration,
    save_loss_event,
    save_recovery_event,
    save_investigation,
    save_corrective_action,
    save_quality_alert,
    save_job,
    DB_PATH,
)


def seed_demo_factory_operations(db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Seed realistic sample factory quality operations dataset.
    """
    init_db(db_path)
    now = datetime.now(timezone.utc)
    t_minus_2h = (now - timedelta(hours=2)).isoformat()
    t_minus_1h = (now - timedelta(hours=1)).isoformat()
    t_now = now.isoformat()

    # 1. Cost Configuration
    cost_cfg = {
        "id": "COST-DEFAULT",
        "currency": "₹",
        "default_part_cost": 1200.0,
        "machine_hourly_cost": 850.0,
        "labor_hourly_cost": 450.0,
        "rework_cost_per_part": 350.0,
        "scrap_cost_per_part": 1200.0,
        "inspection_labor_cost_per_hr": 400.0,
        "downtime_cost_per_hr": 1500.0,
        "updated_at": t_now,
    }
    save_cost_configuration(cost_cfg, db_path=db_path)

    # 2. Machines / Stations
    mach_4_id = save_machine(
        {
            "machine_code": "Machine #4",
            "name": "Okuma LB3000 CNC Turning Center",
            "machine_type": "CNC Lathe",
            "location": "Bay 2 - Precision Turning Line",
            "status": "OPERATIONAL",
            "hourly_operating_cost": 850.0,
            "last_seen": t_now,
        },
        db_path=db_path,
    )
    save_machine(
        {
            "machine_code": "Machine #2",
            "name": "Haas VF-4SS Vertical Machining Center",
            "machine_type": "5-Axis Milling",
            "location": "Bay 1 - Milling Cell",
            "status": "OPERATIONAL",
            "hourly_operating_cost": 950.0,
            "last_seen": t_now,
        },
        db_path=db_path,
    )
    save_machine(
        {
            "machine_code": "CMM-01",
            "name": "Zeiss Contura Bridge CMM",
            "machine_type": "Coordinate Measuring Machine",
            "location": "Quality Inspection Cleanroom",
            "status": "OPERATIONAL",
            "hourly_operating_cost": 600.0,
            "last_seen": t_now,
        },
        db_path=db_path,
    )

    # 3. Part & Characteristics
    part_id = save_part(
        {
            "part_number": "PART-A-10MM",
            "name": "Flange Guide Pin Shaft",
            "category": "CRITICAL_AEROSPACE_COMPONENT",
            "material": "AISI 4140 Hardened Steel (HRC 42)",
            "drawing_number": "DWG-AER-4092-A",
            "description": "High-precision guide pin shaft for aerospace actuator assembly.",
        },
        db_path=db_path,
    )
    rev_id = save_part_revision(
        {
            "part_id": part_id,
            "revision_code": "Rev A",
            "status": "ACTIVE",
            "effective_date": "2026-01-15",
            "notes": "Initial production release drawing revision.",
        },
        db_path=db_path,
    )
    char_id = save_characteristic(
        {
            "part_revision_id": rev_id,
            "name": "Main Outer Diameter",
            "feature_type": "CYLINDRICAL_DIAMETER",
            "nominal_value": 10.0000,
            "tolerance_upper": 0.1000,
            "tolerance_lower": -0.1000,
            "unit": "mm",
            "criticality": "CRITICAL",
            "inspection_frequency": "100%",
            "measurement_method": "Digital Outside Micrometer (Mitutoyo 293-140-30)",
        },
        db_path=db_path,
    )

    # 4. Baseline Inspection Job (Before Correction: 100 parts with tool wear drift & 12 scrap parts)
    baseline_readings = []
    baseline_measurements = []

    for i in range(1, 101):
        if i <= 40:
            val = 10.000 + (i * 0.0008)  # 10.000 to 10.032 mm (PASS)
            tool = "Tool #3"
            stat = "PASS"
            trend = "STABLE"
        elif i <= 88:
            val = 10.032 + ((i - 40) * 0.0014)  # 10.032 to 10.099 mm (WATCH: near upper tolerance)
            tool = "Tool #17"
            stat = "WATCH"
            trend = "DRIFT_UPWARD"
        else:
            val = 10.100 + ((i - 88) * 0.0022)  # 10.102 to 10.126 mm (FAIL: Exceeds +0.100 mm)
            tool = "Tool #17"
            stat = "FAIL"
            trend = "DRIFT_UPWARD"

        dev = val - 10.0000
        tol_consumed = (abs(dev) / 0.100) * 100.0
        baseline_readings.append(val)
        baseline_measurements.append({
            "part_sequence_num": i,
            "nominal": 10.0000,
            "measured_value": round(val, 5),
            "deviation": round(dev, 5),
            "tolerance_consumed_pct": round(tol_consumed, 1),
            "status": stat,
            "trend_signal": trend,
            "unit": "mm",
            "operator": "Marcus Reid (Tech 04)",
            "machine_id": "Machine #4",
            "tool_id": tool,
            "timestamp": t_minus_2h,
        })

    job_1_id = save_inspection_job(
        {
            "id": "INSP-DEMO-001",
            "job_number": "INSP-2026-0831-01",
            "part_id": part_id,
            "revision_id": rev_id,
            "batch_number": "BATCH-2026-884A",
            "machine_id": "Machine #4",
            "tool_id": "Tool #17",
            "operator": "Marcus Reid (Tech 04)",
            "status": "REVIEW_REQUIRED",
            "total_parts": 100,
            "passed_parts": 88,
            "failed_parts": 12,
            "scrap_count": 12,
            "rework_count": 0,
            "summary": {
                "mean_measured": 10.0482,
                "nominal_value": 10.0000,
                "tolerance_upper": 0.1000,
                "tolerance_lower": -0.1000,
                "defect_rate_pct": 12.0,
            },
            "created_at": t_minus_2h,
        },
        db_path=db_path,
    )
    save_inspection_measurements(job_1_id, baseline_measurements, db_path=db_path)

    # Loss Event for Job 1: 12 scrap parts * ₹1,200 = ₹14,400 per batch -> ₹36,000 production exposure
    loss_id = save_loss_event(
        {
            "id": "LOSS-DEMO-001",
            "job_id": job_1_id,
            "machine_id": "Machine #4",
            "part_id": part_id,
            "loss_category": "EXCESSIVE_SCRAP",
            "severity": "CRITICAL",
            "problem_title": "Machine #4 Progressive Diameter Drift & Scrap Surge",
            "evidence_description": "12 of 100 parts exceeded upper tolerance (+0.100 mm). Last 40 measurements continuously drifted upward from 10.032 mm to 10.126 mm.",
            "estimated_loss_amount": 36000.0,
            "assumptions": {"parts_scrapped": 12, "scrap_cost_per_part": 1200.0, "projected_monthly_exposure": 36000.0},
            "status": "ACTIVE",
            "created_at": t_minus_2h,
        },
        db_path=db_path,
    )

    # Quality Alerts
    save_quality_alert(
        {
            "id": "ALT-DEMO-001",
            "alert_type": "MEASUREMENT_DRIFT",
            "severity": "CRITICAL",
            "title": "Machine #4: Diameter Drift Towards Upper Tolerance",
            "evidence_summary": "Measurements 41-100 exhibited a continuous +0.0018 mm/part positive drift on Tool #17.",
            "affected_entities": {"job_id": job_1_id, "machine_id": "Machine #4", "tool_id": "Tool #17"},
            "recommended_action": "Inspect Tool #17 cutting insert for flank wear and reset wear compensation.",
            "status": "ACTIVE",
            "created_at": t_minus_2h,
        },
        db_path=db_path,
    )

    # 5. Root-Cause Investigation
    inv_id = save_investigation(
        {
            "id": "INV-DEMO-001",
            "title": "Machine #4 Tool #17 Diameter Drift Investigation",
            "trigger_loss_id": loss_id,
            "status": "CORRELATION_DETECTED",
            "lead_engineer": "Dr. Aris Thorne (Lead Quality Architect)",
            "affected_jobs": [job_1_id],
            "correlation_matrix": {
                "primary_factor": "TOOLING",
                "finding": "Correlation detected: 100% of out-of-tolerance parts were machined exclusively by Tool #17.",
                "confidence_score_pct": 91.2,
                "correlation_strength": "STRONG",
            },
            "findings": "Physical inspection confirmed micro-chipping and 0.08 mm flank wear on Tool #17 carbide insert.",
            "created_at": t_minus_1h,
        },
        db_path=db_path,
    )

    # Corrective Action
    act_id = save_corrective_action(
        {
            "id": "ACT-DEMO-001",
            "investigation_id": inv_id,
            "action_title": "Replace Tool #17 Insert & Reset CNC Wear Offsets",
            "description": "Installed new Sandvik CNMG 120408 carbide insert on Tool #17, re-zeroed tool presetter, and applied automated tool wear compensation.",
            "assigned_to": "Kiran Patel (Senior CNC Specialist)",
            "status": "RESOLVED",
            "finding_notes": "Tool replaced and verified via test cut.",
            "preventive_measures": "Programmed automated CNC tool life monitor to prompt insert index every 250 parts.",
            "verification_job_id": "INSP-DEMO-002",
            "created_at": t_minus_1h,
            "closed_at": t_now,
        },
        db_path=db_path,
    )

    # 6. Post-Correction Verification Job (After: 100 parts, 0 defects, 100% PASS)
    post_measurements = []
    for i in range(1, 101):
        val = 10.0000 + (math.sin(i * 0.3) * 0.012) + 0.002  # 9.990 to 10.014 mm (Centred, 100% PASS)
        dev = val - 10.0000
        tol_consumed = (abs(dev) / 0.100) * 100.0
        post_measurements.append({
            "part_sequence_num": i,
            "nominal": 10.0000,
            "measured_value": round(val, 5),
            "deviation": round(dev, 5),
            "tolerance_consumed_pct": round(tol_consumed, 1),
            "status": "PASS",
            "trend_signal": "STABLE",
            "unit": "mm",
            "operator": "Marcus Reid (Tech 04)",
            "machine_id": "Machine #4",
            "tool_id": "Tool #17 (New Insert)",
            "timestamp": t_now,
        })

    job_2_id = save_inspection_job(
        {
            "id": "INSP-DEMO-002",
            "job_number": "INSP-2026-0831-02",
            "part_id": part_id,
            "revision_id": rev_id,
            "batch_number": "BATCH-2026-884B",
            "machine_id": "Machine #4",
            "tool_id": "Tool #17",
            "operator": "Marcus Reid (Tech 04)",
            "status": "APPROVED",
            "total_parts": 100,
            "passed_parts": 100,
            "failed_parts": 0,
            "scrap_count": 0,
            "rework_count": 0,
            "summary": {
                "mean_measured": 10.0021,
                "nominal_value": 10.0000,
                "tolerance_upper": 0.1000,
                "tolerance_lower": -0.1000,
                "defect_rate_pct": 0.0,
            },
            "created_at": t_now,
        },
        db_path=db_path,
    )
    save_inspection_measurements(job_2_id, post_measurements, db_path=db_path)

    # 7. Before / After Verified Recovery ROI Proof
    save_recovery_event(
        {
            "id": "REC-DEMO-001",
            "loss_event_id": loss_id,
            "action_id": act_id,
            "baseline_period": "Batch 884A (Pre-Correction)",
            "baseline_loss_rate": 14400.0,
            "post_action_loss_rate": 0.0,
            "actual_recovered_amount": 28800.0,
            "recovery_percentage": 100.0,
            "verification_evidence": {
                "baseline_defect_rate_pct": 12.0,
                "post_correction_defect_rate_pct": 0.0,
                "monthly_recovered_savings": 28800.0,
                "summary": "Tool #17 replacement reduced scrap rate from 12% to 0%. Verified monthly recovery value of ₹28,800/month.",
            },
            "verified_by": "Dr. Aris Thorne (Lead Quality Architect)",
        },
        db_path=db_path,
    )

    return {
        "status": "SUCCESS",
        "seeded_entities": {
            "part_id": part_id,
            "machine_id": mach_4_id,
            "baseline_job_id": job_1_id,
            "verification_job_id": job_2_id,
            "loss_id": loss_id,
            "investigation_id": inv_id,
            "action_id": act_id,
            "recovered_value_per_month": 28800.0,
        },
    }

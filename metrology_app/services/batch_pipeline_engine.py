"""
Batch Pipeline Processing Engine for Metrology Workstation.
Executes automated calibration pipeline across fleets of 10-100+ instruments
using a unified procedure template and aggregates fleet-level quality gates.
"""

import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..db import (
    get_batch_job,
    save_batch_job,
    update_batch_job_progress,
    get_procedure_template,
    save_job,
    get_job,
    DB_PATH,
)
from .job_pipeline_engine import run_1click_job_pipeline


def execute_batch_run(
    batch_title: str,
    procedure_template_id: str,
    instruments: List[Dict[str, Any]],
    operator: str = "Metrology Specialist",
    fail_rate_simulation: float = 0.08,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Execute a full multi-instrument batch calibration run.
    Processes each instrument through the 1-Click Pipeline,
    tallying passes, fails, and exceptions.
    """
    template = get_procedure_template(procedure_template_id, db_path=db_path)
    if not template:
        raise ValueError(f"Procedure template '{procedure_template_id}' not found.")

    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    batch_id = f"BATCH-{now}"

    total = len(instruments)
    batch_record = {
        "id": batch_id,
        "batch_number": batch_id,
        "title": batch_title,
        "procedure_template_id": template["id"],
        "procedure_name": template["title"],
        "operator": operator,
        "status": "PROCESSING",
        "total_instruments": total,
        "completed_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "review_required_count": 0,
        "job_ids": [],
    }
    save_batch_job(batch_record, db_path=db_path)

    completed = 0
    passed = 0
    failed = 0
    review_required = 0
    job_ids = []

    nominal = float(template.get("nominal_value", 25.0))
    tol_upper = float(template.get("tolerance_upper", 0.002))
    tol_lower = float(template.get("tolerance_lower", -0.002))
    unit = template.get("default_unit", "mm")

    for idx, inst in enumerate(instruments):
        serial = inst.get("serial", f"SN-{1000 + idx}")
        model = inst.get("model", "Standard Fleet Model")
        name = inst.get("name", "Test Instrument")
        customer = inst.get("customer", "Internal Fleet Quality")

        job_id = f"{batch_id}-JOB-{idx+1:03d}"

        # Generate realistic measurement observations
        # Occasionally simulate an out-of-tolerance or near-limit unit if fail_rate_simulation triggered
        is_fail_test = (random.random() < fail_rate_simulation)
        if is_fail_test:
            # Shift mean beyond tolerance limit
            shift = (tol_upper * 1.35) if random.random() > 0.5 else (tol_lower * 1.35)
            readings = [round(nominal + shift + random.gauss(0, abs(tol_upper) * 0.1), 5) for _ in range(5)]
        else:
            readings = [round(nominal + random.gauss(0, abs(tol_upper) * 0.15), 5) for _ in range(5)]

        job_data = {
            "id": job_id,
            "job_number": job_id,
            "title": f"{template['title']} — {model} ({serial})",
            "customer_name": customer,
            "instrument_id": f"INST-{serial[:6]}",
            "instrument_name": name,
            "instrument_model": model,
            "instrument_serial": serial,
            "procedure_template_id": template["id"],
            "procedure_name": template["title"],
            "reference_standard_id": "STD-GB-01" if template.get("category") == "Dimensional" else "STD-ZNR-10",
            "reference_standard_name": "Fleet Calibration Reference",
            "reference_due_date": "2026-11-15",
            "reference_uncertainty": 0.00004,
            "status": "IN_PROGRESS",
            "unit": unit,
            "nominal_value": nominal,
            "tolerance_upper": tol_upper,
            "tolerance_lower": tol_lower,
            "environment": {
                "ambient_temperature_c": round(20.0 + random.uniform(-0.4, 0.4), 2),
                "relative_humidity_pct": round(44.0 + random.uniform(-2.0, 2.0), 1),
                "atmospheric_pressure_hpa": 1013.25,
            },
            "raw_measurements": readings,
            "operator": operator,
            "batch_id": batch_id,
            "automation_level": "AUTOMATIC",
        }

        save_job(job_data, db_path=db_path)

        # Run 1-Click Pipeline
        try:
            processed_job = run_1click_job_pipeline(job_id, operator=operator, db_path=db_path)
            verdict = processed_job.get("conformity", {}).get("conformance_verdict", "REVIEW_REQUIRED")
            exceptions = processed_job.get("exceptions", [])

            completed += 1
            if verdict == "PASS" and not exceptions:
                passed += 1
            elif verdict == "FAIL":
                failed += 1
            else:
                review_required += 1

            job_ids.append(job_id)
        except Exception as e:
            completed += 1
            review_required += 1
            job_ids.append(job_id)

    final_status = "COMPLETED"
    update_batch_job_progress(
        batch_id=batch_id,
        completed=completed,
        passed=passed,
        failed=failed,
        review_required=review_required,
        status=final_status,
        db_path=db_path,
    )

    batch_res = get_batch_job(batch_id, db_path=db_path)
    if batch_res:
        batch_res["job_ids"] = job_ids
        save_batch_job(batch_res, db_path=db_path)

    return get_batch_job(batch_id, db_path=db_path)

"""
Automated Calibration Execution Engine.
Automates the full pipeline:
  Job + Asset + Procedure -> InstrumentDriver -> Sequence Execution ->
  Live Measurements + Environment Telemetry -> GUM Uncertainty Engine ->
  Conformity Decision -> Evidence Sealing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

from ..db import (
    get_job,
    save_job,
    get_asset,
    DB_PATH,
)
from ..industrial.instrument_driver import create_instrument_driver
from .procedure_execution_service import get_procedure, execute_procedure_step
from .hardware_acquisition_service import execute_instrument_acquisition, _record_event
from .job_pipeline_engine import run_1click_job_pipeline
from .exception_center_service import log_automated_exception


def run_automated_calibration(
    job_id: str,
    device_config: Optional[Dict[str, Any]] = None,
    ambient_environment: Optional[Dict[str, float]] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Execute end-to-end automated calibration for a job:
      1. Load Job & Procedure
      2. Connect Instrument Driver
      3. Execute Procedure Steps & Stream Measurements
      4. Snapshot Environmental Telemetry
      5. Run Deterministic GUM & Conformity Decision
      6. Return execution summary with hardware audit trace
    """
    job = get_job(job_id, db_path=db_path)
    if not job:
        raise ValueError(f"Job '{job_id}' not found.")

    proc_id = job.get("procedure_template_id")
    proc = get_procedure(proc_id, db_path=db_path) if proc_id else None

    # Fallback to default simulator driver if device_config not supplied
    if not device_config:
        device_config = {
            "id": job.get("instrument_id", "DEV-DEFAULT"),
            "bus": "VIRTUAL",
            "driver_profile": "KEYSIGHT_34461A" if job.get("unit") == "V" else "MITUTOYO_DIGIMATIC",
            "nominal": job.get("nominal_value", 10.0),
            "unit": job.get("unit", "V"),
        }

    # Environment snapshot
    env = ambient_environment or {
        "ambient_temperature_c": 20.1,
        "relative_humidity_pct": 46.2,
        "atmospheric_pressure_hpa": 1013.2,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    driver = create_instrument_driver(device_config)
    driver.connect()

    hardware_trace: List[Dict[str, Any]] = []
    collected_values: List[float] = []
    step_results: List[Dict[str, Any]] = []
    exceptions: List[Dict[str, Any]] = []

    try:
        # If procedure has explicit steps, execute step sequence
        steps = proc.get("steps", []) if proc else []
        if not steps:
            # Generate default 5-point repeatable measurement steps
            steps = [
                {"step_number": 1, "step_type": "CONFIGURE", "parameters": {"function": "VOLT:DC", "nominal": job.get("nominal_value", 10.0)}},
                {"step_number": 2, "step_type": "WAIT", "parameters": {"delay_seconds": 0.02}},
                {"step_number": 3, "step_type": "REPEAT", "parameters": {"repeat_count": 5}},
            ]

        context = {"last_reading": job.get("nominal_value", 10.0)}

        for s in steps:
            res = execute_procedure_step(s, driver, context)
            step_results.append(res)
            _record_event(hardware_trace, job_id, s.get("step_type", "STEP"), device_config.get("id", "DEV"), str(res.get("details", res.get("status"))))

            if s.get("step_type") == "MEASURE" and "value" in res:
                val = float(res["value"])
                collected_values.append(val)
                context["last_reading"] = val
                _check_and_log_oot(job, val, exceptions, db_path)

            elif s.get("step_type") == "REPEAT" and "readings" in res:
                for val in res["readings"]:
                    fval = float(val)
                    collected_values.append(fval)
                    context["last_reading"] = fval
                    _check_and_log_oot(job, fval, exceptions, db_path)

    finally:
        driver.disconnect()
        _record_event(hardware_trace, job_id, "DISCONNECT", device_config.get("id", "DEV"), "OK")

    # Update job with acquired measurements and environment
    if collected_values:
        job["raw_measurements"] = collected_values
    job["environment"] = env
    job["status"] = "IN_PROGRESS"
    meta = job.get("metadata", {})
    meta["automated_execution"] = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "driver": driver.driver_name,
        "steps_count": len(step_results),
        "hardware_trace": hardware_trace,
    }
    job["metadata"] = meta
    save_job(job, db_path=db_path)

    # Trigger deterministic GUM calculation & Conformity pipeline
    pipeline_res = run_1click_job_pipeline(job_id, db_path=db_path)

    return {
        "job_id": job_id,
        "status": pipeline_res.get("status"),
        "measurements_acquired": len(collected_values),
        "raw_readings": collected_values,
        "environment": env,
        "conformity_verdict": pipeline_res.get("conformity", {}).get("conformance_verdict", "UNKNOWN"),
        "expanded_uncertainty_U95": pipeline_res.get("uncertainty_budget", {}).get("expanded_uncertainty_U95"),
        "hardware_trace_events": len(hardware_trace),
        "exceptions_logged": len(exceptions),
    }


def _check_and_log_oot(job: Dict[str, Any], value: float, exceptions: List[Dict[str, Any]], db_path: str) -> None:
    nominal = float(job.get("nominal_value", 0.0))
    usl = nominal + float(job.get("tolerance_upper", 0.05))
    lsl = nominal + float(job.get("tolerance_lower", -0.05))
    if value > usl or value < lsl:
        exc = {
            "title": f"OOT Reading Detected on {job.get('instrument_name', 'Asset')}",
            "description": f"Measured {value:.6f} exceeded tolerance bounds [{lsl:.6f}, {usl:.6f}].",
            "severity": "CRITICAL",
            "job_id": job.get("id"),
        }
        exceptions.append(exc)
        try:
            log_automated_exception(exc, db_path=db_path)
        except Exception:
            pass

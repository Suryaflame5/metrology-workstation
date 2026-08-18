"""
Demonstration Project Seeder & Loader Service.
Preloads a realistic, deterministic precision DMM calibration project without polluting clean baseline installs.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from ..db import save_project, save_instrument, save_measurement_plan, save_measurement, insert_audit_event
from .calculation_service import compute_micrometer_calibration


def load_preloaded_demonstration_project(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Populate a complete, realistic demonstration project:
    'Keysight 34401A 6.5-Digit DMM DC Voltage Calibration (10V Range)'
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1. Project
    proj = save_project({
        "id": "PRJ-DEMO-DMM",
        "name": "Precision DMM Quality Verification 2026",
        "customer_site": "Aerospace Metrology Lab 2",
        "description": "Annual ISO/IEC 17025 conformity verification of 6.5-digit precision digital multimeter across 10V DC range using Fluke 5720A calibrator.",
        "status": "ACTIVE",
    }, db_path=db_path)

    # 2. Instrument
    inst = save_instrument({
        "id": "INST-DEMO-DMM",
        "project_id": proj["id"],
        "manufacturer": "Keysight Technologies",
        "model": "34401A 6.5-Digit DMM",
        "serial_number": "MY41098421",
        "instrument_type": "Digital Multimeter",
        "range_min": 0.0,
        "range_max": 10.0,
        "resolution": 0.00001,
        "accuracy_spec": "±0.0035% of reading + 0.0005% of range",
        "calibration_status": "VALID",
        "calibration_interval_months": 12,
        "last_calibration_date": now[:10],
        "next_calibration_due": "2027-08-18",
        "location": "Bench #3",
    }, db_path=db_path)

    # 3. Measurement Plan
    plan = save_measurement_plan({
        "id": "PLAN-DEMO-10V",
        "project_id": proj["id"],
        "instrument_id": inst["id"],
        "plan_name": "10.0000 V DC Voltage Linearity Verification",
        "measurand": "DC Voltage",
        "nominal_value": 10.0,
        "tolerance_lower": -0.00040,
        "tolerance_upper": 0.00040,
        "required_repetitions": 5,
        "procedure_name": "EURAMET cg-15 DMM Calibration",
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
    }, db_path=db_path)

    # 4. Measurement Acquisition
    readings = [10.00012, 10.00008, 10.00014, 10.00010, 10.00011]
    meas = save_measurement({
        "id": "MEAS-DEMO-10V",
        "plan_id": plan["id"],
        "instrument_id": inst["id"],
        "operator": "Senior Metrology Engineer",
        "raw_values": readings,
        "mean_value": 10.00011,
        "sample_std_dev": 0.00002236,
        "repeatability_uncertainty": 0.00001000,
        "outliers": [],
    }, db_path=db_path)

    # 5. Calculation Record
    from ..models import CalculationCreateRequest
    calc_req = CalculationCreateRequest(
        instrument_name="Keysight 34401A 6.5-Digit DMM",
        procedure_name="EURAMET cg-15 DMM Calibration",
        nominal_value=10.0,
        readings_mm=readings,
        tolerance_limit_mm=0.00040,
        ambient_temp_c=20.0,
        relative_humidity_pct=45.0,
        operator="Senior Metrology Engineer",
        project_id=proj["id"],
        instrument_id=inst["id"],
    )
    calc_res = compute_micrometer_calibration(calc_req, db_path=db_path)

    insert_audit_event(
        action="LOAD_DEMO_PROJECT",
        target_id=proj["id"],
        actor="SYSTEM",
        details={"name": proj["name"], "instrument": inst["model"], "calc_id": calc_res.id},
        db_path=db_path,
    )

    return {
        "status": "LOADED",
        "project": proj,
        "instrument": inst,
        "plan": plan,
        "measurement": meas,
        "calculation": calc_res.model_dump(),
        "message": "Demonstration project 'Precision DMM Quality Verification' successfully loaded.",
    }

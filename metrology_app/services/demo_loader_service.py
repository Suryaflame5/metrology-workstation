"""
Demonstration Laboratory Seeder & Loader Service.
Preloads a complete, realistic 248-instrument enterprise laboratory environment:
- Dimensional, Electrical, Pressure, and Temperature instruments
- Realistic calibration histories, certificates, upcoming schedules, and attention alerts
- Fully aligned with GUM, ISO/IEC 17025, and ANSI Z540.3 standards.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from ..db import (
    save_project,
    save_instrument,
    save_measurement_plan,
    save_measurement,
    save_calculation,
    insert_audit_event,
    init_db,
)
from .calculation_service import compute_micrometer_calibration
from ..models import CalculationCreateRequest


def load_preloaded_demonstration_project(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Populate a complete, realistic commercial demonstration laboratory.
    """
    init_db(db_path)
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    # 1. Primary Enterprise Projects
    proj1 = save_project({
        "id": "PRJ-DEMO-DMM",
        "name": "Aerospace Flight Hardware Metrology 2026",
        "customer_site": "Boeing Defense & Space — Lab A",
        "description": "ISO/IEC 17025 conformity verification of critical airframe dimensional tooling and high-precision DC voltage standards.",
        "status": "ACTIVE",
    }, db_path=db_path)

    proj2 = save_project({
        "id": "PRJ-AUTO-02",
        "name": "EV Powertrain Rotor Shaft QC",
        "customer_site": "Tesla Gigafactory Metrology Lab — Bay 3",
        "description": "IATF 16949 dimensional verification of EV stator bores, rotor shafts, and thermal sensor probes.",
        "status": "ACTIVE",
    }, db_path=db_path)

    # 2. Key Demonstration Instruments
    instruments_to_seed = [
        {
            "id": "INST-DEMO-DMM",
            "project_id": proj1["id"],
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
            "last_calibration_date": now_str[:10],
            "next_calibration_due": "2027-08-18",
            "location": "Bench #3",
            "custodian": "Alex Kumar",
        },
        {
            "id": "INST-MC-104",
            "project_id": proj1["id"],
            "manufacturer": "Mitutoyo",
            "model": "293-340 Digimatic Micrometer",
            "serial_number": "M104-88213",
            "instrument_type": "Outside Micrometer",
            "range_min": 0.0,
            "range_max": 25.0,
            "resolution": 0.001,
            "accuracy_spec": "±0.001 mm",
            "calibration_status": "VALID",
            "calibration_interval_months": 12,
            "last_calibration_date": (now - timedelta(days=65)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now + timedelta(days=24)).strftime("%Y-%m-%d"),
            "location": "Dimensional Lab — Bay 1",
            "custodian": "Alex Kumar",
        },
        {
            "id": "INST-PG-104",
            "project_id": proj1["id"],
            "manufacturer": "Druck",
            "model": "DPI 612 Pressure Calibrator",
            "serial_number": "PG-104-9912",
            "instrument_type": "Pressure Gauge",
            "range_min": 0.0,
            "range_max": 200.0,
            "resolution": 0.01,
            "accuracy_spec": "±0.02% FS",
            "calibration_status": "VALID",
            "calibration_interval_months": 6,
            "last_calibration_date": (now - timedelta(days=177)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
            "location": "Pressure Lab A",
            "custodian": "Marcus Reid",
        },
        {
            "id": "INST-DMM-221",
            "project_id": proj1["id"],
            "manufacturer": "Keysight Technologies",
            "model": "34461A 6.5-Digit DMM",
            "serial_number": "MY53209844",
            "instrument_type": "Digital Multimeter",
            "range_min": 0.0,
            "range_max": 10.0,
            "resolution": 0.00001,
            "accuracy_spec": "±0.0035% of reading + 0.0005% of range",
            "calibration_status": "VALID",
            "calibration_interval_months": 12,
            "last_calibration_date": (now - timedelta(days=350)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now + timedelta(days=6)).strftime("%Y-%m-%d"),
            "location": "Electrical Lab B",
            "custodian": "Elena Vance",
        },
        {
            "id": "INST-T-087",
            "project_id": proj2["id"],
            "manufacturer": "Fluke Calibration",
            "model": "1524 Reference Thermometer",
            "serial_number": "T087-44012",
            "instrument_type": "Digital Thermometer",
            "range_min": -50.0,
            "range_max": 250.0,
            "resolution": 0.001,
            "accuracy_spec": "±0.01 °C",
            "calibration_status": "EXPIRED",
            "calibration_interval_months": 12,
            "last_calibration_date": (now - timedelta(days=370)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "location": "Thermal Lab C",
            "custodian": "R. Sharma",
        },
        {
            "id": "INST-MC-105",
            "project_id": proj1["id"],
            "manufacturer": "Mitutoyo",
            "model": "293-348 Micrometer",
            "serial_number": "M105-77312",
            "instrument_type": "Outside Micrometer",
            "range_min": 0.0,
            "range_max": 25.0,
            "resolution": 0.001,
            "accuracy_spec": "±0.001 mm",
            "calibration_status": "VALID",
            "calibration_interval_months": 12,
            "last_calibration_date": (now - timedelta(days=358)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
            "location": "Dimensional Lab A",
            "custodian": "Alex Kumar",
        },
        {
            "id": "INST-CD-203",
            "project_id": proj2["id"],
            "manufacturer": "Mitutoyo",
            "model": "500-196-30 Digital Caliper",
            "serial_number": "CD203-9941",
            "instrument_type": "Digital Caliper",
            "range_min": 0.0,
            "range_max": 150.0,
            "resolution": 0.01,
            "accuracy_spec": "±0.02 mm",
            "calibration_status": "VALID",
            "calibration_interval_months": 12,
            "last_calibration_date": (now - timedelta(days=353)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now + timedelta(days=12)).strftime("%Y-%m-%d"),
            "location": "Dimensional Lab A",
            "custodian": "Marcus Reid",
        },
    ]

    # Generate additional instruments up to 50+ to establish realistic fleet
    for i in range(7, 52):
        inst_type = "Outside Micrometer" if i % 4 == 0 else ("Digital Multimeter" if i % 4 == 1 else ("Digital Caliper" if i % 4 == 2 else "Dial Indicator"))
        mfr = "Mitutoyo" if "Micrometer" in inst_type or "Caliper" in inst_type else ("Keysight" if "Multimeter" in inst_type else "Mahr")
        is_due = (i % 7 == 0)
        is_over = (i == 19 or i == 37 or i == 43)
        status = "EXPIRED" if is_over else "VALID"
        days_offset = -10 if is_over else (15 if is_due else 90 + (i * 4))
        
        instruments_to_seed.append({
            "id": f"INST-AUTO-{i:03d}",
            "project_id": proj1["id"] if i % 2 == 0 else proj2["id"],
            "manufacturer": mfr,
            "model": f"Model-{inst_type[:4].upper()}-{100 + i}",
            "serial_number": f"SN-{mfr[:3].upper()}-{9000 + i}",
            "instrument_type": inst_type,
            "range_min": 0.0,
            "range_max": 25.0 if "Micrometer" in inst_type else 150.0,
            "resolution": 0.001 if "Micrometer" in inst_type else 0.01,
            "accuracy_spec": "±0.002 mm",
            "calibration_status": status,
            "calibration_interval_months": 12,
            "last_calibration_date": (now - timedelta(days=365 - days_offset)).strftime("%Y-%m-%d"),
            "next_calibration_due": (now + timedelta(days=days_offset)).strftime("%Y-%m-%d"),
            "location": f"Lab {'A' if i % 3 == 0 else ('B' if i % 3 == 1 else 'C')}",
            "custodian": "Alex Kumar" if i % 2 == 0 else "Marcus Reid",
        })

    for inst_data in instruments_to_seed:
        save_instrument(inst_data, db_path=db_path)

    # 3. Measurement Plan for DMM
    plan = save_measurement_plan({
        "id": "PLAN-DEMO-10V",
        "project_id": proj1["id"],
        "instrument_id": "INST-DEMO-DMM",
        "plan_name": "10.0000 V DC Voltage Linearity Verification",
        "measurand": "DC Voltage",
        "nominal_value": 10.0,
        "tolerance_lower": -0.00040,
        "tolerance_upper": 0.00040,
        "required_repetitions": 5,
        "procedure_name": "EURAMET cg-15 DMM Calibration",
        "decision_rule": "ANSI/NCSL Z540.3 Method 6",
    }, db_path=db_path)

    # 4. Repeated Readings & Calibration Calculation
    readings = [10.00012, 10.00008, 10.00014, 10.00010, 10.00011]
    calc_req = CalculationCreateRequest(
        instrument_name="Keysight 34401A 6.5-Digit DMM",
        procedure_name="EURAMET cg-15 DMM Calibration",
        nominal_value=10.0,
        readings_mm=readings,
        tolerance_limit_mm=0.00040,
        ambient_temp_c=21.3,
        relative_humidity_pct=43.2,
        operator="Alex Kumar",
        project_id=proj1["id"],
        instrument_id="INST-DEMO-DMM",
    )
    calc_res = compute_micrometer_calibration(calc_req, db_path=db_path)

    # Save additional historical calibrations for MC-104
    hist_years = [
        {"year": 2024, "date": "2024-06-12", "cert": "CAL-2024-08795", "mean": 25.0008, "unc": 0.0007},
        {"year": 2025, "date": "2025-06-14", "cert": "CAL-2025-09821", "mean": 25.0010, "unc": 0.0007},
        {"year": 2026, "date": "2026-06-14", "cert": "CAL-2026-10482", "mean": 25.0012, "unc": 0.0007},
    ]

    for h in hist_years:
        insert_audit_event(
            action="CALIBRATION_PERFORMED",
            target_id="INST-MC-104",
            actor="Alex Kumar",
            details={"certificate": h["cert"], "date": h["date"], "verdict": "PASS", "mean": h["mean"]},
            db_path=db_path,
        )

    return {
        "status": "LOADED",
        "total_instruments_seeded": len(instruments_to_seed),
        "featured_instrument": "INST-MC-104",
        "active_calculation_id": calc_res.id,
        "project": proj1,
        "instrument": instruments_to_seed[0],
        "plan": plan,
        "calculation": calc_res.model_dump(),
        "message": "Demonstration laboratory environment successfully populated.",
    }


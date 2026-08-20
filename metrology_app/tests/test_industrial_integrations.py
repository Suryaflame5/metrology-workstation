"""
Automated Test Suite for SCPI / VISA Hardware Drivers, QIF 3.0 Interchange, and Sensor Emulator.
"""

import pytest
from metrology_app.industrial.scpi_visa import SCPIInstrumentDriver, execute_scpi_command_live
from metrology_app.industrial.qif_step import parse_qif_plan, export_qif_results
from metrology_app.industrial.telemetry_emulator import generate_live_telemetry_sample


def test_scpi_visa_driver_virtual_loopback():
    driver = SCPIInstrumentDriver("VIRTUAL::KEY34461A")
    conn = driver.connect()
    assert conn["status"] == "CONNECTED_VIRTUAL"

    # Query *IDN?
    idn = driver.query("*IDN?")
    assert "Keysight" in idn or "34461A" in idn

    # Query Measurement
    volt = driver.query("MEAS:VOLT:DC?")
    assert "+" in volt or "10." in volt

    # Query Error Buffer
    err = driver.query("SYST:ERR?")
    assert "No error" in err or "+0" in err

    driver.disconnect()


def test_qif_3_0_plan_parsing_and_export():
    sample_qif_json = """
    {
      "MeasurementPlan": {
        "Characteristics": [
          { "id": "FEAT-01", "name": "Cylinder Diameter", "nominal": 25.0, "tolerance_upper": 0.002, "tolerance_lower": -0.002, "unit": "mm", "datum": "A" }
        ]
      }
    }
    """
    parsed = parse_qif_plan(sample_qif_json)
    assert parsed["format"] == "QIF_3_0_JSON"
    assert parsed["characteristics_count"] == 1
    assert parsed["characteristics"][0]["nominal_value"] == 25.0
    assert parsed["characteristics"][0]["datum_reference"] == "A"

    # Export test
    mock_calc = {
        "id": "CALC-EXP-001",
        "nominal_value": 25.0,
        "conformity_verdict": "PASS",
        "result_data": {
            "summary": {"mean": 25.0012, "error_of_indication_mm": 0.0002},
            "uncertainty_summary": {"expanded_uncertainty_u95_mm": 0.0008, "coverage_factor_k": 2.0},
            "decision_summary": {"decision_rule": "ANSI/NCSL Z540.3 Method 6", "guardband_w_mm": 0.0002},
        },
    }
    qif_out = export_qif_results(mock_calc)
    assert qif_out["QIFResults"]["version"] == "3.0.0"
    assert qif_out["QIFResults"]["inspection_result"]["conformity_verdict"] == "PASS"


def test_industrial_telemetry_emulator():
    sample = generate_live_telemetry_sample(nominal_value=25.0, elapsed_seconds=60.0)
    assert "simulated_reading_mm" in sample
    assert "thermal_error_mm" in sample
    assert "environmental_sensors" in sample
    assert sample["environmental_sensors"]["ambient_temperature_c"] >= 18.0
    assert sample["instrument_status"]["pll_lock"] is True

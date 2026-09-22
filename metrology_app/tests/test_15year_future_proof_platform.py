"""
Automated Test Suite for CALIBRA 10-15 Year Commercial Longevity & Big-Tech Competitive Moat:
  1. Universal DCC (v2.4 - v3.3) Ingestion & Standards Sync
  2. 15-Year Long-Term Verifiable Evidence Capsule
  3. Executive ROI & 10-Year Cumulative Economic Value
  4. OIML D10 Dynamic Interval Adjustment Engine
  5. Industry 4.0 / 5.0 OPC-UA & MQTT Telemetry Bridge
  6. Server REST API Endpoints Verification
"""

import pytest
import tempfile
import os
import json
from fastapi.testclient import TestClient

from metrology_app.db import (
    init_db,
    save_job,
    get_job,
    save_reference_standard,
    get_reference_standard,
)
from metrology_app.services.dcc_ingestion_service import parse_dcc_xml_bytes, parse_dcc_json_string
from metrology_app.services.verifiable_capsule_service import generate_verifiable_evidence_capsule_html
from metrology_app.services.executive_roi_service import compute_executive_economic_roi
from metrology_app.services.interval_intelligence import compute_adaptive_calibration_interval
from metrology_app.services.hardware_device_adapter import (
    format_opcua_telemetry_node,
    ingest_mqtt_smart_cell_packet,
)
from metrology_app.server import app


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    from metrology_app.db import seed_default_jobs_and_standards
    seed_default_jobs_and_standards(db_path)
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_dcc_xml_ingestion_and_auto_registration(test_db):
    sample_dcc_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<dcc:digitalCalibrationCertificate xmlns:dcc="https://ptb.de/dcc" schemaVersion="3.2.0">
  <dcc:administrativeData>
    <dcc:coreData>
      <dcc:uniqueIdentifier>CERT-PTB-2026-8812</dcc:uniqueIdentifier>
      <dcc:performanceDate>2026-06-15</dcc:performanceDate>
      <dcc:calibrationLaboratory>
        <dcc:name>Physikalisch-Technische Bundesanstalt (PTB)</dcc:name>
      </dcc:calibrationLaboratory>
    </dcc:coreData>
    <dcc:item>
      <dcc:name>High Precision DC Reference Standard</dcc:name>
      <dcc:manufacturer>Fluke Calibration</dcc:manufacturer>
      <dcc:model>732B</dcc:model>
      <dcc:serialNumber>SN-732B-99120</dcc:serialNumber>
    </dcc:item>
  </dcc:administrativeData>
  <dcc:measurementResults>
    <dcc:measurementResult>
      <dcc:results>
        <dcc:nominal>10.000000</dcc:nominal>
        <dcc:unitString>V</dcc:unitString>
        <dcc:expandedUncertainty>0.000015</dcc:expandedUncertainty>
        <dcc:coverageFactor>2.0</dcc:coverageFactor>
      </dcc:results>
    </dcc:measurementResult>
  </dcc:measurementResults>
</dcc:digitalCalibrationCertificate>"""

    res = parse_dcc_xml_bytes(sample_dcc_xml, register_as_standard=True, db_path=test_db)
    assert res["status"] == "VALID_DCC_DOCUMENT"
    assert res["certificate_id"] == "CERT-PTB-2026-8812"
    assert res["item"]["manufacturer"] == "Fluke Calibration"
    assert res["item"]["model"] == "732B"
    assert res["metrological_parameters"]["expanded_uncertainty"] == 0.000015
    assert res["registered_standard_id"] == "STD-DCC-SN-732B-99120"

    # Verify stored in database
    std = get_reference_standard("STD-DCC-SN-732B-99120", db_path=test_db)
    assert std is not None
    assert std["serial_number"] == "SN-732B-99120"


def test_dcc_json_ingestion(test_db):
    sample_json = {
        "dcc_version": "3.3.0",
        "administrative_data": {
            "certificate_id": "CERT-NIST-2026-0041",
            "calibration_date": "2026-05-10",
            "laboratory": {"name": "National Institute of Standards and Technology (NIST)"},
        },
        "item_under_test": {
            "name": "Ceramic Gauge Block Set Grade 0",
            "manufacturer": "Mitutoyo",
            "model": "516-966-21",
            "serial_number": "SN-MIT-GB-04",
            "nominal_value": 25.0,
            "unit": "mm",
        },
        "calibration_results": {
            "expanded_uncertainty_U95": 0.000030,
            "coverage_factor_k": 2.0,
            "confidence_interval_pct": 95.45,
        },
    }

    res = parse_dcc_json_string(json.dumps(sample_json), register_as_standard=True, db_path=test_db)
    assert res["status"] == "VALID_DCC_DOCUMENT"
    assert res["item"]["nominal_value"] == 25.0
    assert res["metrological_parameters"]["expanded_uncertainty"] == 0.000030
    assert res["registered_standard_id"] == "STD-DCC-SN-MIT-GB-04"


def test_15year_verifiable_evidence_capsule(test_db):
    job = {
        "id": "JOB-AERO-2026-99",
        "job_number": "JN-9920",
        "title": "Outside Micrometer ISO 3611 Calibration",
        "status": "APPROVED",
        "instrument_name": "Digital Micrometer",
        "instrument_model": "Mitutoyo 293",
        "instrument_serial": "SN-MIT-293-99",
        "nominal_value": 25.0,
        "unit": "mm",
        "raw_measurements": [25.0002, 25.0004, 25.0003, 25.0005, 25.0003],
        "statistics": {"mean": 25.00034, "std_dev": 0.00011},
        "uncertainty_budget": {
            "effective_degrees_of_freedom": 45,
            "combined_uncertainty_uc": 0.0004,
            "expanded_uncertainty_U95": 0.0008,
            "coverage_factor_k": 2.0,
        },
        "conformity": {
            "conformance_verdict": "PASS",
            "decision_rule": "ANSI/NCSL Z540.3 Method 6",
            "tur": 5.2,
            "pfa_pct": 0.01,
        },
    }
    save_job(job, db_path=test_db)

    html = generate_verifiable_evidence_capsule_html("JOB-AERO-2026-99", db_path=test_db)
    assert "<!DOCTYPE html>" in html
    assert "Verifiable Evidence Capsule" in html
    assert "SN-MIT-293-99" in html
    assert "WebCrypto" in html or "crypto.subtle.digest" in html
    assert "reverifyPayload()" in html


def test_executive_roi_calculation(test_db):
    roi = compute_executive_economic_roi(
        active_gauge_count=200,
        monthly_calibrations=40,
        technician_hourly_rate_usd=60.0,
        software_investment_cost_usd=1490.0,
        db_path=test_db,
    )
    # 40 cals * 0.75 hrs * $60 * 12 months = $21,600 labor saved
    assert roi["labor_savings"]["annual_labor_dollars_saved"] == 21600.0
    assert roi["executive_summary"]["total_annual_economic_benefit_usd"] > 35000.0
    assert roi["executive_summary"]["return_on_investment_roi_pct"] > 1000.0
    assert roi["executive_summary"]["payback_period_days"] <= 30
    assert roi["executive_summary"]["ten_year_cumulative_economic_value_usd"] > 300000.0


def test_oiml_d10_interval_optimization():
    # Stable tool with 4 consecutive PASS records and negligible drift
    history = [
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.0002}}},
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.0003}}},
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.0001}}},
        {"conformity_verdict": "PASS", "result_data": {"summary": {"error_of_indication_mm": 0.0002}}},
    ]
    res = compute_adaptive_calibration_interval(
        instrument_id="INST-001",
        manufacturer="Mitutoyo",
        model="Micrometer",
        current_interval_months=12,
        history_records=history,
        tolerance_span_mm=0.004,
    )
    assert res["interval_adjustment"] == "EXTEND"
    assert res["recommended_interval_months"] > 12
    assert res["risk_classification"] == "VERY_LOW_RISK"


def test_opcua_and_mqtt_smart_factory_bridge(test_db):
    # Test OPC-UA Node
    opcua = format_opcua_telemetry_node("DEV-FLK-8508A", db_path=test_db)
    assert opcua["status"] == "ACTIVE_NODE"
    assert opcua["node_id"] == "ns=2;s=Device_DEV-FLK-8508A"
    assert "Double" in opcua["opcua_data_variable"]["data_type"]

    # Test MQTT Sparkplug B packet ingestion
    packet = {
        "topic": "shopfloor/cell_3/cmm/probe_readings",
        "metrics": {"value": 25.00045, "unit": "mm", "asset_id": "CMM-RENISHAW-02"},
    }
    mqtt_res = ingest_mqtt_smart_cell_packet(packet, db_path=test_db)
    assert mqtt_res["status"] == "TELEMETRY_INGESTED"
    assert mqtt_res["measurement"]["value"] == 25.00045
    assert mqtt_res["asset_id"] == "CMM-RENISHAW-02"


def test_server_future_proof_endpoints():
    client = TestClient(app)

    # 1. Executive ROI endpoint
    res = client.get("/api/v1/analytics/executive-roi?active_gauges=150&monthly_cals=30&hourly_rate=50")
    assert res.status_code == 200
    data = res.json()
    assert "executive_summary" in data
    assert data["executive_summary"]["payback_period_days"] > 0

    # 2. OPC-UA endpoint
    res_opc = client.get("/api/v1/hardware/opcua-node/DEV-KEY-34461A")
    assert res_opc.status_code == 200
    assert res_opc.json()["status"] == "ACTIVE_NODE"

    # 3. MQTT telemetry endpoint
    res_mqtt = client.post(
        "/api/v1/hardware/mqtt-telemetry",
        json={"topic": "line1/robot/gauge", "metrics": {"value": 10.0019, "unit": "V"}},
    )
    assert res_mqtt.status_code == 200
    assert res_mqtt.json()["status"] == "TELEMETRY_INGESTED"

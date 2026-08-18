"""
Automated Test Suite for V5 Measurement Intelligence Engines.

Validates the 5 Core Intelligence Experiences:
1. "WHY?" — Explain This Result Engine
2. "WHAT CHANGED?" — Longitudinal Difference Engine
3. "WHAT CAUSED IT?" — Measurement Reliability Profile & Health Scoring
4. "WHAT HAPPENS NEXT?" — Drift & Out-of-Tolerance Risk Forecaster
5. "WHAT SHOULD I DO?" — Evidence-Based Action Recommender
6. REST API Endpoints via FastAPI TestClient
"""

import tempfile
import pytest
from fastapi.testclient import TestClient

from metrology_app.db import init_db, save_calculation
from metrology_app.models import CalculationCreateRequest
from metrology_app.server import app
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.intelligence_service import (
    explain_calculation,
    compare_calibrations,
    compute_instrument_reliability_profile,
    predict_drift_and_risk,
    generate_action_recommendations,
)


@pytest.fixture
def clean_intelligence_env():
    """Create a temporary isolated test environment for intelligence testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_intelligence.db"
        init_db(db_path=db_path)
        yield db_path


def test_v5_experience_1_explain_result(clean_intelligence_env):
    """Verify Experience 1: 'WHY?' produces mathematically grounded engineering explanations."""
    req = CalculationCreateRequest(
        instrument_name="Master Micrometer",
        instrument_model="Mitutoyo 293-240-30",
        nominal_value=25.00000,
        tolerance_upper=0.00200,
        tolerance_lower=-0.00200,
        confidence_level="95%",
        decision_rule="ANSI/NCSL Z540.3 Method 6",
        repeatability={"measurements": [25.0004, 25.0003, 25.0005, 25.0004, 25.0004]},
        reference_standard={"nominal_value": 25.00000, "uncertainty": 0.00030, "coverage_factor_k": 2.0},
        resolution={"resolution": 0.00100},
        record_class="CALIBRATION",
    )
    res = compute_micrometer_calibration(req, calc_id="TEST-INTEL-EXP-01", db_path=clean_intelligence_env)

    explanation = explain_calculation("TEST-INTEL-EXP-01", db_path=clean_intelligence_env)

    assert explanation["calculation_id"] == "TEST-INTEL-EXP-01"
    assert explanation["conformity_verdict"] == "PASS"
    assert "explanation_summary" in explanation
    assert "ANSI/NCSL Z540.3 Method 6" in explanation["explanation_summary"]
    assert "sensitivity_insight" in explanation
    assert "uncertainty_contributions" in explanation
    assert len(explanation["uncertainty_contributions"]) > 0
    assert explanation["top_contributor"]["percentage_contribution"] > 0
    assert len(explanation["evidence_citations"]) >= 3


def test_v5_experience_2_what_changed_engine(clean_intelligence_env):
    """Verify Experience 2: 'WHAT CHANGED?' detects longitudinal shifts between calibration cycles."""
    # Cycle 1 (Baseline)
    req1 = CalculationCreateRequest(
        instrument_name="Shop Micrometer #04",
        instrument_model="Mitutoyo 293",
        nominal_value=25.00000,
        repeatability={"measurements": [25.0001, 25.0001, 25.0002, 25.0001, 25.0001]},
        record_class="CALIBRATION",
    )
    c1 = compute_micrometer_calibration(req1, calc_id="CAL-CYCLE-01", created_at="2025-01-15T10:00:00Z", db_path=clean_intelligence_env)

    # Baseline comparison (no previous)
    diff_baseline = compare_calibrations("CAL-CYCLE-01", db_path=clean_intelligence_env)
    assert diff_baseline["comparison_available"] is False

    # Cycle 2 (1 year later, showing drift and increased dispersion)
    req2 = CalculationCreateRequest(
        instrument_name="Shop Micrometer #04",
        instrument_model="Mitutoyo 293",
        nominal_value=25.00000,
        repeatability={"measurements": [25.0006, 25.0004, 25.0008, 25.0005, 25.0007]},
        record_class="CALIBRATION",
    )
    c2 = compute_micrometer_calibration(req2, calc_id="CAL-CYCLE-02", created_at="2026-01-15T10:00:00Z", db_path=clean_intelligence_env)

    # Compare Cycle 2 to Cycle 1
    diff = compare_calibrations("CAL-CYCLE-02", previous_id="CAL-CYCLE-01", db_path=clean_intelligence_env)
    assert diff["comparison_available"] is True
    assert diff["current_id"] == "CAL-CYCLE-02"
    assert diff["previous_id"] == "CAL-CYCLE-01"
    assert diff["delta_error_mm"] > 0  # Drift detected
    assert diff["days_between_calibrations"] == 365
    assert "alert_level" in diff
    assert "summary" in diff


def test_v5_experience_3_reliability_profile_and_health_scoring(clean_intelligence_env):
    """Verify Experience 3: Reliability Profile computes 0–100 Health Score and sub-indices."""
    req = CalculationCreateRequest(
        instrument_name="Caliper-Lab-01",
        instrument_model="Mitutoyo 500-196-30",
        nominal_value=50.00000,
        tolerance_upper=0.02000,
        tolerance_lower=-0.02000,
        repeatability={"measurements": [50.002, 50.001, 50.003, 50.002, 50.002]},
        record_class="CALIBRATION",
    )
    compute_micrometer_calibration(req, calc_id="CAL-CALIPER-01", db_path=clean_intelligence_env)

    profile = compute_instrument_reliability_profile("Caliper-Lab-01", db_path=clean_intelligence_env)

    assert profile["instrument_name"] == "Caliper-Lab-01"
    assert 0 <= profile["overall_reliability_score"] <= 100
    assert profile["reliability_status"] in ("HEALTHY", "FAIR", "DEGRADED", "CRITICAL", "PRISTINE")
    assert 0 <= profile["conformity_health_index"] <= 100
    assert 0 <= profile["drift_stability_index"] <= 100
    assert 0 <= profile["repeatability_stability_index"] <= 100
    assert profile["recommended_interval_months"] in (6, 8, 12)


def test_v5_experience_4_predictive_drift_and_risk(clean_intelligence_env):
    """Verify Experience 4: Statistical drift forecasting and OOT risk calculation."""
    req = CalculationCreateRequest(
        instrument_name="Torque-Gauge-09",
        instrument_model="Sturtevant Richmont",
        nominal_value=10.00000,
        tolerance_upper=0.00200,
        tolerance_lower=-0.00200,
        repeatability={"measurements": [10.0008, 10.0007, 10.0009, 10.0008, 10.0008]},
        record_class="CALIBRATION",
    )
    compute_micrometer_calibration(req, calc_id="CAL-TORQUE-01", db_path=clean_intelligence_env)

    forecast = predict_drift_and_risk("Torque-Gauge-09", forecast_months=12, db_path=clean_intelligence_env)

    assert forecast["instrument_name"] == "Torque-Gauge-09"
    assert forecast["forecast_months"] == 12
    assert "expected_drift_mm" in forecast
    assert len(forecast["prediction_interval_95_mm"]) == 2
    assert forecast["prediction_interval_95_mm"][0] < forecast["prediction_interval_95_mm"][1]
    assert 0.0 <= forecast["probability_out_of_tolerance_pct"] <= 100.0
    assert forecast["risk_level"] in ("LOW", "ELEVATED", "HIGH")


def test_v5_experience_5_action_recommendations(clean_intelligence_env):
    """Verify Experience 5: Generates concrete, evidence-backed engineering recommendations."""
    req = CalculationCreateRequest(
        instrument_name="Depth-Mic-02",
        nominal_value=25.00000,
        repeatability={"measurements": [25.0015, 25.0005, 25.0019, 25.0008, 25.0018]},  # High dispersion
        record_class="CALIBRATION",
    )
    compute_micrometer_calibration(req, calc_id="CAL-DEPTH-01", db_path=clean_intelligence_env)

    recs = generate_action_recommendations("Depth-Mic-02", db_path=clean_intelligence_env)

    assert isinstance(recs, list)
    assert len(recs) >= 1
    for r in recs:
        assert "category" in r
        assert "priority" in r
        assert "title" in r
        assert "description" in r
        assert "evidence" in r


def test_v5_rest_api_intelligence_endpoints():
    """Verify all 5 V5 REST API endpoints are registered and functioning."""
    client = TestClient(app)

    # 1. Create a calibration via API
    calc_req = {
        "instrument_name": "API-Micrometer-X",
        "instrument_model": "Mitutoyo Digital",
        "nominal_value": 25.0,
        "tolerance_upper": 0.002,
        "tolerance_lower": -0.002,
        "record_class": "CALIBRATION",
    }
    create_res = client.post("/api/calculations", json=calc_req)
    assert create_res.status_code == 200
    calc_id = create_res.json()["id"]

    # 2. Test GET /api/intelligence/explain/{calc_id}
    res_explain = client.get(f"/api/intelligence/explain/{calc_id}")
    assert res_explain.status_code == 200
    assert res_explain.json()["calculation_id"] == calc_id

    # 3. Test GET /api/intelligence/diff/{calc_id}
    res_diff = client.get(f"/api/intelligence/diff/{calc_id}")
    assert res_diff.status_code == 200

    # 4. Test GET /api/intelligence/reliability/{instrument_name}
    res_rel = client.get("/api/intelligence/reliability/API-Micrometer-X")
    assert res_rel.status_code == 200
    assert "overall_reliability_score" in res_rel.json()

    # 5. Test GET /api/intelligence/forecast/{instrument_name}
    res_fore = client.get("/api/intelligence/forecast/API-Micrometer-X?forecast_months=12")
    assert res_fore.status_code == 200
    assert "expected_drift_mm" in res_fore.json()

    # 6. Test GET /api/intelligence/recommendations/{instrument_name}
    res_recs = client.get("/api/intelligence/recommendations/API-Micrometer-X")
    assert res_recs.status_code == 200
    assert isinstance(res_recs.json(), list)

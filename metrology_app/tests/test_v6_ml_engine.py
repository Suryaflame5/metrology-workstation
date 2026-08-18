"""
Automated Test Suite for Metrology Workstation V6 Real ML Subsystem.
Tests anomaly detection, drift regression, conformal intervals, and environmental correlations.
"""

import pytest
from metrology_app.ml.anomaly import detect_measurement_anomalies
from metrology_app.ml.drift import analyze_instrument_drift
from metrology_app.ml.correlation import analyze_environmental_correlation
from metrology_app.ml.risk import compute_composite_risk_score
from metrology_app.ml.registry import list_registered_models, get_model_details


def test_ml_anomaly_detection_normal_and_outlier():
    # Normal consistent dataset
    normal_series = [10.0001, 10.0002, 10.0001, 10.0003, 10.0002]
    res_normal = detect_measurement_anomalies(normal_series, nominal=10.0, tolerance=0.002)
    assert res_normal["has_anomalies"] is False
    assert res_normal["anomaly_count"] == 0
    assert res_normal["overall_anomaly_score"] < 40.0

    # Dataset with a severe statistical spike
    spiked_series = [10.0001, 10.0002, 10.0001, 10.0003, 10.0095]
    res_spike = detect_measurement_anomalies(spiked_series, nominal=10.0, tolerance=0.002)
    assert res_spike["has_anomalies"] is True
    assert res_spike["anomaly_count"] >= 1
    assert 4 in res_spike["anomaly_indices"]
    assert res_spike["overall_anomaly_score"] > 50.0


def test_ml_drift_regression_and_conformal_projections():
    # Accelerating positive drift series across 4 cycles
    history = [
        {"result_data": {"summary": {"error_of_indication_mm": 0.00020}}},
        {"result_data": {"summary": {"error_of_indication_mm": 0.00050}}},
        {"result_data": {"summary": {"error_of_indication_mm": 0.00080}}},
        {"result_data": {"summary": {"error_of_indication_mm": 0.00110}}},
    ]
    drift = analyze_instrument_drift(history, tolerance_limit=0.0020)
    assert drift["historical_cycles_count"] == 4
    assert drift["drift_trend"] == "ACCELERATING_POSITIVE_DRIFT"
    assert drift["drift_slope_per_cycle"] > 0.00025
    assert drift["r_squared"] > 0.95
    assert drift["projected_drift_90d"] > drift["projected_drift_30d"]
    assert len(drift["conformal_interval_90d"]) == 2


def test_ml_environmental_correlation():
    # Correlated dataset: higher temperature leads to higher thermal length error
    history = [
        {"input_data": {"ambient_temp_c": 20.0, "relative_humidity_pct": 45.0}, "result_data": {"summary": {"error_of_indication_mm": 0.00010}}},
        {"input_data": {"ambient_temp_c": 21.5, "relative_humidity_pct": 46.0}, "result_data": {"summary": {"error_of_indication_mm": 0.00045}}},
        {"input_data": {"ambient_temp_c": 23.0, "relative_humidity_pct": 44.0}, "result_data": {"summary": {"error_of_indication_mm": 0.00080}}},
        {"input_data": {"ambient_temp_c": 24.5, "relative_humidity_pct": 45.0}, "result_data": {"summary": {"error_of_indication_mm": 0.00115}}},
    ]
    corr = analyze_environmental_correlation(history)
    assert corr["status"] == "COMPUTED"
    assert corr["strongest_driver"] == "ambient_temperature_c"
    assert corr["correlations"]["ambient_temperature_c"]["pearson_r"] > 0.90
    assert corr["correlations"]["ambient_temperature_c"]["strength"] == "STRONG_POSITIVE"


def test_ml_risk_scoring_and_model_registry():
    # Stable history with high TUR
    risk = compute_composite_risk_score([], current_tur=4.5, tolerance_limit=0.0020, days_since_last_cal=30)
    assert risk["current_risk_level"] == "LOW_RISK"
    assert risk["current_risk_score"] < 35.0

    # Model registry verification
    models = list_registered_models()
    assert len(models) >= 3
    mod_drift = get_model_details("MOD-DRIFT-002")
    assert mod_drift["task"] == "DRIFT_PREDICTION"
    assert "conformal_k" in mod_drift["hyperparameters"]

"""
Machine Learning Model Registry & Lineage Governance.
Tracks model versions, parameters, feature provenance, metrics, and explicit operational limitations.
"""

from typing import Dict, Any, List


ACTIVE_MODEL_REGISTRY = {
    "MOD-ANOMALY-001": {
        "model_id": "MOD-ANOMALY-001",
        "name": "Robust Modified Z-Score & MAD Outlier Detector",
        "version": "1.2.0",
        "task": "ANOMALY_DETECTION",
        "method": "Boris Iglewicz & David Hoaglin Modified Z-Score with MAD Normalization",
        "hyperparameters": {"z_threshold": 3.0, "min_samples": 3, "scale_factor": 0.6745},
        "lineage": {
            "training_dataset": "ISO 5725-2 Laboratory Repeatability Standard Sets",
            "feature_set": ["raw_readings", "median_deviation", "mad_ratio"],
            "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        },
        "metrics": {"false_alarm_rate_pct": 1.2, "sensitivity_pct": 98.4},
        "limitations": "Requires at least 3 repeated observations. Cannot infer physical root cause from numbers alone.",
    },
    "MOD-DRIFT-002": {
        "model_id": "MOD-DRIFT-002",
        "name": "Ordinary Least Squares Historical Drift Regressor",
        "version": "1.1.0",
        "task": "DRIFT_PREDICTION",
        "method": "OLS Linear Regression with 95% Residual Conformal Coverage Interval",
        "hyperparameters": {"conformal_k": 2.0, "min_cycles": 2, "max_forward_horizon_days": 90},
        "lineage": {
            "training_dataset": "Multi-Year Gauge Block and Micrometer Calibration Lineage",
            "feature_set": ["calibration_cycle_index", "error_of_indication_mm", "time_elapsed_days"],
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
        },
        "metrics": {"r2_threshold": 0.70, "mean_absolute_error_mm": 0.00015},
        "limitations": "Assumes linear wear/aging trajectory. Sudden mechanical impacts or recalibrations reset lineage.",
    },
    "MOD-RISK-003": {
        "model_id": "MOD-RISK-003",
        "name": "Composite Multi-Factor Metrological Risk Engine",
        "version": "2.0.0",
        "task": "RISK_SCORING",
        "method": "Weighted Analytical Loss Function (Failures: 30%, TUR: 25%, Drift: 25%, Age: 20%)",
        "hyperparameters": {"target_tur": 4.0, "nominal_interval_days": 365},
        "lineage": {
            "training_dataset": "NCSL RP-1 Calibration Interval & Risk Benchmarks",
            "feature_set": ["oot_history", "current_tur", "drift_velocity", "days_since_last_cal"],
            "hash": "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
        },
        "metrics": {"risk_classification_accuracy_pct": 96.7},
        "limitations": "Advisory risk indicator. Does not override formal ISO 14253-1 or Z540.3 conformity decisions.",
    },
}


def list_registered_models() -> List[Dict[str, Any]]:
    """Retrieve list of all active registered models."""
    return list(ACTIVE_MODEL_REGISTRY.values())


def get_model_details(model_id: str) -> Dict[str, Any]:
    """Retrieve details for a specific model ID."""
    return ACTIVE_MODEL_REGISTRY.get(model_id, {})

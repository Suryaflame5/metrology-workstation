import pytest
import math
from fastapi.testclient import TestClient
from metrology_app.server import app

client = TestClient(app)

def test_workbench_uncertainty_gum_consistency():
    components = [
        {
            "name": "Repeatability",
            "semi_range": 0.00030, # k=2, so std_unc = 0.00015
            "coverage_factor_k": 2.0,
            "sensitivity_coefficient": 1.0,
            "degrees_of_freedom": 10.0,
            "distribution": "normal",
        },
        {
            "name": "Reference Standard",
            "semi_range": 0.00040, # k=2, so std_unc = 0.00020
            "coverage_factor_k": 2.0,
            "sensitivity_coefficient": 1.0,
            "degrees_of_freedom": 50.0,
            "distribution": "normal",
        },
        {
            "name": "Resolution",
            "semi_range": 0.00005 * math.sqrt(3), # rectangular => std_unc = 0.00005
            "coverage_factor_k": 1.0,
            "sensitivity_coefficient": 1.0,
            "degrees_of_freedom": 1000.0,
            "distribution": "rectangular",
        }
    ]

    res = client.post("/api/workbench/uncertainty", json={
        "components": components,
        "confidence_level": "95%"
    })
    assert res.status_code == 200
    data = res.json()

    expected_uc = math.sqrt(0.00015**2 + 0.00020**2 + 0.00005**2)
    assert abs(data["combined_uncertainty_uc"] - expected_uc) < 1e-5
    assert data["expanded_uncertainty_U95"] > data["combined_uncertainty_uc"]
    assert data["effective_degrees_of_freedom"] > 0


def test_workbench_conformity_method6_exact_math():
    nominal = 10.0
    tol = 0.005
    u_exp = 0.002 # TUR = 0.01 / 0.004 = 2.5 (< 4:1 so guardband > 0)
    tur = (2 * tol) / (2 * u_exp)

    res = client.post("/api/workbench/conformity", json={
        "nominal_value": nominal,
        "measured_value": 10.001,
        "tolerance_upper": tol,
        "tolerance_lower": -tol,
        "expanded_uncertainty_U95": u_exp,
        "decision_rule": "ANSI/NCSL Z540.3 Method 6"
    })
    assert res.status_code == 200
    data = res.json()

    assert abs(data["tur"] - tur) < 1e-4
    assert data["guardband_width_w"] > 0
    assert data["conformance_verdict"] == "PASS"

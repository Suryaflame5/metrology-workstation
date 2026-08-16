"""
Unit Tests for 12-Stage Mathematical Replay and System Self-Test.
"""

import pytest
from metrology_app.models import CalculationCreateRequest
from metrology_app.services.calculation_service import compute_micrometer_calibration
from metrology_app.services.verifier_service import replay_calculation
from metrology_app.services.selftest_service import run_system_selftest


def test_calculation_replay_reproduces_all_12_stages():
    req = CalculationCreateRequest(record_class="VALIDATION")
    res = compute_micrometer_calibration(req, calc_id="TEST-REPLAY-001")

    replay = replay_calculation("TEST-REPLAY-001")
    assert replay["reproduced_all_stages"] is True
    assert replay["total_stages"] == 12

    stage_names = [s["title"] for s in replay["stages"]]
    assert any("Type A Sample Statistics" in name for name in stage_names)
    assert any("Combined Standard Uncertainty" in name for name in stage_names)
    assert any("Welch-Satterthwaite" in name for name in stage_names)
    assert any("Conformity Assessment" in name for name in stage_names)
    assert any("Metrological Rounding" in name for name in stage_names)

    for s in replay["stages"]:
        assert s["status"] == "REPRODUCED"


def test_system_selftest_execution():
    selftest_res = run_system_selftest()
    assert selftest_res["overall_status"] == "HEALTHY"
    assert selftest_res["calculation_engine_status"] == "VERIFIED"
    assert selftest_res["evidence_engine_status"] == "VERIFIED"
    assert selftest_res["database_status"] == "INTEGRITY OK"
    assert selftest_res["benchmark_tests_passed"] == selftest_res["benchmark_tests_total"]

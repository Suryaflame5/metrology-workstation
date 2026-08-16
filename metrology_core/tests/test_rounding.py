"""
Unit tests for Metrological Rounding (TC-03, Significant Figures, Resolution Matching, Anti-Sequential Guard).
"""

import pytest
from decimal import Decimal
from metrology_core.rounding.metrological import (
    round_uncertainty,
    round_measurement_to_uncertainty,
    format_metrological_result,
    get_decimal_places,
)
from metrology_core.validation.reference_cases import run_tc03_metrological_rounding


def test_reference_tc03():
    res = run_tc03_metrological_rounding()
    assert res["status"] == "PASSED"
    assert res["formatted"] == "(12.346 ± 0.012)"


def test_round_uncertainty_various_magnitudes():
    # 2 significant figures
    assert round_uncertainty("0.01234", sig_figs=2) == Decimal("0.012")
    assert round_uncertainty("0.0004567", sig_figs=2) == Decimal("0.00046")
    assert round_uncertainty("1.234", sig_figs=2) == Decimal("1.2")
    assert round_uncertainty("12.34", sig_figs=2) == Decimal("12")
    assert round_uncertainty("123.4", sig_figs=2) == Decimal("120")
    assert round_uncertainty("1234.5", sig_figs=2) == Decimal("1200")


def test_single_significant_figure():
    assert round_uncertainty("0.034", sig_figs=1) == Decimal("0.03")
    assert round_uncertainty("0.089", sig_figs=1) == Decimal("0.09")


def test_measurement_resolution_matching():
    # Uncertainty has resolution 0.01 (2 decimal places)
    # Measurement 10.12345 should round to 10.12
    u = Decimal("0.05")
    assert round_measurement_to_uncertainty("10.12345", u) == Decimal("10.12")
    assert round_measurement_to_uncertainty("10.128", u) == Decimal("10.13")

    # Uncertainty has resolution 1 (integer)
    u_int = Decimal("10")  # resolution 1
    assert round_measurement_to_uncertainty("105.7", Decimal("5")) == Decimal("106")


def test_anti_sequential_rounding():
    # Direct vs sequential rounding edge case:
    # 12.3446 with uncertainty resolution 0.01 -> should be 12.34 directly!
    # (If done sequentially: 12.3446 -> 12.345 -> 12.35 which would be a fatal rounding bug)
    u = Decimal("0.01")
    assert round_measurement_to_uncertainty("12.3446", u) == Decimal("12.34")


def test_format_metrological_result_with_units():
    res = format_metrological_result("12.34567", "0.01234", sig_figs=2, unit="V")
    assert res.value == Decimal("12.346")
    assert res.uncertainty == Decimal("0.012")
    assert res.formatted_string == "(12.346 ± 0.012) V"
    assert res.decimal_places == 3

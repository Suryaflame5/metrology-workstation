"""
metrology_core.validation - Benchmark Reference Suite and Regression Runner.
"""

from .reference_cases import (
    run_tc01_high_tur_clamp,
    run_tc02_active_method6_curve,
    run_tc03_metrological_rounding,
    run_tc04_exact_tur4_boundary,
    run_tc05_tur_greater_than_4,
    run_tc06_tur_root_crossing,
    run_tc07_tur_greater_than_root,
    run_correlation_psd_rejection_test,
)
from .boundary_cases import run_boundary_checks
from .regression import run_full_regression

__all__ = [
    "run_tc01_high_tur_clamp",
    "run_tc02_active_method6_curve",
    "run_tc03_metrological_rounding",
    "run_tc04_exact_tur4_boundary",
    "run_tc05_tur_greater_than_4",
    "run_tc06_tur_root_crossing",
    "run_tc07_tur_greater_than_root",
    "run_correlation_psd_rejection_test",
    "run_boundary_checks",
    "run_full_regression",
]

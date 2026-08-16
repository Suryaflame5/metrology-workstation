"""
Executable Regression Test Suite for metrology-core Reference Engine v0.2.
"""

import sys
import io

# Ensure UTF-8 output on Windows consoles if needed
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
from .differential import run_all_differential_tests
from ..provenance import CalculationTrace


def run_full_regression() -> bool:
    """Run all reference, boundary, differential, and provenance tests."""
    print("=" * 75)
    print(" METROLOGY-CORE V0.2 INDEPENDENT MATHEMATICAL VERIFICATION & REGRESSION")
    print("=" * 75)

    tests = [
        ("TC-01: High-TUR clamp (TUR = 4 -> w = 0)", run_tc01_high_tur_clamp),
        ("TC-02: Active Method 6 Curve (TUR = 2 -> M ~= 0.281645, w ~= 0.0140823)", run_tc02_active_method6_curve),
        ("TC-03: Sequential Rounding & Resolution Matching", run_tc03_metrological_rounding),
        ("TC-04: Exact Decimal TUR = 4 Boundary Representation", run_tc04_exact_tur4_boundary),
        ("TC-05: TUR > 4 Non-Negativity Clamp", run_tc05_tur_greater_than_4),
        ("TC-06: TUR ~= 4.5917675 Multiplier Zero Crossing", run_tc06_tur_root_crossing),
        ("TC-07: TUR > 4.5917675 Zero-Guardband Clamp Verification", run_tc07_tur_greater_than_root),
        ("PSD: Correlation Matrix Non-Positive Semi-Definite Rejection", run_correlation_psd_rejection_test),
    ]

    all_passed = True

    print(" 1. Benchmark Reference Suite:")
    for name, test_fn in tests:
        try:
            result = test_fn()
            print(f"  [PASS] {name}")
        except Exception as e:
            all_passed = False
            print(f"  [FAIL] {name}")
            print(f"         Error: {e}")

    print("-" * 75)
    print(" 2. Differential Testing (GUM Analytical vs JCGM 101 Monte Carlo):")
    try:
        diff_results = run_all_differential_tests()
        for d in diff_results:
            print(f"  [PASS] {d['name']} (diff = {d['diff_pct']}%)")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] Differential validation: {e}")

    print("-" * 75)
    print(" 3. Boundary & Singular Stress Suite:")
    boundary_results = run_boundary_checks()
    for b in boundary_results:
        status = b["status"]
        name = b["name"]
        if status == "PASSED":
            print(f"  [PASS] {name}")
        else:
            all_passed = False
            print(f"  [FAIL] {name}: {b.get('reason') or b.get('error')}")

    print("-" * 75)
    print(" 4. Cryptographic Provenance Integrity Verification:")
    try:
        trace = CalculationTrace(
            calculation_id="MC-VERIFY-001",
            measurement_model="Test",
            input_data={"x": 1},
            uncertainty_components=[],
            sensitivity_coefficients=[],
            covariance_matrix=None,
            combined_uncertainty={},
            degrees_of_freedom={},
            coverage_factor={},
            expanded_uncertainty={},
            decision_rule={},
            guardband={},
            conformity_decision={},
            rounding={},
        )
        assert trace.verify_integrity() is True
        print(f"  [PASS] Calculation Provenance Trace SHA-256: {trace.sha256_hash[:16]}... (Self-Verifying)")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] Provenance Trace verification: {e}")

    print("=" * 75)
    if all_passed:
        print(" ALL INDEPENDENT MATHEMATICAL CHECKS & REGRESSION BENCHMARKS PASSED.")
        print("=" * 75)
        return True
    else:
        print(" SOME VERIFICATION CHECKS FAILED. PLEASE REVIEW.")
        print("=" * 75)
        return False


if __name__ == "__main__":
    success = run_full_regression()
    sys.exit(0 if success else 1)

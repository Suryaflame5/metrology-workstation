"""
Automated Test Suite for NIST CTS Reference Benchmarks, ISO 17043 ILC Simulator, and Industry Profiles.
"""

import pytest
from metrology_app.benchmarks.nist_benchmarks import run_nist_benchmark_verification
from metrology_app.benchmarks.ilc_pt import evaluate_interlaboratory_en_ratio, simulate_proficiency_testing_round
from metrology_app.profiles.industry_profiles import list_industry_profiles, get_industry_profile, IndustrySector
from metrology_app.support.support_bundle import generate_enterprise_support_bundle
from metrology_app.support.handbook import list_handbook_articles


def test_nist_cts_reference_benchmarks_zero_deviation():
    bench_res = run_nist_benchmark_verification()
    assert bench_res["status"] == "NIST_EQUIVALENCE_PROVEN"
    assert bench_res["total_benchmarks"] >= 3
    assert bench_res["benchmarks_passed"] == bench_res["total_benchmarks"]


def test_iso_17043_interlaboratory_en_ratio():
    # Satisfactory participant (En <= 1.0)
    res_pass = evaluate_interlaboratory_en_ratio(
        lab_value=25.00010,
        lab_expanded_uncertainty=0.00040,
        reference_value=25.00000,
        reference_expanded_uncertainty=0.00015,
    )
    assert res_pass["is_satisfactory"] is True
    assert abs(res_pass["en_ratio"]) <= 1.0

    # Non-conforming participant with large bias (En > 1.0)
    res_fail = evaluate_interlaboratory_en_ratio(
        lab_value=25.00200,
        lab_expanded_uncertainty=0.00040,
        reference_value=25.00000,
        reference_expanded_uncertainty=0.00015,
    )
    assert res_fail["is_satisfactory"] is False
    assert abs(res_fail["en_ratio"]) > 1.0


def test_industry_profiles_and_handbook():
    profiles = list_industry_profiles()
    assert len(profiles) == 4
    sectors = [p["sector"] for p in profiles]
    assert "AEROSPACE_DEFENSE" in sectors
    assert "AUTOMOTIVE_EV" in sectors
    assert "MEDICAL_PHARMA" in sectors
    assert "SEMICONDUCTOR_PHOTONICS" in sectors

    aero = get_industry_profile(IndustrySector.AEROSPACE_DEFENSE)
    assert "AS9100D" in aero["regulatory_standards"][0]
    assert len(aero["templates"]) >= 2

    # Handbook
    articles = list_handbook_articles()
    assert len(articles) >= 4


def test_enterprise_support_bundle():
    bundle = generate_enterprise_support_bundle()
    assert bundle["support_bundle_id"].startswith("MW-SLA-BUNDLE-")
    assert len(bundle["sha256_checksum"]) == 64
    assert bundle["bundle_data"]["support_sla_tier"] == "ENTERPRISE_24x7_MISSION_CRITICAL"

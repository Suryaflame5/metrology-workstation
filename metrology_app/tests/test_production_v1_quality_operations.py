"""
End-to-End Acceptance & Unit Test Suite for Production V1:
Industrial Measurement & Quality Operations Workstation.
"""

import os
import tempfile
import pytest
from ..db import (
    init_db,
    save_part,
    get_part,
    list_parts,
    save_machine,
    list_machines,
    get_cost_configuration,
    save_cost_configuration,
    list_inspection_jobs,
    get_inspection_job,
    list_loss_events,
    list_investigations,
    list_corrective_actions,
    list_recovery_events,
    list_quality_alerts,
)
from ..services.loss_engine import (
    calculate_inspection_loss_exposure,
    evaluate_machine_drift_loss,
    get_factory_financial_summary,
)
from ..services.investigation_engine import (
    run_root_cause_correlation_analysis,
    create_investigation_from_job_issue,
)
from ..services.recovery_engine import compare_before_after_recovery
from ..services.demo_factory_data import seed_demo_factory_operations
from ..services.watchfolder_service import ingest_measurement_file
from ..services.production_report_service import (
    generate_inspection_report_html,
    generate_loss_recovery_report_html,
)


@pytest.fixture
def test_db():
    """Create an isolated temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix="_test_prod_v1.db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_seed_demo_factory_and_acceptance_workflow(test_db):
    """
    Acceptance Test Scenario (Section 38):
    1. Factory creates Part A (Diameter 10 ± 0.10 mm).
    2. Machine #4 produces 100 parts with progressive tool wear.
    3. System detects diameter drift, 12 defects, and ₹36,000 exposure.
    4. System creates Root-Cause Investigation correlating Tool #17.
    5. Engineer records corrective action (insert replacement).
    6. Post-correction job verified (100% PASS, 0 defects).
    7. System compares Before vs After and proves ₹28,800/mo recovered value.
    """
    seed_res = seed_demo_factory_operations(db_path=test_db)
    assert seed_res["status"] == "SUCCESS"

    # Verify Part A
    parts = list_parts(db_path=test_db)
    assert len(parts) >= 1
    part_a = get_part("PART-A-10MM", db_path=test_db)
    assert part_a is not None
    assert len(part_a["revisions"]) >= 1

    # Verify Machine #4
    machines = list_machines(db_path=test_db)
    assert any(m["machine_code"] == "Machine #4" for m in machines)

    # Verify Baseline Job #1 (12 failures, review required)
    job_1 = get_inspection_job("INSP-DEMO-001", db_path=test_db)
    assert job_1 is not None
    assert job_1["total_parts"] == 100
    assert job_1["failed_parts"] == 12
    assert job_1["status"] == "REVIEW_REQUIRED"
    assert len(job_1["measurements"]) == 100

    # Verify Loss Event & Exposure
    losses = list_loss_events(db_path=test_db)
    assert len(losses) >= 1
    assert any(l["estimated_loss_amount"] == 36000.0 for l in losses)

    # Verify Investigation & Tool #17 Correlation
    invs = list_investigations(db_path=test_db)
    assert len(invs) >= 1
    assert invs[0]["status"] == "CORRELATION_DETECTED"
    assert "Tool #17" in str(invs[0]["correlation_matrix"])

    # Verify Post-Action Verification Job #2 (100% PASS)
    job_2 = get_inspection_job("INSP-DEMO-002", db_path=test_db)
    assert job_2 is not None
    assert job_2["failed_parts"] == 0
    assert job_2["status"] == "APPROVED"

    # Verify Recovery ROI Proof Event
    recoveries = list_recovery_events(db_path=test_db)
    assert len(recoveries) >= 1
    rec = recoveries[0]
    assert rec["actual_recovered_amount"] == 28800.0
    assert rec["recovery_percentage"] == 100.0


def test_loss_calculation_formulas(test_db):
    """Verify deterministic loss breakdown math."""
    save_cost_configuration(
        {
            "currency": "₹",
            "scrap_cost_per_part": 1500.0,
            "rework_cost_per_part": 400.0,
            "inspection_labor_cost_per_hr": 500.0,
            "downtime_cost_per_hr": 2000.0,
        },
        db_path=test_db,
    )

    res = calculate_inspection_loss_exposure(
        job_id="TEST-JOB-01",
        total_parts=100,
        passed_parts=90,
        failed_parts=10,
        scrap_count=8,
        rework_count=2,
        inspection_hours=1.0,
        machine_downtime_hours=0.5,
        db_path=test_db,
    )

    assert res["currency"] == "₹"
    assert res["breakdown"]["scrap_loss"] == 8 * 1500.0  # 12000
    assert res["breakdown"]["rework_loss"] == 2 * 400.0   # 800
    assert res["breakdown"]["inspection_labor_cost"] == 1.0 * 500.0  # 500
    assert res["breakdown"]["downtime_loss"] == 0.5 * 2000.0  # 1000
    assert res["total_loss"] == 14300.0


def test_drift_detection_and_alerting(test_db):
    """Verify machine drift detection on increasing measurements."""
    # 30 readings progressively drifting upward towards upper tolerance
    readings = [10.000 + (i * 0.003) for i in range(30)]
    drift = evaluate_machine_drift_loss(
        machine_code="Machine #4",
        part_name="Shaft",
        measurements=readings,
        nominal=10.0,
        tol_upper=0.100,
        tol_lower=-0.100,
        db_path=test_db,
    )
    assert drift is not None
    assert drift["pct_drift_of_tolerance"] >= 25.0
    assert drift["potential_scrap_exposure"] > 0


def test_before_after_recovery_engine(test_db):
    """Test Before vs After ROI calculation between two jobs."""
    seed_demo_factory_operations(db_path=test_db)
    res = compare_before_after_recovery(
        baseline_job_id="INSP-DEMO-001",
        verification_job_id="INSP-DEMO-002",
        verified_by="QA Director",
        db_path=test_db,
    )
    assert res["status"] == "VERIFIED_ROI_PROOF"
    assert res["comparison"]["defect_rate_reduction_pct"] == 12.0
    assert res["comparison"]["monthly_recovered_value"] > 0


def test_production_reports_html_generation(test_db):
    """Verify HTML generation for Inspection and Recovery reports."""
    seed_demo_factory_operations(db_path=test_db)
    insp_html = generate_inspection_report_html("INSP-DEMO-001", db_path=test_db)
    assert "NovyraX Quality Operations Workstation" in insp_html
    assert "INSP-2026-0831-01" in insp_html

    rec_html = generate_loss_recovery_report_html(db_path=test_db)
    assert "Total Verified Monthly Recovery Value" in rec_html
    assert "ROI VERIFIED" in rec_html

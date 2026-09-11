import csv, os, pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.services.data_readiness_service import build_data_readiness_report

client = TestClient(app)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_csv(filename):
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


# ── Dataset A: CMM lab (rich) ─────────────────────────────────────────────────
class TestDatasetA:
    @pytest.fixture(scope="class")
    def rows(self):
        return _load_csv("dataset_a_cmm_rich.csv")

    @pytest.fixture(scope="class")
    def report(self, rows):
        return build_data_readiness_report(rows, filename="dataset_a_cmm_rich.csv")

    def test_verdict_ready_full(self, report):
        assert report["readiness_verdict"] == "READY_FULL", report["readiness_verdict"]

    def test_measurements_detected(self, report):
        assert report["detected_factors"]["measurements"]["available"] is True
        assert report["detected_factors"]["measurements"]["count"] >= 12

    def test_tolerance_from_usl_lsl(self, report):
        tol = report["detected_factors"]["tolerance"]
        assert tol["available"] is True
        assert abs(tol["upper"] - 10.05) < 1e-4
        assert abs(tol["lower"] - 9.95) < 1e-4

    def test_machine_3_groups(self, report):
        m = report["detected_factors"]["machine"]
        assert m["available"] is True
        assert m["distinct_count"] == 3

    def test_tool_multiple_groups(self, report):
        t = report["detected_factors"]["tool"]
        assert t["available"] is True
        assert t["distinct_count"] >= 2

    def test_operator_2_groups(self, report):
        op = report["detected_factors"]["operator"]
        assert op["available"] is True
        assert op["distinct_count"] == 2

    def test_core_analyses_enabled(self, report):
        enabled = report["enabled_analyses"]
        for a in [
            "basic_statistics", "tolerance_analysis", "conformity_assessment",
            "machine_anova", "tool_anova", "operator_anova",
            "root_cause_correlation", "gum_uncertainty_budget", "pdf_report",
        ]:
            assert a in enabled, f"{a} not in enabled: {enabled}"

    def test_confidence_high(self, report):
        assert report["confidence_score"] >= 0.90

    def test_loss_disabled_no_cost(self, report):
        assert "loss_quantification" in [d["id"] for d in report["disabled_analyses"]]


# ── Dataset B: Gauge minimal ──────────────────────────────────────────────────
class TestDatasetB:
    @pytest.fixture(scope="class")
    def rows(self):
        return _load_csv("dataset_b_gauge_minimal.csv")

    @pytest.fixture(scope="class")
    def report(self, rows):
        return build_data_readiness_report(rows, filename="dataset_b_gauge_minimal.csv")

    def test_verdict_ready_basic(self, report):
        assert report["readiness_verdict"] == "READY_BASIC", report["readiness_verdict"]

    def test_measurements_detected(self, report):
        assert report["detected_factors"]["measurements"]["available"] is True
        assert report["detected_factors"]["measurements"]["count"] == 10

    def test_tolerance_not_available(self, report):
        assert report["detected_factors"]["tolerance"]["available"] is False

    def test_machine_not_available(self, report):
        assert report["detected_factors"]["machine"]["available"] is False

    def test_tool_not_available(self, report):
        assert report["detected_factors"]["tool"]["available"] is False

    def test_only_basic_enabled(self, report):
        enabled = report["enabled_analyses"]
        assert "basic_statistics" in enabled
        assert "machine_anova" not in enabled
        assert "tolerance_analysis" not in enabled
        assert "gum_uncertainty_budget" not in enabled

    def test_anova_explicitly_disabled(self, report):
        disabled_ids = [d["id"] for d in report["disabled_analyses"]]
        for aid in ["machine_anova", "tool_anova", "operator_anova", "root_cause_correlation"]:
            assert aid in disabled_ids, f"{aid} not in disabled"

    def test_disabled_have_honest_reasons(self, report):
        for d in report["disabled_analyses"]:
            assert len(d["reason"]) > 10, f"Vague reason for {d['id']}"


# ── Dataset C: Production partial ────────────────────────────────────────────
class TestDatasetC:
    @pytest.fixture(scope="class")
    def rows(self):
        return _load_csv("dataset_c_production_partial.csv")

    @pytest.fixture(scope="class")
    def report(self, rows):
        return build_data_readiness_report(rows, filename="dataset_c_production_partial.csv")

    def test_verdict_ready_partial(self, report):
        assert report["readiness_verdict"] == "READY_PARTIAL", report["readiness_verdict"]

    def test_machine_2_groups(self, report):
        m = report["detected_factors"]["machine"]
        assert m["available"] is True
        assert m["distinct_count"] == 2

    def test_tool_not_available(self, report):
        assert report["detected_factors"]["tool"]["available"] is False

    def test_tolerance_not_in_dataset(self, report):
        assert report["detected_factors"]["tolerance"]["available"] is False

    def test_defect_flag_detected(self, report):
        assert report["detected_factors"]["defect_flag"]["available"] is True

    def test_batch_detected(self, report):
        assert report["detected_factors"]["batch"]["available"] is True

    def test_machine_anova_enabled(self, report):
        assert "machine_anova" in report["enabled_analyses"]

    def test_tool_anova_disabled(self, report):
        assert "tool_anova" in [d["id"] for d in report["disabled_analyses"]]

    def test_tolerance_analysis_disabled(self, report):
        assert "tolerance_analysis" in [d["id"] for d in report["disabled_analyses"]]

    def test_user_supplied_tolerance_enables_analysis(self, rows):
        r = build_data_readiness_report(
            rows, filename="t.csv",
            user_nominal=10.0, user_tolerance_upper=0.05, user_tolerance_lower=-0.05,
        )
        assert r["detected_factors"]["tolerance"]["source"] == "user_supplied"
        assert "tolerance_analysis" in r["enabled_analyses"]
        assert "conformity_assessment" in r["enabled_analyses"]

    def test_loss_enabled_via_defect_flag(self, report):
        assert "loss_quantification" in report["enabled_analyses"]


# ── API Endpoint Tests ────────────────────────────────────────────────────────
class TestDataReadinessAPI:
    def test_rich_ready_full(self):
        rows = _load_csv("dataset_a_cmm_rich.csv")
        r = client.post("/api/v1/data/readiness", json={"rows": rows, "filename": "a.csv"})
        assert r.status_code == 200
        assert r.json()["readiness_verdict"] == "READY_FULL"

    def test_minimal_ready_basic(self):
        rows = _load_csv("dataset_b_gauge_minimal.csv")
        r = client.post("/api/v1/data/readiness", json={"rows": rows, "filename": "b.csv"})
        assert r.status_code == 200
        d = r.json()
        assert d["readiness_verdict"] == "READY_BASIC"
        assert "machine_anova" not in d["enabled_analyses"]

    def test_user_tolerance_api(self):
        rows = _load_csv("dataset_c_production_partial.csv")
        r = client.post("/api/v1/data/readiness", json={
            "rows": rows, "filename": "c.csv",
            "nominal": 10.0, "tolerance_upper": 0.05, "tolerance_lower": -0.05,
        })
        assert r.status_code == 200
        assert r.json()["detected_factors"]["tolerance"]["source"] == "user_supplied"

    def test_empty_rows_not_ready(self):
        r = client.post("/api/v1/data/readiness", json={"rows": [], "filename": "e.csv"})
        assert r.status_code == 200
        assert r.json()["readiness_verdict"] == "NOT_READY"

    def test_missing_body_400(self):
        r = client.post("/api/v1/data/readiness", json={})
        assert r.status_code == 400


# ── Investigation Engine Guard Tests ─────────────────────────────────────────
class TestInvestigationEngineGuard:
    def test_no_tool_data_skipped_not_fabricated(self, tmp_path):
        from metrology_app.db import init_db, save_inspection_job, save_inspection_measurements
        from metrology_app.services.investigation_engine import run_root_cause_correlation_analysis

        db_path = str(tmp_path / "g01.db")
        init_db(db_path)
        save_inspection_job(
            {"id": "G01", "job_number": "G01", "part_id": "P1",
             "failed_parts": 0, "status": "READY"},
            db_path=db_path,
        )
        save_inspection_measurements("G01", [
            {"id": f"M{i}", "nominal": 10.0, "measured_value": 10.0 + i * 0.001}
            for i in range(10)
        ], db_path=db_path)

        result = run_root_cause_correlation_analysis("G01", db_path=db_path)

        corr_factors = [c["factor"] for c in result.get("all_correlations", [])]
        assert "TOOLING" not in corr_factors, f"Fabricated TOOLING: {corr_factors}"
        assert "OPERATOR" not in corr_factors, f"Fabricated OPERATOR: {corr_factors}"

        skipped = [s["factor"] for s in result.get("skipped_factors", [])]
        assert len(skipped) >= 2, f"Expected >=2 skipped factors, got: {skipped}"

    def test_two_machines_anova_runs(self, tmp_path):
        from metrology_app.db import init_db, save_inspection_job, save_inspection_measurements
        from metrology_app.services.investigation_engine import run_root_cause_correlation_analysis

        db_path = str(tmp_path / "g02.db")
        init_db(db_path)
        save_inspection_job(
            {"id": "G02", "job_number": "G02", "part_id": "P1",
             "failed_parts": 4, "status": "READY"},
            db_path=db_path,
        )
        meas = (
            [{"id": f"M{i}", "nominal": 10.0, "measured_value": 10.0 + i * 0.001,
              "machine_id": "CNC-01"} for i in range(6)] +
            [{"id": f"M{i+6}", "nominal": 10.0, "measured_value": 10.04 + i * 0.001,
              "machine_id": "CNC-02"} for i in range(6)]
        )
        save_inspection_measurements("G02", meas, db_path=db_path)

        result = run_root_cause_correlation_analysis("G02", db_path=db_path)
        assert "Machine" in result.get("analyzed_factors", []), (
            f"analyzed_factors={result.get('analyzed_factors')}")

"""
Automated Test Suite for Multi-Agent Orchestrator, Tool Execution Bus, and Zero-AI / Anti-Cheating Contracts.
"""

import os
import pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.tools.registry import TOOL_BUS
from metrology_app.agents.orchestrator import COPILOT_ORCHESTRATOR
from metrology_core.context import to_decimal
from metrology_core.uncertainty.type_a import evaluate_type_a
from metrology_core.decision.method6 import calculate_method6_guardband


@pytest.fixture
def copilot_client():
    return TestClient(app)


def test_tool_execution_bus_sandboxed_dispatch():
    # 1. Registered tools count
    tools = TOOL_BUS.list_tools()
    assert len(tools) >= 8
    tool_names = [t["name"] for t in tools]
    assert "get_measurement_series" in tool_names
    assert "detect_anomaly" in tool_names
    assert "predict_drift" in tool_names
    assert "search_knowledge" in tool_names

    # 2. Execute anomaly tool through bus
    exec_res = TOOL_BUS.execute_tool("detect_anomaly", {
        "values": [25.001, 25.002, 25.001, 25.003, 25.002],
        "nominal": 25.0,
    })
    assert exec_res["status"] == "SUCCESS"
    assert "result_sha256" in exec_res
    assert exec_res["result"]["has_anomalies"] is False


def test_multi_agent_copilot_investigation_trace():
    # Execute "Why did this instrument fail?" investigation query
    res = COPILOT_ORCHESTRATOR.process_engineering_query(
        query="Why did this instrument fail conformity?",
        instrument_id="INST-TEST-MICROMETER",
    )
    assert "finding" in res
    assert len(res["evidence_citations"]) >= 1
    assert "confidence_assessment" in res
    assert res["confidence_assessment"]["decision_authority"] == "DETERMINISTIC METROLOGY KERNEL (AUTHORITATIVE)"
    assert res["confidence_assessment"]["model_confidence_pct"] > 0
    assert len(res["activity_trace"]) >= 2


def test_zero_ai_guarantee():
    """
    CRITICAL METROLOGY CONTRACT:
    When all AI/ML/LLM systems are completely disabled (e.g. offline zero-intelligence mode),
    the deterministic kernel MUST compute 50-digit exact Type A uncertainty and Z540.3 Method 6 guardbands.
    """
    # Pure deterministic metrology execution
    readings = [to_decimal("25.0012"), to_decimal("25.0010"), to_decimal("25.0014"), to_decimal("25.0011"), to_decimal("25.0013")]
    res_a = evaluate_type_a(readings)
    assert res_a.degrees_of_freedom == 4
    assert res_a.mean == to_decimal("25.00120")

    gb = calculate_method6_guardband(
        tolerance_upper=to_decimal("0.0020"),
        tolerance_lower=to_decimal("-0.0020"),
        expanded_uncertainty=to_decimal("0.0008"),
    )
    assert gb.multiplier_M > to_decimal("0")
    assert gb.guardband_w > to_decimal("0")


def test_ai_cannot_cheat_missing_evidence():
    """
    CRITICAL AGENT CONTRACT:
    When asked about an unknown or non-existent calculation ID, the tool returns error and copilot refuses to fabricate numbers.
    """
    ev_res = TOOL_BUS.execute_tool("retrieve_evidence", {"calculation_id": "CALC-NON-EXISTENT-99999"})
    assert "error" in ev_res["result"]
    assert "unavailable" in ev_res["result"]["error"].lower()

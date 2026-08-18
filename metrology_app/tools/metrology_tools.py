"""
Concrete Tool Handlers for Metrology Workstation V6.
Wraps deterministic core, ML models, RAG search, and evidence queries.
"""

from typing import Dict, Any, List, Optional
from .registry import TOOL_BUS, ToolDefinition
from ..db import list_measurements, list_calculations, get_calculation, get_instrument
from ..ml.anomaly import detect_measurement_anomalies
from ..ml.drift import analyze_instrument_drift
from ..ml.correlation import analyze_environmental_correlation
from ..ml.risk import compute_composite_risk_score
from ..rag.retriever import search_engineering_knowledge
from ..services.mbom_service import generate_measurement_bill_of_materials
from ..services.workbench_service import compute_uncertainty_workbench, compute_conformity_workbench
from ..models import UncertaintyComponentItem, ConformityWorkbenchRequest


def tool_get_measurement_series(instrument_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    measurements = list_measurements(limit=limit)
    if instrument_id:
        measurements = [m for m in measurements if m.get("instrument_id") == instrument_id]
    return {"count": len(measurements), "measurements": measurements}


def tool_get_instrument_history(instrument_id: str) -> Dict[str, Any]:
    calcs = list_calculations(limit=50)
    matching = [c for c in calcs if c.get("instrument_id") == instrument_id or instrument_id.lower() in c.get("instrument_name", "").lower()]
    return {"instrument_id": instrument_id, "calibrations_count": len(matching), "history": matching}


def tool_detect_anomaly(values: List[float], nominal: float, tolerance: Optional[float] = None) -> Dict[str, Any]:
    return detect_measurement_anomalies(values=values, nominal=nominal, tolerance=tolerance)


def tool_predict_drift(instrument_id: str, tolerance_limit: float = 0.0020) -> Dict[str, Any]:
    history_res = tool_get_instrument_history(instrument_id)
    return analyze_instrument_drift(history_res.get("history", []), tolerance_limit=tolerance_limit)


def tool_calculate_risk(instrument_id: str, current_tur: float = 4.0, tolerance_limit: float = 0.0020) -> Dict[str, Any]:
    history_res = tool_get_instrument_history(instrument_id)
    return compute_composite_risk_score(history_res.get("history", []), current_tur=current_tur, tolerance_limit=tolerance_limit)


def tool_search_knowledge(query: str, top_k: int = 3) -> Dict[str, Any]:
    results = search_engineering_knowledge(query=query, top_k=top_k)
    return {"query": query, "results_count": len(results), "documents": results}


def tool_retrieve_evidence(calculation_id: str) -> Dict[str, Any]:
    rec = get_calculation(calculation_id)
    if not rec:
        return {"error": f"Evidence calculation ID '{calculation_id}' unavailable."}
    return {
        "calculation_id": calculation_id,
        "input_sha256": rec.get("input_sha256"),
        "calculation_sha256": rec.get("calculation_sha256"),
        "conformity_verdict": rec.get("conformity_verdict"),
        "nominal_value": rec.get("nominal_value"),
        "summary": rec.get("result_data", {}).get("summary", {}),
        "uncertainty_summary": rec.get("result_data", {}).get("uncertainty_summary", {}),
        "decision_summary": rec.get("result_data", {}).get("decision_summary", {}),
    }


def tool_get_environment_correlation(instrument_id: str) -> Dict[str, Any]:
    history_res = tool_get_instrument_history(instrument_id)
    return analyze_environmental_correlation(history_res.get("history", []))


def tool_generate_mbom(calculation_id: str) -> Dict[str, Any]:
    return generate_measurement_bill_of_materials(calculation_id)


# Register all tools into TOOL_BUS
TOOL_BUS.register(ToolDefinition(
    name="get_measurement_series",
    description="Retrieve raw repeated measurement series and sample stats for an instrument asset.",
    handler=tool_get_measurement_series,
    parameters={"instrument_id": "string (optional)", "limit": "integer (optional, default 10)"},
    permission_level="READ",
))

TOOL_BUS.register(ToolDefinition(
    name="get_instrument_history",
    description="Retrieve chronological calibration history and error trends for an instrument asset.",
    handler=tool_get_instrument_history,
    parameters={"instrument_id": "string"},
    permission_level="READ",
))

TOOL_BUS.register(ToolDefinition(
    name="detect_anomaly",
    description="Run robust statistical anomaly scoring (MAD / Modified Z-Score) on a measurement dataset.",
    handler=tool_detect_anomaly,
    parameters={"values": "list of floats", "nominal": "float", "tolerance": "float (optional)"},
    permission_level="ANALYZE",
))

TOOL_BUS.register(ToolDefinition(
    name="predict_drift",
    description="Execute historical drift regression and calculate 30/60/90-day conformal projections.",
    handler=tool_predict_drift,
    parameters={"instrument_id": "string", "tolerance_limit": "float (optional)"},
    permission_level="ANALYZE",
))

TOOL_BUS.register(ToolDefinition(
    name="calculate_risk",
    description="Compute 0-100 composite metrological risk score based on drift, TUR, and failures.",
    handler=tool_calculate_risk,
    parameters={"instrument_id": "string", "current_tur": "float", "tolerance_limit": "float"},
    permission_level="ANALYZE",
))

TOOL_BUS.register(ToolDefinition(
    name="search_knowledge",
    description="Hybrid RAG search across ISO standards, laboratory SOPs, and calibration manuals.",
    handler=tool_search_knowledge,
    parameters={"query": "string", "top_k": "integer (optional, default 3)"},
    permission_level="READ",
))

TOOL_BUS.register(ToolDefinition(
    name="retrieve_evidence",
    description="Fetch cryptographic calculation trace, SHA-256 hashes, and audit record for a result ID.",
    handler=tool_retrieve_evidence,
    parameters={"calculation_id": "string"},
    permission_level="READ",
))

TOOL_BUS.register(ToolDefinition(
    name="get_environment_correlation",
    description="Compute correlation between ambient temperature/humidity and measurement error of indication.",
    handler=tool_get_environment_correlation,
    parameters={"instrument_id": "string"},
    permission_level="ANALYZE",
))

TOOL_BUS.register(ToolDefinition(
    name="generate_mbom",
    description="Construct full Measurement Bill of Materials (MBOM) specification tree for a result ID.",
    handler=tool_generate_mbom,
    parameters={"calculation_id": "string"},
    permission_level="READ",
))

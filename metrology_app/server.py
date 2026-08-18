"""
FastAPI Server for Metrology Workstation and REST API (v0.9.0 Release Candidate).
"""

import os
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings, save_settings, get_resource_path
from .models import (
    CalculationCreateRequest,
    CalculationResponse,
    MultiPointCalculationCreateRequest,
    MultiPointCalculationResponse,
    ProjectCreateRequest,
    InstrumentCreateRequest,
    MeasurementPlanCreateRequest,
    MeasurementAcquisitionRequest,
    UncertaintyWorkbenchRequest,
    ConformityWorkbenchRequest,
)
from .db import (
    init_db,
    list_calculations,
    get_calculation,
    get_revision_history,
    get_dashboard_stats,
    list_audit_events,
    save_project,
    get_project,
    list_projects,
    delete_project,
    save_instrument,
    get_instrument,
    list_instruments,
    delete_instrument,
    save_measurement_plan,
    get_measurement_plan,
    list_measurement_plans,
    save_measurement,
    get_measurement,
    list_measurements,
    get_v5_dashboard_stats,
)
from .services.workbench_service import compute_uncertainty_workbench, compute_conformity_workbench
from .services.acquisition_service import analyze_measurement_series
from .services.procedure_service import get_available_procedures, get_procedure_by_id
from .services.calculation_service import compute_micrometer_calibration, compute_multi_point_calibration
from .services.evidence_service import export_evidence_package_zip_bytes
from .services.report_service import generate_html_report
from .services.verifier_service import verify_calculation_by_id, verify_calculation_record, replay_calculation
from .services.selftest_service import run_system_selftest
from .services.license_service import get_license_info
from .services.audit_service import record_audit_event, verify_audit_ledger
from .services.backup_service import create_database_backup, list_backups, restore_database_backup

app = FastAPI(
    title="Metrology Workstation",
    version="1.0.0",
    description="Commercial Evidence-First Calibration & Measurement Uncertainty Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()


@app.get("/api/license")
def api_get_license():
    """Retrieve commercial license and entitlement information."""
    return get_license_info()


@app.post("/api/license/trial")
def api_activate_trial():
    """Activate 14-day Professional Trial."""
    from .services.license_service import EntitlementService
    ent = EntitlementService.activate_trial(duration_days=14)
    return {"status": "SUCCESS", "entitlement": ent}


@app.post("/api/license/activate")
def api_activate_license(payload: Dict[str, Any]):
    """Apply and verify a signed license token JSON."""
    from .services.license_service import EntitlementService
    try:
        raw_json = payload.get("token_json") or json.dumps(payload)
        ent = EntitlementService.apply_license_token(raw_json)
        return {"status": "SUCCESS", "entitlement": ent}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/license/reset")
def api_reset_license():
    """Reset to Free / Community Evaluation edition."""
    from .services.license_service import LICENSE_FILE, EntitlementService
    if os.path.exists(LICENSE_FILE):
        try:
            os.remove(LICENSE_FILE)
        except Exception:
            pass
    return {"status": "RESET", "entitlement": EntitlementService.get_current_entitlement()}


@app.get("/api/stats")
def api_get_stats():
    """Get dashboard summary metrics for production calibrations."""
    return get_dashboard_stats()


@app.get("/api/settings")
def api_get_settings():
    """Load laboratory and application settings."""
    return load_settings()


@app.post("/api/settings")
def api_save_settings(settings: Dict[str, Any]):
    """Save laboratory profile and application preferences."""
    save_settings(settings)
    record_audit_event("SETTINGS_UPDATED", "SYSTEM", "Administrator", {"updated_keys": list(settings.keys())})
    return {"status": "SAVED", "settings": load_settings()}


@app.get("/api/selftest")
def api_get_selftest():
    """Execute system self-test and return health status."""
    res = run_system_selftest()
    record_audit_event("SELF_TEST_EXECUTED", "SYSTEM", "System Auto-Check", {"status": res["overall_status"]})
    return res


@app.get("/api/procedures")
def api_get_procedures():
    """Get list of supported calibration procedures."""
    return get_available_procedures()


@app.get("/api/calculations")
def api_list_calculations(
    record_class: Optional[str] = Query(default="CALIBRATION"),
    limit: int = Query(default=50),
):
    """List calculations filtered by record class (CALIBRATION, VALIDATION, SELF_TEST)."""
    filter_class = None if record_class == "ALL" else record_class
    return list_calculations(record_class=filter_class, limit=limit)


@app.get("/api/calculations/{calc_id}")
def api_get_calculation(calc_id: str):
    """Get detailed calculation record by ID."""
    rec = get_calculation(calc_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Calculation '{calc_id}' not found")
    return rec


@app.get("/api/calculations/{calc_id}/revisions")
def api_get_revisions(calc_id: str):
    """Get all revisions of a calculation."""
    rec = get_calculation(calc_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Calculation '{calc_id}' not found")
    root_id = rec.get("root_id") or calc_id
    return get_revision_history(root_id)


@app.post("/api/calculations", response_model=CalculationResponse)
def api_create_calculation(request: CalculationCreateRequest):
    """Execute a single-point calibration calculation."""
    try:
        res = compute_micrometer_calibration(request)
        record_audit_event("CALIBRATION_CREATED", res.id, "Technician", {"verdict": res.conformity_verdict, "class": request.record_class})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculations/multi-point", response_model=MultiPointCalculationResponse)
def api_create_multi_point_calculation(request: MultiPointCalculationCreateRequest):
    """Execute a multi-point calibration calculation across multiple nominal checkpoints."""
    try:
        res = compute_multi_point_calibration(request)
        record_audit_event("MULTI_POINT_CALIBRATION_CREATED", res.id, request.technician, {"points_count": res.total_points, "overall_verdict": res.overall_verdict})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculations/{calc_id}/revise", response_model=CalculationResponse)
def api_revise_calculation(calc_id: str, request: CalculationCreateRequest):
    """Create a new immutable revision linked to parent calculation."""
    parent = get_calculation(calc_id)
    if not parent:
        raise HTTPException(status_code=404, detail=f"Parent calculation '{calc_id}' not found")

    root_id = parent.get("root_id") or calc_id
    rev_num = parent.get("revision_number", 1) + 1
    new_id = f"{root_id}.r{rev_num}"

    request.root_id = root_id
    request.revision_number = rev_num
    request.parent_sha256 = parent.get("calculation_sha256")

    res = compute_micrometer_calibration(request, calc_id=new_id)
    record_audit_event("REVISION_CREATED", new_id, "Technician", {"root_id": root_id, "rev_num": rev_num, "notes": request.revision_notes})
    return res


@app.get("/api/calculations/{calc_id}/verify")
def api_verify_calculation(calc_id: str):
    """Independently verify an existing calculation record."""
    res = verify_calculation_by_id(calc_id)
    record_audit_event("EVIDENCE_VERIFIED", calc_id, "Verifier Engine", {"is_valid": res.is_valid, "overall": res.overall_status})
    return {
        "calculation_id": res.calculation_id,
        "is_valid": res.is_valid,
        "overall_status": res.overall_status,
        "checks": [c._asdict() for c in res.checks],
        "diagnostics": res.diagnostics,
    }


@app.get("/api/calculations/{calc_id}/replay")
def api_replay_calculation(calc_id: str):
    """Execute step-by-step 12-stage mathematical calculation replay."""
    try:
        return replay_calculation(calc_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculations/{calc_id}/tamper-test")
def api_tamper_test(calc_id: str):
    """Demonstrate anti-tampering verification failure by modifying raw inputs."""
    rec = get_calculation(calc_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Calculation '{calc_id}' not found")

    tampered = dict(rec)
    tampered_input = json.loads(json.dumps(tampered["input_data"]))
    if "repeatability" in tampered_input and "measurements" in tampered_input["repeatability"]:
        tampered_input["repeatability"]["measurements"][0] = float(tampered_input["repeatability"]["measurements"][0]) + 0.0500
    tampered["input_data"] = tampered_input

    v_res = verify_calculation_record(tampered)
    record_audit_event("TAMPER_SIMULATION_EXECUTED", calc_id, "Security Lab", {"tamper_detected": not v_res.is_valid})
    return {
        "simulation": "Tampered Raw Measurement (+0.0500 mm in Run 1)",
        "calculation_id": v_res.calculation_id,
        "is_valid": v_res.is_valid,
        "overall_status": v_res.overall_status,
        "checks": [c._asdict() for c in v_res.checks],
        "diagnostics": v_res.diagnostics,
    }


@app.get("/api/calculations/{calc_id}/export/zip")
def api_export_zip(calc_id: str):
    """Download machine-verifiable evidence package as a zip file."""
    try:
        zip_bytes = export_evidence_package_zip_bytes(calc_id)
        record_audit_event("PACKAGE_EXPORTED", calc_id, "Technician", {"type": "zip"})
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=evidence_{calc_id}.zip"},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/calculations/{calc_id}/report", response_class=HTMLResponse)
def api_get_report(calc_id: str):
    """Generate printable HTML calibration certificate."""
    try:
        record_audit_event("CERTIFICATE_VIEWED", calc_id, "Technician", {"format": "html"})
        return generate_html_report(calc_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Audit Ledger Endpoints ---
@app.get("/api/audit")
def api_list_audit(limit: int = 100):
    """List recorded audit events."""
    return list_audit_events(limit=limit)


@app.get("/api/audit/verify")
def api_verify_audit():
    """Verify cryptographic hash chain of the entire audit ledger."""
    return verify_audit_ledger()


# --- Database Backup & Restore Endpoints ---
@app.get("/api/backups")
def api_list_backups():
    """List available verified database backups."""
    return list_backups()


@app.post("/api/backups")
def api_create_backup():
    """Create a live online database backup with SHA-256 manifest."""
    try:
        manifest = create_database_backup()
        record_audit_event("DATABASE_BACKUP_CREATED", manifest["backup_filename"], "Administrator", {"sha256": manifest["sha256"]})
        return manifest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backups/restore")
def api_restore_backup(backup_filename: str = Query(...)):
    """Restore database from a verified backup."""
    try:
        res = restore_database_backup(backup_filename)
        record_audit_event("DATABASE_RESTORED", backup_filename, "Administrator", {"status": "SUCCESS"})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Standards Concordance Endpoints ---
@app.get("/api/standards")
def api_list_standards():
    """List available standards concordance files."""
    standards_dir = get_resource_path("standards")
    if not os.path.exists(standards_dir):
        return []
    files = [f for f in os.listdir(standards_dir) if f.endswith(".md")]
    return sorted(files)


@app.get("/api/standards/{name}")
def api_get_standard_doc(name: str):
    """Get contents of a specific standards concordance markdown document."""
    standards_dir = get_resource_path("standards")
    target = os.path.join(standards_dir, name)
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Standard documentation not found")
    with open(target, "r", encoding="utf-8") as f:
        return {"filename": name, "content": f.read()}


# --- V5 Measurement Intelligence Endpoints ---
from .services.intelligence_service import (
    explain_calculation,
    compare_calibrations,
    compute_instrument_reliability_profile,
    predict_drift_and_risk,
    generate_action_recommendations,
)


@app.get("/api/intelligence/explain/{calc_id}")
def api_explain_calculation(calc_id: str):
    """V5 Experience 1: 'WHY?' — Explain This Result Engine."""
    try:
        return explain_calculation(calc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence/diff/{calc_id}")
def api_diff_calculation(calc_id: str, previous_id: Optional[str] = None):
    """V5 Experience 2: 'WHAT CHANGED?' — Longitudinal Difference Engine."""
    try:
        return compare_calibrations(calc_id, previous_id=previous_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence/reliability/{instrument_name}")
def api_instrument_reliability(instrument_name: str):
    """V5 Experience 3: 'WHAT CAUSED IT?' — Reliability Profile & Health Score."""
    try:
        return compute_instrument_reliability_profile(instrument_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence/forecast/{instrument_name}")
def api_drift_forecast(instrument_name: str, forecast_months: int = 12):
    """V5 Experience 4: 'WHAT HAPPENS NEXT?' — Drift & OOT Risk Forecaster."""
    try:
        return predict_drift_and_risk(instrument_name, forecast_months=forecast_months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence/recommendations/{instrument_name}")
def api_action_recommendations(instrument_name: str):
    """V5 Experience 5: 'WHAT SHOULD I DO?' — Evidence-Based Action Recommender."""
    try:
        return generate_action_recommendations(instrument_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# V5 REST API ENDPOINTS
# ==========================================

# --- Projects ---
@app.post("/api/projects")
def api_create_project(req: ProjectCreateRequest):
    """Create or update an engineering project workspace."""
    try:
        record = save_project(req.model_dump())
        record_audit_event("CREATE_PROJECT", record["id"], "SYSTEM", {"name": record["name"]})
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/projects")
def api_list_projects(status: Optional[str] = None):
    """List all project workspaces."""
    return list_projects(status=status)


@app.get("/api/projects/{project_id}")
def api_get_project(project_id: str):
    """Retrieve an engineering project."""
    record = get_project(project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project not found")
    return record


@app.delete("/api/projects/{project_id}")
def api_delete_project(project_id: str):
    """Delete an engineering project."""
    success = delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    record_audit_event("DELETE_PROJECT", project_id, "SYSTEM", {})
    return {"status": "DELETED", "id": project_id}


# --- Instruments ---
@app.post("/api/instruments")
def api_create_instrument(req: InstrumentCreateRequest):
    """Create or update an instrument in the asset registry."""
    try:
        record = save_instrument(req.model_dump())
        record_audit_event("CREATE_INSTRUMENT", record["id"], "SYSTEM", {"model": record["model"]})
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/instruments")
def api_list_instruments(project_id: Optional[str] = None, status: Optional[str] = None):
    """List registered instruments."""
    return list_instruments(project_id=project_id, status=status)


@app.get("/api/instruments/{instrument_id}")
def api_get_instrument(instrument_id: str):
    """Retrieve a specific instrument."""
    record = get_instrument(instrument_id)
    if not record:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return record


@app.delete("/api/instruments/{instrument_id}")
def api_delete_instrument(instrument_id: str):
    """Delete an instrument from registry."""
    success = delete_instrument(instrument_id)
    if not success:
        raise HTTPException(status_code=404, detail="Instrument not found")
    record_audit_event("DELETE_INSTRUMENT", instrument_id, "SYSTEM", {})
    return {"status": "DELETED", "id": instrument_id}


# --- Measurement Plans ---
@app.post("/api/plans")
def api_create_measurement_plan(req: MeasurementPlanCreateRequest):
    """Create or update a structured measurement plan."""
    try:
        record = save_measurement_plan(req.model_dump())
        record_audit_event("CREATE_PLAN", record["id"], "SYSTEM", {"plan_name": record["plan_name"]})
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/plans")
def api_list_measurement_plans(project_id: Optional[str] = None, instrument_id: Optional[str] = None):
    """List measurement plans."""
    return list_measurement_plans(project_id=project_id, instrument_id=instrument_id)


@app.get("/api/plans/{plan_id}")
def api_get_measurement_plan(plan_id: str):
    """Retrieve a measurement plan."""
    record = get_measurement_plan(plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Plan not found")
    return record


# --- Measurement Acquisition ---
@app.post("/api/measurements")
def api_acquire_measurements(req: MeasurementAcquisitionRequest):
    """Acquire and process repeated measurement series."""
    try:
        mean_val, s_dev, u_rep, outliers = analyze_measurement_series(req.raw_values)
        data = req.model_dump()
        data["mean_value"] = mean_val
        data["sample_std_dev"] = s_dev
        data["repeatability_uncertainty"] = u_rep
        data["outliers"] = outliers
        record = save_measurement(data)
        record_audit_event("ACQUIRE_MEASUREMENTS", record["id"], req.operator or "OPERATOR", {"n": len(req.raw_values), "mean": mean_val})
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/measurements")
def api_list_measurements(plan_id: Optional[str] = None, instrument_id: Optional[str] = None):
    """List acquired measurements."""
    return list_measurements(plan_id=plan_id, instrument_id=instrument_id)


@app.get("/api/measurements/{measurement_id}")
def api_get_measurement(measurement_id: str):
    """Retrieve an acquired measurement dataset."""
    record = get_measurement(measurement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Measurement dataset not found")
    return record


# --- Interactive Workbenches ---
@app.post("/api/workbench/uncertainty")
def api_workbench_uncertainty(req: UncertaintyWorkbenchRequest):
    """Evaluate interactive GUM uncertainty budget in real time."""
    try:
        return compute_uncertainty_workbench(req.components, confidence_level=req.confidence_level)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/workbench/conformity")
def api_workbench_conformity(req: ConformityWorkbenchRequest):
    """Evaluate interactive guardbanded conformity in real time."""
    try:
        return compute_conformity_workbench(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- V5 Workstation Stats ---
@app.get("/api/v5/stats")
def api_v5_stats():
    """Retrieve dynamic V5 workstation dashboard summary metrics."""
    return get_v5_dashboard_stats()


# Mount static web UI assets
STATIC_DIR = get_resource_path(os.path.join("metrology_app", "static"))
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


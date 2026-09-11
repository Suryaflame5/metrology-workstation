"""
Procedure Template Service for Metrology Workstation.
Provides catalog management, search, and 1-click instantiation of standard procedures into jobs.
"""

from typing import Dict, Any, List, Optional
from ..db import (
    get_procedure_template,
    list_procedure_templates,
    save_procedure_template,
    delete_procedure_template,
    save_job,
    DB_PATH,
)


def get_all_templates(category: Optional[str] = None, search: Optional[str] = None, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all available procedure templates."""
    return list_procedure_templates(category=category, search=search, db_path=db_path)


def get_template_by_id(template_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a procedure template by its ID or standard code."""
    return get_procedure_template(template_id, db_path=db_path)


def create_or_update_template(template_data: Dict[str, Any], db_path: str = DB_PATH) -> str:
    """Save or update a procedure template."""
    return save_procedure_template(template_data, db_path=db_path)


def instantiate_job_from_template(
    template_id: str,
    customer_name: str,
    instrument_name: str,
    instrument_model: str,
    instrument_serial: str,
    operator: str = "Metrology Specialist",
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Instantiate a new Measurement Job populated with the procedure template's parameters:
    nominal value, tolerances, decision rule, test points, and uncertainty model.
    """
    template = get_procedure_template(template_id, db_path=db_path)
    if not template:
        raise ValueError(f"Procedure template '{template_id}' not found.")

    from datetime import datetime

    job_id = f"JOB-{datetime.now().strftime('%Y')}-{datetime.now().strftime('%m%d%H%M%S')}"
    job_data = {
        "id": job_id,
        "job_number": job_id,
        "title": f"{template.get('title')} ({instrument_model})",
        "customer_name": customer_name,
        "instrument_id": f"INST-{instrument_serial[:6]}",
        "instrument_name": instrument_name,
        "instrument_model": instrument_model,
        "instrument_serial": instrument_serial,
        "procedure_template_id": template.get("id"),
        "procedure_name": template.get("title"),
        "reference_standard_id": "STD-GB-01" if template.get("category") == "Dimensional" else "STD-ZNR-10",
        "reference_standard_name": "Primary Standard",
        "reference_due_date": "2026-11-15",
        "reference_uncertainty": 0.00004,
        "status": "NEW",
        "unit": template.get("default_unit", "mm"),
        "nominal_value": float(template.get("nominal_value", 25.0)),
        "tolerance_upper": float(template.get("tolerance_upper", 0.002)),
        "tolerance_lower": float(template.get("tolerance_lower", -0.002)),
        "environment": {
            "ambient_temperature_c": 20.0,
            "relative_humidity_pct": 45.0,
            "atmospheric_pressure_hpa": 1013.25,
        },
        "raw_measurements": [],
        "mapped_columns": {},
        "statistics": {},
        "uncertainty_budget": {
            "contributors": template.get("uncertainty_contributors", []),
            "decision_rule": template.get("decision_rule", "ANSI/NCSL Z540.3 Method 6"),
        },
        "conformity": {},
        "exceptions": [],
        "operator": operator,
        "metadata": {
            "template_code": template.get("code"),
            "template_category": template.get("category"),
            "test_points": template.get("test_points", []),
            "instantiated_from_template": True,
        },
    }

    save_job(job_data, db_path=db_path)
    from ..db import get_job
    return get_job(job_id, db_path=db_path)

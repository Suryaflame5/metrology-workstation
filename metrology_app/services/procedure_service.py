"""
Procedure Service: Calibration procedures, instrument models, and metadata repository.
"""

import os
import json
from typing import Dict, Any, List
from ..config import get_resource_path

PROCEDURES_DIR = get_resource_path(os.path.join("metrology_app", "procedures"))


def get_available_procedures() -> List[Dict[str, Any]]:
    """Return all supported calibration procedures from JSON repository."""
    procedures = []
    if not os.path.exists(PROCEDURES_DIR):
        return []

    for fname in sorted(os.listdir(PROCEDURES_DIR)):
        if fname.endswith(".json"):
            fpath = os.path.join(PROCEDURES_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    procedures.append(data)
            except Exception:
                pass
    return procedures


def get_procedure_by_id(proc_id: str) -> Dict[str, Any]:
    """Retrieve procedure by ID or fallback to first available."""
    procs = get_available_procedures()
    for p in procs:
        if p.get("id") == proc_id or proc_id.lower() in p.get("name", "").lower():
            return p
    return procs[0] if procs else {}

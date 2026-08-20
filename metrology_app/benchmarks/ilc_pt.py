"""
ISO/IEC 17043 Interlaboratory Comparison (ILC) & Proficiency Testing (PT) Engine.
Evaluates normalized error En-ratios and Z-scores for laboratory accreditation proficiency.
"""

import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def evaluate_interlaboratory_en_ratio(
    lab_value: float,
    lab_expanded_uncertainty: float,
    reference_value: float,
    reference_expanded_uncertainty: float,
) -> Dict[str, Any]:
    """
    Calculate ISO/IEC 17043 normalized error En-ratio:
      En = (x_lab - X_ref) / sqrt(U_lab^2 + U_ref^2)
    
    Criterion:
      |En| <= 1.0 -> SATISFACTORY (PASS)
      |En| > 1.0  -> UNSATISFACTORY (ACTION REQUIRED)
    """
    denom = math.sqrt(lab_expanded_uncertainty**2 + reference_expanded_uncertainty**2)
    if denom < 1e-15:
        en = 0.0
    else:
        en = (lab_value - reference_value) / denom

    abs_en = abs(en)
    is_satisfactory = (abs_en <= 1.0)

    return {
        "en_ratio": round(en, 4),
        "absolute_en": round(abs_en, 4),
        "is_satisfactory": is_satisfactory,
        "performance_verdict": "SATISFACTORY_EQUIVALENCE" if is_satisfactory else "ACTION_REQUIRED_BIAS_DETECTED",
        "lab_value": lab_value,
        "lab_uncertainty_u95": lab_expanded_uncertainty,
        "ref_value": reference_value,
        "ref_uncertainty_u95": reference_expanded_uncertainty,
        "standard_reference": "ISO/IEC 17043:2023 Conformity assessment — General requirements for proficiency testing",
    }


def simulate_proficiency_testing_round(
    participant_labs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Simulate a multi-lab proficiency testing round across 5 participant laboratories.
    """
    ts = datetime.now(timezone.utc).isoformat()
    ref_value = 25.00000
    ref_u95 = 0.00015

    default_participants = participant_labs or [
        {"lab_name": "NovyraX Primary Metrology Station", "measured_val": 25.00010, "u95": 0.00040},
        {"lab_name": "National Calibration Lab A", "measured_val": 25.00018, "u95": 0.00050},
        {"lab_name": "Regional Automotive Metrology Lab", "measured_val": 24.99985, "u95": 0.00060},
        {"lab_name": "Aerospace Cleanroom Standards Bay", "measured_val": 25.00005, "u95": 0.00035},
        {"lab_name": "Contract Calibration Services X", "measured_val": 25.00095, "u95": 0.00045},
    ]

    evaluations = []
    for lab in default_participants:
        res = evaluate_interlaboratory_en_ratio(
            lab_value=lab["measured_val"],
            lab_expanded_uncertainty=lab["u95"],
            reference_value=ref_value,
            reference_expanded_uncertainty=ref_u95,
        )
        evaluations.append({
            "lab_name": lab["lab_name"],
            "measured_value_mm": lab["measured_val"],
            "stated_uncertainty_mm": lab["u95"],
            "en_ratio": res["en_ratio"],
            "status": "PASS" if res["is_satisfactory"] else "FAIL",
        })

    passing_count = sum(1 for e in evaluations if e["status"] == "PASS")

    return {
        "pt_round_id": "PT-ISO17043-2026-DIM01",
        "timestamp_utc": ts,
        "artifact_description": "25.00000 mm Grade 0 Master Gauge Block",
        "reference_value_mm": ref_value,
        "reference_uncertainty_u95_mm": ref_u95,
        "participant_evaluations": evaluations,
        "total_participants": len(evaluations),
        "satisfactory_participants": passing_count,
        "round_summary": f"{passing_count}/{len(evaluations)} laboratories achieved satisfactory En-ratio (|En| <= 1.0).",
    }

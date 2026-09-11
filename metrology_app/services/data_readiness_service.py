"""
DataReadinessReport Engine -- NovyraX Metrology Workstation

After a file is ingested, this service audits the available data and produces
an honest declaration of:
  - What factors were detected (measurements, machine, tool, operator, etc.)
  - Which analyses CAN be run (statistically valid)
  - Which analyses CANNOT be run (data not available)
  - Overall readiness verdict

This prevents the system from silently running analyses with fake/fallback defaults.
"""

from __future__ import annotations

import re
import math
from typing import Any, Dict, List, Optional


VERDICT_FULL    = "READY_FULL"
VERDICT_PARTIAL = "READY_PARTIAL"
VERDICT_BASIC   = "READY_BASIC"
VERDICT_NOT     = "NOT_READY"


COLUMN_PATTERNS: Dict[str, List[str]] = {
    "measured": [
        r"^measured", r"^reading", r"^indicated", r"^value", r"^result",
        r"^obs", r"^observation", r"^dut", r"^uut", r"^output",
        r"^actual", r"^dimension", r"^meas", r"^dim", r"^size",
    ],
    "nominal": [
        r"^nominal", r"^applied", r"^standard", r"^target", r"^setpoint",
        r"^reference", r"^ref_val", r"^input_qty", r"^true_value",
    ],
    "tolerance_upper": [
        r"^tol.*upper", r"^upper.*tol", r"^usl", r"^upper.*limit", r"^hi.*tol",
    ],
    "tolerance_lower": [
        r"^tol.*lower", r"^lower.*tol", r"^lsl", r"^lower.*limit", r"^lo.*tol",
    ],
    "machine": [
        r"^machine", r"^station", r"^spindle", r"^cell", r"^cnc",
        r"^mcn", r"^mach", r"^equip", r"^asset",
    ],
    "tool": [
        r"^tool", r"^insert", r"^cutter", r"^drill", r"^tap",
        r"^toolid", r"^tool_no", r"^tool_num",
    ],
    "operator": [
        r"^operator", r"^tech", r"^technician", r"^inspector",
        r"^by$", r"^user", r"^op$",
    ],
    "batch": [
        r"^batch", r"^lot", r"^work.*order", r"^wo$", r"^production.*order",
        r"^po$", r"^order", r"^run_id",
    ],
    "part_number": [
        r"^part$", r"^pn$", r"^part.*num", r"^part.*no", r"^partnumber",
        r"^item", r"^product",
    ],
    "defect_flag": [
        r"^pass", r"^fail", r"^verdict", r"^ok$", r"^ng$",
        r"^conform",
    ],
    "timestamp": [
        r"^time", r"^date", r"^timestamp", r"^datetime", r"^acquired",
    ],
    "temperature": [r"^temp", r"^temperature", r"^ambient", r"^deg_c"],
    "humidity":    [r"^humid", r"^rh$", r"^%rh", r"^rel_hum"],
    "run":         [r"^run$", r"^trial", r"^rep$", r"^seq$", r"^index$", r"^sn$"],
    "correction":  [r"^correction", r"^corr$", r"^offset", r"^bias"],
    "cost":        [r"^cost", r"^scrap.*val", r"^loss", r"^price", r"^unit.*cost"],
}


def _match_role(col_clean: str) -> Optional[str]:
    for role, patterns in COLUMN_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, col_clean):
                return role
    return None


def _is_numeric_column(col: str, rows: List[Dict[str, Any]], sample: int = 8) -> bool:
    checked, numeric = 0, 0
    for row in rows[:sample]:
        v = str(row.get(col, "")).strip()
        if not v:
            continue
        checked += 1
        try:
            float(v.replace(",", ""))
            numeric += 1
        except ValueError:
            pass
    return checked > 0 and (numeric / checked) >= 0.6


def _unique_values(col: str, rows: List[Dict[str, Any]], limit: int = 20) -> List[str]:
    seen = set()
    for row in rows:
        v = str(row.get(col, "")).strip()
        if v:
            seen.add(v)
    vals = sorted(seen)
    return vals[:limit] + (["..."] if len(vals) > limit else [])


def _count_valid_numeric(col: str, rows: List[Dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        try:
            float(str(row.get(col, "")).replace(",", ""))
            count += 1
        except (ValueError, TypeError):
            pass
    return count


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _extract_tolerance(rows: List[Dict[str, Any]], role_map: Dict[str, str]) -> Dict[str, Any]:
    upper_col = role_map.get("tolerance_upper")
    lower_col = role_map.get("tolerance_lower")
    if upper_col and lower_col:
        try:
            uppers = [float(str(r.get(upper_col, "")).replace(",", "")) for r in rows if r.get(upper_col)]
            lowers = [float(str(r.get(lower_col, "")).replace(",", "")) for r in rows if r.get(lower_col)]
            if uppers and lowers:
                return {"available": True, "source": "explicit_columns",
                        "upper": round(uppers[0], 6), "lower": round(lowers[0], 6)}
        except ValueError:
            pass
    return {"available": False, "reason": "No tolerance columns detected"}


def build_data_readiness_report(
    rows: List[Dict[str, Any]],
    filename: str = "uploaded_file",
    user_nominal: Optional[float] = None,
    user_tolerance_upper: Optional[float] = None,
    user_tolerance_lower: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Analyse imported rows and produce a DataReadinessReport that honestly
    declares which analyses are valid vs unavailable.
    """
    if not rows:
        return {
            "filename": filename, "readiness_verdict": VERDICT_NOT,
            "confidence_score": 0.0,
            "summary": {"total_rows": 0, "valid_numeric_rows": 0, "rejected_rows": 0,
                        "rejection_reasons": ["No rows found in file"]},
            "detected_factors": {}, "enabled_analyses": [], "data_quality_warnings": [],
            "disabled_analyses": [{"id": "all", "reason": "No data rows found"}],
        }

    headers = list(rows[0].keys())
    role_map: Dict[str, str] = {}

    for col in headers:
        col_clean = col.lower().replace("_", " ").replace("-", " ").strip()
        role = _match_role(col_clean)
        if role is None and "measured" not in role_map and _is_numeric_column(col, rows):
            role = "measured"
        if role and role not in role_map:
            role_map[role] = col

    factors: Dict[str, Any] = {}
    warnings: List[str] = []

    # measurements
    meas_col = role_map.get("measured")
    if meas_col:
        valid_count = _count_valid_numeric(meas_col, rows)
        rej = len(rows) - valid_count
        if rej > 0:
            warnings.append(f"{rej} rows rejected (non-numeric in '{meas_col}')")
        factors["measurements"] = {"available": True, "column": meas_col, "count": valid_count}
    else:
        factors["measurements"] = {"available": False, "reason": "No measurement column identified"}

    # nominal
    nom_col = role_map.get("nominal")
    if user_nominal is not None:
        factors["nominal"] = {"available": True, "source": "user_supplied", "value": user_nominal}
    elif nom_col:
        try:
            vals = [float(str(r.get(nom_col, "")).replace(",", "")) for r in rows if r.get(nom_col)]
            factors["nominal"] = {"available": True, "column": nom_col, "value": round(_mean(vals), 6) if vals else None}
        except ValueError:
            factors["nominal"] = {"available": False, "reason": "Nominal column has non-numeric values"}
    else:
        factors["nominal"] = {"available": False, "reason": "No nominal/reference column detected"}

    # tolerance
    tol = _extract_tolerance(rows, role_map)
    if not tol["available"] and user_tolerance_upper is not None and user_tolerance_lower is not None:
        tol = {"available": True, "source": "user_supplied",
               "upper": user_tolerance_upper, "lower": user_tolerance_lower}
    factors["tolerance"] = tol

    # factor columns
    for factor in ("machine", "tool", "operator", "batch", "part_number",
                   "defect_flag", "timestamp", "cost"):
        col = role_map.get(factor)
        if col:
            unique = _unique_values(col, rows)
            factors[factor] = {
                "available": True, "column": col,
                "unique_values": unique,
                "distinct_count": len([v for v in unique if v != "..."]),
            }
        else:
            factors[factor] = {"available": False, "reason": f"No column matched '{factor}' patterns"}

    # enabled/disabled
    has_meas      = factors["measurements"]["available"]
    has_nom       = factors["nominal"]["available"]
    has_tol       = factors["tolerance"]["available"]
    has_machine   = factors["machine"]["available"] and factors["machine"].get("distinct_count", 0) >= 2
    has_tool      = factors["tool"]["available"]    and factors["tool"].get("distinct_count", 0) >= 2
    has_operator  = factors["operator"]["available"] and factors["operator"].get("distinct_count", 0) >= 2
    has_batch     = factors["batch"]["available"]
    has_defect    = factors["defect_flag"]["available"]
    has_timestamp = factors["timestamp"]["available"]
    has_cost      = factors["cost"]["available"]

    enabled: List[str] = []
    disabled: List[Dict[str, str]] = []

    def E(aid): enabled.append(aid)
    def D(aid, reason): disabled.append({"id": aid, "reason": reason})

    if has_meas:
        E("basic_statistics"); E("grubbs_outlier_test"); E("data_quality_report"); E("evidence_zip")
    else:
        D("basic_statistics", "No measurement column detected")
        D("grubbs_outlier_test", "No measurement column detected")

    if has_meas and has_nom:  E("deviation_analysis")
    else: D("deviation_analysis", "Nominal/reference values not available")

    if has_meas and has_tol:
        E("tolerance_analysis"); E("conformity_assessment"); E("pdf_report")
    else:
        D("tolerance_analysis", "Tolerance limits not available")
        D("conformity_assessment", "Tolerance limits required")

    if has_meas and has_nom and has_tol: E("gum_uncertainty_budget")
    else: D("gum_uncertainty_budget", "Requires measurements + nominal + tolerance")

    if has_meas and has_timestamp:  E("trend_analysis")
    else: D("trend_analysis", "Timestamp column not available")

    if has_meas and has_machine:    E("machine_anova")
    else:
        D("machine_anova", "Machine column not detected" if not factors["machine"]["available"]
          else "Only 1 distinct machine -- ANOVA requires >= 2 groups")

    if has_meas and has_tool:       E("tool_anova")
    else:
        D("tool_anova", "Tool column not detected" if not factors["tool"]["available"]
          else "Only 1 distinct tool -- ANOVA requires >= 2 groups")

    if has_meas and has_operator:   E("operator_anova")
    else:
        D("operator_anova", "Operator column not detected" if not factors["operator"]["available"]
          else "Only 1 distinct operator -- ANOVA requires >= 2 groups")

    if has_meas and (has_machine or has_tool or has_operator):
        E("root_cause_correlation")
    else:
        D("root_cause_correlation",
          "Needs >= 1 factor column (machine/tool/operator) with >= 2 groups")

    if has_cost or has_defect: E("loss_quantification")
    else: D("loss_quantification", "No cost data or defect flags found in dataset")

    D("recovery_proof", "Requires 2 comparable inspection jobs (before + after)")

    # verdict
    factor_count = sum([has_machine, has_tool, has_operator, has_batch])
    context_count = factor_count + sum([has_defect, has_nom, has_tol, has_timestamp])
    if has_meas and has_tol and factor_count >= 2:    verdict = VERDICT_FULL
    elif has_meas and has_tol:                         verdict = VERDICT_PARTIAL
    elif has_meas and context_count >= 1:              verdict = VERDICT_PARTIAL
    elif has_meas:                                     verdict = VERDICT_BASIC
    else:                                              verdict = VERDICT_NOT

    score = 0.0
    if has_meas:      score += 0.40
    if has_nom:       score += 0.15
    if has_tol:       score += 0.20
    if has_machine:   score += 0.10
    if has_tool:      score += 0.08
    if has_operator:  score += 0.05
    if has_timestamp: score += 0.02

    total = len(rows)
    valid_count = factors["measurements"].get("count", 0) if has_meas else 0

    return {
        "filename": filename,
        "readiness_verdict": verdict,
        "confidence_score": round(min(score, 1.0), 3),
        "summary": {
            "total_rows": total,
            "valid_numeric_rows": valid_count,
            "rejected_rows": max(total - valid_count, 0) if has_meas else 0,
            "rejection_reasons": warnings,
        },
        "detected_factors": factors,
        "enabled_analyses": enabled,
        "disabled_analyses": disabled,
        "data_quality_warnings": warnings,
        "factor_column_map": role_map,
    }

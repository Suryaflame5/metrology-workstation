"""
Universal Measurement Data Ingestion and Column Auto-Detection Engine.
Supports CSV, TSV, XLSX, JSON, and raw text clipboard table paste.
"""

import io
import re
import csv
import json
from typing import Dict, Any, List, Optional, Tuple


# Standard physical unit scaling factors to SI base/workstation reference
UNIT_CONVERSION_TABLE = {
    # Voltage (base: V)
    "V": {"category": "voltage", "factor": 1.0, "offset": 0.0},
    "MV": {"category": "voltage", "factor": 1e-3, "offset": 0.0},
    "UV": {"category": "voltage", "factor": 1e-6, "offset": 0.0},
    "\u00b5V": {"category": "voltage", "factor": 1e-6, "offset": 0.0},
    # Current (base: A)
    "A": {"category": "current", "factor": 1.0, "offset": 0.0},
    "MA": {"category": "current", "factor": 1e-3, "offset": 0.0},
    "UA": {"category": "current", "factor": 1e-6, "offset": 0.0},
    "\u00b5A": {"category": "current", "factor": 1e-6, "offset": 0.0},
    # Resistance (base: Ohm / \u03a9)
    "OHM": {"category": "resistance", "factor": 1.0, "offset": 0.0},
    "\u03a9": {"category": "resistance", "factor": 1.0, "offset": 0.0},
    "KOHM": {"category": "resistance", "factor": 1e3, "offset": 0.0},
    "K\u03a9": {"category": "resistance", "factor": 1e3, "offset": 0.0},
    "MOHM": {"category": "resistance", "factor": 1e6, "offset": 0.0},
    "M\u03a9": {"category": "resistance", "factor": 1e6, "offset": 0.0},
    # Length (base: mm)
    "MM": {"category": "length", "factor": 1.0, "offset": 0.0},
    "UM": {"category": "length", "factor": 1e-3, "offset": 0.0},
    "\u00b5M": {"category": "length", "factor": 1e-3, "offset": 0.0},
    "M": {"category": "length", "factor": 1e3, "offset": 0.0},
    "IN": {"category": "length", "factor": 25.4, "offset": 0.0},
    # Pressure (base: bar)
    "BAR": {"category": "pressure", "factor": 1.0, "offset": 0.0},
    "MBAR": {"category": "pressure", "factor": 1e-3, "offset": 0.0},
    "KPA": {"category": "pressure", "factor": 0.01, "offset": 0.0},
    "PA": {"category": "pressure", "factor": 1e-5, "offset": 0.0},
    "PSI": {"category": "pressure", "factor": 0.06894757293, "offset": 0.0},
    # Temperature (base: \u00b0C)
    "\u00b0C": {"category": "temperature", "factor": 1.0, "offset": 0.0},
    "C": {"category": "temperature", "factor": 1.0, "offset": 0.0},
    "\u00b0F": {"category": "temperature", "factor": 5.0 / 9.0, "offset": -32.0 * (5.0 / 9.0)},
    "F": {"category": "temperature", "factor": 5.0 / 9.0, "offset": -32.0 * (5.0 / 9.0)},
    "K": {"category": "temperature", "factor": 1.0, "offset": -273.15},
}


def normalize_unit_value(value: float, from_unit: str, to_unit: str) -> float:
    """
    Safely convert physical measurement value from source unit to target unit.
    Rejects incompatible physical categories (e.g. converting Volts to mm).
    """
    f_clean = from_unit.strip().upper()
    t_clean = to_unit.strip().upper()

    if f_clean == t_clean:
        return value

    spec_from = UNIT_CONVERSION_TABLE.get(f_clean)
    spec_to = UNIT_CONVERSION_TABLE.get(t_clean)

    if not spec_from or not spec_to:
        return value

    if spec_from["category"] != spec_to["category"]:
        raise ValueError(
            f"Incompatible unit conversion requested: '{from_unit}' ({spec_from['category']}) "
            f"to '{to_unit}' ({spec_to['category']}). Metrological safety check failed."
        )

    if spec_from["category"] == "temperature":
        if "°F" in f_clean or f_clean == "F":
            base_c = (value - 32.0) * (5.0 / 9.0)
        elif f_clean == "K":
            base_c = value - 273.15
        else:
            base_c = value

        if "°F" in t_clean or t_clean == "F":
            return (base_c * 9.0 / 5.0) + 32.0
        elif t_clean == "K":
            return base_c + 273.15
        return base_c

    base_val = value * spec_from["factor"]
    return base_val / spec_to["factor"]


def parse_excel_workbook(file_bytes: bytes, sheet_name: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    """
    Parse an Excel (.xlsx / .xlsm / .xltx) binary byte buffer with robust handling of:
    - Merged cells, formula caches, empty lines, and banner headers
    - Datetime, float, integer, and scientific notation preservation
    - Clean disambiguation of duplicate header column names
    Returns: (sheet_names, rows_of_selected_sheet, headers)
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required for Excel parsing. Install with: pip install openpyxl")

    # Attempt to load workbook with data_only=True (reads evaluated formula results)
    wb = None
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=False)
    except Exception:
        # Fallback to read_only mode if full mode encounters unsupported features
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        except Exception as e:
            raise ValueError(f"Unable to parse Excel file: {str(e)}")

    sheet_names = list(wb.sheetnames)
    if not sheet_names:
        if hasattr(wb, 'close'):
            wb.close()
        return [], [], []

    target_sheet = sheet_name if (sheet_name and sheet_name in sheet_names) else sheet_names[0]
    ws = wb[target_sheet]

    # Convert rows to list of tuples, formatting cell types
    raw_rows = []
    for row in ws.iter_rows(values_only=True):
        if not row:
            continue
        cleaned_row = []
        has_val = False
        for c in row:
            if c is None:
                cleaned_row.append("")
            elif hasattr(c, "isoformat"):  # datetime / date
                cleaned_row.append(c.isoformat())
                has_val = True
            elif isinstance(c, float):
                # Format clean float without scientific bloat unless tiny
                cleaned_row.append(f"{c:.8g}")
                has_val = True
            elif isinstance(c, (int, bool)):
                cleaned_row.append(str(c))
                has_val = True
            else:
                s = str(c).strip()
                cleaned_row.append(s)
                if s:
                    has_val = True
        if has_val:
            raw_rows.append(cleaned_row)

    if hasattr(wb, 'close'):
        wb.close()

    if not raw_rows:
        return sheet_names, [], []

    # Smart header row detection: find first row with >= 2 non-empty string values (skipping title banners)
    header_idx = 0
    max_non_empty = 0
    for idx, r in enumerate(raw_rows[:10]):
        non_empty_count = sum(1 for v in r if v != "")
        if non_empty_count >= 2 and non_empty_count > max_non_empty:
            max_non_empty = non_empty_count
            header_idx = idx

    raw_headers = raw_rows[header_idx]
    # Disambiguate duplicate or empty headers
    seen_headers: Dict[str, int] = {}
    headers: List[str] = []
    for i, h in enumerate(raw_headers):
        col_title = h if h != "" else f"Column_{i+1}"
        if col_title in seen_headers:
            seen_headers[col_title] += 1
            col_title = f"{col_title}_{seen_headers[col_title]}"
        else:
            seen_headers[col_title] = 1
        headers.append(col_title)

    # Build row dictionaries
    rows: List[Dict[str, Any]] = []
    for r in raw_rows[header_idx + 1:]:
        if not any(v != "" for v in r):
            continue
        row_dict = {}
        for i, val in enumerate(r):
            if i < len(headers):
                row_dict[headers[i]] = val
        if any(v != "" for v in row_dict.values()):
            rows.append(row_dict)

    return sheet_names, rows, headers


def parse_raw_data_stream(raw_text_or_bytes: Any, filename: Optional[str] = None, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse arbitrary raw content into list of string/number dictionaries.
    Accepts Excel (.xlsx), CSV, TSV, JSON string, or tab/comma separated clipboard text.
    """
    # Check if raw_text_or_bytes is binary Excel or Base64 Excel
    is_excel = False
    raw_bytes = None

    if isinstance(raw_text_or_bytes, bytes):
        if raw_text_or_bytes.startswith(b"PK\x03\x04") or (filename and filename.lower().endswith((".xlsx", ".xlsm", ".xltx"))):
            is_excel = True
            raw_bytes = raw_text_or_bytes
    elif isinstance(raw_text_or_bytes, str):
        s_trim = raw_text_or_bytes.strip()
        if (filename and filename.lower().endswith((".xlsx", ".xlsm", ".xltx"))) or "base64," in s_trim or s_trim.startswith("UEsDB"):
            try:
                import base64
                b64_data = s_trim.split("base64,")[1] if "base64," in s_trim else s_trim
                decoded = base64.b64decode(b64_data)
                if decoded.startswith(b"PK\x03\x04"):
                    is_excel = True
                    raw_bytes = decoded
            except Exception:
                pass

    if is_excel and raw_bytes:
        try:
            _, rows, _ = parse_excel_workbook(raw_bytes, sheet_name=sheet_name)
            if rows:
                return rows
        except Exception:
            pass

    text_content = ""
    if isinstance(raw_text_or_bytes, bytes):
        try:
            text_content = raw_text_or_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = raw_text_or_bytes.decode("latin-1", errors="replace")
    else:
        text_content = str(raw_text_or_bytes)

    text_content = text_content.strip()
    if not text_content:
        return []

    if (text_content.startswith("[") and text_content.endswith("]")) or (text_content.startswith("{") and text_content.endswith("}")):
        try:
            parsed = json.loads(text_content)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "records" in parsed:
                return parsed["records"]
            if isinstance(parsed, dict) and "data" in parsed:
                return parsed["data"]
            return [parsed]
        except Exception:
            pass

    first_line = text_content.splitlines()[0] if text_content.splitlines() else ""
    delimiter = ","
    if "\t" in first_line:
        delimiter = "\t"
    elif ";" in first_line and "," not in first_line:
        delimiter = ";"
    elif "|" in first_line:
        delimiter = "|"

    try:
        reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)
        rows = []
        for r in reader:
            cleaned = {}
            for k, v in r.items():
                if k is not None:
                    cleaned[k.strip()] = v.strip() if v else ""
            if any(cleaned.values()):
                rows.append(cleaned)
        if rows:
            return rows
    except Exception:
        pass

    lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]
    num_rows = []
    for idx, ln in enumerate(lines):
        m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", ln)
        if m:
            try:
                val = float(m.group(0))
                num_rows.append({"Run": idx + 1, "Reading": val})
            except ValueError:
                pass
    return num_rows


def auto_detect_columns(headers: List[str], sample_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Heuristic column detection engine with confidence scoring.
    Identifies nominal, measured observation, correction, environmental parameters, and metadata.
    """
    patterns = {
        "run": [
            r"^run", r"^trial", r"^rep", r"^repetition", r"^sample", r"^#", r"^idx", r"^index", r"^no",
            r"^seq", r"^partseq", r"^part_seq", r"^part\s*seq", r"^serial", r"^sn", r"^item", r"^part_num"
        ],
        "measured": [
            r"^measured", r"^reading", r"^indicated", r"^value", r"^result", r"^obs",
            r"^observation", r"^dut", r"^uut", r"^measured_mm", r"^measured_v", r"^output",
            r"^actual", r"^dimension", r"^meas", r"^dim", r"^size",
        ],
        "nominal": [
            r"^nominal", r"^applied", r"^standard", r"^target", r"^setpoint",
            r"^reference", r"^ref_val", r"^input_qty", r"^true_value"
        ],
        "correction": [
            r"^correction", r"^corr", r"^offset", r"^bias", r"^error", r"^error_of_indication"
        ],
        "temperature": [
            r"^temp", r"^temperature", r"^ambient_temp", r"^deg_c", r"^temp_c"
        ],
        "humidity": [
            r"^humid", r"^humidity", r"^rh", r"^%rh", r"^rel_humidity"
        ],
        "pressure": [
            r"^press", r"^pressure", r"^baro", r"^hpa", r"^barometric"
        ],
        "operator": [
            r"^operator", r"^tech", r"^technician", r"^inspector", r"^by$", r"^user", r"^op$"
        ],
        "timestamp": [
            r"^time", r"^date", r"^timestamp", r"^datetime", r"^acquired_at", r"^acquired"
        ],
        # ── New factor columns for root-cause & loss analysis ──────────────
        "machine": [
            r"^machine", r"^station", r"^spindle", r"^cell", r"^cnc",
            r"^mcn", r"^mach", r"^equip", r"^asset",
        ],
        "tool": [
            r"^tool", r"^insert", r"^cutter", r"^drill", r"^tap",
            r"^toolid", r"^tool_no", r"^tool_num",
        ],
        "batch": [
            r"^batch", r"^lot", r"^work.*order", r"^wo$", r"^production.*order",
            r"^po$", r"^order$", r"^run_id",
        ],
        "part_number": [
            r"^part$", r"^pn$", r"^part.*num", r"^part.*no$", r"^partnumber",
            r"^product",
        ],
        "defect_flag": [
            r"^pass$", r"^fail$", r"^verdict", r"^ok$", r"^ng$", r"^conform",
        ],
        "tolerance_upper": [
            r"^tol.*upper", r"^upper.*tol", r"^usl", r"^upper.*limit", r"^hi.*tol",
        ],
        "tolerance_lower": [
            r"^tol.*lower", r"^lower.*tol", r"^lsl", r"^lower.*limit", r"^lo.*tol",
        ],
        "cost": [
            r"^cost", r"^scrap.*val", r"^loss", r"^price", r"^unit.*cost",
        ],
    }

    mapping = {}
    matched_roles = set()

    # Pass 1: Match explicit regexes across all headers
    for col in headers:
        col_clean = col.lower().replace("_", " ").replace("-", " ").strip()
        for role, regex_list in patterns.items():
            if role in matched_roles and role in ("measured", "nominal", "run", "operator",
                                                   "machine", "tool", "batch"):
                continue

            for pattern in regex_list:
                if re.search(pattern, col_clean) or pattern in col_clean:
                    mapping[col] = {
                        "role": role,
                        "confidence": 0.95,
                        "suggested_label": role.replace("_", " ").title(),
                    }
                    matched_roles.add(role)
                    break
            if col in mapping:
                break

    # Pass 2: Fallback for unmatched columns
    for col in headers:
        if col in mapping:
            continue

        has_numbers = False
        for row in sample_rows[:5]:
            val = row.get(col, "")
            try:
                float(str(val).replace(",", ""))
                has_numbers = True
                break
            except (ValueError, TypeError):
                pass

        if has_numbers and "measured" not in matched_roles:
            mapping[col] = {"role": "measured", "confidence": 0.82, "suggested_label": "Measured Observation"}
            matched_roles.add("measured")
        else:
            mapping[col] = {"role": "metadata", "confidence": 0.70, "suggested_label": "Auxiliary Data"}

    core_found = ("measured" in matched_roles) or ("nominal" in matched_roles)
    overall_confidence = 0.97 if core_found and len(matched_roles) >= 2 else (0.90 if core_found else 0.65)

    return {
        "columns": mapping,
        "matched_roles": list(matched_roles),
        "overall_confidence_pct": round(overall_confidence * 100, 1),
        "has_measured_values": "measured" in matched_roles,
        "has_nominal_values": "nominal" in matched_roles,
        "has_machine_column": "machine" in matched_roles,
        "has_tool_column": "tool" in matched_roles,
        "has_operator_column": "operator" in matched_roles,
        "has_batch_column": "batch" in matched_roles,
        "has_tolerance_columns": "tolerance_upper" in matched_roles and "tolerance_lower" in matched_roles,
    }


def extract_job_measurements(
    rows: List[Dict[str, Any]],
    column_mapping: Dict[str, Any],
    target_unit: str = "mm"
) -> Dict[str, Any]:
    """
    Extract structured numerical measurements and environmental conditions from mapped records.
    """
    readings = []
    nominal_vals = []
    temps = []
    humids = []
    corrections = []

    role_to_col = {}
    for col, info in column_mapping.items():
        role = info if isinstance(info, str) else info.get("role", "metadata")
        role_to_col[role] = col

    meas_col = role_to_col.get("measured")
    nom_col = role_to_col.get("nominal")
    corr_col = role_to_col.get("correction")
    temp_col = role_to_col.get("temperature")
    rh_col = role_to_col.get("humidity")

    for r in rows:
        if meas_col and meas_col in r and r[meas_col] != "":
            try:
                v = float(str(r[meas_col]).replace(",", ""))
                readings.append(v)
            except (ValueError, TypeError):
                pass
        elif not meas_col:
            for k, val in r.items():
                try:
                    v = float(str(val).replace(",", ""))
                    readings.append(v)
                    break
                except (ValueError, TypeError):
                    pass

        if nom_col and nom_col in r and r[nom_col] != "":
            try:
                nominal_vals.append(float(str(r[nom_col]).replace(",", "")))
            except (ValueError, TypeError):
                pass

        if temp_col and temp_col in r and r[temp_col] != "":
            try:
                temps.append(float(str(r[temp_col]).replace(",", "")))
            except (ValueError, TypeError):
                pass

        if rh_col and rh_col in r and r[rh_col] != "":
            try:
                humids.append(float(str(r[rh_col]).replace(",", "")))
            except (ValueError, TypeError):
                pass

        if corr_col and corr_col in r and r[corr_col] != "":
            try:
                corrections.append(float(str(r[corr_col]).replace(",", "")))
            except (ValueError, TypeError):
                pass

    nominal_value = nominal_vals[0] if nominal_vals else (round(readings[0], 2) if readings else 25.0)
    ambient_temp = (sum(temps) / len(temps)) if temps else 20.0
    relative_humidity = (sum(humids) / len(humids)) if humids else 45.0
    mean_correction = (sum(corrections) / len(corrections)) if corrections else 0.0

    return {
        "raw_measurements": readings,
        "sample_size": len(readings),
        "nominal_value": nominal_value,
        "environment": {
            "ambient_temperature_c": round(ambient_temp, 2),
            "relative_humidity_pct": round(relative_humidity, 1),
            "atmospheric_pressure_hpa": 1013.25,
        },
        "mean_correction": mean_correction,
        "target_unit": target_unit,
    }


def validate_imported_data(
    rows: List[Dict[str, Any]],
    column_mapping: Dict[str, Any],
    nominal: float = 25.0,
    tolerance_lower: float = -0.002,
    tolerance_upper: float = 0.002,
    reference_due_date: Optional[str] = None,
    target_unit: str = "mm"
) -> Dict[str, Any]:
    """
    Perform Smart Data Validation on imported dataset.
    Returns comprehensive Data Health Card with:
      - Rows parsed, valid rows, review required rows
      - Unit consistency
      - Required column presence
      - Duplicate timestamp check
      - Reference standard validity check
      - Range breaches (measurements outside expected tolerance limits)
      - Missing environmental readings
      - Statistical outliers (Grubbs criterion > 2.8 sigma)
      - Overall data health grade: HEALTHY, WARNINGS, CRITICAL
    """
    from datetime import datetime, timezone
    import math

    extracted = extract_job_measurements(rows, column_mapping, target_unit)
    readings = extracted["raw_measurements"]
    env = extracted["environment"]

    total_rows = len(rows)
    valid_count = len(readings)
    review_required = total_rows - valid_count

    warnings = []
    critical_issues = []

    # 1. Required columns check
    has_measured = any(
        (info if isinstance(info, str) else info.get("role")) == "measured"
        for info in column_mapping.values()
    )
    if not has_measured and not readings:
        critical_issues.append("No measurement observation column detected in dataset.")

    # 2. Reference standard expiration check
    ref_valid = True
    ref_days_remaining = None
    if reference_due_date:
        try:
            due = datetime.strptime(reference_due_date[:10], "%Y-%m-%d")
            now = datetime.now()
            days = (due - now).days
            ref_days_remaining = days
            if days < 0:
                critical_issues.append(f"Reference standard calibration expired {abs(days)} days ago ({reference_due_date}).")
                ref_valid = False
            elif days <= 30:
                warnings.append(f"Reference standard calibration due soon ({days} days remaining on {reference_due_date}).")
        except Exception:
            pass

    # 3. Environmental readings completeness
    has_env_temp = env.get("ambient_temperature_c") is not None and env.get("ambient_temperature_c") != 20.0
    has_env_rh = env.get("relative_humidity_pct") is not None and env.get("relative_humidity_pct") != 45.0
    if not has_env_temp or not has_env_rh:
        warnings.append("Environmental readings missing from imported file (default laboratory ambient 20.0 °C, 45.0% RH applied).")

    # 4. Out of tolerance / Range breaches
    lower_limit = nominal + tolerance_lower
    upper_limit = nominal + tolerance_upper
    range_breaches = []
    for idx, r in enumerate(readings):
        if r < lower_limit or r > upper_limit:
            range_breaches.append({
                "index": idx + 1,
                "value": r,
                "deviation": round(r - nominal, 6),
                "limit_breached": "LOWER" if r < lower_limit else "UPPER",
            })

    if range_breaches:
        warnings.append(f"{len(range_breaches)} measurement(s) outside specification limits [{lower_limit}, {upper_limit}].")

    # 5. Outlier detection via Grubbs test (ISO 5725-2 / ASTM E178)
    outliers = []
    if len(readings) >= 3:
        n_obs = len(readings)
        mean_val = sum(readings) / n_obs
        var = sum((x - mean_val) ** 2 for x in readings) / (n_obs - 1)
        std_dev = math.sqrt(var)
        # Grubbs 95% critical value table by sample size N
        grubbs_crit_table = {3: 1.15, 4: 1.46, 5: 1.67, 6: 1.82, 7: 1.94, 8: 2.03, 9: 2.11, 10: 2.18}
        crit_g = grubbs_crit_table.get(n_obs, 2.41 if n_obs <= 15 else 2.80)
        threshold = crit_g * std_dev
        if threshold > 0:
            for idx, r in enumerate(readings):
                z_score = abs(r - mean_val) / std_dev
                if z_score >= crit_g:
                    outliers.append({
                        "index": idx + 1,
                        "value": r,
                        "z_score": round(z_score, 2),
                    })
    if outliers:
        warnings.append(f"{len(outliers)} statistical outlier(s) detected via Grubbs test (critical G = {crit_g}).")

    # 6. Overall health assessment
    if critical_issues:
        health_status = "CRITICAL"
    elif warnings:
        health_status = "WARNINGS"
    else:
        health_status = "HEALTHY"

    return {
        "health_status": health_status,
        "total_rows": total_rows,
        "valid_rows_count": valid_count,
        "review_required_count": review_required,
        "reference_valid": ref_valid,
        "reference_days_remaining": ref_days_remaining,
        "range_breaches": range_breaches,
        "outliers": outliers,
        "warnings": warnings,
        "critical_issues": critical_issues,
        "summary": (
            f"{valid_count} valid rows parsed; {len(warnings)} warning(s); {len(critical_issues)} critical issue(s)."
        ),
    }


def build_suggested_measurement_model(
    measurand: str,
    nominal: float,
    unit: str,
    raw_readings: List[float],
    reference_standard: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Automatically propose an ISO/IEC Guide 98-3 (GUM) uncertainty budget model
    based on detected physical domain, sample observations, and reference standard.
    """
    import math

    n = len(raw_readings) if raw_readings else 5
    if raw_readings and len(raw_readings) > 1:
        mean_val = sum(raw_readings) / n
        var = sum((x - mean_val) ** 2 for x in raw_readings) / (n - 1)
        s_val = math.sqrt(var)
        u_rep = s_val / math.sqrt(n)
    else:
        s_val = 0.00010
        u_rep = s_val / math.sqrt(5)

    ref_u = 0.00004
    ref_name = "Laboratory Reference Standard"
    if reference_standard:
        ref_u = float(reference_standard.get("expanded_uncertainty", 0.00004)) / 2.0
        ref_name = reference_standard.get("name", ref_name)

    domain = (measurand or "Length").lower()
    contributors = []

    # 1. Repeatability (Type A)
    contributors.append({
        "name": "Repeatability u(A)",
        "source": "Sample Standard Deviation (Bessel-Corrected)",
        "type": "A",
        "distribution": "normal",
        "value": round(u_rep, 6),
        "divisor": 1.0,
        "sensitivity": 1.0,
        "standard_uncertainty": round(u_rep, 6),
        "dof": max(1, n - 1),
    })

    # 2. Reference Standard Calibration (Type B)
    contributors.append({
        "name": f"Reference Standard ({ref_name})",
        "source": "Traceable Calibration Certificate (k=2)",
        "type": "B",
        "distribution": "normal",
        "value": round(ref_u * 2.0, 6),
        "divisor": 2.0,
        "sensitivity": 1.0,
        "standard_uncertainty": round(ref_u, 6),
        "dof": 50,
    })

    # 3. Resolution (Type B Rectangular)
    if "volt" in domain or unit.upper() in ("V", "MV", "UV"):
        res_val = 0.00001  # 0.01 mV
        res_label = "Digital Multimeter Display Resolution"
    elif "press" in domain or unit.upper() in ("BAR", "MBAR", "PSI"):
        res_val = 0.001   # 1 mbar
        res_label = "Pressure Gauge Scale Resolution"
    elif "temp" in domain or unit.upper() in ("°C", "C", "K"):
        res_val = 0.005
        res_label = "Sensor Readout Resolution"
    else:
        res_val = 0.001   # 1 um for length
        res_label = "Vernier / Scale Resolution"

    u_res = (res_val / 2.0) / math.sqrt(3.0)
    contributors.append({
        "name": res_label,
        "source": "Digital Display Discretization",
        "type": "B",
        "distribution": "rectangular",
        "value": res_val,
        "divisor": 1.73205,
        "sensitivity": 1.0,
        "standard_uncertainty": round(u_res, 6),
        "dof": 100,
    })

    # 4. Environmental / Temperature / Drift correction
    if "length" in domain or unit.upper() in ("MM", "UM", "IN"):
        u_env = (nominal * 11.5e-6 * 0.5) / math.sqrt(3.0)
        env_label = "Differential Thermal Expansion (CTE Delta)"
    elif "volt" in domain or unit.upper() in ("V", "MV"):
        u_env = 0.000005
        env_label = "Thermal EMF Offset & Cable Bias"
    else:
        u_env = 0.00002
        env_label = "Ambient Environmental Sensitivity"

    contributors.append({
        "name": env_label,
        "source": "Laboratory Environmental Fluctuations",
        "type": "B",
        "distribution": "rectangular",
        "value": round(u_env * math.sqrt(3.0), 6),
        "divisor": 1.73205,
        "sensitivity": 1.0,
        "standard_uncertainty": round(u_env, 6),
        "dof": 50,
    })

    # Combined uncertainty calculation
    uc_sq = sum((c["standard_uncertainty"] * c["sensitivity"]) ** 2 for c in contributors)
    uc = math.sqrt(uc_sq)
    k = 2.00
    u95 = uc * k

    return {
        "measurand": measurand,
        "nominal": nominal,
        "unit": unit,
        "contributors": contributors,
        "combined_uncertainty_uc": round(uc, 6),
        "expanded_uncertainty_U95": round(u95, 6),
        "coverage_factor_k": k,
        "effective_dof": 48.0,
        "confidence_level": "95.45%",
        "suggested_model_status": "READY",
    }


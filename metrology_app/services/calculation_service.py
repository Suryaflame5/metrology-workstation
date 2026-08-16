"""
Calculation Service: Orchestrates pure metrology-core calculations and provenance tracking.
"""

from decimal import Decimal
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from metrology_core.context import to_decimal, decimal_sqrt
from metrology_core.uncertainty.type_a import evaluate_type_a
from metrology_core.uncertainty.type_b import evaluate_type_b, DistributionType
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.uncertainty.degrees_of_freedom import calculate_welch_satterthwaite
from metrology_core.decision.tur import calculate_tur
from metrology_core.decision.method6 import calculate_method6_guardband, evaluate_method6_conformance
from metrology_core.decision.method5 import calculate_method5_guardband
from metrology_core.decision.iso14253 import calculate_iso14253_limits, evaluate_iso14253_conformance
from metrology_core.rounding.metrological import format_metrological_result
from metrology_core.provenance import CalculationTrace

from ..models import (
    CalculationCreateRequest,
    UncertaintyBudgetRow,
    UncertaintySummary,
    DecisionSummary,
    CalculationResponse,
    CalibrationPointInput,
    CalibrationPointResult,
    MultiPointCalculationCreateRequest,
    MultiPointCalculationResponse,
)
from ..db import save_calculation, get_calculation, DB_PATH


def compute_micrometer_calibration(
    request: CalculationCreateRequest,
    calc_id: Optional[str] = None,
    created_at: Optional[str] = None,
    db_path: str = DB_PATH,
) -> CalculationResponse:
    """
    Execute complete end-to-end micrometer calibration uncertainty and decision calculation.
    """
    cid = calc_id or f"MC-{str(uuid.uuid4().int)[:8]}"
    ts = created_at or datetime.now(timezone.utc).isoformat()

    # 1. Type A Repeatability Evaluation
    obs = request.repeatability.measurements
    type_a_res = evaluate_type_a(obs)
    mean_val = type_a_res.mean
    u_repeatability = type_a_res.standard_uncertainty
    dof_repeatability = Decimal(str(type_a_res.degrees_of_freedom))

    # 2. Type B Reference Standard
    ref_u_exp = to_decimal(request.reference_standard.uncertainty)
    ref_k = to_decimal(request.reference_standard.coverage_factor_k)
    ref_dof = (
        to_decimal(request.reference_standard.degrees_of_freedom)
        if request.reference_standard.degrees_of_freedom
        else None
    )
    type_b_ref = evaluate_type_b(
        expanded_uncertainty=ref_u_exp,
        coverage_factor=ref_k,
        distribution=DistributionType.NORMAL,
        degrees_of_freedom=ref_dof,
    )
    u_ref = type_b_ref.standard_uncertainty

    # 3. Type B Scale Resolution
    res_val = to_decimal(request.resolution.resolution)
    res_half_width = res_val / Decimal("2")  # ±0.5 resolution
    type_b_res = evaluate_type_b(
        half_width=res_half_width,
        distribution=DistributionType.RECTANGULAR,
    )
    u_resolution = type_b_res.standard_uncertainty

    # 4. Type B Temperature Effect
    temp_hw = to_decimal(request.temperature.half_width_mm)
    type_b_temp = evaluate_type_b(
        half_width=temp_hw,
        distribution=DistributionType.RECTANGULAR,
    )
    u_temp = type_b_temp.standard_uncertainty

    # 5. Law of Propagation (GUM Section 5)
    u_list = [u_repeatability, u_ref, u_resolution, u_temp]
    c_list = [Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1")]
    labels = ["Repeatability (Type A)", "Reference Standard (Type B)", "Resolution (Type B)", "Temperature Effect (Type B)"]
    dof_list = [dof_repeatability, ref_dof, None, None]

    prop_res = propagate_uncertainty(
        standard_uncertainties=u_list,
        sensitivity_coefficients=c_list,
        labels=labels,
        degrees_of_freedom=dof_list,
    )
    u_c = prop_res.combined_standard_uncertainty

    # 6. Welch-Satterthwaite Effective Degrees of Freedom (Annex G)
    dof_res = calculate_welch_satterthwaite(prop_res)
    nu_eff = dof_res.effective_degrees_of_freedom
    k_val = dof_res.coverage_factor_95
    u_95 = dof_res.expanded_uncertainty_95

    # 7. Metrological Rounding (GUM 7.2.6)
    formatted = format_metrological_result(mean_val, u_95, sig_figs=2, unit=request.unit)

    # 8. Error of Indication & Conformity Decision
    nominal = to_decimal(request.nominal_value)
    error_of_indication = mean_val - nominal
    tol_upper = to_decimal(request.tolerance_upper)
    tol_lower = to_decimal(request.tolerance_lower)

    tur_assessment = calculate_tur(tol_upper, tol_lower, u_95)
    tur_val = tur_assessment.tur

    rule_name = request.decision_rule
    if "method 6" in rule_name.lower():
        decision_res = calculate_method6_guardband(tol_upper, tol_lower, u_95)
        raw_verdict = evaluate_method6_conformance(error_of_indication, decision_res)
        verdict = "PASS" if raw_verdict == "ACCEPT" else ("FAIL" if raw_verdict == "REJECT" else "GUARD_BAND")
        w_guardband = decision_res.guardband_w
        m_multiplier = decision_res.multiplier_M
        a_l = decision_res.acceptance_lower
        a_u = decision_res.acceptance_upper
        explanation = (
            f"Evaluated under ANSI/NCSL Z540.3 Method 6 (2% False Accept Risk). "
            f"TUR = {tur_val:.3f}. Guardband w = {w_guardband:.6f} mm (M = {m_multiplier:.4f}). "
            f"Acceptance Zone = [{a_l:.5f}, {a_u:.5f}] mm. "
            f"Measured Error = {error_of_indication:+.5f} mm -> Verdict: {verdict}."
        )
    elif "method 5" in rule_name.lower():
        m5_res = calculate_method5_guardband(tol_upper, tol_lower, u_95)
        w_guardband = m5_res.guardband_w
        m_multiplier = Decimal("1.0")
        a_l = m5_res.acceptance_lower
        a_u = m5_res.acceptance_upper
        if a_l <= error_of_indication <= a_u:
            verdict = "PASS"
        elif tol_lower <= error_of_indication <= tol_upper:
            verdict = "GUARD_BAND"
        else:
            verdict = "FAIL"
        explanation = (
            f"Evaluated under ANSI/NCSL Z540.3 Method 5 (RSS Guardband). "
            f"TUR = {tur_val:.3f}. Guardband w = {w_guardband:.6f} mm. "
            f"Acceptance Zone = [{a_l:.5f}, {a_u:.5f}] mm. "
            f"Measured Error = {error_of_indication:+.5f} mm -> Verdict: {verdict}."
        )
    else:  # ISO 14253-1:2017
        iso_res = calculate_iso14253_limits(tol_upper, tol_lower, u_95)
        iso_verdict = evaluate_iso14253_conformance(error_of_indication, iso_res)
        verdict = "PASS" if iso_verdict == "CONFORMITY" else ("FAIL" if iso_verdict == "NON_CONFORMITY" else "GUARD_BAND")
        w_guardband = iso_res.guardband_w
        m_multiplier = Decimal("1.0")
        a_l = iso_res.conformance_lower
        a_u = iso_res.conformance_upper
        explanation = (
            f"Evaluated under ISO 14253-1:2017 Decision Rules (Guardband w = U). "
            f"Conformance Zone = [{a_l:.5f}, {a_u:.5f}] mm. "
            f"Measured Error = {error_of_indication:+.5f} mm -> Verdict: {iso_verdict}."
        )

    # 9. Build Detailed Budget Rows with Provenance
    budget_rows: List[UncertaintyBudgetRow] = []
    comp_types = ["A", "B", "B", "B"]
    comp_dists = ["Statistical (Normal)", "Normal (k=2)", "Rectangular", "Rectangular"]
    comp_divs = [f"sqrt({len(obs)})", str(ref_k), "sqrt(3)", "sqrt(3)"]
    comp_sources = [
        f"Lab Repeated Observations (n={len(obs)})",
        f"Gauge Block Certificate ({request.reference_standard.certificate_id})",
        f"Digital Scale Scale Division ({request.resolution.resolution} mm)",
        f"Thermal Model (CTE={request.temperature.expansion_coefficient_ppm_k} ppm/K, ΔT={request.temperature.delta_temperature_c} °C)",
    ]
    
    for i, c in enumerate(prop_res.components):
        dof_str = f"{c.degrees_of_freedom:.1f}" if c.degrees_of_freedom is not None else "inf"
        comp_raw_str = f"{c.label}:{comp_types[i]}:{comp_dists[i]}:{c.standard_uncertainty}:{dof_str}"
        comp_hash = hashlib.sha256(comp_raw_str.encode("utf-8")).hexdigest()[:16]
        budget_rows.append(
            UncertaintyBudgetRow(
                label=c.label,
                component_type=comp_types[i],
                distribution=comp_dists[i],
                divisor=comp_divs[i],
                standard_uncertainty_mm=f"{c.standard_uncertainty:.6f}",
                sensitivity_coefficient=f"{c.sensitivity_coefficient:.1f}",
                variance_contribution=f"{c.variance_contribution:.8f}",
                percentage_contribution=f"{c.percentage_contribution:.2f}%",
                degrees_of_freedom=dof_str,
                source_reference=comp_sources[i],
                component_hash=comp_hash,
            )
        )

    nu_eff_str = f"{nu_eff:.1f}" if nu_eff is not None else "inf"

    uncertainty_summary = UncertaintySummary(
        combined_standard_uncertainty_mm=f"{u_c:.6f}",
        effective_degrees_of_freedom=nu_eff_str,
        coverage_factor_k=f"{k_val:.4f}",
        expanded_uncertainty_U95_mm=f"{u_95:.6f}",
        formatted_result=formatted.formatted_string,
        budget_rows=budget_rows,
    )

    decision_summary = DecisionSummary(
        nominal_mm=f"{nominal:.5f}",
        mean_measured_mm=f"{mean_val:.5f}",
        error_of_indication_mm=f"{error_of_indication:+.5f}",
        tolerance_lower_mm=f"{tol_lower:.5f}",
        tolerance_upper_mm=f"{tol_upper:.5f}",
        tur=f"{tur_val:.3f}",
        guardband_multiplier_M=f"{m_multiplier:.4f}",
        guardband_w_mm=f"{w_guardband:.6f}",
        acceptance_lower_mm=f"{a_l:.5f}",
        acceptance_upper_mm=f"{a_u:.5f}",
        decision_rule=rule_name,
        conformity_verdict=verdict,
        decision_explanation=explanation,
    )

    # 10. Cryptographic Provenance & Digests
    input_dict = request.model_dump()
    canonical_input_json = json.dumps(input_dict, sort_keys=True)
    input_sha256 = hashlib.sha256(canonical_input_json.encode("utf-8")).hexdigest()

    root_id = request.root_id or cid
    rev_num = request.revision_number
    parent_hash = request.parent_sha256
    rec_class = request.record_class

    trace = CalculationTrace(
        calculation_id=cid,
        measurement_model=f"Error = Mean(Observations) - Nominal ({request.nominal_value} mm)",
        input_data=input_dict,
        uncertainty_components=[row.model_dump() for row in budget_rows],
        sensitivity_coefficients=[{"label": l, "c": "1"} for l in labels],
        covariance_matrix=None,
        combined_uncertainty={"u_c": str(u_c), "variance": str(u_c ** 2)},
        degrees_of_freedom={"nu_eff": nu_eff_str},
        coverage_factor={"k": str(k_val), "confidence": request.confidence_level},
        expanded_uncertainty={"U_95": str(u_95)},
        decision_rule={"name": rule_name},
        guardband={"w": str(w_guardband), "M": str(m_multiplier), "TUR": str(tur_val)},
        conformity_decision={"verdict": verdict, "error": str(error_of_indication)},
        rounding={"formatted": formatted.formatted_string},
        timestamp=ts,
    )
    calculation_sha256 = trace.sha256_hash

    response = CalculationResponse(
        id=cid,
        root_id=root_id,
        revision_number=rev_num,
        parent_sha256=parent_hash,
        revision_notes=request.revision_notes,
        record_class=rec_class,
        created_at=ts,
        instrument_name=request.instrument_name,
        instrument_model=request.instrument_model,
        procedure_name=request.procedure_name,
        procedure_version=request.procedure_version,
        unit=request.unit,
        status="VALIDATED",
        conformity_verdict=verdict,
        input_sha256=input_sha256,
        calculation_sha256=calculation_sha256,
        input_data=input_dict,
        uncertainty_summary=uncertainty_summary,
        decision_summary=decision_summary,
    )

    # 11. Save to SQLite database
    save_calculation(
        {
            "id": cid,
            "root_id": root_id,
            "revision_number": rev_num,
            "parent_sha256": parent_hash,
            "revision_notes": request.revision_notes,
            "record_class": rec_class,
            "created_at": ts,
            "instrument_name": request.instrument_name,
            "instrument_model": request.instrument_model,
            "procedure_name": request.procedure_name,
            "procedure_version": request.procedure_version,
            "unit": request.unit,
            "nominal_value": request.nominal_value,
            "tolerance_upper": request.tolerance_upper,
            "tolerance_lower": request.tolerance_lower,
            "confidence_level": request.confidence_level,
            "decision_rule": request.decision_rule,
            "input_data": input_dict,
            "result_data": response.model_dump(),
            "input_sha256": input_sha256,
            "calculation_sha256": calculation_sha256,
            "status": "VALIDATED",
            "conformity_verdict": verdict,
        },
        db_path=db_path,
    )

    return response


def compute_multi_point_calibration(
    request: MultiPointCalculationCreateRequest,
    calc_id: Optional[str] = None,
    db_path: str = DB_PATH,
) -> MultiPointCalculationResponse:
    """
    Execute multi-point calibration processing across multiple nominal checkpoints.
    """
    cid = calc_id or f"MP-{str(uuid.uuid4().int)[:8]}"
    ts = datetime.now(timezone.utc).isoformat()

    point_results: List[CalibrationPointResult] = []
    max_error = Decimal("0")
    max_u95 = Decimal("0")
    has_fail = False
    has_guard = False

    for idx, pt in enumerate(request.points):
        # 1. Type A Repeatability
        type_a_res = evaluate_type_a(pt.readings)
        error_val = type_a_res.mean - to_decimal(pt.nominal_value)

        # 2. Type B components
        u_ref = evaluate_type_b(expanded_uncertainty=to_decimal(pt.reference_uncertainty), coverage_factor=Decimal("2.0"), distribution=DistributionType.NORMAL)
        u_res = evaluate_type_b(half_width=to_decimal(request.resolution) / Decimal("2"), distribution=DistributionType.RECTANGULAR)
        u_temp = evaluate_type_b(half_width=to_decimal(request.temperature_half_width), distribution=DistributionType.RECTANGULAR)

        # 3. Propagation & DoF
        u_list = [type_a_res.standard_uncertainty, u_ref.standard_uncertainty, u_res.standard_uncertainty, u_temp.standard_uncertainty]
        c_list = [Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1")]
        dof_list = [type_a_res.degrees_of_freedom, 50, None, None]
        prop_res = propagate_uncertainty(u_list, c_list, degrees_of_freedom=dof_list)
        dof_res = calculate_welch_satterthwaite(prop_res)

        u_c = prop_res.combined_standard_uncertainty
        u_95 = dof_res.expanded_uncertainty_95

        # 4. Decision Rule
        tol_up = to_decimal(pt.tolerance)
        tol_low = -to_decimal(pt.tolerance)
        tur_res = calculate_tur(tol_up, tol_low, u_95)

        if "method 5" in request.decision_rule.lower():
            m5_res = calculate_method5_guardband(tol_up, tol_low, u_95)
            w_val = m5_res.guardband_w
            a_l = m5_res.acceptance_lower
            a_u = m5_res.acceptance_upper
            v = "PASS" if a_l <= error_val <= a_u else ("GUARD_BAND" if tol_low <= error_val <= tol_up else "FAIL")
        elif "iso 14253" in request.decision_rule.lower():
            iso_res = calculate_iso14253_limits(tol_up, tol_low, u_95)
            raw_v = evaluate_iso14253_conformance(error_val, iso_res)
            v = "PASS" if raw_v == "CONFORMITY" else ("FAIL" if raw_v == "NON_CONFORMITY" else "GUARD_BAND")
            w_val = iso_res.guardband_w
            a_l = iso_res.conformance_lower
            a_u = iso_res.conformance_upper
        else: # Method 6
            m6_res = calculate_method6_guardband(tol_up, tol_low, u_95)
            raw_v = evaluate_method6_conformance(error_val, m6_res)
            v = "PASS" if raw_v == "ACCEPT" else ("FAIL" if raw_v == "REJECT" else "GUARD_BAND")
            w_val = m6_res.guardband_w
            a_l = m6_res.acceptance_lower
            a_u = m6_res.acceptance_upper

        if v == "FAIL":
            has_fail = True
        elif v == "GUARD_BAND":
            has_guard = True

        if abs(error_val) > max_error:
            max_error = abs(error_val)
        if u_95 > max_u95:
            max_u95 = u_95

        point_results.append(
            CalibrationPointResult(
                point_index=idx + 1,
                nominal_value=pt.nominal_value,
                mean_measured=float(type_a_res.mean),
                error_of_indication=float(error_val),
                combined_uncertainty_uc=float(u_c),
                expanded_uncertainty_U95=float(u_95),
                tur=float(tur_res.tur),
                guardband_w=float(w_val),
                acceptance_lower=float(a_l),
                acceptance_upper=float(a_u),
                verdict=v,
            )
        )

    overall_verdict = "FAIL" if has_fail else ("GUARD_BAND" if has_guard else "PASS")

    inp_dict = request.model_dump()
    canonical_inp = json.dumps(inp_dict, sort_keys=True)
    input_sha256 = hashlib.sha256(canonical_inp.encode("utf-8")).hexdigest()

    res_dict = {
        "id": cid,
        "created_at": ts,
        "instrument_name": request.instrument_name,
        "instrument_model": request.instrument_model,
        "procedure_name": request.procedure_name,
        "unit": request.unit,
        "total_points": len(point_results),
        "max_error_of_indication": float(max_error),
        "max_expanded_uncertainty": float(max_u95),
        "overall_verdict": overall_verdict,
        "point_results": [p.model_dump() for p in point_results],
    }
    canonical_res = json.dumps(res_dict, sort_keys=True)
    calc_sha256 = hashlib.sha256(canonical_res.encode("utf-8")).hexdigest()

    response = MultiPointCalculationResponse(
        id=cid,
        created_at=ts,
        instrument_name=request.instrument_name,
        instrument_model=request.instrument_model,
        procedure_name=request.procedure_name,
        unit=request.unit,
        total_points=len(point_results),
        max_error_of_indication=float(max_error),
        max_expanded_uncertainty=float(max_u95),
        overall_verdict=overall_verdict,
        point_results=point_results,
        input_sha256=input_sha256,
        calculation_sha256=calc_sha256,
    )

    # Save to database
    save_calculation(
        {
            "id": cid,
            "root_id": cid,
            "revision_number": 1,
            "record_class": request.record_class,
            "created_at": ts,
            "instrument_name": request.instrument_name,
            "instrument_model": request.instrument_model,
            "procedure_name": request.procedure_name,
            "procedure_version": request.procedure_version,
            "unit": request.unit,
            "nominal_value": f"{request.points[0].nominal_value}..{request.points[-1].nominal_value}" if request.points else "0.0",
            "tolerance_upper": f"±{request.points[0].tolerance}" if request.points else "0.0",
            "tolerance_lower": f"±{request.points[0].tolerance}" if request.points else "0.0",
            "confidence_level": "95%",
            "decision_rule": request.decision_rule,
            "input_data": inp_dict,
            "result_data": response.model_dump(),
            "input_sha256": input_sha256,
            "calculation_sha256": calc_sha256,
            "status": "VALIDATED",
            "conformity_verdict": overall_verdict,
        },
        db_path=db_path,
    )

    return response

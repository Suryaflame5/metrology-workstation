"""
V5 Interactive Uncertainty & Conformity Workbench Service.
Grounded in metrology_core exact decimal mathematics.
"""

from decimal import Decimal
from typing import List, Dict, Any
from metrology_core.context import to_decimal
from metrology_core.uncertainty.type_b import evaluate_type_b, DistributionType
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.uncertainty.degrees_of_freedom import calculate_welch_satterthwaite
from metrology_core.decision.tur import calculate_tur
from metrology_core.decision.method6 import calculate_method6_guardband, evaluate_method6_conformance
from metrology_core.decision.method5 import calculate_method5_guardband
from metrology_core.decision.iso14253 import calculate_iso14253_limits
from ..models import (
    UncertaintyComponentInput,
    UncertaintyWorkbenchResponse,
    ConformityWorkbenchRequest,
    ConformityWorkbenchResponse,
)


def compute_uncertainty_workbench(
    components: List[UncertaintyComponentInput],
    confidence_level: str = "95%",
) -> UncertaintyWorkbenchResponse:
    """
    Evaluates an interactive uncertainty budget in real time using metrology_core.
    """
    u_list: List[Decimal] = []
    c_list: List[Decimal] = []
    labels: List[str] = []
    dof_list: List[Any] = []
    dist_names: List[str] = []

    for comp in components:
        dist_str = comp.distribution.lower()
        if dist_str in ("normal", "gaussian"):
            dist_enum = DistributionType.NORMAL
            u_b = evaluate_type_b(
                distribution=dist_enum,
                expanded_uncertainty=to_decimal(comp.semi_range),
                coverage_factor=to_decimal(comp.coverage_factor_k),
                degrees_of_freedom=to_decimal(comp.degrees_of_freedom) if comp.degrees_of_freedom else None,
            )
        elif dist_str == "triangular":
            dist_enum = DistributionType.TRIANGULAR
            u_b = evaluate_type_b(
                distribution=dist_enum,
                half_width=to_decimal(comp.semi_range),
            )
        elif dist_str == "u_shaped":
            dist_enum = DistributionType.U_SHAPED
            u_b = evaluate_type_b(
                distribution=dist_enum,
                half_width=to_decimal(comp.semi_range),
            )
        else:
            dist_enum = DistributionType.RECTANGULAR
            u_b = evaluate_type_b(
                distribution=dist_enum,
                half_width=to_decimal(comp.semi_range),
            )

        u_list.append(u_b.standard_uncertainty)
        c_list.append(to_decimal(comp.sensitivity_coefficient))
        labels.append(comp.name)
        dof_list.append(u_b.degrees_of_freedom)
        dist_names.append(comp.distribution)

    # Propagate combined uncertainty
    prop_result = propagate_uncertainty(
        standard_uncertainties=u_list,
        sensitivity_coefficients=c_list,
        labels=labels,
        degrees_of_freedom=dof_list,
    )
    u_c = prop_result.combined_standard_uncertainty

    # Welch-Satterthwaite DoF
    dof_result = calculate_welch_satterthwaite(prop_result)
    k = dof_result.coverage_factor_95
    u_95 = dof_result.expanded_uncertainty_95
    nu_eff = dof_result.effective_degrees_of_freedom if dof_result.effective_degrees_of_freedom is not None else Decimal("50.0")

    # Build breakdown
    budget_breakdown: List[Dict[str, Any]] = []
    for idx, comp in enumerate(prop_result.components):
        budget_breakdown.append({
            "name": comp.label,
            "distribution": dist_names[idx],
            "standard_uncertainty": float(comp.standard_uncertainty),
            "sensitivity_coefficient": float(comp.sensitivity_coefficient),
            "variance_contribution": float(comp.variance_contribution),
            "percentage_contribution": f"{float(comp.percentage_contribution):.2f}%",
            "degrees_of_freedom": float(comp.degrees_of_freedom) if comp.degrees_of_freedom is not None else 50.0,
        })

    return UncertaintyWorkbenchResponse(
        combined_uncertainty_uc=float(u_c),
        effective_degrees_of_freedom=float(nu_eff),
        coverage_factor_k=float(k),
        expanded_uncertainty_U95=float(u_95),
        budget_breakdown=budget_breakdown,
    )


def compute_conformity_workbench(
    req: ConformityWorkbenchRequest,
) -> ConformityWorkbenchResponse:
    """
    Evaluates guardbanded conformity boundaries and consumer risk in real time.
    """
    nom = to_decimal(req.nominal_value)
    meas = to_decimal(req.measured_value)
    tol_l = to_decimal(req.tolerance_lower)
    tol_u = to_decimal(req.tolerance_upper)
    u_95 = to_decimal(req.expanded_uncertainty_U95)

    error = meas - nom

    # TUR
    tur_res = calculate_tur(tol_u, tol_l, u_95)
    tur_val = tur_res.tur

    rule = req.decision_rule.upper()

    if "METHOD 6" in rule or "Z540.3" in rule:
        decision_res = calculate_method6_guardband(tol_u, tol_l, u_95)
        raw_verdict = evaluate_method6_conformance(error, decision_res)
        verdict = "PASS" if raw_verdict == "ACCEPT" else ("FAIL" if raw_verdict == "REJECT" else "GUARD_BAND")
        guard_w = decision_res.guardband_w
        mult = decision_res.multiplier_M
        acc_l = nom + decision_res.acceptance_lower
        acc_u = nom + decision_res.acceptance_upper
        pfa = 2.0 if verdict != "FAIL" else 0.0
        statement = (
            f"ANSI/NCSL Z540.3 Method 6 Guardbanding applied with Multiplier M={float(mult):.4f}. "
            f"Acceptance boundary reduced by w={float(guard_w):.5f} mm to guarantee P(CR) <= 2.0%."
        )
    elif "METHOD 5" in rule:
        m5_res = calculate_method5_guardband(tol_u, tol_l, u_95)
        guard_w = m5_res.guardband_w
        mult = Decimal("1.0")
        acc_l = nom + m5_res.acceptance_lower
        acc_u = nom + m5_res.acceptance_upper
        if m5_res.acceptance_lower <= error <= m5_res.acceptance_upper:
            verdict = "PASS"
        elif tol_l <= error <= tol_u:
            verdict = "GUARD_BAND"
        else:
            verdict = "FAIL"
        pfa = 2.0
        statement = f"ANSI/NCSL Z540.3 Method 5 RSS Guardband width w={float(guard_w):.5f} mm applied."
    else:  # ISO 14253-1
        iso_res = calculate_iso14253_limits(tol_u, tol_l, u_95)
        guard_w = iso_res.guardband_w
        mult = Decimal("1.0")
        acc_l = nom + iso_res.conformance_lower
        acc_u = nom + iso_res.conformance_upper
        if iso_res.conformance_lower <= error <= iso_res.conformance_upper:
            verdict = "PASS"
        elif iso_res.non_conformance_lower <= error <= iso_res.non_conformance_upper:
            verdict = "GUARD_BAND"
        else:
            verdict = "FAIL"
        pfa = 0.5
        statement = f"ISO 14253-1 Complete Conformance Guardband w=U95={float(u_95):.5f} mm applied."

    return ConformityWorkbenchResponse(
        error_of_indication=float(error),
        tur=float(tur_val),
        guardband_multiplier=float(mult),
        guardband_width_w=float(guard_w),
        acceptance_lower=float(acc_l),
        acceptance_upper=float(acc_u),
        consumer_risk_pfa_pct=pfa,
        conformance_verdict=verdict,
        derivation_statement=statement,
    )

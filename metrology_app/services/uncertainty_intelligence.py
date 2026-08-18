"""
Uncertainty Contribution Intelligence & What-If Sensitivity Engine (JCGM 100:2008).
Evaluates dominant contributors, sensitivity rankings, and deterministic variance reduction simulation.
"""

from decimal import Decimal
import math
from typing import Dict, Any, List, Optional
from metrology_core.context import to_decimal
from metrology_core.uncertainty.type_b import evaluate_type_b, DistributionType
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.uncertainty.degrees_of_freedom import calculate_welch_satterthwaite
from ..models import UncertaintyComponentItem


def analyze_uncertainty_contributions(components: List[UncertaintyComponentItem]) -> Dict[str, Any]:
    """
    Compute dominant uncertainty contributors, percentage shares, and ranking.
    """
    if not components:
        return {"dominant_contributor": None, "ranked_contributors": [], "total_variance": 0.0}

    eval_components = []
    for c in components:
        # Convert distribution string to DistributionType
        dist_map = {
            "normal": DistributionType.NORMAL,
            "rectangular": DistributionType.RECTANGULAR,
            "triangular": DistributionType.TRIANGULAR,
            "u_shaped": DistributionType.U_SHAPED,
        }
        dist_enum = dist_map.get(c.distribution.lower(), DistributionType.RECTANGULAR)
        b_res = evaluate_type_b(c.semi_range, dist_enum, coverage_factor=c.coverage_factor_k)
        
        std_unc = float(b_res.standard_uncertainty)
        sens = float(c.sensitivity_coefficient)
        var_contrib = (sens * std_unc) ** 2
        dof = float(c.degrees_of_freedom)
        
        eval_components.append({
            "name": c.name,
            "distribution": c.distribution,
            "standard_uncertainty": std_unc,
            "sensitivity_coefficient": sens,
            "variance_contribution": var_contrib,
            "degrees_of_freedom": dof,
        })

    total_variance = sum(item["variance_contribution"] for item in eval_components)
    combined_uc = math.sqrt(total_variance) if total_variance > 0 else 0.0

    # Calculate percentage contributions
    for item in eval_components:
        item["percentage_share"] = round((item["variance_contribution"] / total_variance) * 100.0, 2) if total_variance > 0 else 0.0

    # Sort descending by variance contribution
    ranked = sorted(eval_components, key=lambda x: x["variance_contribution"], reverse=True)
    dominant = ranked[0] if ranked else None

    # Improvement opportunity: What happens if dominant contributor is reduced by 50%?
    potential_uc = combined_uc
    if dominant and total_variance > 0:
        reduced_dominant_var = dominant["variance_contribution"] * 0.25  # 50% reduction in u means 25% of variance
        new_total_var = (total_variance - dominant["variance_contribution"]) + reduced_dominant_var
        potential_uc = math.sqrt(new_total_var)
        pct_improvement = ((combined_uc - potential_uc) / combined_uc) * 100.0 if combined_uc > 0 else 0.0
    else:
        pct_improvement = 0.0

    return {
        "combined_uncertainty_uc": round(combined_uc, 6),
        "total_variance": total_variance,
        "dominant_contributor": dominant["name"] if dominant else None,
        "dominant_contributor_share_pct": dominant["percentage_share"] if dominant else 0.0,
        "ranked_contributors": ranked,
        "potential_improvement": {
            "strategy": f"Reduce dominant contributor '{dominant['name'] if dominant else 'N/A'}' by 50%",
            "potential_uc": round(potential_uc, 6),
            "uncertainty_reduction_pct": round(pct_improvement, 1),
        },
    }


def simulate_what_if_uncertainty_reduction(
    components: List[UncertaintyComponentItem],
    target_component_name: str,
    reduction_percentage: float = 50.0,
) -> Dict[str, Any]:
    """
    Deterministically simulate the impact of reducing a specific uncertainty source.
    """
    baseline_analysis = analyze_uncertainty_contributions(components)
    baseline_uc = baseline_analysis["combined_uncertainty_uc"]

    # Modify the target component's semi_range
    modified_components = []
    factor = 1.0 - (reduction_percentage / 100.0)

    for c in components:
        if c.name.lower() == target_component_name.lower():
            mod_c = UncertaintyComponentItem(
                name=c.name,
                distribution=c.distribution,
                semi_range=c.semi_range * factor,
                coverage_factor_k=c.coverage_factor_k,
                sensitivity_coefficient=c.sensitivity_coefficient,
                degrees_of_freedom=c.degrees_of_freedom,
            )
            modified_components.append(mod_c)
        else:
            modified_components.append(c)

    sim_analysis = analyze_uncertainty_contributions(modified_components)
    sim_uc = sim_analysis["combined_uncertainty_uc"]
    uc_delta = baseline_uc - sim_uc
    delta_pct = (uc_delta / baseline_uc) * 100.0 if baseline_uc > 0 else 0.0

    return {
        "target_component": target_component_name,
        "reduction_percentage": reduction_percentage,
        "baseline_combined_uc": baseline_uc,
        "simulated_combined_uc": sim_uc,
        "uncertainty_reduction_magnitude": round(uc_delta, 6),
        "uncertainty_reduction_percentage": round(delta_pct, 2),
        "baseline_expanded_u95": round(baseline_uc * 2.0, 6),
        "simulated_expanded_u95": round(sim_uc * 2.0, 6),
        "verdict": "SIGNIFICANT_IMPROVEMENT" if delta_pct >= 15.0 else "MODEST_IMPROVEMENT",
    }

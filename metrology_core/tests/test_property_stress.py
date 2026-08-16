"""
Property-based and randomized stress testing for metrology-core invariants.
"""

import pytest
from decimal import Decimal
import random
from metrology_core.context import to_decimal, MetrologyValidationError
from metrology_core.decision.tur import calculate_tur
from metrology_core.decision.method6 import calculate_method6_guardband
from metrology_core.uncertainty.covariance import CorrelationMatrix
from metrology_core.uncertainty.propagation import propagate_uncertainty
from metrology_core.rounding.metrological import round_uncertainty, round_measurement_to_uncertainty


def test_property_method6_monotonicity():
    """Property: Multiplier M(TUR) is strictly non-increasing with TUR."""
    previous_m = Decimal("1000")
    # Sweep TUR from 0.5 to 6.0 in steps of 0.05
    for i in range(50, 600, 5):
        tur_val = Decimal(i) / Decimal("100")
        # Tol width = 2 * TUR, U = 1.0 -> TUR
        t_u = tur_val
        t_l = -tur_val
        u = Decimal("1.0")
        res = calculate_method6_guardband(t_u, t_l, u)
        assert res.multiplier_M <= previous_m, (
            f"Monotonicity violation at TUR={tur_val}: M={res.multiplier_M} > prev_M={previous_m}"
        )
        previous_m = res.multiplier_M


def test_property_guardband_non_negativity_and_containment():
    """Property: For any valid tolerance and uncertainty, w >= 0 and [A_L, A_U] is inside [T_L, T_U]."""
    random.seed(42)
    for _ in range(200):
        # Generate positive tolerance half-width between 1e-4 and 1e4
        exp_tol = random.uniform(-4, 4)
        t_half = Decimal(str(round(10 ** exp_tol, 6)))
        
        # Generate uncertainty between 0.05 * t_half and 2 * t_half (TUR between 0.5 and 20)
        u_ratio = Decimal(str(round(random.uniform(0.05, 1.5), 4)))
        u = t_half * u_ratio

        res = calculate_method6_guardband(t_half, -t_half, u)

        # Invariant 1: Non-negativity
        assert res.guardband_w >= Decimal("0"), f"Negative guardband: {res.guardband_w}"
        # Invariant 2: Multiplier non-negativity
        assert res.multiplier_M >= Decimal("0"), f"Negative multiplier: {res.multiplier_M}"
        # Invariant 3: Containment
        assert res.acceptance_lower >= res.tolerance_lower, f"A_L < T_L: {res.acceptance_lower} < {res.tolerance_lower}"
        assert res.acceptance_upper <= res.tolerance_upper, f"A_U > T_U: {res.acceptance_upper} > {res.tolerance_upper}"
        # Invariant 4: Symmetry
        assert abs(res.acceptance_lower + res.acceptance_upper) < Decimal("1e-20"), "Symmetry violation"


def test_property_correlation_propagation_permutation_invariance():
    """Property: Permuting the order of variables leaves combined uncertainty invariant."""
    random.seed(1337)
    for _ in range(50):
        u1 = Decimal(str(round(random.uniform(0.1, 10.0), 3)))
        u2 = Decimal(str(round(random.uniform(0.1, 10.0), 3)))
        r_val = Decimal(str(round(random.uniform(-0.95, 0.95), 3)))

        mat1 = CorrelationMatrix([[Decimal("1"), r_val], [r_val, Decimal("1")]], labels=["X1", "X2"])
        res1 = propagate_uncertainty([u1, u2], correlation_matrix=mat1)

        mat2 = CorrelationMatrix([[Decimal("1"), r_val], [r_val, Decimal("1")]], labels=["X2", "X1"])
        res2 = propagate_uncertainty([u2, u1], correlation_matrix=mat2)

        diff = abs(res1.combined_standard_uncertainty - res2.combined_standard_uncertainty)
        assert diff < Decimal("1e-25"), f"Permutation variance mismatch: {diff}"

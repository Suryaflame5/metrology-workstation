"""
Unit tests for Immutable Calculation Provenance and Cryptographic Hash Auditing.
"""

import pytest
import json
from decimal import Decimal
from metrology_core.provenance import CalculationTrace, verify_calculation_json


def test_calculation_trace_integrity_and_hashing():
    trace = CalculationTrace(
        calculation_id="MC-00000142",
        measurement_model="Y = X1 + X2",
        input_data={"voltage": Decimal("10.005"), "unit": "V", "tolerance": "±0.1"},
        uncertainty_components=[
            {"label": "Repeatability", "type": "Type A", "u": Decimal("0.015")},
            {"label": "Calibration", "type": "Type B", "u": Decimal("0.020")},
        ],
        sensitivity_coefficients=[{"label": "Repeatability", "c": Decimal("1")}, {"label": "Calibration", "c": Decimal("1")}],
        covariance_matrix=[[Decimal("1"), Decimal("0")], [Decimal("0"), Decimal("1")]],
        combined_uncertainty={"u_c": Decimal("0.025"), "variance": Decimal("0.000625")},
        degrees_of_freedom={"nu_eff": Decimal("45.2")},
        coverage_factor={"k": Decimal("2.0"), "confidence": "95.45%"},
        expanded_uncertainty={"U": Decimal("0.050")},
        decision_rule={"standard": "ANSI/NCSL Z540.3 Method 6", "target_pfa": "2%"},
        guardband={"TUR": Decimal("2.0"), "M": Decimal("0.281645"), "w": Decimal("0.0140823")},
        conformity_decision={"status": "PASS", "measured": Decimal("10.005"), "A_L": Decimal("-0.0859"), "A_U": Decimal("0.0859")},
        rounding={"formatted": "(10.005 ± 0.050) V"},
    )

    # 1. Verify that hash is a 64-char hex string
    assert len(trace.sha256_hash) == 64
    # 2. Verify self-integrity
    assert trace.verify_integrity() is True

    # 3. Serialize to JSON and verify via external JSON validator
    json_repr = trace.to_json()
    assert verify_calculation_json(json_repr) is True

    # 4. Tamper with JSON and verify that validator rejects it
    tampered_dict = json.loads(json_repr)
    tampered_dict["input_data"]["voltage"] = "10.999"  # Tampered!
    tampered_json = json.dumps(tampered_dict)
    assert verify_calculation_json(tampered_json) is False

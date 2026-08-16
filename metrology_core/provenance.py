"""
Immutable Calculation Provenance Tracer and Cryptographic Audit Hash Engine.

Produces reproducible, tamper-evident end-to-end audit receipts for metrology calculations.
"""

from decimal import Decimal
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from .context import to_decimal, DECIMAL_CONTEXT


def _decimal_to_str(obj: Any) -> Any:
    """Helper to recursively convert Decimals and tuples to JSON-serializable types."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, tuple) and hasattr(obj, "_asdict"):
        return {k: _decimal_to_str(v) for k, v in obj._asdict().items()}
    if isinstance(obj, dict):
        return {k: _decimal_to_str(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_decimal_to_str(v) for v in obj]
    return obj


class CalculationTrace:
    """
    Immutable, serializable calculation provenance receipt with SHA-256 cryptographic verification.
    """

    def __init__(
        self,
        calculation_id: str,
        measurement_model: str,
        input_data: Dict[str, Any],
        uncertainty_components: List[Dict[str, Any]],
        sensitivity_coefficients: List[Dict[str, Any]],
        covariance_matrix: Optional[List[List[Any]]],
        combined_uncertainty: Dict[str, Any],
        degrees_of_freedom: Dict[str, Any],
        coverage_factor: Dict[str, Any],
        expanded_uncertainty: Dict[str, Any],
        decision_rule: Dict[str, Any],
        guardband: Dict[str, Any],
        conformity_decision: Dict[str, Any],
        rounding: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> None:
        self.calculation_id = calculation_id
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.measurement_model = measurement_model
        self.input_data = _decimal_to_str(input_data)
        self.uncertainty_components = _decimal_to_str(uncertainty_components)
        self.sensitivity_coefficients = _decimal_to_str(sensitivity_coefficients)
        self.covariance_matrix = _decimal_to_str(covariance_matrix)
        self.combined_uncertainty = _decimal_to_str(combined_uncertainty)
        self.degrees_of_freedom = _decimal_to_str(degrees_of_freedom)
        self.coverage_factor = _decimal_to_str(coverage_factor)
        self.expanded_uncertainty = _decimal_to_str(expanded_uncertainty)
        self.decision_rule = _decimal_to_str(decision_rule)
        self.guardband = _decimal_to_str(guardband)
        self.conformity_decision = _decimal_to_str(conformity_decision)
        self.rounding = _decimal_to_str(rounding)

        self.canonical_dict = self._build_canonical_dict()
        self.sha256_hash = self._compute_sha256()

    def _build_canonical_dict(self) -> Dict[str, Any]:
        """Build dictionary with sorted keys for deterministic hashing."""
        return {
            "calculation_id": self.calculation_id,
            "timestamp": self.timestamp,
            "measurement_model": self.measurement_model,
            "input_data": self.input_data,
            "uncertainty_components": self.uncertainty_components,
            "sensitivity_coefficients": self.sensitivity_coefficients,
            "covariance_matrix": self.covariance_matrix,
            "combined_uncertainty": self.combined_uncertainty,
            "degrees_of_freedom": self.degrees_of_freedom,
            "coverage_factor": self.coverage_factor,
            "expanded_uncertainty": self.expanded_uncertainty,
            "decision_rule": self.decision_rule,
            "guardband": self.guardband,
            "conformity_decision": self.conformity_decision,
            "rounding": self.rounding,
        }

    def _compute_sha256(self) -> str:
        """Compute SHA-256 hash of canonical JSON string."""
        canonical_json = json.dumps(self.canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Return full dictionary including SHA-256 provenance hash."""
        d = dict(self.canonical_dict)
        d["sha256_hash"] = self.sha256_hash
        return d

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def verify_integrity(self) -> bool:
        """Verify that the recorded SHA-256 hash matches the contents."""
        computed = self._compute_sha256()
        return computed == self.sha256_hash


def verify_calculation_json(json_str: str) -> bool:
    """Verify cryptographic integrity of a serialized calculation trace JSON string."""
    data = json.loads(json_str)
    recorded_hash = data.get("sha256_hash")
    if not recorded_hash:
        return False
    data_without_hash = {k: v for k, v in data.items() if k != "sha256_hash"}
    canonical_json = json.dumps(data_without_hash, sort_keys=True, separators=(",", ":"))
    recomputed_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return recomputed_hash == recorded_hash

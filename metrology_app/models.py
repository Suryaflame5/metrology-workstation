"""
Pydantic Data Models for Metrology Application and Workstation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ReferenceStandardInput(BaseModel):
    nominal_value: float = Field(default=25.00000, description="Nominal standard length in mm")
    uncertainty: float = Field(default=0.00040, description="Expanded uncertainty of standard in mm")
    distribution: str = Field(default="normal", description="Distribution of standard")
    coverage_factor_k: float = Field(default=2.0, description="Coverage factor k of standard")
    degrees_of_freedom: Optional[float] = Field(default=50.0, description="Degrees of freedom")
    certificate_id: Optional[str] = Field(default="CAL-STD-9921", description="Calibration certificate reference")


class RepeatabilityInput(BaseModel):
    measurements: List[float] = Field(
        default_factory=lambda: [25.0012, 25.0010, 25.0014, 25.0011, 25.0013],
        description="Repeated measurements under repeatability conditions",
    )


class ResolutionInput(BaseModel):
    resolution: float = Field(default=0.001, description="Instrument scale / digital resolution in mm")
    distribution: str = Field(default="rectangular", description="Resolution distribution")


class TemperatureInput(BaseModel):
    delta_temperature_c: float = Field(default=1.0, description="Max temperature difference from 20 deg C")
    expansion_coefficient_ppm_k: float = Field(default=11.5, description="CTE in ppm/K")
    half_width_mm: float = Field(default=0.00030, description="Thermal expansion uncertainty semi-range in mm")
    distribution: str = Field(default="rectangular", description="Temperature effect distribution")


class EnvironmentalConditionsInput(BaseModel):
    ambient_temperature_c: float = Field(default=20.0, description="Ambient temperature in °C")
    temperature_tolerance_c: float = Field(default=1.0, description="Temperature permissible band in ±°C")
    relative_humidity_pct: float = Field(default=45.0, description="Relative humidity in %")
    atmospheric_pressure_hpa: float = Field(default=1013.25, description="Barometric pressure in hPa")


class CalculationCreateRequest(BaseModel):
    instrument_name: str = Field(default="Micrometer")
    instrument_model: str = Field(default="0–25 mm Outside Micrometer")
    procedure_name: str = Field(default="Micrometer Calibration v1")
    procedure_version: str = Field(default="1.0.0")
    unit: str = Field(default="mm")
    nominal_value: float = Field(default=25.00000)
    tolerance_upper: float = Field(default=0.00200)
    tolerance_lower: float = Field(default=-0.00200)
    confidence_level: str = Field(default="95%")
    decision_rule: str = Field(default="ANSI/NCSL Z540.3 Method 6")
    
    reference_standard: ReferenceStandardInput = Field(default_factory=ReferenceStandardInput)
    repeatability: RepeatabilityInput = Field(default_factory=RepeatabilityInput)
    resolution: ResolutionInput = Field(default_factory=ResolutionInput)
    temperature: TemperatureInput = Field(default_factory=TemperatureInput)
    environment: EnvironmentalConditionsInput = Field(default_factory=EnvironmentalConditionsInput)
    
    # Revisions & Classification
    record_class: str = Field(default="CALIBRATION", description="CALIBRATION, VALIDATION, SELF_TEST, IMPORT")
    root_id: Optional[str] = Field(default=None, description="Root calculation ID for revision lineage")
    revision_number: int = Field(default=1, description="Revision index (1, 2, ...)")
    parent_sha256: Optional[str] = Field(default=None, description="Hash of parent revision")
    revision_notes: Optional[str] = Field(default=None, description="Audit rationale for revision")


class UncertaintyBudgetRow(BaseModel):
    label: str
    component_type: str
    distribution: str
    divisor: str
    standard_uncertainty_mm: str
    sensitivity_coefficient: str
    variance_contribution: str
    percentage_contribution: str
    degrees_of_freedom: str
    source_reference: Optional[str] = "Calibration Certificate / Lab Manual"
    component_hash: Optional[str] = None


class UncertaintySummary(BaseModel):
    combined_standard_uncertainty_mm: str
    effective_degrees_of_freedom: str
    coverage_factor_k: str
    expanded_uncertainty_U95_mm: str
    formatted_result: str
    budget_rows: List[UncertaintyBudgetRow]


class DecisionSummary(BaseModel):
    nominal_mm: str
    mean_measured_mm: str
    error_of_indication_mm: str
    tolerance_lower_mm: str
    tolerance_upper_mm: str
    tur: str
    guardband_multiplier_M: str
    guardband_w_mm: str
    acceptance_lower_mm: str
    acceptance_upper_mm: str
    decision_rule: str
    conformity_verdict: str  # "PASS", "GUARD_BAND", "FAIL"
    decision_explanation: str


class CalculationResponse(BaseModel):
    id: str
    root_id: str = Field(default="")
    revision_number: int = Field(default=1)
    parent_sha256: Optional[str] = None
    revision_notes: Optional[str] = None
    record_class: str = Field(default="CALIBRATION")
    created_at: str
    instrument_name: str
    instrument_model: str
    procedure_name: str
    procedure_version: str
    unit: str
    status: str
    conformity_verdict: str
    input_sha256: str
    calculation_sha256: str
    input_data: Dict[str, Any]
    uncertainty_summary: UncertaintySummary
    decision_summary: DecisionSummary


class CalibrationPointInput(BaseModel):
    nominal_value: float
    tolerance: float = 0.00200
    readings: List[float] = Field(default_factory=list)
    reference_uncertainty: float = 0.00040


class MultiPointCalculationCreateRequest(BaseModel):
    instrument_name: str = Field(default="Caliper")
    instrument_model: str = Field(default="0–150 mm Digital Caliper")
    procedure_name: str = Field(default="Caliper Calibration v1")
    procedure_version: str = Field(default="1.0.0")
    unit: str = Field(default="mm")
    decision_rule: str = Field(default="ANSI/NCSL Z540.3 Method 6")
    points: List[CalibrationPointInput] = Field(default_factory=list)
    resolution: float = 0.010
    temperature_half_width: float = 0.00050
    record_class: str = "CALIBRATION"
    technician: str = "Metrology Specialist"


class CalibrationPointResult(BaseModel):
    point_index: int
    nominal_value: float
    mean_measured: float
    error_of_indication: float
    combined_uncertainty_uc: float
    expanded_uncertainty_U95: float
    tur: float
    guardband_w: float
    acceptance_lower: float
    acceptance_upper: float
    verdict: str


class MultiPointCalculationResponse(BaseModel):
    id: str
    created_at: str
    instrument_name: str
    instrument_model: str
    procedure_name: str
    unit: str
    total_points: int
    max_error_of_indication: float
    max_expanded_uncertainty: float
    overall_verdict: str
    point_results: List[CalibrationPointResult]
    input_sha256: str
    calculation_sha256: str


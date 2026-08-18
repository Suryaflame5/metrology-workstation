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


# ==========================================
# V5 WORKSPACE MODELS
# ==========================================

class ProjectCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., description="Project workspace name")
    customer_site: Optional[str] = Field(default="", description="Customer / Laboratory site")
    description: Optional[str] = Field(default="", description="Project scope and description")
    status: str = Field(default="ACTIVE", description="Project status (ACTIVE, COMPLETED, ARCHIVED)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    id: str
    name: str
    customer_site: str
    description: str
    status: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class InstrumentCreateRequest(BaseModel):
    id: Optional[str] = None
    project_id: Optional[str] = None
    manufacturer: str = Field(..., description="Instrument manufacturer")
    model: str = Field(..., description="Model number or designation")
    serial_number: Optional[str] = Field(default="", description="Asset serial number")
    instrument_type: str = Field(default="Micrometer", description="Physical instrument category")
    range_min: float = Field(default=0.0, description="Minimum measuring range")
    range_max: float = Field(default=25.0, description="Maximum measuring range")
    resolution: float = Field(default=0.001, description="Scale or digital resolution")
    accuracy_spec: Optional[str] = Field(default="±0.002 mm", description="Manufacturer accuracy specification")
    calibration_status: str = Field(default="VALID", description="Status (VALID, DUE_SOON, EXPIRED, OUT_OF_SERVICE)")
    calibration_interval_months: int = Field(default=12, description="Calibration cycle in months")
    last_calibration_date: Optional[str] = None
    next_calibration_due: Optional[str] = None
    reference_standard_id: Optional[str] = Field(default="", description="Primary reference standard ID")
    location: Optional[str] = Field(default="Laboratory A", description="Physical location")


class InstrumentResponse(BaseModel):
    id: str
    project_id: Optional[str]
    manufacturer: str
    model: str
    serial_number: str
    instrument_type: str
    range_min: float
    range_max: float
    resolution: float
    accuracy_spec: str
    calibration_status: str
    calibration_interval_months: int
    last_calibration_date: Optional[str]
    next_calibration_due: Optional[str]
    reference_standard_id: str
    location: str
    created_at: str


class MeasurementPlanCreateRequest(BaseModel):
    id: Optional[str] = None
    project_id: Optional[str] = None
    instrument_id: Optional[str] = None
    plan_name: str = Field(..., description="Measurement plan designation")
    measurand: str = Field(default="Length", description="Physical quantity being measured")
    nominal_value: float = Field(default=25.0, description="Target calibration point")
    tolerance_lower: float = Field(default=-0.002, description="Lower specification limit")
    tolerance_upper: float = Field(default=0.002, description="Upper specification limit")
    required_repetitions: int = Field(default=5, description="Required repeated observations")
    procedure_name: Optional[str] = Field(default="CAL-MIC-001", description="Standard procedure reference")
    decision_rule: str = Field(default="ANSI/NCSL Z540.3 Method 6", description="Conformity decision rule")
    environmental_limits: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"temp_c": 20.0, "temp_tolerance_c": 1.0})


class MeasurementPlanResponse(BaseModel):
    id: str
    project_id: Optional[str]
    instrument_id: Optional[str]
    plan_name: str
    measurand: str
    nominal_value: float
    tolerance_lower: float
    tolerance_upper: float
    required_repetitions: int
    procedure_name: str
    decision_rule: str
    environmental_limits: Dict[str, Any]
    created_at: str


class MeasurementAcquisitionRequest(BaseModel):
    id: Optional[str] = None
    plan_id: Optional[str] = None
    instrument_id: Optional[str] = None
    project_id: Optional[str] = None
    acquisition_mode: str = Field(default="MANUAL", description="Mode (MANUAL or IMPORT)")
    raw_values: List[float] = Field(..., description="Array of repeated measurement observations")
    operator: Optional[str] = Field(default="Lab Technician", description="Operator name")
    environmental_readings: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"temp_c": 20.0, "humidity_pct": 45.0})


class MeasurementAcquisitionResponse(BaseModel):
    id: str
    plan_id: Optional[str]
    instrument_id: Optional[str]
    project_id: Optional[str]
    acquisition_mode: str
    raw_values: List[float]
    mean_value: float
    sample_std_dev: float
    repeatability_uncertainty: float
    outliers: List[float]
    operator: str
    environmental_readings: Dict[str, Any]
    acquired_at: str


class UncertaintyComponentInput(BaseModel):
    name: str = Field(..., description="Component identifier / source of uncertainty")
    distribution: str = Field(default="rectangular", description="Distribution (normal, rectangular, triangular, u_shaped)")
    semi_range: float = Field(..., description="Semi-range a or expanded uncertainty U")
    coverage_factor_k: float = Field(default=2.0, description="Coverage factor if normal distribution")
    sensitivity_coefficient: float = Field(default=1.0, description="Partial derivative c_i")
    degrees_of_freedom: float = Field(default=50.0, description="Degrees of freedom (infinity or finite)")


class UncertaintyWorkbenchRequest(BaseModel):
    components: List[UncertaintyComponentInput] = Field(..., description="Uncertainty budget components")
    confidence_level: str = Field(default="95%", description="Target confidence interval")


class UncertaintyWorkbenchResponse(BaseModel):
    combined_uncertainty_uc: float
    effective_degrees_of_freedom: float
    coverage_factor_k: float
    expanded_uncertainty_U95: float
    budget_breakdown: List[Dict[str, Any]]


class ConformityWorkbenchRequest(BaseModel):
    nominal_value: float = Field(default=25.0)
    measured_value: float = Field(default=25.0012)
    tolerance_lower: float = Field(default=-0.002)
    tolerance_upper: float = Field(default=0.002)
    expanded_uncertainty_U95: float = Field(default=0.00078)
    decision_rule: str = Field(default="ANSI/NCSL Z540.3 Method 6")


class ConformityWorkbenchResponse(BaseModel):
    error_of_indication: float
    tur: float
    guardband_multiplier: float
    guardband_width_w: float
    acceptance_lower: float
    acceptance_upper: float
    consumer_risk_pfa_pct: float
    conformance_verdict: str
    derivation_statement: str



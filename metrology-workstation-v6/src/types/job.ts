export type JobStatus =
  | 'NEW'
  | 'IMPORTING'
  | 'ANALYZING'
  | 'REVIEW_REQUIRED'
  | 'READY_FOR_APPROVAL'
  | 'APPROVED'
  | 'RELEASED'
  | 'ARCHIVED';

export interface JobException {
  type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  message: string;
}

export interface UncertaintyComponentRow {
  name: string;
  distribution: string;
  standard_uncertainty: number;
  sensitivity_coefficient: number;
  variance_percent: number;
  dof: number;
}

export interface UncertaintyBudget {
  combined_uncertainty_uc?: number;
  expanded_uncertainty_U95?: number;
  coverage_factor_k?: number;
  effective_dof?: number;
  budget_breakdown?: UncertaintyComponentRow[];
}

export interface ConformityAssessment {
  nominal_value?: number;
  mean_measured?: number;
  error_of_indication?: number;
  tolerance_upper?: number;
  tolerance_lower?: number;
  tur?: number;
  guardband_multiplier?: number;
  guardband_w?: number;
  acceptance_lower?: number;
  acceptance_upper?: number;
  consumer_risk_pfa_pct?: number;
  conformance_verdict?: 'PASS' | 'GUARD_BAND' | 'FAIL' | 'INCONCLUSIVE';
  diagnostic_explanation?: string;
}

export interface JobStatistics {
  count?: number;
  mean?: number;
  median?: number;
  sample_std_dev?: number;
  repeatability_uncertainty?: number;
  min?: number;
  max?: number;
  range?: number;
  drift_rate?: number;
  outliers?: number[];
}

export interface JobEnvironment {
  ambient_temperature_c?: number;
  relative_humidity_pct?: number;
  atmospheric_pressure_hpa?: number;
}

export interface DigitalSignature {
  signer_name?: string;
  signer_role?: string;
  meaning?: string;
  timestamp?: string;
  signature_hash?: string;
  cfr_part11_compliant?: boolean;
}

export interface MeasurementJob {
  id: string;
  job_number: string;
  title: string;
  customer_name: string;
  instrument_id: string;
  instrument_name: string;
  instrument_model: string;
  instrument_serial: string;
  procedure_template_id: string;
  procedure_name: string;
  reference_standard_id: string;
  reference_standard_name: string;
  reference_due_date?: string;
  reference_uncertainty?: number;
  status: JobStatus;
  unit: string;
  nominal_value: number;
  tolerance_upper: number;
  tolerance_lower: number;
  environment: JobEnvironment;
  raw_measurements: number[];
  mapped_columns?: Record<string, any>;
  statistics?: JobStatistics;
  uncertainty_budget?: UncertaintyBudget;
  conformity?: ConformityAssessment;
  exceptions?: JobException[];
  calculation_id?: string;
  certificate_id?: string;
  operator: string;
  reviewer?: string;
  reviewed_at?: string;
  digital_signature?: DigitalSignature;
  evidence_package_path?: string;
  parent_job_id?: string;
  revision_number: number;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface ReferenceStandard {
  id: string;
  name: string;
  model: string;
  serial_number: string;
  category: string;
  nominal_value: number;
  expanded_uncertainty: number;
  coverage_factor_k: number;
  unit: string;
  calibration_date: string;
  calibration_due_date: string;
  certificate_id: string;
  accredited_lab: string;
  status: 'VALID' | 'DUE_SOON' | 'EXPIRED';
  days_until_due?: number;
  expiration_status?: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | 'UNKNOWN';
}

export interface ColumnMappingInfo {
  role: string;
  confidence: number;
  suggested_label: string;
}

export interface ImportPreviewResponse {
  status: 'success' | 'error';
  message?: string;
  sample_rows: Record<string, any>[];
  total_rows: number;
  headers: string[];
  mapping: Record<string, ColumnMappingInfo>;
  confidence_pct: number;
  extracted_summary?: {
    sample_size: number;
    nominal_value: number;
    environment: JobEnvironment;
    readings_preview: number[];
    raw_measurements?: number[];
  };
}

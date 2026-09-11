export type WorkspaceId =
  | 'overview'
  | 'projects'
  | 'jobs'
  | 'assets'
  | 'instrument'
  | 'procedure'
  | 'active-runs'
  | 'job-workflow'
  | 'batch-processing'
  | 'exception-center'
  | 'measurements'
  | 'uncertainty'
  | 'conformity'
  | 'reports'
  | 'certificates'
  | 'evidence'
  | 'audit'
  | 'review-cockpit'
  | 'users-roles'
  | 'settings'
  | 'customers'
  | 'hardware'
  | 'validation'
  | 'calculation'
  | 'calculation-chain'
  | 'model'
  | 'monte-carlo'
  | 'guardband'
  | 'tur'
  | 'calibration-history'
  | 'comparison'
  | 'documents'
  | 'about';

export type MeasurementStatus = 'VALID' | 'OUT_TOL' | 'IN_TOL' | 'REJECT' | 'PENDING';

export interface MeasurementRecord {
  id: string;
  reference: number; // in Volts (e.g. 10.0000)
  measured: number; // in Volts (e.g. 10.0021 or 10.0142)
  unit: string;
  timestamp: string;
  status: MeasurementStatus;
  isLocked: boolean;
  operator: string;
  instrumentId: string;
  envTemp: number; // in °C
  humidity: number; // in % RH
  notes?: string;
}

export type DistributionType = 'Normal' | 'Rectangular' | 'U-Shape' | 'Triangular' | 'Student-t';

export interface UncertaintySource {
  id: string;
  name: string;
  symbol: string;
  estimate: number;
  estimateStr?: string;
  unit: string;
  distribution: DistributionType;
  stdUncertainty: number; // u_i
  degreesOfFreedom: number | 'inf'; // v_i
  sensitivityCoeff: number; // c_i = df/dx_i
  contribution: number; // u_i(y) = |c_i| * u_i
  type: 'A' | 'B';
  variancePercent?: number;
}

export type DecisionRuleType =
  | 'Guardband Method 6 (ISO 14253-1)'
  | 'ILAC-G8:09 (Binary Simple Acceptance)'
  | 'ILAC-G8:09 (Guardbanded w=U)'
  | 'ANSI/NCSL Z540.3 Method 5 (TUR >= 4:1)'
  | '17025 Shared Risk (2% PFA)';

export interface ConformityConfig {
  nominal: number;
  specTolerance: number; // ± tolerance in Volts (e.g. 0.0100)
  ltl: number; // nominal - tolerance (9.9900)
  utl: number; // nominal + tolerance (10.0100)
  decisionRule: DecisionRuleType;
  guardbandMultiplier: number; // e.g. 1.0 for Method 6
  guardbandWidth: number; // w = multiplier * U
  lal: number; // ltl + w (9.9925)
  ual: number; // utl - w (10.0075)
  decision: 'CONFORMING' | 'NON-CONFORMING' | 'INDETERMINATE';
  measuredValue: number;
  expandedUncertainty: number;
  kFactor: number;
  confidenceLevel: number; // 95%
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}

export interface MonteCarloConfig {
  iterations: number;
  seed: string;
  adaptive: boolean;
  tolerance: number;
  isSimulating: boolean;
  results?: {
    mean: number;
    median: number;
    stdDev: number;
    ci95Low: number;
    ci95High: number;
    histogram: { bin: string; count: number; freq: number; heightPercent: number }[];
    gumComparison: {
      parameter: string;
      gumValue: string;
      mcmValue: string;
    }[];
    validationPassed: boolean;
    dLow: number;
    tVal: number;
  };
}

export interface ProvenanceNode {
  id: string;
  nodeType: 'raw' | 'validated' | 'uncertainty' | 'conformity' | 'report';
  title: string;
  version: string;
  timestamp: string;
  isLocked: boolean;
  checksum: string;
  metrics: { label: string; value: string; isAlert?: boolean }[];
  description?: string;
  dependencies: string[]; // IDs of preceding nodes
}

export interface LineageEvent {
  id: string;
  timestamp: string;
  actor: string;
  message: string;
  type: 'system' | 'engine' | 'operator';
}

export interface AuditRecord {
  id: string;
  timestamp: string;
  user: string;
  role: string;
  event: string;
  objectId: string;
  previousState: string;
  newState: string;
  reason: string;
  checksum: string;
  verificationState: 'VERIFIED' | 'FLAGGED';
}

export interface InstrumentInfo {
  id: string;
  name: string;
  model: string;
  manufacturer: string;
  serialNumber: string;
  calDate: string;
  dueDate: string;
  accuracy: string;
  resolution: string;
  terminals: string;
  filter: string;
  connectionStatus: 'ONLINE' | 'STANDBY' | 'CAL_DUE';
  certificateNumber: string;
  location: string;
}

export interface CalibrationHistoryCycle {
  cycle: string; // CY-18, CY-19, etc.
  year: number;
  biasPpm: number;
  biasUncertaintyPpm: number;
  expandedUncertaintyPpm: number;
}

export interface StabilityTestPoint {
  pointName: string;
  nominal: string;
  baselineVal: number;
  prevVal: number;
  currentVal: number;
  deltaPrev: number;
  deltaBaseline: number;
  status: 'STABLE' | 'DRIFT_WARNING';
}

export interface ReportConfig {
  reportId: string;
  title: string;
  clientName: string;
  clientContact: string;
  clientAddress: string;
  labName: string;
  labAddress: string;
  date: string;
  status: 'DRAFT' | 'GENERATED' | 'REVIEW' | 'APPROVED' | 'LOCKED';
  sections: {
    clientDetails: boolean;
    instrumentDetails: boolean;
    environmentalConditions: boolean;
    procedure: boolean;
    nominalValue: boolean;
    measuredValue: boolean;
    error: boolean;
    toleranceLimits: boolean;
    uncertaintyBudget: boolean;
    conformityDecision: boolean;
    signatures: boolean;
  };
  calibratedBy: string;
  approvedBy: string;
  signDate?: string;
}

export interface AssetItem {
  id: string;
  asset_tag: string;
  serial_number: string;
  manufacturer: string;
  model: string;
  instrument_type: string;
  range_min?: number;
  range_max?: number;
  resolution?: number;
  accuracy_spec?: string;
  location?: string;
  owner_customer_name?: string;
  status: 'IN_SERVICE' | 'OUT_FOR_CALIBRATION' | 'OVERDUE' | 'QUARANTINED' | 'RETIRED';
  calibration_interval_days: number;
  last_calibration_date?: string;
  next_calibration_due?: string;
  days_until_due?: number;
  calibration_health?: 'COMPLIANT' | 'EXPIRING_SOON' | 'OVERDUE' | 'NOT_SCHEDULED';
  barcode_data?: string;
  metadata?: Record<string, any>;
}

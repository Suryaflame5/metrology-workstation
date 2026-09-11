/**
 * Backend API Client for Metrology Workstation (FastAPI & 50-Digit Metrology Core)
 */

const API_BASE = '/api';

export interface BackendStats {
  total_calibrations: number;
  passed_count: number;
  failed_count: number;
  guard_band_count: number;
  needs_review_count: number;
  validation_runs_count: number;
}

export interface BackendAuditVerification {
  is_valid: boolean;
  total_events: number;
  verified_at: string;
  chain_status: string;
}

export interface BackendSelftestResult {
  overall_status: string;
  results: Array<{
    name: string;
    status: string;
    details: string;
  }>;
}

export interface CalculationReplayStage {
  step_number: number;
  title: string;
  standard_clause: string;
  formula: string;
  inputs: Record<string, any>;
  result_label: string;
  result_value: string;
  status: string;
}

export interface CalculationReplayResponse {
  calculation_id: string;
  reproduced_all_stages: boolean;
  total_stages: number;
  stages: CalculationReplayStage[];
}

export interface ProcessCapabilityResponse {
  instrument_name: string;
  sample_size: number;
  mean_error: number;
  std_deviation: number;
  specification_limits: {
    upper: number;
    lower: number;
  };
  process_capability: {
    cp: number;
    cpk: number;
    cpu: number;
    cpl: number;
  };
  process_performance: {
    pp: number;
    ppk: number;
    ppu: number;
    ppl: number;
  };
  capability_status: string;
  interpretation: string;
  timestamp: string;
}

export interface AdaptiveIntervalResponse {
  instrument_id: string;
  instrument_model: string;
  recommended_interval_months: number;
  current_interval_months: number;
  risk_level: string;
  rationale: string;
  drift_rate_ppm_year?: number;
  confidence?: string;
}

export interface Part11SignaturePayload {
  calculation_id: string;
  calculation_sha256: string;
  username: string;
  password: string;
  reason: string;
}

export const MetrologyAPI = {
  // Stats & Dashboard
  async getStats(): Promise<BackendStats | null> {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async getV6DashboardOverview(): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/v6/dashboard/overview`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Instruments
  async getInstruments(): Promise<any[] | null> {
    try {
      const res = await fetch(`${API_BASE}/instruments`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async getInstrumentProfile(instrumentId: string): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/v6/instruments/profile/${instrumentId}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Calculations & Lineage
  async getCalculations(recordClass = 'CALIBRATION'): Promise<any[] | null> {
    try {
      const res = await fetch(`${API_BASE}/calculations?record_class=${recordClass}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async getCalculation(id: string): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/calculations/${id}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async replayCalculation(id: string): Promise<CalculationReplayResponse | null> {
    try {
      const res = await fetch(`${API_BASE}/calculations/${id}/replay`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async tamperTest(id: string): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/calculations/${id}/tamper-test`, {
        method: 'POST',
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async saveCalculation(data: any): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/calculations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Measurements
  async getMeasurements(): Promise<any[] | null> {
    try {
      const res = await fetch(`${API_BASE}/measurements`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Uncertainty Workbench (Exact 50-digit GUM kernel)
  async evaluateUncertainty(components: any[], confidenceLevel = 0.9545) {
    try {
      const res = await fetch(`${API_BASE}/workbench/uncertainty`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ components, confidence_level: confidenceLevel }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Conformity Workbench (ANSI Z540.3 Method 6 root guardband)
  async evaluateConformity(params: {
    measured_mean: number;
    nominal: number;
    tolerance_lower: number;
    tolerance_upper: number;
    expanded_uncertainty: number;
    decision_rule?: string;
  }) {
    try {
      const res = await fetch(`${API_BASE}/workbench/conformity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Reports & PDF Certificates
  getCertificatePdfUrl(calculationId: string): string {
    return `${API_BASE}/reports/pdf/${calculationId}`;
  },

  getCertificateHtmlUrl(calculationId: string): string {
    return `${API_BASE}/reports/html/${calculationId}`;
  },

  getEvidenceZipUrl(calculationId: string): string {
    return `${API_BASE}/calculations/${calculationId}/export/zip`;
  },

  // Digital Signatures (FDA 21 CFR Part 11)
  async executePart11Signature(payload: Part11SignaturePayload): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/enterprise/compliance/sign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Signature rejected');
      }
      return await res.json();
    } catch (e: any) {
      throw e;
    }
  },

  // Instrument Connectivity & SCPI
  async executeScpi(resourceString: string, command: string): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/enterprise/industrial/scpi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resource_string: resourceString, command }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async getTelemetrySample(nominal = 25.0, elapsedSec = 0.0): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/enterprise/industrial/telemetry/sample?nominal=${nominal}&elapsed_sec=${elapsedSec}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async importExcelBatch(records: any[]): Promise<any | null> {
    try {
      const res = await fetch(`${API_BASE}/v6/import/excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ records }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Measurement Templates & Sandbox
  async getSandboxScenarios(): Promise<any[] | null> {
    try {
      const res = await fetch(`${API_BASE}/sandbox/scenarios`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Adaptive Calibration Interval
  async getAdaptiveInterval(instrumentId: string): Promise<AdaptiveIntervalResponse | null> {
    try {
      const res = await fetch(`${API_BASE}/intelligence/adaptive-interval/${instrumentId}`, {
        method: 'POST',
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // SPC Process & Measurement Capability
  async getProcessCapability(instrumentName: string): Promise<ProcessCapabilityResponse | null> {
    try {
      const res = await fetch(`${API_BASE}/v6/analytics/capability/${encodeURIComponent(instrumentName)}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Audit Ledger
  async getAuditEvents(limit = 100): Promise<any[] | null> {
    try {
      const res = await fetch(`${API_BASE}/audit?limit=${limit}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async verifyAuditChain(): Promise<BackendAuditVerification | null> {
    try {
      const res = await fetch(`${API_BASE}/audit/verify`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // Self-Test
  async runSelftest(): Promise<BackendSelftestResult | null> {
    try {
      const res = await fetch(`${API_BASE}/selftest`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // License & Entitlements
  async getLicenseInfo() {
    try {
      const res = await fetch(`${API_BASE}/license`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async activateTrial() {
    try {
      const res = await fetch(`${API_BASE}/license/trial`, { method: 'POST' });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // NIST Benchmarks
  async getNistBenchmarks() {
    try {
      const res = await fetch(`${API_BASE}/enterprise/benchmarks/nist`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  // ============================================================================
  // PRODUCTION V1: INDUSTRIAL QUALITY OPERATIONS & LOSS RECOVERY CLIENT
  // ============================================================================

  async getFactoryOverview() {
    try {
      const res = await fetch(`${API_BASE}/v1/factory/overview`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async getFactoryParts() {
    try {
      const res = await fetch(`${API_BASE}/v1/factory/parts`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getFactoryMachines() {
    try {
      const res = await fetch(`${API_BASE}/v1/factory/machines`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getFactoryInspections(status?: string) {
    try {
      const url = status ? `${API_BASE}/v1/factory/inspections?status=${status}` : `${API_BASE}/v1/factory/inspections`;
      const res = await fetch(url);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getFactoryLosses() {
    try {
      const res = await fetch(`${API_BASE}/v1/factory/losses`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getFactoryInvestigations() {
    try {
      const res = await fetch(`${API_BASE}/v1/factory/investigations`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async triggerInvestigationFromJob(jobId: string, leadEngineer: string = 'Lead Quality Engineer') {
    const res = await fetch(`${API_BASE}/v1/factory/investigations/trigger-from-job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, lead_engineer: leadEngineer }),
    });
    if (!res.ok) throw new Error('Failed to trigger investigation');
    return await res.json();
  },

  async compareRecovery(baselineJobId: string, verificationJobId: string, actionId?: string, lossEventId?: string) {
    const res = await fetch(`${API_BASE}/v1/factory/recovery/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseline_job_id: baselineJobId,
        verification_job_id: verificationJobId,
        action_id: actionId,
        loss_event_id: lossEventId,
      }),
    });
    if (!res.ok) throw new Error('Failed to compare recovery ROI');
    return await res.json();
  },

  async seedDemoFactory() {
    const res = await fetch(`${API_BASE}/v1/factory/demo/seed`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to seed demo factory operations');
    return await res.json();
  },

  async getCostConfig() {
    try {
      const res = await fetch(`${API_BASE}/v1/factory/cost-config`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async saveCostConfig(config: any) {
    const res = await fetch(`${API_BASE}/v1/factory/cost-config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error('Failed to update cost configuration');
    return await res.json();
  },
};

export const api = MetrologyAPI;



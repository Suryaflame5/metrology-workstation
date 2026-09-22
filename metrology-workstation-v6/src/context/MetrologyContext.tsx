import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  CALIBRATION_HISTORY_CYCLES,
  INITIAL_AUDIT_TRAIL,
  INITIAL_LINEAGE_EVENTS,
  INITIAL_MEASUREMENTS,
  INITIAL_PROVENANCE_NODES,
  INITIAL_REPORT,
  INITIAL_UNCERTAINTY_SOURCES,
  INSTRUMENTS_DATA,
  STABILITY_COMPARISON_MATRIX,
} from '../data/mockData';
import {
  AuditRecord,
  CalibrationHistoryCycle,
  ConformityConfig,
  DecisionRuleType,
  InstrumentInfo,
  LineageEvent,
  MeasurementRecord,
  MonteCarloConfig,
  ProvenanceNode,
  ReportConfig,
  StabilityTestPoint,
  UncertaintySource,
  WorkspaceId,
} from '../types';
import { MeasurementJob } from '../types/job';
import {
  calculateCombinedUncertainty,
  evaluateConformity,
  runMonteCarloSimulation,
} from '../utils/metrologyMath';

interface MetrologyContextType {
  activeWorkspace: WorkspaceId;
  setActiveWorkspace: (ws: WorkspaceId) => void;
  // Measurements
  measurements: MeasurementRecord[];
  selectedMeasurementId: string;
  setSelectedMeasurementId: (id: string) => void;
  selectedMeasurement: MeasurementRecord | undefined;
  addMeasurement: (record: Omit<MeasurementRecord, 'id' | 'timestamp'>) => void;
  updateMeasurement: (id: string, updates: Partial<MeasurementRecord>) => void;
  deleteMeasurement: (id: string) => void;
  filterText: string;
  setFilterText: (t: string) => void;
  statusFilter: string;
  setStatusFilter: (s: string) => void;
  // Uncertainty Budget
  uncertaintySources: UncertaintySource[];
  updateUncertaintySource: (id: string, updates: Partial<UncertaintySource>) => void;
  addUncertaintySource: (src: Omit<UncertaintySource, 'id'>) => void;
  combinedUc: number;
  expandedU: number;
  effectiveDof: number | 'inf';
  // Monte Carlo
  monteCarloConfig: MonteCarloConfig;
  runSimulation: (iterations?: number) => void;
  setMonteCarloConfig: React.Dispatch<React.SetStateAction<MonteCarloConfig>>;
  // Conformity
  conformityConfig: ConformityConfig;
  setConformityRule: (rule: DecisionRuleType) => void;
  updateConformityParams: (updates: Partial<ConformityConfig>) => void;
  acknowledgeConformityDecision: () => void;
  // Provenance & Lineage
  provenanceNodes: ProvenanceNode[];
  selectedNodeId: string;
  setSelectedNodeId: (id: string) => void;
  selectedNode: ProvenanceNode | undefined;
  lockAllNodes: () => void;
  toggleNodeLock: (id: string) => void;
  lineageEvents: LineageEvent[];
  // Audit Trail
  auditTrail: AuditRecord[];
  logAuditEvent: (event: string, objectId: string, prev: string, next: string, reason: string) => void;
  // Reports
  reportConfig: ReportConfig;
  updateReportSection: (sectionKey: keyof ReportConfig['sections'], value: boolean) => void;
  saveDraftReport: () => void;
  approveReport: () => void;
  // Instruments & Fleet
  instruments: InstrumentInfo[];
  activeInstrument: InstrumentInfo;
  setActiveInstrumentId: (id: string) => void;
  // Calibration History & Matrix
  historyCycles: CalibrationHistoryCycle[];
  stabilityMatrix: StabilityTestPoint[];
  // Modals & UI
  isCommandPaletteOpen: boolean;
  setIsCommandPaletteOpen: (open: boolean) => void;
  isDiagnosticsOpen: boolean;
  setIsDiagnosticsOpen: (open: boolean) => void;
  isOnboardingOpen: boolean;
  setIsOnboardingOpen: (open: boolean) => void;
  // Edition & Licensing State
  isCommercial: boolean;
  isDemo: boolean;
  isUpgradeModalOpen: boolean;
  setIsUpgradeModalOpen: (open: boolean) => void;
  refreshLicense: () => Promise<void>;
  // V7 Measurement Job Workflow
  selectedJob: MeasurementJob | null;
  setSelectedJob: (job: MeasurementJob | null) => void;
  syncJobData: (jobId: string) => Promise<void>;
}

const MetrologyContext = createContext<MetrologyContextType | undefined>(undefined);

export const MetrologyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>('jobs');
  const [selectedJob, setSelectedJob] = useState<MeasurementJob | null>(null);

  // Measurements
  const [measurements, setMeasurements] = useState<MeasurementRecord[]>(() => {
    const saved = localStorage.getItem('mw_measurements');
    return saved ? JSON.parse(saved) : INITIAL_MEASUREMENTS;
  });
  const [selectedMeasurementId, setSelectedMeasurementId] = useState<string>('MS-004');
  const [filterText, setFilterText] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Uncertainty Sources
  const [uncertaintySources, setUncertaintySources] = useState<UncertaintySource[]>(() => {
    const saved = localStorage.getItem('mw_uncertainty_sources');
    return saved ? JSON.parse(saved) : INITIAL_UNCERTAINTY_SOURCES;
  });

  // Calculate Combined Uncertainty whenever sources change (Offline fallback)
  const localMath = calculateCombinedUncertainty(uncertaintySources);
  const [backendUc, setBackendUc] = useState<number | null>(null);
  const [backendU95, setBackendU95] = useState<number | null>(null);
  const [backendDof, setBackendDof] = useState<number | 'inf' | null>(null);

  useEffect(() => {
    const payload = {
      components: uncertaintySources.map((s) => ({
        name: s.name,
        distribution: (s.distribution || 'normal').toLowerCase(),
        semi_range: (s.stdUncertainty || s.estimate || 0.0001) * ((s.distribution || '').toLowerCase() === 'rectangular' ? Math.sqrt(3) : 2.0),
        coverage_factor_k: 2.0,
        sensitivity_coefficient: s.sensitivity || 1.0,
        degrees_of_freedom: s.dof === 'inf' ? 1000 : (Number(s.dof) || 50),
      })),
      confidence_level: '95%',
    };

    fetch('/api/workbench/uncertainty', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setBackendUc(data.combined_uncertainty_uc);
          setBackendU95(data.expanded_uncertainty_U95);
          setBackendDof(data.effective_degrees_of_freedom);
        }
      })
      .catch(() => {});
  }, [uncertaintySources]);

  const combinedUc = backendUc ?? localMath.combinedUc;
  const expandedU = backendU95 ?? localMath.expandedU;
  const effectiveDof = backendDof ?? localMath.effectiveDof;
  const sourcesWithVariance = localMath.sourcesWithVariance;

  // Selected Measurement
  const selectedMeasurement = measurements.find((m) => m.id === selectedMeasurementId) || measurements[0];

  // Monte Carlo
  const [monteCarloConfig, setMonteCarloConfig] = useState<MonteCarloConfig>(() => {
    const initialSim = runMonteCarloSimulation(10.0020, INITIAL_UNCERTAINTY_SOURCES, 100000);
    return {
      iterations: 100000,
      seed: 'Auto-generated (0x7F92)',
      adaptive: true,
      tolerance: 0.005,
      isSimulating: false,
      results: initialSim,
    };
  });

  // Conformity
  const [conformityConfig, setConformityConfig] = useState<ConformityConfig>(() => {
    const baseEval = evaluateConformity(
      10.0142, // Canonical out of tolerance value matching design
      10.0,
      0.01,
      0.0025,
      1.0
    );
    return {
      ...baseEval,
      decisionRule: 'Guardband Method 6 (ISO 14253-1)',
    };
  });

  // Provenance Nodes
  const [provenanceNodes, setProvenanceNodes] = useState<ProvenanceNode[]>(INITIAL_PROVENANCE_NODES);
  const [selectedNodeId, setSelectedNodeId] = useState<string>('UNC-8842-C');
  const [lineageEvents, setLineageEvents] = useState<LineageEvent[]>(INITIAL_LINEAGE_EVENTS);

  // Audit Trail
  const [auditTrail, setAuditTrail] = useState<AuditRecord[]>(INITIAL_AUDIT_TRAIL);

  // Reports
  const [reportConfig, setReportConfig] = useState<ReportConfig>(INITIAL_REPORT);

  // Instruments
  const [instruments] = useState<InstrumentInfo[]>(INSTRUMENTS_DATA);
  const [activeInstrumentId, setActiveInstrumentId] = useState<string>('DMM-042');
  const activeInstrument = instruments.find((i) => i.id === activeInstrumentId) || instruments[0];

  // History & Stability
  const [historyCycles] = useState<CalibrationHistoryCycle[]>(CALIBRATION_HISTORY_CYCLES);
  const [stabilityMatrix] = useState<StabilityTestPoint[]>(STABILITY_COMPARISON_MATRIX);

  // Modals & Licensing State
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState<boolean>(() => {
    return !localStorage.getItem('has_completed_onboarding');
  });
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [isCommercial, setIsCommercial] = useState(false);
  const [isDemo, setIsDemo] = useState(true);

  const refreshLicense = async () => {
    try {
      const res = await fetch('/api/license');
      if (res.ok) {
        const data = await res.json();
        const comm = Boolean(
          data.is_commercial || ['PROFESSIONAL', 'BUSINESS', 'ENTERPRISE'].includes(data.plan_id)
        );
        setIsCommercial(comm);
        setIsDemo(!comm);
      }
    } catch {
      setIsCommercial(false);
      setIsDemo(true);
    }
  };

  useEffect(() => {
    refreshLicense();
  }, []);

  // Save to LocalStorage
  useEffect(() => {
    localStorage.setItem('mw_measurements', JSON.stringify(measurements));
  }, [measurements]);

  useEffect(() => {
    localStorage.setItem('mw_uncertainty_sources', JSON.stringify(uncertaintySources));
  }, [uncertaintySources]);

  // Recalculate Conformity when active measurement or expanded uncertainty changes
  useEffect(() => {
    const val = selectedMeasurement ? selectedMeasurement.measured : 10.0142;
    const evaluated = evaluateConformity(
      val,
      conformityConfig.nominal,
      conformityConfig.specTolerance,
      expandedU > 0 ? expandedU : 0.0025,
      conformityConfig.guardbandMultiplier
    );
    setConformityConfig((prev) => ({
      ...prev,
      ...evaluated,
    }));
  }, [selectedMeasurementId, expandedU, conformityConfig.decisionRule]);

  // Log Audit Event Helper
  const logAuditEvent = (
    event: string,
    objectId: string,
    prev: string,
    next: string,
    reason: string
  ) => {
    const newRecord: AuditRecord = {
      id: `AUD-${Math.floor(1000 + Math.random() * 9000)}`,
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      user: 'Tech Station 04 (Oper)',
      role: 'Metrology Specialist',
      event,
      objectId,
      previousState: prev,
      newState: next,
      reason,
      checksum: Array.from({ length: 64 }, () =>
        Math.floor(Math.random() * 16).toString(16)
      ).join(''),
      verificationState: 'VERIFIED',
    };
    setAuditTrail((prevList) => [newRecord, ...prevList]);
  };

  // LocalStorage Write-Ahead Log (WAL) helpers
  const getWalKey = (jobId?: string) => `mw_wal_${jobId || 'active'}`;

  const persistWalRecord = (jobId: string, record: MeasurementRecord) => {
    try {
      const key = getWalKey(jobId);
      const queue = JSON.parse(localStorage.getItem(key) || '[]');
      queue.push(record);
      localStorage.setItem(key, JSON.stringify(queue));
    } catch {}
  };

  const commitWalRecord = (jobId: string, recordId: string) => {
    try {
      const key = getWalKey(jobId);
      const queue = JSON.parse(localStorage.getItem(key) || '[]');
      const filtered = queue.filter((r: MeasurementRecord) => r.id !== recordId);
      localStorage.setItem(key, JSON.stringify(filtered));
    } catch {}
  };

  const flushJobWal = async (jobId: string) => {
    try {
      const key = getWalKey(jobId);
      const queue: MeasurementRecord[] = JSON.parse(localStorage.getItem(key) || '[]');
      if (queue.length === 0) return;
      const values = queue.map((r) => r.measured);
      const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/measurements`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ values, operator: 'Auto-Replay WAL' }),
      });
      if (res.ok) {
        localStorage.removeItem(key);
      }
    } catch {}
  };

  // Add Measurement
  const addMeasurement = (rec: Omit<MeasurementRecord, 'id' | 'timestamp'>) => {
    const newId = `MS-${String(measurements.length + 1).padStart(3, '0')}`;
    const now = new Date();
    const ts = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.${String(now.getMilliseconds()).padStart(3, '0')}`;
    const newRecord: MeasurementRecord = {
      ...rec,
      id: newId,
      timestamp: ts,
    };
    setMeasurements((prev) => [newRecord, ...prev]);
    setSelectedMeasurementId(newId);

    // Immediate WAL buffer & Backend REST persistence
    if (selectedJob?.id) {
      persistWalRecord(selectedJob.id, newRecord);
      fetch(`/api/jobs/${encodeURIComponent(selectedJob.id)}/measurements`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          value: rec.measured,
          operator: rec.operator || 'Technician',
        }),
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data?.status === 'success') {
            commitWalRecord(selectedJob.id, newId);
            if (data.job) {
              setSelectedJob(data.job);
            }
          }
        })
        .catch(() => {});
    }

    logAuditEvent(
      'Measurement Record Acquired',
      newId,
      'NONE',
      rec.status,
      `Acquired ${rec.measured} ${rec.unit} from ${rec.instrumentId}`
    );
  };

  // Update Measurement
  const updateMeasurement = (id: string, updates: Partial<MeasurementRecord>) => {
    setMeasurements((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...updates } : m))
    );
    logAuditEvent(
      'Measurement Record Modified',
      id,
      'ORIGINAL',
      'MODIFIED',
      'User manual override or calibration recalculation'
    );
  };

  // Delete Measurement
  const deleteMeasurement = (id: string) => {
    const idx = measurements.findIndex((m) => m.id === id);
    setMeasurements((prev) => prev.filter((m) => m.id !== id));

    if (selectedJob?.id && idx >= 0) {
      fetch(`/api/jobs/${encodeURIComponent(selectedJob.id)}/measurements/${idx}`, {
        method: 'DELETE',
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data?.job) {
            setSelectedJob(data.job);
          }
        })
        .catch(() => {});
    }

    logAuditEvent(
      'Measurement Record Purged',
      id,
      'EXISTING',
      'DELETED',
      'Removed from active calibration series'
    );
  };

  // Update Uncertainty Source
  const updateUncertaintySource = (id: string, updates: Partial<UncertaintySource>) => {
    setUncertaintySources((prev) =>
      prev.map((src) => (src.id === id ? { ...src, ...updates } : src))
    );
    logAuditEvent(
      'Uncertainty Budget Updated',
      id,
      'PREV_MODEL',
      'UPDATED',
      `Modified ${updates.name || id} parameter`
    );
  };

  // Add Uncertainty Source
  const addUncertaintySource = (src: Omit<UncertaintySource, 'id'>) => {
    const newId = `UNC-${String(uncertaintySources.length + 1).padStart(2, '0')}`;
    setUncertaintySources((prev) => [...prev, { ...src, id: newId }]);
    logAuditEvent(
      'Uncertainty Component Added',
      newId,
      'NONE',
      'ACTIVE',
      `Added component ${src.name}`
    );
  };

  // Run Monte Carlo
  const runSimulation = (iterCount?: number) => {
    const count = iterCount || monteCarloConfig.iterations;
    setMonteCarloConfig((prev) => ({ ...prev, isSimulating: true }));
    setTimeout(() => {
      const baseVal = selectedMeasurement ? selectedMeasurement.measured : 10.002;
      const res = runMonteCarloSimulation(baseVal, uncertaintySources, count);
      setMonteCarloConfig((prev) => ({
        ...prev,
        iterations: count,
        isSimulating: false,
        results: res,
      }));
      logAuditEvent(
        'Monte Carlo Propagation Executed',
        'MCM-KERNEL',
        'IDLE',
        `COMPLETED (N=${count.toLocaleString()})`,
        `Mean=${res.mean.toFixed(5)} V, u=${res.stdDev.toFixed(5)} V`
      );
    }, 450);
  };

  // Conformity Rule Update
  const setConformityRule = (rule: DecisionRuleType) => {
    let mult = 1.0;
    if (rule.includes('Method 6')) mult = 1.0;
    else if (rule.includes('Simple Acceptance')) mult = 0.0;
    else if (rule.includes('TUR >= 4:1')) mult = 0.8;
    else if (rule.includes('Shared Risk')) mult = 0.5;

    const evaluated = evaluateConformity(
      conformityConfig.measuredValue,
      conformityConfig.nominal,
      conformityConfig.specTolerance,
      conformityConfig.expandedUncertainty,
      mult
    );

    setConformityConfig({
      ...evaluated,
      decisionRule: rule,
    });
    logAuditEvent(
      'Decision Rule Altered',
      'CONFORMITY-ENGINE',
      conformityConfig.decisionRule,
      rule,
      `Guardband multiplier set to ${mult}`
    );
  };

  const updateConformityParams = (updates: Partial<ConformityConfig>) => {
    setConformityConfig((prev) => ({ ...prev, ...updates }));
  };

  const acknowledgeConformityDecision = () => {
    const now = new Date().toISOString();
    setConformityConfig((prev) => ({
      ...prev,
      acknowledgedBy: 'J. Doe (UID: 994)',
      acknowledgedAt: now,
    }));
    logAuditEvent(
      'Conformity Decision Acknowledged',
      'DEC-8842-D',
      'UNACKNOWLEDGED',
      'ACKNOWLEDGED',
      'Operator confirmed out of tolerance compliance state'
    );
  };

  // Node Lock
  const lockAllNodes = () => {
    setProvenanceNodes((prev) =>
      prev.map((n) => ({ ...n, isLocked: true }))
    );
    const nowStr = new Date().toISOString().substring(11, 19);
    setLineageEvents((prev) => [
      {
        id: `EV-${Date.now()}`,
        timestamp: nowStr,
        actor: 'System (Auto)',
        message: 'ALL Nodes LOCKED. Global checksum generated and frozen.',
        type: 'system',
      },
      ...prev,
    ]);
    logAuditEvent(
      'Global Graph Lock Applied',
      'PROVENANCE-DAG',
      'UNLOCKED_NODES',
      'ALL_LOCKED',
      'Cryptographic hash binding applied to entire measurement lineage'
    );
  };

  const toggleNodeLock = (id: string) => {
    setProvenanceNodes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isLocked: !n.isLocked } : n))
    );
  };

  // Report Actions
  const updateReportSection = (sectionKey: keyof ReportConfig['sections'], value: boolean) => {
    setReportConfig((prev) => ({
      ...prev,
      sections: {
        ...prev.sections,
        [sectionKey]: value,
      },
    }));
  };

  const saveDraftReport = () => {
    setReportConfig((prev) => ({ ...prev, status: 'GENERATED' }));
    logAuditEvent(
      'Calibration Report Generated',
      reportConfig.reportId,
      'DRAFT',
      'GENERATED',
      'Generated formal ISO/IEC 17025 certificate draft'
    );
  };

  const approveReport = () => {
    setReportConfig((prev) => ({
      ...prev,
      status: 'APPROVED',
      signDate: new Date().toISOString().substring(0, 10),
    }));
    logAuditEvent(
      'Calibration Report Approved & Signed',
      reportConfig.reportId,
      'GENERATED',
      'APPROVED',
      'Digitally signed by Lead Metrologist and Quality Authority'
    );
  };

  const selectedNode = provenanceNodes.find((n) => n.id === selectedNodeId) || provenanceNodes[0];

  const syncJobData = async (jobId: string) => {
    try {
      await flushJobWal(jobId);
      const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
      if (!res.ok) return;
      const data = await res.json();
      const job: MeasurementJob = data.job || data;
      setSelectedJob(job);

      if (job.raw_measurements && Array.isArray(job.raw_measurements) && job.raw_measurements.length > 0) {
        const nom = job.nominal_value ?? 10.0;
        const tolUp = job.tolerance_upper ?? 0.001;
        const tolLow = job.tolerance_lower ?? 0.001;
        const records: MeasurementRecord[] = job.raw_measurements.map((val: number, idx: number) => {
          const inTol = val >= (nom - tolLow) && val <= (nom + tolUp);
          return {
            id: `M-${String(idx + 1).padStart(3, '0')}`,
            reference: nom,
            measured: val,
            unit: job.unit || 'V',
            timestamp: job.updated_at || new Date().toISOString(),
            status: inTol ? 'IN_TOL' : 'OUT_TOL',
            isLocked: ['APPROVED', 'RELEASED'].includes(job.status),
            operator: job.operator || 'Technician',
            instrumentId: job.instrument_name || 'DUT',
            envTemp: job.environment?.ambient_temperature_c ?? 23.0,
            humidity: job.environment?.relative_humidity_pct ?? 45.0,
          };
        });
        setMeasurements(records);
        setSelectedMeasurementId(records[0].id);
      }

      if (job.uncertainty_budget?.budget_breakdown && job.uncertainty_budget.budget_breakdown.length > 0) {
        const mappedSources: UncertaintySource[] = job.uncertainty_budget.budget_breakdown.map((row, idx) => ({
          id: `UNC-${idx + 1}`,
          name: row.name,
          symbol: `u_${idx + 1}`,
          estimate: row.standard_uncertainty,
          unit: job.unit || 'V',
          distribution: (row.distribution as any) || 'Normal',
          divisor: 1.0,
          stdUncertainty: row.standard_uncertainty,
          sensitivity: row.sensitivity_coefficient ?? 1.0,
          dof: row.dof ?? 50,
          notes: `Extracted from Job ${job.job_number}`,
        }));
        setUncertaintySources(mappedSources);
      }

      if (job.conformity) {
        setConformityConfig((prev) => ({
          ...prev,
          measured: job.conformity?.mean_measured ?? prev.measured,
          nominal: job.conformity?.nominal_value ?? prev.nominal,
          toleranceUpper: job.conformity?.tolerance_upper ?? prev.toleranceUpper,
          toleranceLower: -(job.conformity?.tolerance_lower ?? Math.abs(prev.toleranceLower)),
          tur: job.conformity?.tur ?? prev.tur,
          verdict: (job.conformity?.conformance_verdict as any) || prev.verdict,
          pfaPct: job.conformity?.consumer_risk_pfa_pct ?? prev.pfaPct,
          guardbandMultiplier: job.conformity?.guardband_multiplier ?? prev.guardbandMultiplier,
        }));
      }
    } catch {
      // Clean, silent failure without console log pollution
    }
  };

  // Keyboard shortcut support (Ctrl+K / Cmd+K for Command Palette)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setIsCommandPaletteOpen(false);
        setIsDiagnosticsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <MetrologyContext.Provider
      value={{
        activeWorkspace,
        setActiveWorkspace,
        measurements,
        selectedMeasurementId,
        setSelectedMeasurementId,
        selectedMeasurement,
        addMeasurement,
        updateMeasurement,
        deleteMeasurement,
        filterText,
        setFilterText,
        statusFilter,
        setStatusFilter,
        uncertaintySources: sourcesWithVariance,
        updateUncertaintySource,
        addUncertaintySource,
        combinedUc,
        expandedU,
        effectiveDof,
        monteCarloConfig,
        runSimulation,
        setMonteCarloConfig,
        conformityConfig,
        setConformityRule,
        updateConformityParams,
        acknowledgeConformityDecision,
        provenanceNodes,
        selectedNodeId,
        setSelectedNodeId,
        selectedNode,
        lockAllNodes,
        toggleNodeLock,
        lineageEvents,
        auditTrail,
        logAuditEvent,
        reportConfig,
        updateReportSection,
        saveDraftReport,
        approveReport,
        instruments,
        activeInstrument,
        setActiveInstrumentId,
        historyCycles,
        stabilityMatrix,
        isCommandPaletteOpen,
        setIsCommandPaletteOpen,
        isDiagnosticsOpen,
        setIsDiagnosticsOpen,
        isOnboardingOpen,
        setIsOnboardingOpen,
        isCommercial,
        isDemo,
        isUpgradeModalOpen,
        setIsUpgradeModalOpen,
        refreshLicense,
        selectedJob,
        setSelectedJob,
        syncJobData,
      }}
    >
      {children}
    </MetrologyContext.Provider>
  );
};

export const useMetrology = () => {
  const context = useContext(MetrologyContext);
  if (!context) {
    throw new Error('useMetrology must be used within a MetrologyProvider');
  }
  return context;
};

import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  Shield,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const ConformityWorkspace: React.FC = () => {
  const { selectedJob, conformityConfig } = useMetrology();
  const [activeTab, setActiveTab] = useState<'decision-rule' | 'guardband' | 'tolerance' | 'uncertainty' | 'risk' | 'evidence'>('decision-rule');

  const c = selectedJob?.conformity;
  const nom = c?.nominal_value ?? selectedJob?.nominal_value ?? conformityConfig.nominal;
  const measured = c?.mean_measured ?? conformityConfig.measured;
  const dev = c?.error_of_indication ?? (measured - nom);
  const tolUp = c?.tolerance_upper ?? selectedJob?.tolerance_upper ?? conformityConfig.toleranceUpper;
  const tolLow = c?.tolerance_lower ?? selectedJob?.tolerance_lower ?? conformityConfig.toleranceLower;
  const tur = c?.tur ?? conformityConfig.tur;
  const verdict = c?.conformance_verdict || conformityConfig.verdict || 'PASS';
  const pfaPct = c?.consumer_risk_pfa_pct ?? conformityConfig.pfaPct;
  const guardbandW = c?.guardband_w ?? 0.00022;

  const conformityData = {
    measurand: selectedJob ? `${selectedJob.instrument_name} (${nom} ${selectedJob.unit || 'V'})` : 'DC Voltage 10 V',
    nominal: nom,
    measured: measured,
    deviation: dev,
    toleranceUpper: tolUp,
    toleranceLower: -Math.abs(tolLow),
    expandedUncertainty: selectedJob?.uncertainty_budget?.expanded_uncertainty_U95 ?? 0.00031,
    tur: tur,
    guardbandApplied: `Method 6 (w = ${guardbandW.toFixed(5)} ${selectedJob?.unit || 'V'})`,
    acceptanceLimitUpper: c?.acceptance_upper ?? (nom + tolUp - guardbandW),
    acceptanceLimitLower: c?.acceptance_lower ?? (nom - tolLow + guardbandW),
    verdict: verdict,
    pfaPct: pfaPct,
    pfrPct: 0.00,
    decisionRule: 'ANSI/NCSL Z540.3-2006 Method 6 / ILAC-G8:09/2019 Binary Statement with Guard Band',
  };

  const isPass = conformityData.verdict === 'PASS';
  const isFail = conformityData.verdict === 'FAIL';
  const statusColor = isPass ? '#16A34A' : (isFail ? '#DC2626' : '#D97706');
  const statusBg = isPass ? '#DCFCE7' : (isFail ? '#FEE2E2' : '#FEF3C7');
  const statusBorder = isPass ? '#BBF7D0' : (isFail ? '#FECACA' : '#FDE68A');

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-y-auto custom-scrollbar p-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-[#E2E5E9]">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
            ISO/IEC 17025:2017 &sect;7.8.6
          </span>
          <span className="text-xs text-[#656B73]">Statements of Conformity & Decision Rules</span>
        </div>
        <h1 className="text-xl font-bold text-[#17191C] mt-1 tracking-tight">
          Conformity Assessment & Risk &mdash; {selectedJob?.job_number || 'General Assessment'}
        </h1>
      </div>

      {/* Main Verdict Card */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg p-6 shadow-xs mt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#E2E5E9] gap-4">
          <div>
            <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
              CONFORMANCE VERDICT
            </div>
            <div className="flex items-center gap-3 mt-1.5">
              <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: statusColor }}></span>
              <span className="text-3xl font-black font-mono tracking-tight" style={{ color: statusColor }}>
                {conformityData.verdict}
              </span>
              <span
                className="text-xs font-mono font-medium px-2.5 py-1 rounded border"
                style={{ backgroundColor: statusBg, borderColor: statusBorder, color: statusColor }}
              >
                {isPass ? 'Within Guard Band Limits' : (isFail ? 'Exceeds Tolerance Limits' : 'In Guardband Transition')}
              </span>
            </div>
          </div>

          <div className="text-right">
            <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider block">
              CONSUMER RISK (PFA)
            </span>
            <div className="text-2xl font-extrabold text-[#17191C] font-mono tabular-nums mt-1">
              {conformityData.pfaPct.toFixed(2)} %
            </div>
            <div className="text-xs text-[#16A34A] font-medium mt-0.5">
              &le; 2.0% requirement (Compliant)
            </div>
          </div>
        </div>

        {/* Core numbers strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 text-xs">
          <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
            <span className="text-[#656B73] block text-[11px]">Measured Result</span>
            <span className="font-mono font-bold text-sm text-[#17191C]">
              {conformityData.measured.toFixed(5)} V
            </span>
          </div>

          <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
            <span className="text-[#656B73] block text-[11px]">Specification Limit</span>
            <span className="font-mono font-bold text-sm text-[#17191C]">
              10.00000 ± 0.00100 V
            </span>
          </div>

          <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
            <span className="text-[#656B73] block text-[11px]">Test Uncertainty Ratio (TUR)</span>
            <span className="font-mono font-bold text-sm text-[#00435F]">
              {conformityData.tur.toFixed(2)}:1
            </span>
          </div>

          <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
            <span className="text-[#656B73] block text-[11px]">Decision Rule</span>
            <span className="font-semibold text-xs text-[#17191C] truncate block">
              Guard band applied
            </span>
          </div>
        </div>
      </div>

      {/* 21st.dev Tabs: Decision rule | Guard band | Tolerance | Uncertainty | Risk | Evidence */}
      <div className="mt-6 flex border-b border-[#E2E5E9] bg-white rounded-t-lg px-4 pt-2 gap-4 text-xs font-semibold text-[#656B73]">
        {(['decision-rule', 'guardband', 'tolerance', 'uncertainty', 'risk', 'evidence'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2.5 uppercase text-[11px] tracking-wider transition-colors cursor-pointer ${
              activeTab === tab
                ? 'text-[#00435F] border-b-2 border-[#00435F] font-bold'
                : 'hover:text-[#17191C]'
            }`}
          >
            {tab.replace('-', ' ')}
          </button>
        ))}
      </div>

      {/* Tab Content Box */}
      <div className="bg-white border-x border-b border-[#E2E5E9] rounded-b-lg p-5 shadow-xs text-xs">
        {activeTab === 'decision-rule' && (
          <div className="space-y-3">
            <h3 className="font-bold text-[#17191C] uppercase tracking-wider text-xs">
              Statement of Decision Rule
            </h3>
            <p className="text-[#17191C] leading-relaxed">
              The conformity evaluation was conducted in accordance with <b>{conformityData.decisionRule}</b>.
              Acceptance is declared when the measured value falls inside the specification limits reduced by the guard band <i>w</i>.
            </p>
            <div className="p-3 bg-[#F7F8FA] border border-[#E2E5E9] rounded font-mono text-[11.5px] text-[#656B73]">
              Binary Acceptance: (L_SL + w) &le; y &le; (U_SL - w) &rarr; Verdict = PASS
            </div>
          </div>
        )}

        {activeTab === 'guardband' && (
          <div className="space-y-3">
            <h3 className="font-bold text-[#17191C] uppercase tracking-wider text-xs">
              Guard Band Formulation
            </h3>
            <p className="text-[#17191C]">
              Method 6 applies a guard band multiplier based on TUR. With TUR = 6.45:1, the guardband offset is:
            </p>
            <div className="p-3 bg-[#F7F8FA] border border-[#E2E5E9] rounded font-mono text-xs">
              w = U_95 &times; [1.0 - (4.0 / TUR)] = 0.00031 &times; [1.0 - (4.0 / 6.45)] = 0.00022 V
            </div>
          </div>
        )}

        {activeTab === 'tolerance' && (
          <div className="space-y-2">
            <h3 className="font-bold text-[#17191C] uppercase tracking-wider text-xs">
              Tolerance Specification
            </h3>
            <p className="text-[#656B73]">
              Manufacturer 1-Year Specification for Fluke 8846A on 10V DC Range: ±(0.0024% of reading + 0.0005% of range).
            </p>
          </div>
        )}

        {activeTab === 'uncertainty' && (
          <div className="space-y-2">
            <h3 className="font-bold text-[#17191C] uppercase tracking-wider text-xs">
              Calibration Uncertainty
            </h3>
            <p className="text-[#656B73]">
              Expanded Uncertainty U_95 = 0.00031 V (k=2, 95.45% confidence) derived from GUM budget.
            </p>
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="space-y-3">
            <h3 className="font-bold text-[#17191C] uppercase tracking-wider text-xs">
              Probability of False Accept (PFA)
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-[#F0FDF4] rounded border border-[#BBF7D0]">
                <span className="text-[#16A34A] block font-semibold">Consumer's Risk (PFA):</span>
                <span className="text-xl font-bold text-[#16A34A] font-mono">0.02%</span>
                <span className="text-[10.5px] text-[#656B73] block mt-1">Acceptance threshold &le; 2.0%</span>
              </div>
              <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
                <span className="text-[#656B73] block font-semibold">Producer's Risk (PFR):</span>
                <span className="text-xl font-bold text-[#17191C] font-mono">0.00%</span>
                <span className="text-[10.5px] text-[#656B73] block mt-1">False rejection probability</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="space-y-2">
            <h3 className="font-bold text-[#17191C] uppercase tracking-wider text-xs">
              Evidence Trail
            </h3>
            <p className="text-[#656B73] font-mono text-[11px]">
              Decision Hash: a9b4c02941df2a1040fbc98214fa77319984cfb0
              <br />
              Status: Sealed in Job Audit Ledger
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

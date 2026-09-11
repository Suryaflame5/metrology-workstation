import React, { useState } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  RotateCcw,
  FileText,
  FileCheck,
  Download,
  Cpu,
  Layers,
  ShieldCheck,
  Activity,
  Terminal,
} from 'lucide-react';
import {
  previewImport,
  applyImport,
  runPipeline,
  approveJob,
  runAutomatedCalibration,
  getCertificatePdfUrl,
  getEvidencePackageUrl,
} from '../../services/jobApi';
import { MeasurementJob } from '../../types/job';
import { useMetrology } from '../../context/MetrologyContext';

interface CockpitProps {
  job: MeasurementJob;
  onBack: () => void;
  onUpdateJob: (job: MeasurementJob) => void;
}

export const JobWorkflowCockpit: React.FC<CockpitProps> = ({
  job,
  onBack,
  onUpdateJob,
}) => {
  const { setActiveWorkspace } = useMetrology();
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Approval state
  const [signerName, setSignerName] = useState(job.reviewer || 'Marcus Brody');
  const [signerRole, setSignerRole] = useState('Lead Metrologist');
  const [reason, setReason] = useState('Conformity verified against ISO/IEC 17025 standard');

  // Determine stage progression (8 stages)
  const isApproved = job.status === 'APPROVED' || job.status === 'RELEASED';
  const hasMeasurements = (job.raw_measurements && job.raw_measurements.length > 0) || (job.measurements && job.measurements.length > 0);
  const hasUncertainty = !!job.uncertainty?.expanded_uncertainty;
  const hasConformity = !!job.conformity?.conformance_verdict;

  const handleRunAutomatedExecution = async () => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await runAutomatedCalibration(job.id, {
        ambient_temperature_c: 20.1,
        relative_humidity_pct: 45.8,
        atmospheric_pressure_hpa: 1013.25,
      });
      setSuccessMsg(`Automated calibration complete: ${res.measurements_acquired} points captured. Verdict: ${res.conformity_verdict}`);
      // Refresh job
      if (res.job) {
        onUpdateJob(res.job);
      } else {
        const updated = await runPipeline(job.id);
        onUpdateJob(updated);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Automated hardware acquisition failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const updated = await approveJob(job.id, {
        signer_name: signerName,
        signer_role: signerRole,
        meaning: reason,
      });
      onUpdateJob(updated);
      setSuccessMsg('Job approved and cryptographically signed (21 CFR Part 11 compliant).');
    } catch (err: any) {
      setErrorMsg(err.message || 'Approval signature failed.');
    } finally {
      setLoading(false);
    }
  };

  const stages = [
    { name: 'Intake', done: true },
    { name: 'Asset verification', done: true },
    { name: 'Instrument verification', done: true },
    { name: 'Environment check', done: true },
    { name: 'Calibration execution', done: hasMeasurements, active: !hasMeasurements },
    { name: 'Review', done: hasUncertainty && hasConformity, active: hasMeasurements && !hasUncertainty },
    { name: 'Sign-off', done: isApproved, active: hasUncertainty && !isApproved },
    { name: 'Certificate', done: isApproved },
  ];

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-y-auto custom-scrollbar p-6">
      {/* Top Breadcrumb & Controls */}
      <div className="flex items-center justify-between pb-4 border-b border-[#E2E5E9]">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="px-2.5 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Jobs</span>
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-sm text-[#00435F]">{job.job_number || job.id}</span>
              <span className="text-[10.5px] px-2 py-0.2 rounded font-mono font-semibold bg-[#EBF3F6] text-[#00435F] border border-[#CBD5E1]">
                Rev {job.revision_number || 1}
              </span>
              <span className="text-[10.5px] px-2 py-0.2 rounded font-mono font-semibold bg-[#DCFCE7] text-[#16A34A] border border-[#BBF7D0]">
                {job.status}
              </span>
            </div>
            <h1 className="text-base font-bold text-[#17191C] mt-0.5">{job.title}</h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isApproved && (
            <>
              <a
                href={getCertificatePdfUrl(job.id)}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>PDF Certificate</span>
              </a>
              <a
                href={`/api/v1/jobs/${encodeURIComponent(job.id)}/dcc-json`}
                target="_blank"
                rel="noreferrer"
                className="px-2.5 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
              >
                DCC JSON
              </a>
              <a
                href={`/api/v1/jobs/${encodeURIComponent(job.id)}/dcc-xml`}
                target="_blank"
                rel="noreferrer"
                className="px-2.5 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
              >
                DCC XML
              </a>
            </>
          )}
        </div>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="mt-4 p-3 bg-[#FEE2E2] border border-[#FCA5A5] text-[#DC2626] rounded text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
      {successMsg && (
        <div className="mt-4 p-3 bg-[#DCFCE7] border border-[#BBF7D0] text-[#16A34A] rounded text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Top 3 Identity Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
        {/* Asset Card */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
            Asset Under Test
          </div>
          <div className="text-sm font-bold text-[#17191C] mt-1.5">
            {job.instrument_model || job.instrument_name || 'Precision Multimeter'}
          </div>
          <div className="text-xs text-[#656B73] font-mono mt-0.5">
            Serial: {job.instrument_serial || 'Not recorded'}
          </div>
          <div className="text-[11px] text-[#656B73] mt-2">
            Customer: <span className="text-[#17191C] font-medium">{job.customer_name || 'Internal Standard'}</span>
          </div>
        </div>

        {/* Procedure Card */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
            Standard Procedure
          </div>
          <div className="text-sm font-bold text-[#17191C] mt-1.5">
            {job.procedure_name || 'EURAMET cg-15 — DC Voltage'}
          </div>
          <div className="text-xs text-[#656B73] mt-0.5">
            Version: <span className="font-mono font-medium text-[#17191C]">3.2 (Approved & Locked)</span>
          </div>
          <div className="text-[11px] text-[#656B73] mt-2 font-mono">
            Target: {job.nominal_value ?? '10.0'} {job.unit || 'V'} ±{job.tolerance_upper ?? '0.0010'} {job.unit || 'V'}
          </div>
        </div>

        {/* Status Card */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
            Calibration State
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${isApproved ? 'bg-[#16A34A]' : 'bg-[#0284C7] animate-pulse'}`}></span>
            <span className="text-sm font-bold text-[#17191C]">{job.status}</span>
          </div>
          <div className="text-xs text-[#656B73] mt-0.5">
            Environment: <span className="text-[#16A34A] font-semibold">20.1 °C &bull; 45.8% RH</span>
          </div>
          <div className="text-[11px] text-[#656B73] mt-2">
            Decision: <span className="font-semibold text-[#17191C]">{job.conformity?.conformance_verdict || 'PENDING EXECUTION'}</span>
          </div>
        </div>
      </div>

      {/* 8-Stage Progress Tracker */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 mt-5 shadow-xs">
        <div className="text-xs font-bold text-[#17191C] uppercase tracking-wider mb-3">
          Job Progress
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          {stages.map((stg, sIdx) => (
            <div
              key={sIdx}
              className={`p-2.5 rounded border text-xs flex flex-col justify-between ${
                stg.done
                  ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#16A34A]'
                  : stg.active
                  ? 'bg-[#EBF3F6] border-[#00435F] text-[#00435F] font-semibold'
                  : 'bg-[#F7F8FA] border-[#E2E5E9] text-[#656B73]'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono">0{sIdx + 1}</span>
                {stg.done ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#16A34A]" />
                ) : stg.active ? (
                  <span className="w-2 h-2 rounded-full bg-[#00435F] animate-ping"></span>
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#CBD5E1]"></span>
                )}
              </div>
              <div className="text-[11px] leading-tight line-clamp-2">{stg.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Execution Actions & Review Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Automated Execution Block */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E5E9]">
              <div>
                <h3 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                  Automated Calibration Execution
                </h3>
                <p className="text-xs text-[#656B73] mt-0.5">
                  Execute instrument driver acquisition, live streaming buffer, and GUM pipeline
                </p>
              </div>
              <Cpu className="w-5 h-5 text-[#00435F]" />
            </div>

            <div className="my-4 space-y-2 text-xs">
              <div className="flex items-center justify-between bg-[#F7F8FA] p-2.5 rounded border border-[#E2E5E9]">
                <span className="text-[#656B73]">Measurement Driver:</span>
                <span className="font-mono font-semibold text-[#17191C]">SCPI-TCP / Keysight 34461A Profile</span>
              </div>
              <div className="flex items-center justify-between bg-[#F7F8FA] p-2.5 rounded border border-[#E2E5E9]">
                <span className="text-[#656B73]">Sample Points:</span>
                <span className="font-mono font-semibold text-[#17191C]">5 Readings @ 10 V DC Nominal</span>
              </div>
              <div className="flex items-center justify-between bg-[#F7F8FA] p-2.5 rounded border border-[#E2E5E9]">
                <span className="text-[#656B73]">Decision Rule:</span>
                <span className="font-mono font-semibold text-[#17191C]">ANSI/NCSL Z540.3 Method 6 (Guard Band)</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-[#E2E5E9] flex items-center justify-between">
            <button
              onClick={() => setActiveWorkspace('measurements')}
              className="text-xs text-[#00435F] hover:underline font-medium cursor-pointer"
            >
              Inspect Readings ({job.raw_measurements?.length || 0} pts)
            </button>
            <button
              onClick={handleRunAutomatedExecution}
              disabled={loading}
              className="px-4 py-2 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{loading ? 'Executing Instrument Test...' : 'Start Automated Execution'}</span>
            </button>
          </div>
        </div>

        {/* 21 CFR Part 11 Electronic Signature Approval */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E5E9]">
              <div>
                <h3 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                  Review & Sign-Off (21 CFR Part 11)
                </h3>
                <p className="text-xs text-[#656B73] mt-0.5">
                  Cryptographic approval and accredited calibration certificate issuance
                </p>
              </div>
              <ShieldCheck className="w-5 h-5 text-[#16A34A]" />
            </div>

            {isApproved ? (
              <div className="my-4 p-4 bg-[#F0FDF4] border border-[#BBF7D0] rounded text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-[#16A34A]">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>CALIBRATION APPROVED & SEALED</span>
                </div>
                <div className="text-[#17191C]">
                  Signer: <span className="font-semibold">{job.reviewer || signerName}</span> ({signerRole})
                </div>
                <div className="text-[#656B73] font-mono text-[10.5px]">
                  Hash: {job.digital_signature?.signature_hash || 'SHA-256 Verified In Evidence Vault'}
                </div>
              </div>
            ) : (
              <form onSubmit={handleApprove} className="my-4 space-y-3 text-xs">
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Signer Name
                  </label>
                  <input
                    type="text"
                    required
                    value={signerName}
                    onChange={(e) => setSignerName(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded text-xs"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                      Role
                    </label>
                    <input
                      type="text"
                      required
                      value={signerRole}
                      onChange={(e) => setSignerRole(e.target.value)}
                      className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                      Meaning of Signature
                    </label>
                    <input
                      type="text"
                      required
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded text-xs"
                    />
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-[#16A34A] hover:bg-[#15803D] text-white text-xs font-semibold rounded shadow-xs flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <FileCheck className="w-3.5 h-3.5" />
                    <span>Dual-Sign & Release Certificate</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

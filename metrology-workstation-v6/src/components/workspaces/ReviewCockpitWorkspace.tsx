import React, { useState, useEffect } from "react";
import {
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Shield,
  ShieldCheck,
  Download,
  Printer,
  History,
  GitCompare,
  Lock,
  UserCheck,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { useMetrology } from "../../context/MetrologyContext";

interface ReviewData {
  job_id: string;
  job_number: string;
  title: string;
  customer_name: string;
  instrument_name: string;
  instrument_model: string;
  instrument_serial: string;
  procedure_name: string;
  status: string;
  unit: string;
  result: {
    mean: number;
    expanded_uncertainty: number;
    formatted_statement: string;
    coverage_factor: number;
  };
  specification_limits: {
    nominal: number;
    tolerance_lower: number;
    tolerance_upper: number;
    lower_limit: number;
    upper_limit: number;
    span: number;
  };
  conformity: {
    verdict: string;
    tur: number;
    guardband_w: number;
    acceptance_lower: number;
    acceptance_upper: number;
    consumer_risk_pct: string;
  };
  quality_checks: Array<{
    id: string;
    label: string;
    passed: boolean;
    detail: string;
  }>;
  all_checks_passed: boolean;
  exceptions: any[];
  evidence: {
    calculation_id?: string;
    certificate_id?: string;
    evidence_package_path?: string;
    is_signed: boolean;
    signer?: string;
    signed_at?: string;
  };
  operator: string;
  reviewer?: string;
}

export const ReviewCockpitWorkspace: React.FC = () => {
  const { selectedJobId, setSelectedJobId, setActiveWorkspace } = useMetrology();
  const [data, setData] = useState<ReviewData | null>(null);
  const [allJobs, setAllJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [signing, setSigning] = useState(false);
  const [signerName, setSignerName] = useState("Marcus Brody, CQA");
  const [signerRole, setSignerRole] = useState("Lead Metrology Reviewer");
  const [signReason, setSignReason] = useState("Technical Conformance Concurrence under ISO/IEC 17025 §7.8");
  const [revNotes, setRevNotes] = useState("");
  const [showRevModal, setShowRevModal] = useState(false);
  const [verificationResult, setVerificationResult] = useState<string | null>(null);

  const fetchJobReview = async (id: string) => {
    setLoading(true);
    setVerificationResult(null);
    try {
      const res = await fetch(`/api/v8/review-cockpit/${id}`).then((r) => r.json());
      if (res && res.job_id) {
        setData(res);
      }
    } catch (e) {
      console.error("Error fetching review cockpit:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllJobs = async () => {
    try {
      const res = await fetch("/api/jobs").then((r) => r.json());
      if (res && res.jobs) {
        setAllJobs(res.jobs);
        if (!selectedJobId && res.jobs.length > 0) {
          setSelectedJobId(res.jobs[0].id);
        }
      }
    } catch (e) {
      console.error("Error fetching job list:", e);
    }
  };

  useEffect(() => {
    fetchAllJobs();
  }, []);

  useEffect(() => {
    if (selectedJobId) {
      fetchJobReview(selectedJobId);
    }
  }, [selectedJobId]);

  const handleSignAndApprove = async () => {
    if (!data) return;
    setSigning(true);
    try {
      const res = await fetch(`/api/jobs/${data.job_id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signer_name: signerName,
          role: signerRole,
          reason: signReason,
        }),
      });
      const updated = await res.json();
      if (updated && updated.job) {
        fetchJobReview(data.job_id);
      }
    } catch (e) {
      console.error("Error signing job:", e);
    } finally {
      setSigning(false);
    }
  };

  const handleCreateRevision = async () => {
    if (!data) return;
    try {
      const res = await fetch(`/api/v8/jobs/${data.job_id}/revisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          notes: revNotes || "Recalibration revision",
          operator: signerName,
        }),
      });
      const result = await res.json();
      if (result && result.job) {
        setShowRevModal(false);
        setSelectedJobId(result.job.id);
        fetchAllJobs();
      }
    } catch (e) {
      console.error("Error creating revision:", e);
    }
  };

  const handleVerifyPackage = async () => {
    if (!data?.evidence?.calculation_id) return;
    setLoading(true);
    try {
      const zipRes = await fetch(`/api/jobs/${data.job_id}/evidence-package`);
      const blob = await zipRes.blob();
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64data = (reader.result as string).split(",")[1];
        const vRes = await fetch("/api/v8/evidence/verify-package", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ zip_base64: base64data }),
        }).then((r) => r.json());
        if (vRes.is_valid) {
          setVerificationResult(`✓ Verified! ${vRes.total_files_verified} files cryptographically intact.`);
        } else {
          setVerificationResult(`❌ Verification Alert: ${vRes.error || "Hash mismatch detected"}`);
        }
        setLoading(false);
      };
      reader.readAsDataURL(blob);
    } catch (e) {
      console.error("Verification failed:", e);
      setLoading(false);
    }
  };

  if (!data) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#f8fafc] text-slate-500">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-2" />
        <span>Loading Review Cockpit...</span>
      </div>
    );
  }

  const isApproved = data.status === "APPROVED" || data.evidence.is_signed;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto custom-scrollbar">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                Review &amp; 1-Click Release Cockpit
              </h1>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full font-mono ${
                isApproved
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : data.conformity.verdict === "FAIL"
                  ? "bg-rose-100 text-rose-800 border border-rose-300"
                  : "bg-blue-100 text-blue-800 border border-blue-300"
              }`}>
                {data.status}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              High-efficiency 30-second sign-off: Result vs Limits, ANSI Z540.3 Guardband, 5 Quality Gates, and 21 CFR Part 11 signature.
            </p>
          </div>
        </div>

        {/* Job Selector Dropdown */}
        <div className="flex items-center gap-2">
          <select
            value={data.job_id}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="text-xs font-semibold px-3 py-1.5 border border-slate-300 rounded-md bg-white text-slate-800 focus:outline-hidden"
          >
            {allJobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.job_number || j.id} — {j.instrument_name} ({j.customer_name})
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowRevModal(true)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 cursor-pointer"
          >
            <History className="w-3.5 h-3.5" />
            New Rev
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Unit Under Test Header Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-xs text-slate-500 font-mono">
              Job: <strong className="text-slate-800">{data.job_number || data.job_id}</strong> • Customer: <strong className="text-slate-800">{data.customer_name}</strong>
            </div>
            <h2 className="text-base font-bold text-slate-900">
              {data.instrument_name} — {data.instrument_model} (SN: {data.instrument_serial})
            </h2>
            <div className="text-xs text-slate-600">
              Procedure: <span className="font-semibold text-slate-800">{data.procedure_name}</span>
            </div>
          </div>

          <div className="text-right">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Conformity Decision</div>
            <div className={`text-xl font-bold font-mono ${
              data.conformity.verdict === "PASS"
                ? "text-emerald-600"
                : data.conformity.verdict === "FAIL"
                ? "text-rose-600"
                : "text-amber-600"
            }`}>
              {data.conformity.verdict}
            </div>
            <div className="text-[10px] text-slate-400">TUR {data.conformity.tur?.toFixed(2)}:1</div>
          </div>
        </div>

        {/* Section 1 & 2: Result vs Limits & Guardband */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Result vs Specification Limits */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                1. Measurement Result vs Specification Limits
              </h3>
              <span className="font-mono text-xs text-slate-500">Unit: {data.unit}</span>
            </div>

            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-3">
              <div className="flex justify-between items-baseline">
                <span className="text-xs text-slate-500 font-semibold">Reported Value (y ± U95):</span>
                <span className="text-base font-mono font-bold text-slate-900">
                  {data.result.formatted_statement}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs pt-2 border-t border-slate-200">
                <div className="bg-white p-2 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">Lower Spec Limit</div>
                  <div className="font-mono font-bold text-slate-700 mt-0.5">
                    {data.specification_limits.lower_limit.toFixed(5)}
                  </div>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">Nominal Target</div>
                  <div className="font-mono font-bold text-blue-700 mt-0.5">
                    {data.specification_limits.nominal.toFixed(5)}
                  </div>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">Upper Spec Limit</div>
                  <div className="font-mono font-bold text-slate-700 mt-0.5">
                    {data.specification_limits.upper_limit.toFixed(5)}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 leading-relaxed">
              Confidence level: 95.45% using Student’s t coverage factor k = {data.result.coverage_factor.toFixed(2)}.
              Traceable to BIPM SI standards via primary calibration chain.
            </p>
          </div>

          {/* ANSI Z540.3 Method 6 Guardband */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                2. ANSI/NCSL Z540.3 Method 6 Guardband
              </h3>
              <span className="bg-blue-100 text-blue-800 font-mono text-[10px] font-bold px-2 py-0.5 rounded">
                PCR &lt; 2.0%
              </span>
            </div>

            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-600 font-semibold">Test Uncertainty Ratio (TUR):</span>
                <span className="font-mono font-bold text-slate-800">{data.conformity.tur?.toFixed(2)} : 1</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-600 font-semibold">Root Guardband Width (w):</span>
                <span className="font-mono font-bold text-slate-800">±{data.conformity.guardband_w?.toFixed(6)} {data.unit}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-600 font-semibold">Acceptance Zone [LAL, UAL]:</span>
                <span className="font-mono font-bold text-emerald-700">
                  [{data.conformity.acceptance_lower?.toFixed(5)}, {data.conformity.acceptance_upper?.toFixed(5)}] {data.unit}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs pt-1 border-t border-slate-200">
                <span className="text-slate-600 font-semibold">Consumer Risk Probability:</span>
                <span className="font-mono font-bold text-emerald-600">{data.conformity.consumer_risk_pct}</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 leading-relaxed">
              Standard guardband reduction applied to specification limits ensures the maximum probability of false accept (PFA) remains below 2% per ANSI/NCSL Z540.3 Handbook §5.3.
            </p>
          </div>
        </div>

        {/* Section 3: Metrology Quality Gates Checklist */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                3. Automated Metrological Quality Gates (5-Point Checklist)
              </h3>
            </div>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
              data.all_checks_passed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
            }`}>
              {data.all_checks_passed ? "ALL CHECKS PASSED (5/5)" : "ACTION REQUIRED"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.quality_checks.map((qc) => (
              <div
                key={qc.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-slate-50"
              >
                {qc.passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                )}
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-slate-800">{qc.label}</div>
                  <div className="text-[11px] text-slate-500 font-mono">{qc.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: 21 CFR Part 11 Electronic Signature Ceremony */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-blue-600" />
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                4. FDA 21 CFR Part 11 Electronic Signature Ceremony
              </h3>
            </div>
            {isApproved && (
              <span className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                <Lock className="w-3 h-3" />
                RECORD CRYPTOGRAPHICALLY SEALED
              </span>
            )}
          </div>

          {isApproved ? (
            <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 space-y-2">
              <div className="flex items-center gap-2 text-emerald-800 text-xs font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Certificate Technically Approved &amp; Released</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-emerald-900 pt-2 border-t border-emerald-200 font-mono">
                <div>Signer: <strong>{data.evidence.signer || data.reviewer || signerName}</strong></div>
                <div>Role: <strong>{signerRole}</strong></div>
                <div>Signed At: <strong>{data.evidence.signed_at || "Traceable ISO Timestamp"}</strong></div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Authorized Signer Name</label>
                  <input
                    type="text"
                    value={signerName}
                    onChange={(e) => setSignerName(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Role / Authorization Level</label>
                  <input
                    type="text"
                    value={signerRole}
                    onChange={(e) => setSignerRole(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Sign-Off Intent Statement</label>
                  <input
                    type="text"
                    value={signReason}
                    onChange={(e) => setSignReason(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <p className="text-[11px] text-slate-500">
                  By clicking approve, you apply a legally-binding cryptographic SHA-256 digital signature under 21 CFR Part 11 and ISO/IEC 17025 §7.8.
                </p>

                <button
                  onClick={handleSignAndApprove}
                  disabled={signing}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50"
                >
                  <UserCheck className="w-4 h-4" />
                  {signing ? "Sealing Cryptographic Certificate..." : "1-Click Sign & Approve Certificate"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Section 5: Evidence & Certificate Outputs */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              5. Certified Evidence Outputs &amp; Cryptographic Verification
            </h3>
            {verificationResult && (
              <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                {verificationResult}
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <a
              href={`/api/v1/jobs/${encodeURIComponent(data.job_id)}/advanced-certificate-pdf`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold transition cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Printable ISO 17025 Certificate (PDF)</span>
              <ExternalLink className="w-3 h-3 ml-1" />
            </a>

            <a
              href={`/api/jobs/${data.job_id}/evidence-package`}
              download
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Evidence ZIP Package</span>
            </a>

            <button
              onClick={handleVerifyPackage}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-700 text-xs font-semibold transition cursor-pointer"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verify Cryptographic Package</span>
            </button>
          </div>
        </div>
      </div>

      {/* New Revision Modal */}
      {showRevModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center gap-2 text-slate-900 font-bold text-sm">
              <History className="w-4 h-4 text-blue-600" />
              <span>Create New Calibration Revision</span>
            </div>
            <p className="text-xs text-slate-500">
              Instantiates a new version of this calibration job (e.g. Rev 2) while preserving immutable audit link to previous revision.
            </p>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Reason for Revision</label>
              <textarea
                value={revNotes}
                onChange={(e) => setRevNotes(e.target.value)}
                placeholder="e.g. Recalibration following zero-offset thermal stabilization adjustment"
                className="w-full text-xs p-2.5 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowRevModal(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-800 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRevision}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-bold hover:bg-blue-700 cursor-pointer"
              >
                Create Revision
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

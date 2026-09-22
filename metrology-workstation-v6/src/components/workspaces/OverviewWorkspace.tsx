import React, { useState, useEffect } from 'react';
import {
  Clock,
  CheckCircle2,
  PlayCircle,
  AlertTriangle,
  Calendar,
  ArrowRight,
  RefreshCw,
  Tag,
  Cpu,
  Inbox,
  ShieldAlert,
  Sparkles,
  Calculator,
  FileBarChart,
  ShieldCheck,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';
import { fetchJobs, fetchAssets } from '../../services/jobApi';

export const OverviewWorkspace: React.FC = () => {
  const {
    setActiveWorkspace,
    setSelectedJob,
    isCommercial,
    isDemo,
    setIsUpgradeModalOpen,
  } = useMetrology();

  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  const [recentExceptions, setRecentExceptions] = useState<any[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [jList, aList, excData] = await Promise.all([
        fetchJobs(),
        fetchAssets(),
        fetch('/api/v8/exceptions?limit=5')
          .then((r) => (r.ok ? r.json() : { feed: [] }))
          .catch(() => ({ feed: [] })),
      ]);
      setJobs(jList || []);
      setAssets(aList || []);
      const mappedExceptions = (excData.feed || []).slice(0, 3).map((item: any) => ({
        id: item.job_id,
        code: item.job_number || item.job_id,
        title: item.primary_reason || 'Out of tolerance',
        detail: item.reasons?.join('; ') || 'Quality check flagged for review.',
        severity: item.severity === 'CRITICAL' ? 'HIGH' : item.severity === 'WARNING' ? 'MEDIUM' : 'LOW',
        time: item.created_at ? new Date(item.created_at).toLocaleTimeString().substring(0, 5) : 'Recent',
        jobId: item.job_number || item.job_id,
      }));
      setRecentExceptions(mappedExceptions);
    } catch {
      // Fallback handled gracefully
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Compute operational metrics
  const activeCount = jobs.filter((j) => ['RUNNING', 'IMPORTING', 'ANALYZING', 'IN_PROGRESS'].includes(j.status)).length;
  const reviewCount = jobs.filter((j) => ['REVIEW_REQUIRED', 'READY_FOR_APPROVAL', 'REVIEW'].includes(j.status)).length;
  const dueCount = jobs.length;
  const overdueCount = assets.filter((a) => a.calibration_health === 'OVERDUE' || a.due_status === 'EXPIRED').length;

  const todayWorkList = jobs.slice(0, 5);
  const upcomingCalibrations = assets.slice(0, 4);

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'RUNNING':
      case 'IN_PROGRESS':
        return <span className="bg-[#E0F2FE] text-[#0284C7] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">RUNNING</span>;
      case 'REVIEW':
      case 'REVIEW_REQUIRED':
      case 'READY_FOR_APPROVAL':
        return <span className="bg-[#FEF3C7] text-[#D97706] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">REVIEW</span>;
      case 'READY':
      case 'NEW':
        return <span className="bg-[#F1F5F9] text-[#475569] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">READY</span>;
      case 'APPROVED':
      case 'RELEASED':
        return <span className="bg-[#DCFCE7] text-[#16A34A] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">APPROVED</span>;
      default:
        return <span className="bg-[#F1F5F9] text-[#475569] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">{status}</span>;
    }
  };

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-y-auto custom-scrollbar p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-[#E2E5E9] gap-4">
        <div>
          <h1 className="text-xl font-bold text-[#17191C] tracking-tight">
            Calibration Operations
          </h1>
          <p className="text-xs text-[#656B73] mt-0.5 font-medium">
            Tuesday, September 3, 2026 &bull; Chennai Calibration Lab &bull; Station 04
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-medium rounded shadow-xs transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#656B73] ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Feed</span>
          </button>
          <button
            onClick={() => setActiveWorkspace('jobs')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded shadow-xs hover:bg-[#003348] transition-colors cursor-pointer"
          >
            <Inbox className="w-3.5 h-3.5" />
            <span>Job Hub</span>
          </button>
        </div>
      </div>

      {/* Guided Evaluation Hub (Demo Mode Only) */}
      {isDemo && (
        <div className="mt-5 p-5 bg-gradient-to-br from-[#00435F]/5 via-amber-500/5 to-transparent border-2 border-[#00435F]/20 rounded-xl space-y-4 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-[#00435F]/15">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#00435F] text-white flex items-center justify-center shrink-0 shadow-xs">
                <Sparkles className="w-4 h-4 text-amber-300" />
              </div>
              <div>
                <h2 className="font-bold text-sm text-[#0F172A] tracking-tight">
                  Guided Evaluation Mode &mdash; How CALIBRA Works in 3 Steps
                </h2>
                <p className="text-[11.5px] text-[#64748B]">
                  Explore the 50-digit arbitrary precision kernel, uncertainty propagation, and official certificate generation.
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsUpgradeModalOpen(true)}
              className="px-3.5 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white font-semibold text-xs rounded-lg shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer shrink-0"
            >
              <span>Compare Editions &amp; Upgrade ↗</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Step 1: Exact Math Engine */}
            <div
              onClick={() => setActiveWorkspace('uncertainty')}
              className="p-3.5 bg-white border border-[#CBD5E1] hover:border-[#00435F] rounded-lg transition-all cursor-pointer group shadow-2xs hover:shadow-xs space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase text-[#00435F] bg-[#EBF3F6] px-1.5 py-0.5 rounded">
                  STEP 1: UNCERTAINTY
                </span>
                <Calculator className="w-4 h-4 text-[#00435F] group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-bold text-xs text-[#0F172A] group-hover:text-[#00435F]">
                Inspect 50-Digit GUM Budget
              </h3>
              <p className="text-[11px] text-[#64748B] leading-relaxed">
                Experience JCGM 100:2008 Type A repeatability and Type B sensitivity calculations with zero floating-point cancellation errors.
              </p>
              <div className="text-[11px] text-[#00435F] font-semibold flex items-center gap-1 pt-1">
                <span>Open Uncertainty Budget</span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>

            {/* Step 2: Monte Carlo Simulation */}
            <div
              onClick={() => setActiveWorkspace('monte-carlo')}
              className="p-3.5 bg-white border border-[#CBD5E1] hover:border-[#00435F] rounded-lg transition-all cursor-pointer group shadow-2xs hover:shadow-xs space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase text-[#00435F] bg-[#EBF3F6] px-1.5 py-0.5 rounded">
                  STEP 2: SIMULATION
                </span>
                <ShieldCheck className="w-4 h-4 text-[#00435F] group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-bold text-xs text-[#0F172A] group-hover:text-[#00435F]">
                Run Monte Carlo (100k Draws)
              </h3>
              <p className="text-[11px] text-[#64748B] leading-relaxed">
                Propagate non-linear statistical distributions according to JCGM 101:2008 to compute coverage intervals.
              </p>
              <div className="text-[11px] text-[#00435F] font-semibold flex items-center gap-1 pt-1">
                <span>Launch Monte Carlo Studio</span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>

            {/* Step 3: Certificate Preview */}
            <div
              onClick={() => setActiveWorkspace('reports')}
              className="p-3.5 bg-white border border-[#CBD5E1] hover:border-[#00435F] rounded-lg transition-all cursor-pointer group shadow-2xs hover:shadow-xs space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase text-[#00435F] bg-[#EBF3F6] px-1.5 py-0.5 rounded">
                  STEP 3: CERTIFICATES
                </span>
                <FileBarChart className="w-4 h-4 text-[#00435F] group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-bold text-xs text-[#0F172A] group-hover:text-[#00435F]">
                Preview Watermarked Certificate
              </h3>
              <p className="text-[11px] text-[#64748B] leading-relaxed">
                Inspect official 4-page ISO/IEC 17025 certificate formatting. Learn why accredited labs upgrade to remove watermarks.
              </p>
              <div className="text-[11px] text-[#00435F] font-semibold flex items-center gap-1 pt-1">
                <span>Inspect Certificate Preview</span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {/* DUE TODAY */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
              DUE TODAY
            </span>
            <span className="bg-[#FEE2E2] text-[#DC2626] font-mono text-[10.5px] font-semibold px-2 py-0.5 rounded">
              {overdueCount} overdue
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-[#17191C] font-mono tabular-nums">
              {dueCount}
            </span>
            <span className="text-xs text-[#656B73]">calibrations scheduled</span>
          </div>
        </div>

        {/* AWAITING REVIEW */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
              AWAITING REVIEW
            </span>
            <span className="bg-[#FEF3C7] text-[#D97706] font-mono text-[10.5px] font-semibold px-2 py-0.5 rounded">
              1 high priority
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-[#17191C] font-mono tabular-nums">
              {reviewCount}
            </span>
            <span className="text-xs text-[#656B73]">jobs pending sign-off</span>
          </div>
        </div>

        {/* ACTIVE RUNS */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
              ACTIVE RUNS
            </span>
            <span className="bg-[#E0F2FE] text-[#0284C7] font-mono text-[10.5px] font-semibold px-2 py-0.5 rounded">
              1 paused
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-[#17191C] font-mono tabular-nums">
              {activeCount}
            </span>
            <span className="text-xs text-[#656B73]">benches executing</span>
          </div>
        </div>
      </div>

      {/* Main Split: Today's Work & Right Panel (Exceptions + Upcoming) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Left: TODAY'S WORK (2 Cols) */}
        <div className="lg:col-span-2 bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden flex flex-col">
          <div className="p-4 border-b border-[#E2E5E9] flex items-center justify-between bg-[#FAFAFA]">
            <div>
              <h2 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                TODAY'S WORK
              </h2>
              <p className="text-[11px] text-[#656B73] mt-0.5">Active calibration work orders on the floor</p>
            </div>
            <button
              onClick={() => setActiveWorkspace('jobs')}
              className="text-xs text-[#00435F] hover:underline flex items-center gap-1 font-medium cursor-pointer"
            >
              <span>View all jobs</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F8FA] border-b border-[#E2E5E9] text-[#656B73] font-semibold">
                <tr>
                  <th className="py-2.5 px-3.5 font-medium">Job ID</th>
                  <th className="py-2.5 px-3.5 font-medium">Asset Under Test</th>
                  <th className="py-2.5 px-3.5 font-medium">Procedure</th>
                  <th className="py-2.5 px-3.5 font-medium">Status</th>
                  <th className="py-2.5 px-3.5 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E5E9]">
                {todayWorkList.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-xs text-[#656B73]">
                      No active calibration jobs found. Click "New Job" or visit Job Hub to schedule work orders.
                    </td>
                  </tr>
                ) : (
                  todayWorkList.map((j) => (
                    <tr key={j.id} className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-2.5 px-3.5 font-mono font-semibold text-[#00435F]">
                      {j.job_number || j.id}
                    </td>
                    <td className="py-2.5 px-3.5">
                      <div className="font-medium text-[#17191C]">{j.instrument_name || 'Precision Multimeter'}</div>
                      <div className="text-[10.5px] font-mono text-[#656B73]">SN: {j.instrument_serial || 'Not recorded'}</div>
                    </td>
                    <td className="py-2.5 px-3.5 text-[#17191C]">
                      {j.title || 'Standard DC Voltage Calibration'}
                    </td>
                    <td className="py-2.5 px-3.5">
                      {getStatusBadge(j.status)}
                    </td>
                    <td className="py-2.5 px-3.5 text-right">
                      <button
                        onClick={() => {
                          setSelectedJob(j);
                          setActiveWorkspace('job-workflow');
                        }}
                        className="px-2.5 py-1 text-[11px] font-semibold text-[#00435F] bg-[#EBF3F6] hover:bg-[#D5E6EC] rounded transition-colors cursor-pointer"
                      >
                        {j.status === 'REVIEW' ? 'Review' : j.status === 'RUNNING' ? 'Cockpit' : 'Start'}
                      </button>
                    </td>
                  </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Exceptions + Upcoming */}
        <div className="space-y-6">
          {/* RECENT EXCEPTIONS */}
          <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden">
            <div className="p-3.5 border-b border-[#E2E5E9] flex items-center justify-between bg-[#FAFAFA]">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-[#DC2626]" />
                <h2 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                  RECENT EXCEPTIONS
                </h2>
              </div>
              <button
                onClick={() => setActiveWorkspace('exception-center')}
                className="text-[11px] text-[#00435F] hover:underline font-medium cursor-pointer"
              >
                Center
              </button>
            </div>

            <div className="divide-y divide-[#E2E5E9]">
              {recentExceptions.map((exc) => (
                <div
                  key={exc.id}
                  onClick={() => setActiveWorkspace('exception-center')}
                  className="p-3 hover:bg-[#F9FAFB] cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold text-[#DC2626]">
                      {exc.code}
                    </span>
                    <span className="text-[10px] font-mono text-[#656B73]">{exc.time}</span>
                  </div>
                  <div className="text-xs font-medium text-[#17191C] mt-0.5">{exc.title}</div>
                  <div className="text-[10.5px] text-[#656B73] mt-0.5 line-clamp-1">{exc.detail}</div>
                </div>
              ))}
            </div>
          </div>

          {/* UPCOMING CALIBRATIONS */}
          <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden">
            <div className="p-3.5 border-b border-[#E2E5E9] flex items-center justify-between bg-[#FAFAFA]">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-[#00435F]" />
                <h2 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                  UPCOMING CALIBRATIONS
                </h2>
              </div>
              <button
                onClick={() => setActiveWorkspace('assets')}
                className="text-[11px] text-[#00435F] hover:underline font-medium cursor-pointer"
              >
                Assets
              </button>
            </div>

            <div className="divide-y divide-[#E2E5E9]">
              {upcomingCalibrations.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#656B73]">
                  No upcoming asset calibration deadlines.
                </div>
              ) : (
                upcomingCalibrations.map((item, idx) => (
                  <div key={idx} className="p-3 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-mono font-semibold text-[#17191C]">{item.asset_tag || item.tag || item.id}</div>
                      <div className="text-[10.5px] text-[#656B73]">{item.model || item.name || 'Standard Unit'}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-[#17191C]">{item.due || item.next_calibration_due || 'Scheduled'}</div>
                      <span
                        className={`inline-block text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                          item.isUrgent || item.due_status === 'EXPIRED'
                            ? 'bg-[#FEE2E2] text-[#DC2626]'
                            : 'bg-[#F1F5F9] text-[#656B73]'
                        }`}
                      >
                        {item.status || item.due_status || 'Active'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

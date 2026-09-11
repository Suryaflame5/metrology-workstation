import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Clock,
  CheckCircle2,
  X,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

interface ExceptionItem {
  id: string;
  code: string;
  title: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  jobId: string;
  assetTag: string;
  step: string;
  observed: string;
  limit: string;
  time: string;
  details: string;
}

export const ExceptionCenterWorkspace: React.FC = () => {
  const { setActiveWorkspace, setSelectedJob, syncJobData } = useMetrology();
  const [selectedException, setSelectedException] = useState<ExceptionItem | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchExceptions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterSeverity !== 'ALL') {
        params.append('filter_severity', filterSeverity === 'HIGH' ? 'CRITICAL' : (filterSeverity === 'MEDIUM' ? 'WARNING' : 'OK'));
      }
      if (searchQuery) {
        params.append('search', searchQuery);
      }
      const res = await fetch(`/api/v8/exceptions?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to load exceptions');
      const data = await res.json();
      const feed = data.feed || [];
      const mapped: ExceptionItem[] = feed.map((item: any) => ({
        id: item.job_id,
        code: item.job_number || item.job_id,
        title: item.primary_reason || 'Quality Assessment Flag',
        severity: item.severity === 'CRITICAL' ? 'HIGH' : (item.severity === 'WARNING' ? 'MEDIUM' : 'LOW'),
        jobId: item.job_number || item.job_id,
        assetTag: item.instrument || 'UUT Standard',
        step: item.action_required || 'Inspect Verification Profile',
        observed: item.verdict || (item.tur ? `TUR: ${item.tur.toFixed(2)}` : 'FLAGGED'),
        limit: 'Guardband Method 6 (ISO 14253-1)',
        time: item.created_at ? new Date(item.created_at).toLocaleTimeString() : 'Active',
        details: item.reasons?.join(' • ') || item.primary_reason || 'Conformity or statistical anomaly flagged for human evaluation.',
      }));
      setExceptions(mapped);
    } catch (err) {
      console.error('Error fetching exceptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, [filterSeverity, searchQuery]);

  const filteredExceptions = exceptions;

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-hidden">
      {/* Top Header */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-lg font-bold text-[#17191C] tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-[#DC2626]" />
            <span>Exception Center</span>
          </h1>
          <p className="text-xs text-[#656B73]">
            Operational quality exceptions, out-of-tolerance events, communication drops, and environmental anomalies
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-white border border-[#E2E5E9] rounded px-2.5 py-1.5 font-medium outline-none focus:border-[#00435F] cursor-pointer"
          >
            <option value="ALL">All Severities</option>
            <option value="HIGH">High Severity</option>
            <option value="MEDIUM">Medium Severity</option>
            <option value="LOW">Low Severity</option>
          </select>
        </div>
      </div>

      {/* Main List & Drawer Container */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Table list */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
          <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F8FA] border-b border-[#E2E5E9] text-[#656B73] font-semibold">
                <tr>
                  <th className="py-2.5 px-3.5 font-medium">Severity</th>
                  <th className="py-2.5 px-3.5 font-medium">Code</th>
                  <th className="py-2.5 px-3.5 font-medium">Exception Summary</th>
                  <th className="py-2.5 px-3.5 font-medium">Job ID</th>
                  <th className="py-2.5 px-3.5 font-medium">Asset</th>
                  <th className="py-2.5 px-3.5 font-medium">Time</th>
                  <th className="py-2.5 px-3.5 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E5E9]">
                {filteredExceptions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <CheckCircle2 className="w-8 h-8 text-[#16A34A] mb-2" />
                        <span className="font-semibold text-sm text-[#17191C]">
                          Zero Exceptions Detected
                        </span>
                        <span className="text-xs text-[#656B73] mt-1 max-w-sm">
                          All laboratory instruments, measurement series, and conformity guardbands are within acceptable statistical limits.
                        </span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredExceptions.map((exc) => (
                    <tr
                      key={exc.id}
                      onClick={() => setSelectedException(exc)}
                      className="hover:bg-[#F9FAFB] cursor-pointer transition-colors"
                    >
                    <td className="py-3 px-3.5">
                      <span
                        className={`inline-block text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                          exc.severity === 'HIGH'
                            ? 'bg-[#FEE2E2] text-[#DC2626]'
                            : exc.severity === 'MEDIUM'
                            ? 'bg-[#FEF3C7] text-[#D97706]'
                            : 'bg-[#E0F2FE] text-[#0284C7]'
                        }`}
                      >
                        {exc.severity}
                      </span>
                    </td>
                    <td className="py-3 px-3.5 font-mono font-bold text-[#17191C]">
                      {exc.code}
                    </td>
                    <td className="py-3 px-3.5">
                      <div className="font-semibold text-[#17191C]">{exc.title}</div>
                      <div className="text-[10.5px] text-[#656B73] line-clamp-1">{exc.details}</div>
                    </td>
                    <td className="py-3 px-3.5 font-mono font-semibold text-[#00435F]">
                      {exc.jobId}
                    </td>
                    <td className="py-3 px-3.5 font-mono text-[#17191C]">
                      {exc.assetTag}
                    </td>
                    <td className="py-3 px-3.5 font-mono text-[#656B73]">
                      {exc.time}
                    </td>
                    <td className="py-3 px-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedException(exc);
                        }}
                        className="px-2.5 py-1 bg-[#EBF3F6] hover:bg-[#D5E6EC] text-[#00435F] text-[11px] font-semibold rounded cursor-pointer"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Action Drawer (21st.dev Drawer Pattern) */}
        {selectedException && (
          <div className="w-96 border-l border-[#E2E5E9] bg-white shadow-2xl flex flex-col shrink-0 z-20">
            <div className="p-4 border-b border-[#E2E5E9] bg-[#F7F8FA] flex items-center justify-between">
              <div>
                <span
                  className={`text-[10px] font-mono font-bold uppercase px-1.5 py-0.2 rounded ${
                    selectedException.severity === 'HIGH'
                      ? 'bg-[#FEE2E2] text-[#DC2626]'
                      : selectedException.severity === 'MEDIUM'
                      ? 'bg-[#FEF3C7] text-[#D97706]'
                      : 'bg-[#E0F2FE] text-[#0284C7]'
                  }`}
                >
                  {selectedException.severity} SEVERITY
                </span>
                <h2 className="text-sm font-bold text-[#17191C] mt-1">
                  {selectedException.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedException(null)}
                className="p-1 hover:bg-[#E2E5E9] rounded text-[#656B73] hover:text-[#17191C]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex-1 overflow-y-auto custom-scrollbar space-y-4 text-xs">
              <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] space-y-2">
                <div className="flex justify-between">
                  <span className="text-[#656B73]">Job ID:</span>
                  <span className="font-mono font-bold text-[#00435F]">{selectedException.jobId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#656B73]">Asset Under Test:</span>
                  <span className="font-mono font-bold text-[#17191C]">{selectedException.assetTag}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#656B73]">Step:</span>
                  <span className="font-semibold text-[#17191C]">{selectedException.step}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-[#FEE2E2] border border-[#FCA5A5] rounded">
                  <span className="text-[10.5px] font-bold text-[#DC2626] uppercase block">Observed Value</span>
                  <span className="text-base font-extrabold font-mono text-[#DC2626] mt-1 block">
                    {selectedException.observed}
                  </span>
                </div>
                <div className="p-3 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
                  <span className="text-[10.5px] font-bold text-[#656B73] uppercase block">Limit / Spec</span>
                  <span className="text-base font-bold font-mono text-[#17191C] mt-1 block">
                    {selectedException.limit}
                  </span>
                </div>
              </div>

              <div>
                <span className="font-semibold text-[#17191C] block mb-1">Diagnostic Detail</span>
                <p className="text-[#656B73] leading-relaxed bg-[#FAFAFA] p-3 rounded border border-[#E2E5E9]">
                  {selectedException.details}
                </p>
              </div>

              <div className="pt-2">
                <span className="font-bold text-[11px] text-[#17191C] uppercase tracking-wider block mb-2">
                  Required Action
                </span>
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      alert(`Investigation initiated for ${selectedException.code}.`);
                      setSelectedException(null);
                    }}
                    className="w-full py-2 px-3 bg-[#00435F] hover:bg-[#003348] text-white font-semibold rounded shadow-xs cursor-pointer text-xs"
                  >
                    Investigate & Open Diagnostics
                  </button>
                  <button
                    onClick={() => {
                      alert(`Repeating measurement for step ${selectedException.step}.`);
                      setSelectedException(null);
                    }}
                    className="w-full py-2 px-3 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] font-semibold rounded shadow-xs cursor-pointer text-xs"
                  >
                    Repeat Measurement
                  </button>
                  <button
                    onClick={() => {
                      alert(`Quality deviation ticket created for ${selectedException.jobId}.`);
                      setSelectedException(null);
                    }}
                    className="w-full py-2 px-3 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] font-semibold rounded shadow-xs cursor-pointer text-xs"
                  >
                    Create Deviation Form
                  </button>
                  <button
                    onClick={() => {
                      alert(`Escalated ${selectedException.code} to Quality Director.`);
                      setSelectedException(null);
                    }}
                    className="w-full py-2 px-3 bg-[#FEE2E2] hover:bg-[#FCD34D] text-[#DC2626] font-semibold rounded border border-[#FCA5A5] cursor-pointer text-xs"
                  >
                    Escalate to Quality Lead
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

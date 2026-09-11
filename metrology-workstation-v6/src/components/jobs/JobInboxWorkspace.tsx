import React, { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  Filter,
  RefreshCw,
  ArrowUpDown,
  CheckCircle2,
  AlertCircle,
  Clock,
  Play,
  FileText,
  Copy,
  ChevronRight,
  Inbox,
  Calendar,
  User,
} from 'lucide-react';
import {
  fetchJobs,
  createJob,
  duplicateJob,
  getCertificatePdfUrl,
} from '../../services/jobApi';
import { MeasurementJob } from '../../types/job';
import { useMetrology } from '../../context/MetrologyContext';

interface JobInboxProps {
  onSelectJob: (job: MeasurementJob) => void;
}

export const JobInboxWorkspace: React.FC<JobInboxProps> = ({ onSelectJob }) => {
  const { setSelectedJob } = useMetrology();
  const [jobs, setJobs] = useState<MeasurementJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter controls
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [technicianFilter, setTechnicianFilter] = useState<string>('ALL');

  // New Job Modal
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState('EURAMET cg-15 DC Voltage 10 V');
  const [newCustomer, setNewCustomer] = useState('');
  const [newInstName, setNewInstName] = useState('Digital Multimeter');
  const [newInstModel, setNewInstModel] = useState('Fluke 8846A');
  const [newInstSerial, setNewInstSerial] = useState('');
  const [newProcedure, setNewProcedure] = useState('EURAMET cg-15');
  const [newUnit, setNewUnit] = useState('V');
  const [newNominal, setNewNominal] = useState('10.0');
  const [newTolUpper, setNewTolUpper] = useState('0.0010');
  const [newTolLower, setNewTolLower] = useState('-0.0010');

  const loadJobsList = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJobs(statusFilter, searchQuery);
      setJobs(data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobsList();
  }, [statusFilter, searchQuery]);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createJob({
        title: newTitle,
        customer_name: newCustomer.trim() || undefined,
        instrument_name: newInstName,
        instrument_model: newInstModel,
        instrument_serial: newInstSerial.trim() || undefined,
        procedure_name: newProcedure,
        unit: newUnit,
        nominal_value: parseFloat(newNominal) || 10.0,
        tolerance_upper: parseFloat(newTolUpper) || 0.001,
        tolerance_lower: parseFloat(newTolLower) || -0.001,
        status: 'NEW',
        raw_measurements: [],
      });
      setShowNewModal(false);
      await loadJobsList();
      setSelectedJob(created);
      onSelectJob(created);
    } catch (err: any) {
      alert(`Could not create job: ${err.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'RUNNING':
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1 bg-[#E0F2FE] text-[#0284C7] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-[#0284C7] animate-pulse"></span>
            RUNNING
          </span>
        );
      case 'REVIEW':
      case 'REVIEW_REQUIRED':
      case 'READY_FOR_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1 bg-[#FEF3C7] text-[#D97706] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">
            <Clock className="w-3 h-3" />
            REVIEW
          </span>
        );
      case 'APPROVED':
      case 'RELEASED':
      case 'COMPLETE':
        return (
          <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#16A34A] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">
            <CheckCircle2 className="w-3 h-3" />
            COMPLETE
          </span>
        );
      case 'FAILED':
      case 'OUT_OF_TOLERANCE':
        return (
          <span className="inline-flex items-center gap-1 bg-[#FEE2E2] text-[#DC2626] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">
            <AlertCircle className="w-3 h-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 bg-[#F1F5F9] text-[#475569] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">
            READY
          </span>
        );
    }
  };

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-hidden">
      {/* Top Header */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-lg font-bold text-[#17191C] tracking-tight flex items-center gap-2">
            <Inbox className="w-5 h-5 text-[#00435F]" />
            <span>Calibration Jobs</span>
          </h1>
          <p className="text-xs text-[#656B73]">
            Active calibration work orders, customer equipment intakes, and verification workflows
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadJobsList}
            disabled={loading}
            className="p-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] rounded shadow-xs transition-colors cursor-pointer"
            title="Refresh jobs table"
          >
            <RefreshCw className={`w-4 h-4 text-[#656B73] ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Create Job</span>
          </button>
        </div>
      </div>

      {/* Filter Bar (21st.dev Data Table pattern) */}
      <div className="p-3 bg-[#FAFAFA] border-b border-[#E2E5E9] flex flex-wrap items-center justify-between gap-2 shrink-0 text-xs">
        <div className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#656B73]" />
            <input
              type="text"
              placeholder="Search jobs by ID, asset, customer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-[#E2E5E9] rounded text-xs text-[#17191C] placeholder-[#656B73] outline-none focus:border-[#00435F]"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-[#E2E5E9] rounded px-2.5 py-1.5 text-xs text-[#17191C] outline-none focus:border-[#00435F] cursor-pointer font-medium"
          >
            <option value="ALL">Status: All</option>
            <option value="RUNNING">Status: Running</option>
            <option value="REVIEW_REQUIRED">Status: Review</option>
            <option value="NEW">Status: Ready</option>
            <option value="APPROVED">Status: Complete</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-white border border-[#E2E5E9] rounded px-2.5 py-1.5 text-xs text-[#17191C] outline-none focus:border-[#00435F] cursor-pointer font-medium"
          >
            <option value="ALL">Priority: All</option>
            <option value="HIGH">Priority: High</option>
            <option value="NORMAL">Priority: Normal</option>
          </select>

          {/* Technician Filter */}
          <select
            value={technicianFilter}
            onChange={(e) => setTechnicianFilter(e.target.value)}
            className="bg-white border border-[#E2E5E9] rounded px-2.5 py-1.5 text-xs text-[#17191C] outline-none focus:border-[#00435F] cursor-pointer font-medium"
          >
            <option value="ALL">Technician: All</option>
            <option value="MARCUS">Marcus Brody</option>
            <option value="S_KUMAR">S. Kumar</option>
          </select>
        </div>
      </div>

      {/* Main Table Area */}
      <div className="flex-1 overflow-auto custom-scrollbar p-4">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#656B73]">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-[#00435F]" />
            <span>Loading calibration jobs from database...</span>
          </div>
        ) : jobs.length === 0 ? (
          <div className="bg-white border border-[#E2E5E9] rounded-lg p-12 text-center shadow-xs max-w-md mx-auto mt-8">
            <Inbox className="w-10 h-10 text-[#656B73] mx-auto mb-3" />
            <h2 className="text-sm font-bold text-[#17191C]">No calibration jobs yet</h2>
            <p className="text-xs text-[#656B73] mt-1 mb-4">
              Create a job to begin your first calibration.
            </p>
            <button
              onClick={() => setShowNewModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Job</span>
            </button>
          </div>
        ) : (
          <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[#F7F8FA] border-b border-[#E2E5E9] text-[#656B73] font-semibold select-none">
                <tr>
                  <th className="py-3 px-3.5 font-medium">Job ID</th>
                  <th className="py-3 px-3.5 font-medium">Asset Under Test</th>
                  <th className="py-3 px-3.5 font-medium">Procedure</th>
                  <th className="py-3 px-3.5 font-medium">Customer</th>
                  <th className="py-3 px-3.5 font-medium">Status</th>
                  <th className="py-3 px-3.5 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E5E9]">
                {jobs.map((job) => {
                  const displayId = job.job_number || job.id;
                  const displayCustomer = job.customer_name || 'No customer assigned';
                  const serialText = job.instrument_serial ? `SN: ${job.instrument_serial}` : 'Serial: Not recorded';

                  return (
                    <tr
                      key={job.id}
                      onClick={() => {
                        setSelectedJob(job);
                        onSelectJob(job);
                      }}
                      className="hover:bg-[#F9FAFB] cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-3.5 font-mono font-semibold text-[#00435F]">
                        {displayId}
                      </td>
                      <td className="py-3 px-3.5">
                        <div className="font-semibold text-[#17191C]">
                          {job.instrument_model || job.instrument_name || 'Precision Instrument'}
                        </div>
                        <div className="text-[10.5px] font-mono text-[#656B73]">{serialText}</div>
                      </td>
                      <td className="py-3 px-3.5">
                        <div className="font-medium text-[#17191C]">{job.procedure_name || job.title}</div>
                        <div className="text-[10.5px] text-[#656B73]">
                          Nominal: {job.nominal_value ?? '10.0'} {job.unit || 'V'}
                        </div>
                      </td>
                      <td className="py-3 px-3.5">
                        <span className={job.customer_name ? 'text-[#17191C] font-medium' : 'text-[#656B73] italic'}>
                          {displayCustomer}
                        </span>
                      </td>
                      <td className="py-3 px-3.5">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="py-3 px-3.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedJob(job);
                            onSelectJob(job);
                          }}
                          className="px-2.5 py-1 bg-[#EBF3F6] hover:bg-[#D5E6EC] text-[#00435F] text-[11px] font-semibold rounded transition-colors cursor-pointer inline-flex items-center gap-1"
                        >
                          <span>Open</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Job Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-2xl max-w-lg w-full overflow-hidden flex flex-col">
            <div className="p-3.5 border-b border-[#E2E5E9] bg-[#F7F8FA] flex items-center justify-between">
              <div className="font-bold text-sm text-[#17191C]">Create Calibration Job</div>
              <button
                onClick={() => setShowNewModal(false)}
                className="text-[#656B73] hover:text-[#17191C] text-xs font-semibold p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateJob} className="p-4 space-y-3.5 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                  Job / Procedure Title
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded outline-none focus:border-[#00435F]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Customer (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Leave blank if internal standard"
                    value={newCustomer}
                    onChange={(e) => setNewCustomer(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded outline-none focus:border-[#00435F]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Serial Number (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. SN-8846-9921"
                    value={newInstSerial}
                    onChange={(e) => setNewInstSerial(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded outline-none focus:border-[#00435F]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Instrument Model
                  </label>
                  <input
                    type="text"
                    required
                    value={newInstModel}
                    onChange={(e) => setNewInstModel(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded outline-none focus:border-[#00435F]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Procedure Reference
                  </label>
                  <input
                    type="text"
                    required
                    value={newProcedure}
                    onChange={(e) => setNewProcedure(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded outline-none focus:border-[#00435F]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Nominal Value
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={newNominal}
                    onChange={(e) => setNewNominal(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Tolerance (±)
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={newTolUpper}
                    onChange={(e) => setNewTolUpper(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#17191C] mb-1">
                    Unit
                  </label>
                  <input
                    type="text"
                    required
                    value={newUnit}
                    onChange={(e) => setNewUnit(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-[#E2E5E9] rounded font-mono"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-[#E2E5E9] flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-3 py-1.5 border border-[#E2E5E9] text-[#17191C] rounded hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-[#00435F] text-white rounded font-semibold hover:bg-[#003348]"
                >
                  Create & Launch Job
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from "react";
import {
  FolderGit2,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  Layers,
  ArrowRight,
  RefreshCw,
  Building2,
  User,
  Calendar,
  ShieldCheck,
  ChevronRight,
  Filter,
} from "lucide-react";
import { useMetrology } from "../../context/MetrologyContext";

interface Project {
  id: string;
  name: string;
  description: string;
  customer_site: string;
  status: "DRAFT" | "PLANNING" | "IN_PROGRESS" | "REVIEW" | "COMPLETED" | "ARCHIVED";
  created_at: string;
  updated_at: string;
  metadata?: {
    lead_metrologist?: string;
    target_standard?: string;
    due_date?: string;
  };
  metrics?: {
    total_jobs: number;
    completed_jobs: number;
    in_progress_jobs: number;
    completion_pct: number;
  };
}

export const ProjectsWorkspace: React.FC = () => {
  const { setActiveWorkspace } = useMetrology();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [showNewModal, setShowNewModal] = useState(false);

  // New Project Form
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [customerSite, setCustomerSite] = useState("");
  const [leadMetrologist, setLeadMetrologist] = useState("Marcus Brody");
  const [targetStandard, setTargetStandard] = useState("ISO/IEC 17025:2017");
  const [dueDate, setDueDate] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const q = statusFilter !== "ALL" ? `?status=${statusFilter}` : "";
      const res = await fetch(`/api/v1/projects${q}`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      }
    } catch {
      // Silent error handling
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [statusFilter]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      const res = await fetch("/api/v1/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          customer_site: customerSite,
          lead_metrologist: leadMetrologist,
          target_standard: targetStandard,
          due_date: dueDate || null,
        }),
      });

      if (res.ok) {
        setShowNewModal(false);
        setName("");
        setDescription("");
        setCustomerSite("");
        setDueDate("");
        fetchProjects();
      }
    } catch {
      // Silent error handling
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (projectId: string, newStatus: string) => {
    try {
      const res = await fetch(`/api/v1/projects/${projectId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus, operator: "Marcus Brody" }),
      });
      if (res.ok) {
        fetchProjects();
      }
    } catch {
      // Silent error handling
    }
  };

  const filteredProjects = projects.filter((p) => {
    const q = search.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      p.id.toLowerCase().includes(q) ||
      p.customer_site.toLowerCase().includes(q)
    );
  });

  const getStatusColor = (st: string) => {
    switch (st) {
      case "COMPLETED":
        return "bg-[#F0FDF4] text-[#16A34A] border-[#BBF7D0]";
      case "IN_PROGRESS":
        return "bg-[#E0F2FE] text-[#0284C7] border-[#BAE6FD]";
      case "REVIEW":
        return "bg-[#FEF3C7] text-[#D97706] border-[#FDE68A]";
      case "PLANNING":
        return "bg-[#F3F4F6] text-[#475569] border-[#E2E8F0]";
      default:
        return "bg-[#F3F4F6] text-[#64748B] border-[#E2E8F0]";
    }
  };

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-hidden">
      {/* Top Header */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
              PROJECT LIFECYCLE
            </span>
            <span className="text-xs text-[#656B73]">Multi-Job Calibration Programs</span>
          </div>
          <h1 className="text-xl font-bold text-[#17191C] mt-1 tracking-tight">
            Engineering Projects & Campaigns
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNewModal(true)}
            className="px-3 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Project Workspace</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-wrap items-center justify-between gap-3 shrink-0 text-xs">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#656B73] absolute left-2.5 top-2.5" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search projects by name, ID or site..."
              className="pl-8 pr-3 py-1.5 bg-[#F7F8FA] border border-[#CBD5E1] rounded text-xs text-[#17191C] outline-none focus:border-[#00435F] w-64"
            />
          </div>

          <div className="flex items-center gap-1 border border-[#CBD5E1] rounded p-0.5 bg-[#F7F8FA]">
            {["ALL", "PLANNING", "IN_PROGRESS", "REVIEW", "COMPLETED"].map((tab) => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                  statusFilter === tab
                    ? "bg-white text-[#00435F] shadow-xs"
                    : "text-[#656B73] hover:text-[#17191C]"
                }`}
              >
                {tab.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={fetchProjects}
          className="p-1.5 hover:bg-[#F1F5F9] rounded text-[#656B73] cursor-pointer"
          title="Refresh projects"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Project Cards Grid */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        {filteredProjects.length === 0 ? (
          <div className="bg-white border border-[#E2E5E9] rounded-xl p-12 text-center max-w-md mx-auto mt-12">
            <FolderGit2 className="w-12 h-12 text-[#CBD5E1] mx-auto mb-3" />
            <h3 className="text-base font-bold text-[#17191C]">No Engineering Projects Found</h3>
            <p className="text-xs text-[#656B73] mt-1 mb-4">
              Create a project workspace to bundle multiple work orders, track milestone progress, and coordinate campaign calibration.
            </p>
            <button
              onClick={() => setShowNewModal(true)}
              className="px-4 py-2 bg-[#00435F] text-white text-xs font-semibold rounded shadow-xs hover:bg-[#003348] cursor-pointer"
            >
              Create First Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProjects.map((p) => {
              const metrics = p.metrics || { total_jobs: 0, completed_jobs: 0, in_progress_jobs: 0, completion_pct: 0 };
              const meta = p.metadata || {};

              return (
                <div
                  key={p.id}
                  className="bg-white border border-[#E2E5E9] rounded-xl p-5 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <span className="font-mono text-[11px] font-bold text-[#00435F]">
                          {p.id}
                        </span>
                        <h3 className="text-sm font-bold text-[#17191C] leading-snug mt-0.5">
                          {p.name}
                        </h3>
                      </div>
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${getStatusColor(
                          p.status
                        )}`}
                      >
                        {p.status}
                      </span>
                    </div>

                    <p className="text-xs text-[#656B73] line-clamp-2 mb-4">
                      {p.description || "No description provided."}
                    </p>

                    {/* Metadata Grid */}
                    <div className="space-y-1.5 text-xs text-[#656B73] mb-4 pb-4 border-b border-[#E2E5E9]">
                      {p.customer_site && (
                        <div className="flex items-center gap-2">
                          <Building2 className="w-3.5 h-3.5 text-[#00435F] shrink-0" />
                          <span className="truncate">{p.customer_site}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <User className="w-3.5 h-3.5 text-[#00435F] shrink-0" />
                        <span>Lead: <strong>{meta.lead_metrologist || "Marcus Brody"}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-3.5 h-3.5 text-[#00435F] shrink-0" />
                        <span className="truncate">{meta.target_standard || "ISO/IEC 17025"}</span>
                      </div>
                      {meta.due_date && (
                        <div className="flex items-center gap-2">
                          <Calendar className="w-3.5 h-3.5 text-[#00435F] shrink-0" />
                          <span>Target: {meta.due_date}</span>
                        </div>
                      )}
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="flex justify-between items-center text-xs mb-1">
                        <span className="text-[#656B73] font-medium">Work Order Progress</span>
                        <span className="font-mono font-bold text-[#00435F]">
                          {metrics.completion_pct}%
                        </span>
                      </div>
                      <div className="w-full bg-[#E2E5E9] rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-[#00435F] h-2 rounded-full transition-all duration-300"
                          style={{ width: `${metrics.completion_pct}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between text-[11px] text-[#656B73] mt-1 font-mono">
                        <span>{metrics.completed_jobs} completed</span>
                        <span>{metrics.total_jobs} total jobs</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-2 border-t border-[#E2E5E9] flex items-center justify-between gap-2 text-xs">
                    <select
                      value={p.status}
                      onChange={(e) => handleStatusChange(p.id, e.target.value)}
                      className="text-xs bg-[#F7F8FA] border border-[#CBD5E1] rounded px-2 py-1 font-semibold text-[#00435F] outline-none cursor-pointer"
                    >
                      <option value="PLANNING">Set: PLANNING</option>
                      <option value="IN_PROGRESS">Set: IN_PROGRESS</option>
                      <option value="REVIEW">Set: REVIEW</option>
                      <option value="COMPLETED">Set: COMPLETED</option>
                      <option value="ARCHIVED">Set: ARCHIVED</option>
                    </select>

                    <button
                      onClick={() => setActiveWorkspace("jobs")}
                      className="px-2.5 py-1 text-xs font-semibold text-[#00435F] hover:bg-[#EBF3F6] rounded flex items-center gap-1 cursor-pointer"
                    >
                      <span>View Jobs</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* New Project Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#E2E5E9] rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-4 border-b border-[#E2E5E9] bg-[#F7F8FA] flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#17191C]">Create New Project Workspace</h2>
              <button onClick={() => setShowNewModal(false)} className="text-[#656B73] hover:text-[#17191C]">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="p-5 space-y-4 text-xs">
              <div>
                <label className="font-semibold text-[#17191C] block mb-1">Project Name *</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Q4 Multimeter Accreditation Program"
                  className="w-full p-2 bg-[#F7F8FA] border border-[#CBD5E1] rounded font-medium text-[#17191C] outline-none focus:border-[#00435F]"
                />
              </div>

              <div>
                <label className="font-semibold text-[#17191C] block mb-1">Description</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Scope, objectives, and batch parameters..."
                  className="w-full p-2 bg-[#F7F8FA] border border-[#CBD5E1] rounded font-medium text-[#17191C] outline-none focus:border-[#00435F]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#17191C] block mb-1">Facility / Customer Site</label>
                  <input
                    value={customerSite}
                    onChange={(e) => setCustomerSite(e.target.value)}
                    placeholder="e.g. Plant 2, Bangalore"
                    className="w-full p-2 bg-[#F7F8FA] border border-[#CBD5E1] rounded text-[#17191C] outline-none focus:border-[#00435F]"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#17191C] block mb-1">Target Due Date</label>
                  <input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full p-2 bg-[#F7F8FA] border border-[#CBD5E1] rounded text-[#17191C] outline-none focus:border-[#00435F]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#17191C] block mb-1">Lead Metrologist</label>
                  <input
                    value={leadMetrologist}
                    onChange={(e) => setLeadMetrologist(e.target.value)}
                    className="w-full p-2 bg-[#F7F8FA] border border-[#CBD5E1] rounded text-[#17191C] outline-none focus:border-[#00435F]"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#17191C] block mb-1">Quality Standard</label>
                  <input
                    value={targetStandard}
                    onChange={(e) => setTargetStandard(e.target.value)}
                    className="w-full p-2 bg-[#F7F8FA] border border-[#CBD5E1] rounded text-[#17191C] outline-none focus:border-[#00435F]"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-[#E2E5E9] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-3 py-1.5 bg-white border border-[#CBD5E1] rounded text-xs font-semibold text-[#17191C]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded shadow-xs hover:bg-[#003348] disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

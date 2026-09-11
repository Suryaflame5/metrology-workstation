import React, { useState, useEffect } from "react";
import {
  Layers,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  Cpu,
  FileCheck,
} from "lucide-react";
import { useMetrology } from "../../context/MetrologyContext";

interface BatchJob {
  id: string;
  batch_number: string;
  title: string;
  procedure_template_id: string;
  procedure_name: string;
  operator: string;
  status: string;
  total_instruments: number;
  completed_count: number;
  passed_count: number;
  failed_count: number;
  review_required_count: number;
  job_ids?: string[];
  created_at?: string;
}

interface ProcedureTemplate {
  id: string;
  code: string;
  title: string;
  category: string;
  nominal_value: number;
  default_unit: string;
}

export const BatchProcessingWorkspace: React.FC = () => {
  const { setActiveWorkspace, setSelectedJobId } = useMetrology();
  const [batches, setBatches] = useState<BatchJob[]>([]);
  const [templates, setTemplates] = useState<ProcedureTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  // New batch form
  const [title, setTitle] = useState("Shop Floor Handheld DMM Fleet Batch #24");
  const [selectedTemplate, setSelectedTemplate] = useState("PROC-EURAMET-CG-15");
  const [fleetSize, setFleetSize] = useState(15);
  const [failSimRate, setFailSimRate] = useState(8);
  const [activeBatch, setActiveBatch] = useState<BatchJob | null>(null);

  const fetchBatchesAndTemplates = async () => {
    setLoading(true);
    try {
      const [resB, resT] = await Promise.all([
        fetch("/api/v8/batch").then((r) => r.json()),
        fetch("/api/v8/templates").then((r) => r.json()),
      ]);
      if (resB && resB.batches) {
        setBatches(resB.batches);
        if (resB.batches.length > 0 && !activeBatch) {
          setActiveBatch(resB.batches[0]);
        }
      }
      if (resT && resT.templates) {
        setTemplates(resT.templates);
      }
    } catch (e) {
      console.error("Error fetching batches:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatchesAndTemplates();
  }, []);

  const handleLaunchBatch = async () => {
    setRunning(true);
    try {
      const instruments = Array.from({ length: fleetSize }, (_, i) => ({
        serial: `SN-FLK-${1000 + i}`,
        model: "87V Handheld Multimeter",
        name: `Digital Multimeter Unit #${i + 1}`,
        customer: "Tesla Energy Metrology Lab",
      }));

      const res = await fetch("/api/v8/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          procedure_template_id: selectedTemplate,
          instruments,
          operator: "Marcus Reid (Metrology Tech)",
        }),
      });

      const data = await res.json();
      if (data && data.batch) {
        setActiveBatch(data.batch);
        fetchBatchesAndTemplates();
      }
    } catch (e) {
      console.error("Batch execution failed:", e);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto custom-scrollbar">
      {/* Header Banner */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-700">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                Batch Fleet Calibration Engine
              </h1>
              <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full font-mono">
                V8 HIGH-THROUGHPUT
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Automated multi-instrument calibration pipeline across 10–100+ units with unified ISO/EURAMET templates.
            </p>
          </div>
        </div>

        <button
          onClick={fetchBatchesAndTemplates}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-300 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Fleets
        </button>
      </div>

      {/* Main Grid */}
      <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Launch Panel */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <div className="flex items-center gap-2">
              <Play className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                Configure & Launch New Fleet Run
              </h2>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Auto-generates GUM budgets & ANSI Z540.3 decisions
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-2 space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Batch Run Description</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                placeholder="e.g. Lockheed Micrometer Inspection Batch #08"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Procedure Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden bg-white"
              >
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.code} — {t.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Fleet Quantity</label>
              <div className="flex items-center gap-2">
                {[10, 15, 25, 50].map((size) => (
                  <button
                    key={size}
                    onClick={() => setFleetSize(size)}
                    type="button"
                    className={`flex-1 py-1.5 text-xs font-bold rounded-md border transition cursor-pointer ${
                      fleetSize === size
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs text-slate-600">
              <span>Simulation Non-Conformance Rate:</span>
              <input
                type="range"
                min="0"
                max="25"
                value={failSimRate}
                onChange={(e) => setFailSimRate(Number(e.target.value))}
                className="w-28 accent-blue-600"
              />
              <span className="font-mono font-bold text-slate-800">{failSimRate}%</span>
            </div>

            <button
              onClick={handleLaunchBatch}
              disabled={running}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50"
            >
              {running ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Executing Fleet Pipeline ({fleetSize} Units)...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Launch Fleet Calibration ({fleetSize} Units)
                </>
              )}
            </button>
          </div>
        </div>

        {/* Active / Selected Batch Progress Card */}
        {activeBatch && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md">
                    {activeBatch.batch_number}
                  </span>
                  <h3 className="text-base font-bold text-slate-900">{activeBatch.title}</h3>
                </div>
                <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                  <span>Procedure: <strong className="text-slate-700">{activeBatch.procedure_name}</strong></span>
                  <span>•</span>
                  <span>Operator: <strong className="text-slate-700">{activeBatch.operator}</strong></span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {activeBatch.created_at ? new Date(activeBatch.created_at).toLocaleTimeString() : "Just now"}
                  </span>
                </div>
              </div>

              <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                activeBatch.status === "COMPLETED"
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : "bg-amber-100 text-amber-800 border border-amber-300"
              }`}>
                {activeBatch.status}
              </span>
            </div>

            {/* Metric Counters */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <div className="text-[11px] font-semibold text-slate-500 uppercase">Total Instruments</div>
                <div className="text-2xl font-bold text-slate-800 font-mono mt-1">
                  {activeBatch.total_instruments}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">100% Pipeline Ingested</div>
              </div>

              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                <div className="text-[11px] font-semibold text-emerald-700 uppercase flex items-center justify-between">
                  <span>Conforming (Pass)</span>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div className="text-2xl font-bold text-emerald-700 font-mono mt-1">
                  {activeBatch.passed_count}
                </div>
                <div className="text-[10px] text-emerald-600 mt-0.5">
                  {activeBatch.total_instruments > 0
                    ? `${Math.round((activeBatch.passed_count / activeBatch.total_instruments) * 100)}% Pass Yield`
                    : "0%"}
                </div>
              </div>

              <div className="bg-rose-50 border border-rose-200 rounded-lg p-3">
                <div className="text-[11px] font-semibold text-rose-700 uppercase flex items-center justify-between">
                  <span>Out of Tolerance</span>
                  <XCircle className="w-3.5 h-3.5" />
                </div>
                <div className="text-2xl font-bold text-rose-700 font-mono mt-1">
                  {activeBatch.failed_count}
                </div>
                <div className="text-[10px] text-rose-600 mt-0.5">Corrective Action Alert</div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <div className="text-[11px] font-semibold text-amber-700 uppercase flex items-center justify-between">
                  <span>Review Required</span>
                  <AlertTriangle className="w-3.5 h-3.5" />
                </div>
                <div className="text-2xl font-bold text-amber-700 font-mono mt-1">
                  {activeBatch.review_required_count}
                </div>
                <div className="text-[10px] text-amber-600 mt-0.5">Exception Center Triage</div>
              </div>
            </div>

            {/* Quick Actions Bar */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <div className="text-xs text-slate-500">
                Processed {activeBatch.completed_count} of {activeBatch.total_instruments} calibration jobs through full 6-stage mathematical engine.
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveWorkspace("exception-center")}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-amber-300 text-amber-800 bg-amber-50 hover:bg-amber-100 text-xs font-semibold cursor-pointer transition"
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  View Fleet Exceptions ({activeBatch.failed_count + activeBatch.review_required_count})
                </button>
                <button
                  onClick={() => setActiveWorkspace("jobs")}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold cursor-pointer transition"
                >
                  <span>Open Job Inbox</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Recent Batch Runs Table */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Batch Execution History ({batches.length} Runs)
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">
              Traceable records retained under ISO 17025 §7.8
            </span>
          </div>

          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                <th className="py-2.5 px-4">Batch ID</th>
                <th className="py-2.5 px-4">Title / Description</th>
                <th className="py-2.5 px-4">Procedure</th>
                <th className="py-2.5 px-4 text-center">Fleet</th>
                <th className="py-2.5 px-4 text-center">Passed</th>
                <th className="py-2.5 px-4 text-center">Failed</th>
                <th className="py-2.5 px-4 text-center">Exceptions</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {batches.map((b) => (
                <tr
                  key={b.id}
                  onClick={() => setActiveBatch(b)}
                  className={`hover:bg-slate-50 transition cursor-pointer ${
                    activeBatch?.id === b.id ? "bg-blue-50/50" : ""
                  }`}
                >
                  <td className="py-2.5 px-4 font-mono font-bold text-blue-700">{b.batch_number}</td>
                  <td className="py-2.5 px-4 font-medium text-slate-800">{b.title}</td>
                  <td className="py-2.5 px-4 text-slate-600 truncate max-w-xs">{b.procedure_name}</td>
                  <td className="py-2.5 px-4 text-center font-mono font-bold text-slate-700">{b.total_instruments}</td>
                  <td className="py-2.5 px-4 text-center font-mono font-bold text-emerald-600">{b.passed_count}</td>
                  <td className="py-2.5 px-4 text-center font-mono font-bold text-rose-600">{b.failed_count}</td>
                  <td className="py-2.5 px-4 text-center font-mono font-bold text-amber-600">{b.review_required_count}</td>
                  <td className="py-2.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-slate-100 text-slate-700">
                      {b.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveBatch(b);
                      }}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                    >
                      Select
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

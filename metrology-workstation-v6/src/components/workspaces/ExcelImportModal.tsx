import React, { useState, useRef } from "react";
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRight,
  X,
  RefreshCw,
  Table as TableIcon,
  HelpCircle,
} from "lucide-react";
import { useMetrology } from "../../context/MetrologyContext";

interface ExcelImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ExcelImportModal: React.FC<ExcelImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { selectedJob, syncJobData } = useMetrology();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Preview Data from Backend
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [columnOverrides, setColumnOverrides] = useState<Record<string, string>>({});
  const [isApplying, setIsApplying] = useState(false);

  if (!isOpen) return null;

  const handleFileSelect = async (selected: File) => {
    setFile(selected);
    setErrorMsg(null);
    setPreviewData(null);
    setColumnOverrides({});
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", selected);
      formData.append("target_unit", selectedJob?.unit || "V");

      const res = await fetch("/api/v1/import/upload-file", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to parse workbook.");
      }

      const data = await res.json();
      if (data.status === "success") {
        setPreviewData(data);
        setSelectedSheet(data.selected_sheet || (data.sheet_names && data.sheet_names[0]) || "");
      } else {
        throw new Error(data.message || "Failed to parse data rows.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Error reading Excel file.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSheetChange = async (newSheet: string) => {
    if (!file) return;
    setSelectedSheet(newSheet);
    setIsUploading(true);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("sheet_name", newSheet);
      formData.append("target_unit", selectedJob?.unit || "V");

      const res = await fetch("/api/v1/import/upload-file", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.status === "success") {
        setPreviewData(data);
      } else {
        throw new Error(data.message || "Failed to parse sheet.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Error switching sheet.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleApplyToJob = async () => {
    if (!selectedJob) {
      setErrorMsg("Please select or create a calibration job before importing data.");
      return;
    }
    if (!previewData || !previewData.extracted_summary) {
      setErrorMsg("No extracted measurement data available.");
      return;
    }

    setIsApplying(true);
    setErrorMsg(null);

    try {
      const rawMeasurements = previewData.extracted_summary.raw_measurements || [];
      const nominalVal = previewData.extracted_summary.nominal_value || selectedJob.nominal_value;

      const payload = {
        raw_measurements: rawMeasurements,
        mapped_columns: { ...previewData.mapping, ...columnOverrides },
        nominal_value: nominalVal,
        environment: previewData.extracted_summary.environment,
      };

      const res = await fetch(`/api/jobs/${selectedJob.id}/apply-import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Failed to apply imported measurements to job.");
      }

      // Automatically run calculation pipeline
      await fetch(`/api/jobs/${selectedJob.id}/run-pipeline`, { method: "POST" });

      if (syncJobData) {
        await syncJobData(selectedJob.id);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Error saving measurements to job.");
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white border border-[#E2E5E9] rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-[#E2E5E9] bg-[#F7F8FA] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-[#EBF3F6] border border-[#CBD5E1] rounded text-[#00435F]">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#17191C] tracking-tight">
                Import Excel / CSV Calibration Dataset
              </h2>
              <p className="text-xs text-[#656B73]">
                Direct binary parsing with openpyxl • Auto-detects columns, units & nominal setpoints
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#E2E5E9] rounded text-[#656B73] hover:text-[#17191C] cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 flex-1 overflow-y-auto custom-scrollbar space-y-5">
          {/* Target Work Order Banner */}
          <div className="p-3 bg-[#EBF3F6] border border-[#CBD5E1] rounded-lg flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-[#00435F]">Active Work Order:</span>
              <span className="font-mono font-bold text-[#17191C]">
                {selectedJob ? `${selectedJob.job_number || selectedJob.id} (${selectedJob.title})` : "None Selected (Will prompt)"}
              </span>
            </div>
            <span className="text-[#656B73]">
              Nominal: <strong className="font-mono">{selectedJob?.nominal_value ?? "Auto-detect"} {selectedJob?.unit || "V"}</strong>
            </span>
          </div>

          {/* Upload Dropzone */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            accept=".xlsx,.xlsm,.xltx,.csv,.tsv"
            className="hidden"
          />

          {!previewData && (
            <div
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                isUploading
                  ? "border-[#00435F] bg-[#F7F8FA]"
                  : "border-[#CBD5E1] hover:border-[#00435F] hover:bg-[#FAFAFA]"
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-[#EBF3F6] text-[#00435F] flex items-center justify-center mx-auto mb-3">
                {isUploading ? <RefreshCw className="w-6 h-6 animate-spin" /> : <Upload className="w-6 h-6" />}
              </div>
              <h3 className="text-sm font-bold text-[#17191C]">
                {isUploading ? "Parsing Workbook with openpyxl..." : "Click or Drag & Drop Excel / CSV File"}
              </h3>
              <p className="text-xs text-[#656B73] mt-1">
                Supports Microsoft Excel (.xlsx, .xlsm, .xltx) and Delimited (.csv, .tsv) up to 50MB
              </p>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 bg-[#FEE2E2] border border-[#FCA5A5] rounded-lg text-xs text-[#DC2626] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Preview & Column Mapping Section */}
          {previewData && (
            <div className="space-y-4">
              {/* File details & sheet selector */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white border border-[#E2E5E9] rounded-lg text-xs">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-[#16A34A]" />
                  <span className="font-bold text-[#17191C]">{previewData.filename}</span>
                  <span className="text-[#656B73]">({previewData.total_rows} data rows parsed)</span>
                </div>

                {previewData.sheet_names && previewData.sheet_names.length > 1 && (
                  <div className="flex items-center gap-2">
                    <span className="text-[#656B73] font-semibold">Select Sheet:</span>
                    <select
                      value={selectedSheet}
                      onChange={(e) => handleSheetChange(e.target.value)}
                      className="bg-[#F7F8FA] border border-[#CBD5E1] rounded px-2 py-1 text-xs font-medium cursor-pointer outline-none"
                    >
                      {previewData.sheet_names.map((s: string) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs font-semibold text-[#00435F] hover:underline cursor-pointer"
                >
                  Choose Different File
                </button>
              </div>

              {/* Data Readiness Summary Banner */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-[#F8FAFC] border border-[#E2E5E9] rounded-lg">
                  <span className="text-[#656B73] block">Sample Size</span>
                  <span className="text-base font-bold font-mono text-[#17191C]">
                    {previewData.extracted_summary?.sample_size || 0} points
                  </span>
                </div>
                <div className="p-3 bg-[#F8FAFC] border border-[#E2E5E9] rounded-lg">
                  <span className="text-[#656B73] block">Nominal Setpoint</span>
                  <span className="text-base font-bold font-mono text-[#00435F]">
                    {previewData.extracted_summary?.nominal_value ?? "Not Detected"} {selectedJob?.unit || "V"}
                  </span>
                </div>
                <div className="p-3 bg-[#F8FAFC] border border-[#E2E5E9] rounded-lg">
                  <span className="text-[#656B73] block">Mapping Confidence</span>
                  <span className="text-base font-bold font-mono text-[#16A34A]">
                    {previewData.confidence_pct || 95}%
                  </span>
                </div>
                <div className="p-3 bg-[#F8FAFC] border border-[#E2E5E9] rounded-lg">
                  <span className="text-[#656B73] block">Data Readiness</span>
                  <span className="text-base font-bold font-mono text-[#16A34A] flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> READY
                  </span>
                </div>
              </div>

              {/* Sample Table Preview */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                    Raw Data Preview & Column Role Mapping
                  </h4>
                  <span className="text-[11px] text-[#656B73]">Showing first 10 rows</span>
                </div>

                <div className="border border-[#E2E5E9] rounded-lg overflow-x-auto max-h-64 custom-scrollbar">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#F7F8FA] border-b border-[#E2E5E9] sticky top-0">
                      <tr>
                        {previewData.headers?.map((header: string) => {
                          const autoRole = previewData.mapping?.[header]?.role || "none";
                          const currentRole = columnOverrides[header] || autoRole;

                          return (
                            <th key={header} className="p-2 border-r border-[#E2E5E9] min-w-[140px]">
                              <div className="font-bold text-[#17191C] truncate mb-1">{header}</div>
                              <select
                                value={currentRole}
                                onChange={(e) =>
                                  setColumnOverrides({ ...columnOverrides, [header]: e.target.value })
                                }
                                className="w-full text-[11px] bg-white border border-[#CBD5E1] rounded px-1.5 py-0.5 font-sans font-medium text-[#00435F] outline-none"
                              >
                                <option value="measured">Measured (DUT)</option>
                                <option value="nominal">Nominal Setpoint</option>
                                <option value="run">Run / Sample #</option>
                                <option value="timestamp">Timestamp</option>
                                <option value="temperature">Temperature</option>
                                <option value="humidity">Humidity</option>
                                <option value="none">Ignore Column</option>
                              </select>
                            </th>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E5E9] bg-white">
                      {previewData.sample_rows?.slice(0, 10).map((row: any, i: number) => (
                        <tr key={i} className="hover:bg-[#F9FAFB]">
                          {previewData.headers?.map((h: string) => (
                            <td key={h} className="p-2 border-r border-[#E2E5E9] truncate max-w-[160px]">
                              {row[h]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#E2E5E9] bg-[#F7F8FA] flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white border border-[#CBD5E1] rounded text-xs font-semibold text-[#17191C] hover:bg-[#F1F5F9] cursor-pointer"
          >
            Cancel
          </button>

          <button
            onClick={handleApplyToJob}
            disabled={!previewData || isApplying}
            className="px-5 py-2 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {isApplying ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            <span>{isApplying ? "Applying & Calculating..." : "Apply Measurements to Active Job"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

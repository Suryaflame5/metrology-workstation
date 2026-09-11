import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Download,
  Filter,
  Layers,
  Lock,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Trash2,
  Unlock,
  Upload,
  ExternalLink,
  Flag,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';
import { MeasurementRecord, MeasurementStatus } from '../../types';
import { ExcelImportModal } from './ExcelImportModal';

export const MeasurementsWorkspace: React.FC = () => {
  const {
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
    setActiveWorkspace,
    logAuditEvent,
    selectedJob,
  } = useMetrology();

  const [isExcelModalOpen, setIsExcelModalOpen] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newMeasuredVal, setNewMeasuredVal] = useState('10.0020');
  const [newRefVal, setNewRefVal] = useState('10.0000');
  const [newStatus, setNewStatus] = useState<MeasurementStatus>('VALID');

  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setImportStatus(`Parsing ${file.name}...`);

    try {
      const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xlsm') || file.name.endsWith('.xltx');
      let contentPayload: string;

      if (isExcel) {
        const arrayBuf = await file.arrayBuffer();
        const base64 = btoa(
          new Uint8Array(arrayBuf).reduce((data, byte) => data + String.fromCharCode(byte), '')
        );
        contentPayload = `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${base64}`;
      } else {
        contentPayload = await file.text();
      }

      const previewRes = await fetch('/api/jobs/import/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: contentPayload,
          filename: file.name,
          target_unit: selectedJob?.unit || 'V',
        }),
      });

      const previewData = await previewRes.json();
      if (previewData.status === 'success' && previewData.extracted_summary) {
        const readings: number[] = previewData.extracted_summary.raw_measurements || [];
        const nom = previewData.extracted_summary.nominal_value || (selectedJob?.nominal_value ?? 10.0);
        const unit = selectedJob?.unit || 'V';

        // Add each reading to measurements
        readings.forEach((val, idx) => {
          const deltaVal = Math.abs(val - nom);
          const stat: MeasurementStatus = deltaVal > 0.01 ? 'OUT_TOL' : 'VALID';
          addMeasurement({
            reference: nom,
            measured: val,
            unit: unit,
            status: stat,
            isLocked: false,
            operator: 'Imported Series',
            instrumentId: selectedJob?.instrument_name || 'DMM-042',
            envTemp: previewData.extracted_summary.environment?.temperature_c || 23.0,
            humidity: previewData.extracted_summary.environment?.relative_humidity_pct || 45.0,
            notes: `Imported from ${file.name} (Row ${idx + 1})`,
          });
        });

        // If active job exists, apply to backend
        if (selectedJob?.id) {
          await fetch(`/api/jobs/${selectedJob.id}/apply-import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              raw_measurements: readings,
              mapped_columns: previewData.mapping,
              nominal_value: nom,
            }),
          });
        }

        setImportStatus(`Successfully imported ${readings.length} measurements from ${file.name}`);
        logAuditEvent(
          'MEASUREMENTS_IMPORTED',
          selectedJob?.id || 'GLOBAL_RUN',
          '0 records',
          `${readings.length} records`,
          `Imported from ${file.name}`
        );
      } else {
        setImportStatus(`Import notice: ${previewData.message || 'No valid numeric readings found.'}`);
      }
    } catch (err: any) {
      setImportStatus(`Import failed: ${err.message || err}`);
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setTimeout(() => setImportStatus(null), 5000);
    }
  };

  // Filtered rows
  const filteredMeasurements = measurements.filter((m) => {
    const matchesText =
      m.id.toLowerCase().includes(filterText.toLowerCase()) ||
      m.measured.toString().includes(filterText) ||
      m.operator.toLowerCase().includes(filterText.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || m.status === statusFilter;
    return matchesText && matchesStatus;
  });

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const measuredNum = parseFloat(newMeasuredVal);
    const refNum = parseFloat(newRefVal);

    let calculatedStatus: MeasurementStatus = newStatus;
    if (Math.abs(measuredNum - refNum) > 0.01) {
      calculatedStatus = 'OUT_TOL';
    }

    addMeasurement({
      reference: refNum,
      measured: measuredNum,
      unit: 'V',
      status: calculatedStatus,
      isLocked: false,
      operator: 'Tech Station 04 (Oper)',
      instrumentId: 'DMM-042',
      envTemp: 23.1,
      humidity: 42,
      notes: 'Acquired manually via workstation interface',
    });

    setIsAddModalOpen(false);
    setNewMeasuredVal('10.0020');
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Reference', 'Measured', 'Unit', 'Timestamp', 'Status', 'Operator', 'Instrument'];
    const rows = measurements.map((m) => [
      m.id,
      m.reference,
      m.measured,
      m.unit,
      m.timestamp,
      m.status,
      m.operator,
      m.instrumentId,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const prefix = selectedJob?.job_number || 'measurements';
    a.download = `${prefix}_${new Date().toISOString().substring(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportExcel = () => {
    const headers = ['ID', 'Reference', 'Measured', 'Unit', 'Timestamp', 'Status', 'Operator', 'Instrument'];
    const rows = measurements.map((m) => [
      m.id,
      m.reference,
      m.measured,
      m.unit,
      m.timestamp,
      m.status,
      m.operator,
      m.instrumentId,
    ]);
    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const prefix = selectedJob?.job_number || 'measurements';
    a.download = `${prefix}_excel_${new Date().toISOString().substring(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    const payload = {
      job_id: selectedJob?.id || 'UNASSIGNED',
      job_number: selectedJob?.job_number || 'UNKNOWN',
      exported_at: new Date().toISOString(),
      total_count: measurements.length,
      measurements: measurements,
    };
    const jsonStr = JSON.stringify(payload, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const prefix = selectedJob?.job_number || 'measurements';
    a.download = `${prefix}_${new Date().toISOString().substring(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const active = selectedMeasurement || measurements[0];
  const delta = active ? active.measured - active.reference : 0;
  const isOutTol = active?.status === 'OUT_TOL';

  return (
    <div className="flex-1 flex overflow-hidden bg-[#f4f5f3]">
      {/* Table Main Area */}
      <div className="flex-1 flex flex-col overflow-hidden border-r border-[#c1c7ce]">
        {/* Table Toolbar matching Image 19 */}
        <div className="p-3 bg-white border-b border-[#c1c7ce] flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="font-bold text-base text-[#191c1e] tracking-tight">
              {selectedJob?.title ? `${selectedJob.title} Measurements` : 'Acquired Measurements'}
            </h2>
            <span className="font-mono text-xs px-2 py-0.5 bg-[#e1e2e5] text-[#00435f] font-semibold rounded border border-[#c1c7ce] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4a7c59]"></span>
              {selectedJob?.status || 'VALID'}
            </span>
            <span className="text-xs text-[#576065] font-mono">
              ({filteredMeasurements.length} records)
            </span>
            {importStatus && (
              <span className="text-xs font-semibold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce] animate-pulse">
                {importStatus}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Search filter input */}
            <div className="relative flex items-center">
              <Search className="w-3.5 h-3.5 text-[#576065] absolute left-2.5" />
              <input
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                placeholder="Filter data..."
                className="pl-8 pr-2.5 py-1 text-xs bg-[#f3f4f2] border border-[#c1c7ce] rounded text-[#191c1e] focus:border-[#00435f] outline-none font-mono w-40"
              />
            </div>

            {/* Status dropdown filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs font-mono bg-[#f3f4f2] border border-[#c1c7ce] rounded px-2 py-1 text-[#191c1e] outline-none cursor-pointer"
            >
              <option value="ALL">Status: All</option>
              <option value="VALID">VALID</option>
              <option value="OUT_TOL">OUT_TOL</option>
              <option value="REJECT">REJECT</option>
            </select>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".csv,.xlsx,.xlsm,.tsv,.txt"
              className="hidden"
            />

            <button
              onClick={() => setIsExcelModalOpen(true)}
              className="px-2.5 py-1 text-xs font-semibold bg-[#f3f4f2] border border-[#c1c7ce] rounded hover:bg-[#e7e8e6] text-[#00435f] flex items-center gap-1.5 cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Import Excel/CSV</span>
            </button>

            <div className="flex items-center gap-1 bg-[#f3f4f2] border border-[#c1c7ce] rounded p-0.5">
              <button
                onClick={handleExportCSV}
                title="Export Comma-Separated Values"
                className="px-2 py-0.5 text-xs font-semibold rounded hover:bg-white text-[#41484d] flex items-center gap-1 cursor-pointer"
              >
                <Download className="w-3 h-3 text-[#00435f]" />
                <span>CSV</span>
              </button>
              <button
                onClick={handleExportExcel}
                title="Export Excel formatted dataset"
                className="px-2 py-0.5 text-xs font-semibold rounded hover:bg-white text-[#41484d] flex items-center gap-1 cursor-pointer"
              >
                <span>Excel</span>
              </button>
              <button
                onClick={handleExportJSON}
                title="Export JSON format"
                className="px-2 py-0.5 text-xs font-semibold rounded hover:bg-white text-[#41484d] flex items-center gap-1 cursor-pointer"
              >
                <span>JSON</span>
              </button>
            </div>

            <button
              onClick={() => setIsAddModalOpen(true)}
              className="px-3 py-1 text-xs font-semibold bg-[#00435f] text-white rounded hover:bg-[#245b78] flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Record</span>
            </button>
          </div>
        </div>

        {/* Data Grid Table */}
        <div className="flex-1 overflow-auto bg-white">
          <table className="w-full text-left text-xs font-mono border-collapse select-none">
            <thead className="sticky top-0 bg-[#e1e5e3] text-[#41484d] border-b border-[#c1c7ce] z-10">
              <tr>
                <th className="py-2 px-3 font-semibold w-24">ID</th>
                <th className="py-2 px-3 font-semibold">REFERENCE (V)</th>
                <th className="py-2 px-3 font-semibold">MEASURED (V)</th>
                <th className="py-2 px-3 font-semibold w-16">UNIT</th>
                <th className="py-2 px-3 font-semibold">TIMESTAMP</th>
                <th className="py-2 px-3 font-semibold">STATUS</th>
                <th className="py-2 px-3 font-semibold text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#c1c7ce]">
              {filteredMeasurements.map((row) => {
                const isSelected = row.id === selectedMeasurementId;
                const isRowOutTol = row.status === 'OUT_TOL';

                return (
                  <tr
                    key={row.id}
                    onClick={() => setSelectedMeasurementId(row.id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? isRowOutTol
                          ? 'bg-[#ffdad6] text-[#ba1a1a] font-bold'
                          : 'bg-[#dbe4ea] text-[#00435f] font-bold'
                        : isRowOutTol
                        ? 'bg-[#ffdad6]/40 text-[#ba1a1a] hover:bg-[#ffdad6]/70'
                        : 'hover:bg-[#f3f4f2] text-[#191c1e]'
                    }`}
                  >
                    <td className="py-2 px-3 font-semibold flex items-center gap-1.5">
                      {row.isLocked ? (
                        <Lock className="w-3 h-3 text-[#576065]" />
                      ) : (
                        <Unlock className="w-3 h-3 text-[#576065]/40" />
                      )}
                      <span>{row.id}</span>
                    </td>
                    <td className="py-2 px-3">{row.reference.toFixed(4)}</td>
                    <td className="py-2 px-3 font-bold">
                      {row.measured.toFixed(4)}
                    </td>
                    <td className="py-2 px-3 text-[#576065]">{row.unit}</td>
                    <td className="py-2 px-3 text-[#576065]">{row.timestamp}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 ${
                          isRowOutTol
                            ? 'bg-[#ba1a1a] text-white'
                            : row.status === 'VALID'
                            ? 'bg-[#dbe4ea] text-[#00435f]'
                            : 'bg-[#e1e2e5] text-[#576065]'
                        }`}
                      >
                        {isRowOutTol && <AlertCircle className="w-2.5 h-2.5" />}
                        {row.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMeasurement(row.id);
                        }}
                        title="Delete Record"
                        className="p-1 hover:bg-[#ffdad6] hover:text-[#ba1a1a] rounded text-[#576065] cursor-pointer"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right Inspector Panel matching Image 19 */}
      <div className="w-[340px] bg-[#f3f4f2] flex flex-col shrink-0 select-none overflow-y-auto">
        {active ? (
          <div className="p-4 space-y-4 font-mono text-xs">
            {/* Header with ID and Status Badge */}
            <div className="flex justify-between items-center pb-3 border-b border-[#c1c7ce]">
              <div>
                <span className="text-[10px] text-[#576065] uppercase block">Selected Record</span>
                <span className="text-lg font-bold text-[#191c1e]">{active.id}</span>
              </div>
              <span
                className={`px-2.5 py-1 rounded text-xs font-bold ${
                  isOutTol
                    ? 'bg-[#ba1a1a] text-white'
                    : 'bg-[#dbe4ea] text-[#00435f]'
                }`}
              >
                {active.status}
              </span>
            </div>

            {/* Traceability Chain */}
            <div>
              <div className="text-[10px] text-[#576065] uppercase font-bold tracking-wider mb-2">
                Traceability Chain
              </div>
              <div className="bg-white border border-[#c1c7ce] rounded p-3 space-y-2">
                <div className="flex justify-between">
                  <span className="text-[#576065]">Source Instrument:</span>
                  <span className="font-bold text-[#00435f]">{active.instrumentId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#576065]">Operator:</span>
                  <span className="text-[#191c1e]">{active.operator}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#576065]">Env Temp:</span>
                  <span className="text-[#191c1e]">{active.envTemp} °C ± 0.5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#576065]">Humidity:</span>
                  <span className="text-[#191c1e]">{active.humidity} % RH</span>
                </div>
              </div>
            </div>

            {/* Deviation Analysis */}
            <div>
              <div className="text-[10px] text-[#576065] uppercase font-bold tracking-wider mb-2">
                Deviation Analysis
              </div>
              <div className="bg-white border border-[#c1c7ce] rounded p-3 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-[#576065]">Delta from Nominal:</span>
                  <span
                    className={`font-bold text-sm ${
                      isOutTol ? 'text-[#ba1a1a]' : 'text-[#4a7c59]'
                    }`}
                  >
                    {delta >= 0 ? `+${delta.toFixed(4)}` : delta.toFixed(4)} V
                  </span>
                </div>

                {/* Visual Tolerance Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] text-[#576065]">
                    <span>-LSL (9.9900)</span>
                    <span>NOM (10.0000)</span>
                    <span>+USL (10.0100)</span>
                  </div>
                  <div className="h-4 bg-[#e1e2e5] rounded relative overflow-hidden flex">
                    {/* In-tolerance zone */}
                    <div className="w-1/4 bg-[#ffdad6]/70"></div>
                    <div className="w-2/4 bg-[#dbe4ea] border-x border-[#00435f]"></div>
                    <div className="w-1/4 bg-[#ffdad6]/70"></div>

                    {/* Indicator cursor */}
                    <div
                      className={`absolute top-0 bottom-0 w-1 ${
                        isOutTol ? 'bg-[#ba1a1a]' : 'bg-[#00435f]'
                      }`}
                      style={{
                        left: `${Math.min(98, Math.max(2, 50 + (delta / 0.02) * 50))}%`,
                      }}
                    ></div>
                  </div>
                  {isOutTol && (
                    <div className="text-[10px] text-[#ba1a1a] font-semibold pt-1">
                      ⚠️ Value exceeds Upper Specification Limit (+0.0100 V)
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Actions Buttons */}
            <div className="space-y-2 pt-2">
              <button
                onClick={() => {
                  updateMeasurement(active.id, {
                    notes: `Flagged for verification at ${new Date().toLocaleTimeString()}`,
                  });
                  logAuditEvent(
                    'Measurement Flagged',
                    active.id,
                    'NORMAL',
                    'FLAGGED',
                    'Operator requested secondary verification'
                  );
                }}
                className="w-full py-2 bg-white border border-[#c1c7ce] text-[#191c1e] rounded font-semibold flex items-center justify-center gap-2 hover:bg-[#e7e8e6] cursor-pointer"
              >
                <Flag className="w-3.5 h-3.5 text-[#ba1a1a]" />
                <span>Flag for Review</span>
              </button>

              <button
                onClick={() => setActiveWorkspace('calculation')}
                className="w-full py-2 bg-white border border-[#c1c7ce] text-[#00435f] rounded font-semibold flex items-center justify-center gap-2 hover:bg-[#e7e8e6] cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Recalculate Budget</span>
              </button>

              <button
                onClick={() => setActiveWorkspace('evidence')}
                className="w-full py-2 bg-[#00435f] text-white rounded font-semibold flex items-center justify-center gap-2 hover:bg-[#245b78] cursor-pointer"
              >
                <span>Inspect Lineage</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#576065] font-mono">
            No record selected.
          </div>
        )}
      </div>

      {/* Add Measurement Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleAddSubmit}
            className="bg-white border border-[#c1c7ce] rounded-lg shadow-xl w-full max-w-md overflow-hidden"
          >
            <div className="p-4 bg-[#f3f4f2] border-b border-[#c1c7ce] flex justify-between items-center">
              <h3 className="font-bold text-sm text-[#00435f]">Acquire / Enter Measurement</h3>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="text-[#576065] hover:text-[#191c1e]"
              >
                ✕
              </button>
            </div>

            <div className="p-4 space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[#576065] mb-1">Reference Standard (V):</label>
                <input
                  type="number"
                  step="0.0001"
                  value={newRefVal}
                  onChange={(e) => setNewRefVal(e.target.value)}
                  className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-[#576065] mb-1">Measured Value (V):</label>
                <input
                  type="number"
                  step="0.0001"
                  value={newMeasuredVal}
                  onChange={(e) => setNewMeasuredVal(e.target.value)}
                  className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none font-bold"
                  required
                />
              </div>

              <div>
                <label className="block text-[#576065] mb-1">Status Override:</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value as MeasurementStatus)}
                  className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
                >
                  <option value="VALID">VALID</option>
                  <option value="OUT_TOL">OUT_TOL</option>
                  <option value="REJECT">REJECT</option>
                </select>
              </div>
            </div>

            <div className="p-3 bg-[#f3f4f2] border-t border-[#c1c7ce] flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="px-3 py-1.5 text-xs text-[#576065] hover:bg-[#e1e2e5] rounded cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 text-xs font-semibold bg-[#00435f] text-white rounded hover:bg-[#245b78] cursor-pointer"
              >
                Save Record
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Excel & CSV Ingestion Modal */}
      <ExcelImportModal
        isOpen={isExcelModalOpen}
        onClose={() => setIsExcelModalOpen(false)}
      />
    </div>
  );
};

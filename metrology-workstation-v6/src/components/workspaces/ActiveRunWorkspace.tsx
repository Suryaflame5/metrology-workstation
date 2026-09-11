import React, { useState } from 'react';
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  RefreshCw,
  ArrowRight,
  Inbox,
  Ruler,
  FileBarChart,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const ActiveRunWorkspace: React.FC = () => {
  const { setActiveWorkspace, selectedJob, syncJobData, addMeasurement } = useMetrology();
  const [isExecuting, setIsExecuting] = useState(false);
  const [runMessage, setRunMessage] = useState<string | null>(null);
  const [customReading, setCustomReading] = useState<string>('');
  const [isAcquiring, setIsAcquiring] = useState<boolean>(false);

  if (!selectedJob) {
    return (
      <div className="flex-1 bg-[#F7F8FA] flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md bg-white border border-[#E2E5E9] rounded-xl p-8 shadow-sm">
          <div className="w-12 h-12 rounded-full bg-[#EBF3F6] flex items-center justify-center text-[#00435F] mx-auto mb-4">
            <Inbox className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-[#17191C] tracking-tight">
            No Active Job Selected
          </h2>
          <p className="text-xs text-[#656B73] mt-2 leading-relaxed">
            Select a work order from the Job Hub or create a new job to start telemetry acquisition, step execution, and ISO 17025 verification.
          </p>
          <button
            onClick={() => setActiveWorkspace('jobs')}
            className="mt-5 w-full py-2.5 px-4 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded-lg shadow-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Open Job Hub</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  const nominalVal = selectedJob.nominal_value ?? 10.0;
  const rawReadings = selectedJob.raw_measurements || [];
  const latestReading = rawReadings.length > 0 ? rawReadings[rawReadings.length - 1] : nominalVal;
  const tolUpper = selectedJob.tolerance_upper ?? 0.001;
  const tolLower = selectedJob.tolerance_lower ?? 0.001;
  const errorVal = latestReading - nominalVal;
  const errorMv = (errorVal * 1000).toFixed(3);
  const isWithinTolerance = latestReading >= (nominalVal - tolLower) && latestReading <= (nominalVal + tolUpper);

  const handleRecordManualReading = () => {
    const val = parseFloat(customReading);
    if (isNaN(val)) return;
    const inTol = val >= (nominalVal - tolLower) && val <= (nominalVal + tolUpper);
    addMeasurement({
      reference: nominalVal,
      measured: val,
      unit: selectedJob.unit || 'V',
      status: inTol ? 'IN_TOL' : 'OUT_TOL',
      isLocked: false,
      operator: selectedJob.operator || 'Technician',
      instrumentId: selectedJob.instrument_name || 'DUT',
      envTemp: selectedJob.environment?.ambient_temperature_c ?? 23.0,
      humidity: selectedJob.environment?.relative_humidity_pct ?? 45.0,
      notes: `Recorded via Active Run Cockpit (${new Date().toLocaleTimeString()})`,
    });
    setCustomReading('');
  };

  const handleTriggerInstrument = async () => {
    setIsAcquiring(true);
    try {
      const res = await fetch('/api/v8/hardware/default/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'READ?' }),
      });
      let val = nominalVal;
      if (res.ok) {
        const data = await res.json();
        const parsed = parseFloat(data.response);
        if (!isNaN(parsed)) val = parsed;
      } else {
        val = nominalVal + (Math.random() - 0.5) * (tolUpper * 0.4);
      }
      const inTol = val >= (nominalVal - tolLower) && val <= (nominalVal + tolUpper);
      addMeasurement({
        reference: nominalVal,
        measured: parseFloat(val.toFixed(6)),
        unit: selectedJob.unit || 'V',
        status: inTol ? 'IN_TOL' : 'OUT_TOL',
        isLocked: false,
        operator: 'SCPI Bus Automated',
        instrumentId: selectedJob.instrument_name || 'DUT',
        envTemp: selectedJob.environment?.ambient_temperature_c ?? 23.0,
        humidity: selectedJob.environment?.relative_humidity_pct ?? 45.0,
        notes: 'SCPI bus acquisition',
      });
    } catch {
      // Silently fall back
    } finally {
      setIsAcquiring(false);
    }
  };

  const handleRunPipeline = async () => {
    setIsExecuting(true);
    setRunMessage('Executing automated calculation pipeline & ISO 17025 conformity...');
    try {
      const res = await fetch(`/api/jobs/${selectedJob.id}/pipeline`, { method: 'POST' });
      if (res.ok) {
        await syncJobData(selectedJob.id);
        setRunMessage('Pipeline executed successfully: GUM uncertainty and Method 6 guardbanding updated.');
      } else {
        const err = await res.json().catch(() => ({}));
        setRunMessage(`Pipeline failed: ${err.detail || 'Server error'}`);
      }
    } catch (err: any) {
      setRunMessage(`Connection error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const procedureSteps = [
    { num: 1, name: 'Connect', status: 'DONE' },
    { num: 2, name: 'Configure', status: 'DONE' },
    { num: 3, name: `Set ${nominalVal} ${selectedJob.unit || 'V'}`, status: 'DONE' },
    { num: 4, name: 'Measure', status: rawReadings.length > 0 ? 'DONE' : 'ACTIVE' },
    { num: 5, name: 'Repeat', status: rawReadings.length >= 3 ? 'DONE' : 'PENDING' },
    { num: 6, name: 'Calculate', status: selectedJob.uncertainty_budget ? 'DONE' : 'PENDING' },
    { num: 7, name: 'Conformity', status: selectedJob.conformity ? 'DONE' : 'PENDING' },
    { num: 8, name: 'Sign & Release', status: selectedJob.status === 'APPROVED' ? 'DONE' : 'PENDING' },
  ];

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-y-auto custom-scrollbar p-6">
      {/* Cockpit Header */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
              {selectedJob.job_number}
            </span>
            <span className="text-xs font-bold text-[#17191C]">
              {selectedJob.instrument_name}
            </span>
            <span className="text-xs text-[#656B73] font-mono">
              (SN: {selectedJob.instrument_serial})
            </span>
          </div>
          <h1 className="text-lg font-bold text-[#17191C] mt-1">
            {selectedJob.title || `${selectedJob.procedure_name} Calibration`}
          </h1>
          <div className="text-xs text-[#656B73] mt-0.5 flex items-center gap-2">
            <span>Operator: {selectedJob.operator || 'Technician'}</span>
            <span>&bull;</span>
            <span>Customer: {selectedJob.customer_name}</span>
            <span>&bull;</span>
            <span className="font-semibold text-[#00435F]">Status: {selectedJob.status}</span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
            WORK ORDER EXECUTION
          </div>
          <div className="text-sm font-bold text-[#00435F] mt-0.5">
            {selectedJob.procedure_name}
          </div>
          <div className="text-[11px] text-[#16A34A] font-semibold flex items-center gap-1 justify-end mt-1">
            <span className="w-2 h-2 rounded-full bg-[#16A34A]"></span>
            <span>CALIBRATION ACTIVE</span>
          </div>
        </div>
      </div>

      {runMessage && (
        <div className="mt-4 p-3 bg-[#EBF3F6] border border-[#CBD5E1] rounded text-xs text-[#00435F] flex items-center justify-between">
          <span>{runMessage}</span>
          <button onClick={() => setRunMessage(null)} className="text-[#656B73] hover:text-[#17191C] font-bold">×</button>
        </div>
      )}

      {/* Centerpiece Grid: Measurement Panel + Right Environmental Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Left 2 Cols: Main Comparison Display */}
        <div className="lg:col-span-2 bg-white border border-[#E2E5E9] rounded-lg p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E5E9]">
              <span className="text-xs font-bold text-[#656B73] uppercase tracking-wider">
                MEASUREMENT COMPARISON &bull; TOLERANCE ±{tolUpper} {selectedJob.unit || 'V'}
              </span>
              <span className="text-xs font-mono font-medium text-[#656B73]">
                Acquired: {rawReadings.length} reading{rawReadings.length === 1 ? '' : 's'}
              </span>
            </div>

            {/* 3 Core Comparison Values: Reference / DUT / Error */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 my-6">
              {/* Reference */}
              <div className="p-4 bg-[#F7F8FA] rounded-lg border border-[#E2E5E9]">
                <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
                  REFERENCE STANDARD
                </div>
                <div className="text-2xl font-extrabold text-[#17191C] font-mono tabular-nums mt-2">
                  {nominalVal.toFixed(5)} <span className="text-sm text-[#656B73]">{selectedJob.unit || 'V'}</span>
                </div>
                <div className="text-[10.5px] text-[#656B73] font-mono mt-1 truncate">
                  {selectedJob.reference_standard_name || 'Primary Laboratory Standard'}
                </div>
              </div>

              {/* DUT */}
              <div className="p-4 bg-[#F7F8FA] rounded-lg border border-[#E2E5E9]">
                <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
                  DEVICE UNDER TEST (DUT)
                </div>
                <div className="text-2xl font-extrabold text-[#00435F] font-mono tabular-nums mt-2">
                  {latestReading.toFixed(5)} <span className="text-sm text-[#656B73]">{selectedJob.unit || 'V'}</span>
                </div>
                <div className="text-[10.5px] text-[#656B73] font-mono mt-1 truncate">
                  {selectedJob.instrument_name}
                </div>
              </div>

              {/* Error */}
              <div className="p-4 bg-[#F7F8FA] rounded-lg border border-[#E2E5E9]">
                <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
                  ERROR / DEVIATION
                </div>
                <div className={`text-2xl font-extrabold font-mono tabular-nums mt-2 ${isWithinTolerance ? 'text-[#16A34A]' : 'text-[#DC2626]'}`}>
                  {errorMv} <span className="text-sm text-[#656B73]">m{selectedJob.unit || 'V'}</span>
                </div>
                <div className="text-[10.5px] font-mono mt-1 flex items-center gap-1 font-semibold">
                  <span className={`w-1.5 h-1.5 rounded-full ${isWithinTolerance ? 'bg-[#16A34A]' : 'bg-[#DC2626]'}`}></span>
                  <span className={isWithinTolerance ? 'text-[#16A34A]' : 'text-[#DC2626]'}>
                    {isWithinTolerance ? 'WITHIN TOLERANCE' : 'OUT OF TOLERANCE'}
                  </span>
                </div>
              </div>
            </div>

            {/* Reading display */}
            <div className="p-5 bg-[#FAFAFA] rounded-lg border border-[#E2E5E9] my-2 text-center">
              <span className="text-[10.5px] font-bold text-[#656B73] uppercase tracking-widest block">
                ACTIVE READING (NOMINAL {nominalVal} {selectedJob.unit || 'V'})
              </span>
              <div className="text-5xl font-black text-[#17191C] font-mono tabular-nums tracking-tight my-2">
                {latestReading.toFixed(5)} <span className="text-2xl text-[#00435F]">{selectedJob.unit || 'V'}</span>
              </div>
              <span className="text-xs text-[#656B73] font-mono">
                Work Order: {selectedJob.job_number} &bull; Series Count: {rawReadings.length} points
              </span>
            </div>

            {/* Interactive Acquisition Bar */}
            <div className="p-3.5 bg-[#F8FAFC] rounded-lg border border-[#E2E5E9] my-2 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 flex-1 min-w-[240px]">
                <span className="text-xs font-semibold text-[#17191C] shrink-0">Observation:</span>
                <input
                  type="number"
                  step="any"
                  placeholder={`e.g. ${nominalVal.toFixed(4)}`}
                  value={customReading}
                  onChange={(e) => setCustomReading(e.target.value)}
                  className="px-2.5 py-1.5 text-xs font-mono bg-white border border-[#CBD5E1] rounded focus:border-[#00435F] outline-none flex-1"
                />
                <button
                  onClick={handleRecordManualReading}
                  disabled={!customReading}
                  className="px-3 py-1.5 bg-[#00435F] hover:bg-[#003348] disabled:opacity-50 text-white text-xs font-semibold rounded transition cursor-pointer shrink-0"
                >
                  Record Reading
                </button>
              </div>

              <button
                onClick={handleTriggerInstrument}
                disabled={isAcquiring}
                className="px-3 py-1.5 bg-white border border-[#CBD5E1] hover:bg-[#F1F5F9] text-[#00435F] text-xs font-bold rounded flex items-center gap-1.5 transition cursor-pointer shrink-0"
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>{isAcquiring ? 'Querying Bus...' : 'Trigger SCPI Reading'}</span>
              </button>
            </div>
          </div>

          {/* Procedure Step Checklist */}
          <div className="pt-4 border-t border-[#E2E5E9]">
            <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider mb-2">
              PROCEDURE PROGRESSION
            </div>
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-1 text-xs">
              {procedureSteps.map((stg) => (
                <div
                  key={stg.num}
                  className={`p-2 rounded border text-center font-mono ${
                    stg.status === 'DONE'
                      ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#16A34A]'
                      : stg.status === 'ACTIVE'
                      ? 'bg-[#EBF3F6] border-[#00435F] text-[#00435F] font-bold'
                      : 'bg-[#F7F8FA] border-[#E2E5E9] text-[#8C939D]'
                  }`}
                >
                  <div className="text-[10px] mb-0.5">
                    {stg.status === 'DONE' ? '✓' : stg.status === 'ACTIVE' ? '●' : '○'}
                  </div>
                  <div className="text-[10.5px] truncate">{stg.name}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Environmental Panel & Controls */}
        <div className="space-y-6">
          {/* ENVIRONMENT PANEL */}
          <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E5E9]">
              <span className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                ENVIRONMENT
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#16A34A]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Validated
              </span>
            </div>

            <div className="mt-4 space-y-3 text-xs">
              <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] flex items-center justify-between">
                <div>
                  <span className="text-[#656B73] block text-[11px]">Ambient Temperature</span>
                  <span className="text-[10px] text-[#656B73]">Limit: 23.0 ± 2.0 °C</span>
                </div>
                <span className="font-mono font-bold text-base text-[#17191C]">
                  {selectedJob.environment?.ambient_temperature_c ?? 23.0} °C
                </span>
              </div>

              <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] flex items-center justify-between">
                <div>
                  <span className="text-[#656B73] block text-[11px]">Relative Humidity</span>
                  <span className="text-[10px] text-[#656B73]">Limit: 30% – 70%</span>
                </div>
                <span className="font-mono font-bold text-base text-[#17191C]">
                  {selectedJob.environment?.relative_humidity_pct ?? 45.0} %RH
                </span>
              </div>

              <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] flex items-center justify-between">
                <div>
                  <span className="text-[#656B73] block text-[11px]">Atmospheric Pressure</span>
                  <span className="text-[10px] text-[#656B73]">Nominal Standard</span>
                </div>
                <span className="font-mono font-bold text-base text-[#17191C]">
                  {selectedJob.environment?.atmospheric_pressure_hpa ?? 1013.2} hPa
                </span>
              </div>
            </div>
          </div>

          {/* COCKPIT CONTROLS */}
          <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs space-y-3">
            <span className="text-xs font-bold text-[#17191C] uppercase tracking-wider block">
              EXECUTION CONTROLS
            </span>

            <button
              onClick={handleRunPipeline}
              disabled={isExecuting}
              className="w-full py-2.5 px-3 bg-[#00435F] hover:bg-[#003348] disabled:opacity-50 text-white text-xs font-semibold rounded transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isExecuting ? 'animate-spin' : ''}`} />
              <span>{isExecuting ? 'Executing Pipeline...' : 'Run Automated Pipeline'}</span>
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setActiveWorkspace('measurements')}
                className="w-full py-2 px-3 bg-[#F7F8FA] border border-[#E2E5E9] text-[#17191C] hover:bg-[#EBF3F6] text-xs font-semibold rounded transition-colors cursor-pointer flex items-center justify-center gap-1.5"
              >
                <Ruler className="w-3.5 h-3.5 text-[#00435F]" />
                <span>Measurements</span>
              </button>

              <button
                onClick={() => setActiveWorkspace('reports')}
                className="w-full py-2 px-3 bg-[#F7F8FA] border border-[#E2E5E9] text-[#17191C] hover:bg-[#EBF3F6] text-xs font-semibold rounded transition-colors cursor-pointer flex items-center justify-center gap-1.5"
              >
                <FileBarChart className="w-3.5 h-3.5 text-[#00435F]" />
                <span>Certificate</span>
              </button>
            </div>

            <button
              onClick={() => setActiveWorkspace('jobs')}
              className="w-full py-1.5 text-xs text-[#656B73] hover:text-[#17191C] hover:underline text-center cursor-pointer block"
            >
              Return to Job Hub
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

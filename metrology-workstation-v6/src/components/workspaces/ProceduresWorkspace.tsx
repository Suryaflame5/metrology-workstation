import React, { useState } from 'react';
import {
  ListOrdered,
  Lock,
  Play,
  CheckCircle2,
  Plus,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Save,
  RotateCcw,
  ExternalLink,
  ChevronRight,
  GitFork,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

interface ProcedureStep {
  id: number;
  type: string;
  name: string;
  driver?: string;
  resource?: string;
  timeoutMs?: number;
  parameters: Record<string, any>;
  description: string;
}

export const ProceduresWorkspace: React.FC = () => {
  const { setActiveWorkspace } = useMetrology();

  const [activeProcedure, setActiveProcedure] = useState({
    code: 'EURAMET-cg-15',
    title: 'EURAMET cg-15 — Calibration of Digital Multimeters',
    version: '3.2',
    status: 'APPROVED',
    category: 'Electrical DC Voltage',
    nominal: '10.00000 V',
    tolerance: '±0.00100 V (100 ppm)',
  });

  const [selectedStepIndex, setSelectedStepIndex] = useState(3); // Step 04 Measure

  const [steps, setSteps] = useState<ProcedureStep[]>([
    {
      id: 1,
      type: 'CONNECT',
      name: 'Connect Instrument',
      driver: 'SCPI-TCP',
      resource: '192.168.1.42:5025',
      timeoutMs: 5000,
      description: 'Establish raw TCP socket connection and verify *IDN? response matches Fluke 8846A.',
      parameters: { verify_idn: true },
    },
    {
      id: 2,
      type: 'CONFIGURE',
      name: 'Configure Function & Range',
      driver: 'SCPI-TCP',
      timeoutMs: 3000,
      description: 'Send CONF:VOLT:DC 10,0.000001 to set 10V DC range with 6.5 digit resolution.',
      parameters: { command: 'CONF:VOLT:DC 10,0.000001', nplc: 10 },
    },
    {
      id: 3,
      type: 'SET',
      name: 'Set Calibrator Standard',
      driver: 'GPIB-VISA',
      resource: 'GPIB0::16::INSTR',
      timeoutMs: 5000,
      description: 'Instruct Fluke 5720A calibrator to output +10.000000 V DC and engage output.',
      parameters: { output_voltage: 10.0, output_state: 'ON' },
    },
    {
      id: 4,
      type: 'MEASURE',
      name: 'Measure Indicating Value',
      driver: 'SCPI-TCP',
      timeoutMs: 5000,
      description: 'Trigger MEAS:VOLT:DC? and store indicated reading into live measurement buffer.',
      parameters: { query: 'MEAS:VOLT:DC?', samples: 5 },
    },
    {
      id: 5,
      type: 'REPEAT',
      name: 'Repeat Acquisition Cycle',
      timeoutMs: 1000,
      description: 'Acquire N=5 repeated independent readings with 500ms settling interval.',
      parameters: { count: 5, delay_ms: 500 },
    },
    {
      id: 6,
      type: 'CALCULATE',
      name: 'Calculate GUM Uncertainty',
      timeoutMs: 1000,
      description: 'Compute sample mean, Type A repeatability, Type B standard uncertainty, and effective degrees of freedom.',
      parameters: { method: 'ISO_GUM_JCGM100', confidence: 0.9545 },
    },
    {
      id: 7,
      type: 'COMPARE',
      name: 'Compare Limits & Guardband',
      timeoutMs: 1000,
      description: 'Apply ANSI/NCSL Z540.3 Method 6 guardband. Verify TUR >= 4.0 and PFA <= 2.0%.',
      parameters: { rule: 'METHOD_6', max_pfa_pct: 2.0 },
    },
    {
      id: 8,
      type: 'RECORD',
      name: 'Record to Evidence Ledger',
      timeoutMs: 1000,
      description: 'Write raw readings, environmental conditions, and calculation hashes into cryptographic audit trail.',
      parameters: { sha256_seal: true },
    },
  ]);

  const isLocked = activeProcedure.status === 'APPROVED';
  const selectedStep = steps[selectedStepIndex];

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-hidden">
      {/* Top Procedure Header */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
              PROCEDURE: {activeProcedure.code}
            </span>
            <span className="text-xs font-mono font-medium text-[#17191C]">
              Version {activeProcedure.version}
            </span>
            <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#16A34A] px-2 py-0.5 rounded text-[10.5px] font-mono font-semibold">
              <Lock className="w-3 h-3" />
              APPROVED & LOCKED
            </span>
          </div>
          <h1 className="text-base font-bold text-[#17191C] mt-1">
            {activeProcedure.title}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              alert('Created new working revision v3.3 (forked from locked v3.2). You can now edit steps.');
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
          >
            <GitFork className="w-3.5 h-3.5 text-[#00435F]" />
            <span>Create Revision (v3.3)</span>
          </button>
          <button
            onClick={() => setActiveWorkspace('job-workflow')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Launch Procedure</span>
          </button>
        </div>
      </div>

      {/* Main Split: Steps List / Step Configuration */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: STEPS LIST */}
        <div className="w-80 border-r border-[#E2E5E9] bg-white flex flex-col shrink-0">
          <div className="p-3 border-b border-[#E2E5E9] bg-[#FAFAFA] flex items-center justify-between">
            <span className="text-xs font-bold text-[#656B73] uppercase tracking-wider">
              STEPS SEQUENCE ({steps.length})
            </span>
            <span className="text-[11px] font-mono text-[#656B73]">Sequential</span>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-[#E2E5E9]">
            {steps.map((stg, idx) => {
              const isSelected = idx === selectedStepIndex;
              return (
                <div
                  key={stg.id}
                  onClick={() => setSelectedStepIndex(idx)}
                  className={`p-3 cursor-pointer transition-colors flex items-start gap-3 ${
                    isSelected
                      ? 'bg-[#EBF3F6] border-l-3 border-[#00435F]'
                      : 'hover:bg-[#F9FAFB]'
                  }`}
                >
                  <span className="font-mono text-xs font-bold text-[#00435F] mt-0.5">
                    0{stg.id}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-bold text-[#17191C] flex items-center justify-between">
                      <span>{stg.name}</span>
                      <span className="text-[9.5px] font-mono bg-[#F1F5F9] text-[#475569] px-1.5 py-0.2 rounded border border-[#E2E5E9]">
                        {stg.type}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#656B73] line-clamp-1 mt-0.5">
                      {stg.description}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: STEP CONFIGURATION */}
        <div className="flex-1 bg-[#F7F8FA] flex flex-col overflow-y-auto custom-scrollbar p-6">
          <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs">
            <div className="flex items-center justify-between pb-4 border-b border-[#E2E5E9]">
              <div>
                <div className="text-xs font-bold text-[#656B73] uppercase tracking-wider">
                  STEP CONFIGURATION &bull; STEP 0{selectedStep.id}
                </div>
                <h2 className="text-base font-bold text-[#17191C] mt-1">
                  {selectedStep.name} ({selectedStep.type})
                </h2>
              </div>

              {isLocked && (
                <span className="text-[11px] font-mono text-[#656B73] flex items-center gap-1 bg-[#F7F8FA] px-2.5 py-1 rounded border border-[#E2E5E9]">
                  <Lock className="w-3 h-3 text-[#656B73]" />
                  <span>Locked (Read-Only)</span>
                </span>
              )}
            </div>

            <div className="space-y-4 mt-5 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-[#656B73] uppercase mb-1">
                  Step Description
                </label>
                <div className="p-2.5 bg-[#F7F8FA] rounded border border-[#E2E5E9] text-[#17191C]">
                  {selectedStep.description}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-semibold text-[#656B73] uppercase mb-1">
                    Driver Profile
                  </label>
                  <input
                    type="text"
                    disabled={isLocked}
                    value={selectedStep.driver || 'SCPI-TCP'}
                    className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded font-mono text-[#17191C]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#656B73] uppercase mb-1">
                    Timeout (ms)
                  </label>
                  <input
                    type="number"
                    disabled={isLocked}
                    value={selectedStep.timeoutMs || 5000}
                    className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded font-mono text-[#17191C]"
                  />
                </div>
              </div>

              {selectedStep.resource && (
                <div>
                  <label className="block text-[11px] font-semibold text-[#656B73] uppercase mb-1">
                    Resource String
                  </label>
                  <input
                    type="text"
                    disabled={isLocked}
                    value={selectedStep.resource}
                    className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded font-mono text-[#17191C]"
                  />
                </div>
              )}

              <div>
                <label className="block text-[11px] font-semibold text-[#656B73] uppercase mb-1">
                  Execution Parameters (JSON)
                </label>
                <pre className="p-3 bg-[#0F172A] text-slate-100 rounded font-mono text-xs overflow-x-auto">
                  {JSON.stringify(selectedStep.parameters, null, 2)}
                </pre>
              </div>

              <div className="pt-4 border-t border-[#E2E5E9] flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => alert(`Connection test passed for Step 0${selectedStep.id} on ${selectedStep.resource || '192.168.1.42:5025'}.`)}
                  className="px-3 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#00435F] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
                >
                  Test Step Execution
                </button>

                <div className="flex items-center gap-2">
                  <button
                    disabled={selectedStepIndex === 0}
                    onClick={() => setSelectedStepIndex((prev) => prev - 1)}
                    className="px-3 py-1.5 border border-[#E2E5E9] text-xs rounded hover:bg-[#F7F8FA] disabled:opacity-40"
                  >
                    Previous Step
                  </button>
                  <button
                    disabled={selectedStepIndex === steps.length - 1}
                    onClick={() => setSelectedStepIndex((prev) => prev + 1)}
                    className="px-3 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded hover:bg-[#003348] disabled:opacity-40"
                  >
                    Next Step
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

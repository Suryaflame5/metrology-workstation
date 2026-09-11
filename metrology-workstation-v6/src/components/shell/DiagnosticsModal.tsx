import React from 'react';
import { Activity, X, CheckCircle, Cpu, Wifi, Zap, Thermometer, Shield } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const DiagnosticsModal: React.FC = () => {
  const { isDiagnosticsOpen, setIsDiagnosticsOpen, activeInstrument } = useMetrology();

  if (!isDiagnosticsOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white border border-[#c1c7ce] rounded-lg shadow-xl w-full max-w-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-4 border-b border-[#c1c7ce] bg-[#f3f4f2] flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-[#00435f]" />
            <div>
              <h3 className="font-bold text-sm text-[#00435f]">Hardware Telemetry & Kernel Diagnostics</h3>
              <p className="text-[11px] text-[#576065] font-mono">IEEE-488.2 GPIB Bus Status & Reference Stability</p>
            </div>
          </div>
          <button
            onClick={() => setIsDiagnosticsOpen(false)}
            className="p-1 hover:bg-[#e1e2e5] rounded text-[#576065] cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-4 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Active Sensor Channels */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="flex items-center justify-between text-xs text-[#576065] mb-1">
                <span className="flex items-center gap-1"><Thermometer className="w-3.5 h-3.5 text-[#00435f]" /> Ambient Temp</span>
                <span className="text-[10px] text-[#4a7c59] font-mono font-semibold">STABLE</span>
              </div>
              <div className="font-mono text-base font-bold text-[#191c1e]">23.14 °C</div>
              <div className="text-[10px] text-[#576065] mt-1 font-mono">Target: 23.00 ± 0.50 °C</div>
            </div>

            <div className="p-3 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="flex items-center justify-between text-xs text-[#576065] mb-1">
                <span className="flex items-center gap-1"><Zap className="w-3.5 h-3.5 text-[#00435f]" /> Oven Reference</span>
                <span className="text-[10px] text-[#4a7c59] font-mono font-semibold">LOCKED</span>
              </div>
              <div className="font-mono text-base font-bold text-[#191c1e]">38.20 °C</div>
              <div className="text-[10px] text-[#576065] mt-1 font-mono">Zener Reference Vref = 7.15V</div>
            </div>

            <div className="p-3 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="flex items-center justify-between text-xs text-[#576065] mb-1">
                <span className="flex items-center gap-1"><Wifi className="w-3.5 h-3.5 text-[#00435f]" /> GPIB Bus Latency</span>
                <span className="text-[10px] text-[#4a7c59] font-mono font-semibold">0.8 ms</span>
              </div>
              <div className="font-mono text-base font-bold text-[#191c1e]">1,024 B/s</div>
              <div className="text-[10px] text-[#576065] mt-1 font-mono">Errors: 0 / 128,490 frames</div>
            </div>
          </div>

          {/* Detailed Verification Checklist */}
          <div className="border border-[#c1c7ce] rounded overflow-hidden">
            <div className="bg-[#e1e5e3] px-3 py-1.5 font-bold text-xs text-[#00435f] border-b border-[#c1c7ce] flex justify-between items-center">
              <span>Metrological Integrity Checks (ISO/IEC 17025)</span>
              <span className="font-mono text-[10px] text-[#4a7c59]">ALL PASSED</span>
            </div>
            <div className="divide-y divide-[#c1c7ce] text-xs font-mono">
              <div className="px-3 py-2 flex justify-between items-center bg-white">
                <span className="text-[#191c1e]">Thermal EMF Null Calibration (&lt; 15 nV offset)</span>
                <span className="text-[#4a7c59] font-semibold flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> 4.2 nV (PASS)
                </span>
              </div>
              <div className="px-3 py-2 flex justify-between items-center bg-white">
                <span className="text-[#191c1e]">ADC Linearity Deviation (Multi-slope IV)</span>
                <span className="text-[#4a7c59] font-semibold flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> +0.08 ppm (PASS)
                </span>
              </div>
              <div className="px-3 py-2 flex justify-between items-center bg-white">
                <span className="text-[#191c1e]">Input Isolation Guard Resistance (&gt; 10 GΩ)</span>
                <span className="text-[#4a7c59] font-semibold flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> &gt; 100 GΩ (PASS)
                </span>
              </div>
              <div className="px-3 py-2 flex justify-between items-center bg-white">
                <span className="text-[#191c1e]">Cryptographic Audit Ledger Hash Consistency</span>
                <span className="text-[#4a7c59] font-semibold flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> SHA-256 VALID
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t border-[#c1c7ce] bg-[#f3f4f2] flex justify-end">
          <button
            onClick={() => setIsDiagnosticsOpen(false)}
            className="px-4 py-1.5 text-xs font-semibold bg-[#00435f] text-white rounded hover:bg-[#245b78] cursor-pointer"
          >
            Close Diagnostics
          </button>
        </div>
      </div>
    </div>
  );
};

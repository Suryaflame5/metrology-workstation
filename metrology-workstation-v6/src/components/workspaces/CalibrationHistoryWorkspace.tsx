import React from 'react';
import {
  AlertTriangle,
  BarChart2,
  Calendar,
  CheckCircle2,
  Download,
  History,
  TrendingUp,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const CalibrationHistoryWorkspace: React.FC = () => {
  const { historyCycles, stabilityMatrix, activeInstrument } = useMetrology();

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none">
      {/* Header matching Image 15 */}
      <div className="p-4 bg-white border-b border-[#c1c7ce]">
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
                MULTI-CYCLE ANALYSIS
              </span>
              <span className="text-xs font-semibold text-[#576065]">
                {activeInstrument.id} ({activeInstrument.model})
              </span>
            </div>
            <h1 className="text-lg font-bold text-[#191c1e] tracking-tight">
              Calibration History & Long-Term Stability Comparison
            </h1>
            <p className="text-xs text-[#576065] font-mono mt-1">
              6 Retained Calibration Cycles (2018 - 2023) | Trend Drift Rate: +0.8 ppm / Year
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2.5 py-1 bg-[#dbe4ea] text-[#00435f] font-semibold rounded border border-[#c1c7ce] flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              <span>Next Due: {activeInstrument.dueDate}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Charts & Matrix Content matching Image 15 */}
      <div className="p-4 space-y-4 max-w-7xl mx-auto w-full">
        {/* Top 2 Visual Charts Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Chart 1: Instrument Bias Progression */}
          <div className="bg-white border border-[#c1c7ce] rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <div>
                <h3 className="font-bold text-xs text-[#00435f]">Instrument Bias Progression (10V DC)</h3>
                <p className="text-[11px] text-[#576065] font-mono">Deviation in parts-per-million (ppm) with ±U error bars</p>
              </div>
              <span className="font-mono text-[10px] bg-[#e1e2e5] px-2 py-0.5 rounded text-[#41484d] border border-[#c1c7ce]">
                Spec: ± 3.0 ppm
              </span>
            </div>

            {/* Custom SVG Bias Chart */}
            <div className="h-52 bg-[#f9f9fc] border border-[#c1c7ce] rounded relative p-3 font-mono text-[10px] flex flex-col justify-between overflow-hidden">
              <div className="flex justify-between text-[#ba1a1a]">
                <span>+3.0 ppm (Spec Limit)</span>
              </div>
              <div className="flex justify-between text-[#576065] border-b border-dashed border-[#c1c7ce] pb-0.5">
                <span>0.0 ppm (Nominal)</span>
              </div>
              <div className="flex justify-between text-[#ba1a1a]">
                <span>-3.0 ppm (Spec Limit)</span>
              </div>

              {/* Chart Lines and Points */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
                <line x1="0" y1="20%" x2="100%" y2="20%" stroke="#ba1a1a" strokeDasharray="3 3" strokeWidth="1" />
                <line x1="0" y1="50%" x2="100%" y2="50%" stroke="#71787e" strokeWidth="1" />
                <line x1="0" y1="80%" x2="100%" y2="80%" stroke="#ba1a1a" strokeDasharray="3 3" strokeWidth="1" />

                {/* Polyline */}
                <polyline
                  fill="none"
                  stroke="#00435f"
                  strokeWidth="2"
                  points="40,115 100,95 160,80 220,65 280,85 340,30"
                />

                {/* Error bar whiskers & Points */}
                {historyCycles.map((c, idx) => {
                  const x = 40 + idx * 60;
                  const y = 100 - (c.biasPpm / 6) * 100;
                  return (
                    <g key={c.cycle}>
                      {/* Whisker */}
                      <line x1={x} y1={y - 12} x2={x} y2={y + 12} stroke="#71787e" strokeWidth="1.5" />
                      <line x1={x - 4} y1={y - 12} x2={x + 4} y2={y - 12} stroke="#71787e" strokeWidth="1.5" />
                      <line x1={x - 4} y1={y + 12} x2={x + 4} y2={y + 12} stroke="#71787e" strokeWidth="1.5" />
                      {/* Point */}
                      <circle cx={x} cy={y} r="4" fill={c.biasPpm > 3.0 ? '#ba1a1a' : '#00435f'} />
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Chart 2: Expanded Uncertainty Trend */}
          <div className="bg-white border border-[#c1c7ce] rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <div>
                <h3 className="font-bold text-xs text-[#00435f]">Expanded Uncertainty (U) Trend</h3>
                <p className="text-[11px] text-[#576065] font-mono">Calibrated laboratory capability per annual cycle</p>
              </div>
              <span className="font-mono text-[10px] bg-[#dbe4ea] text-[#00435f] px-2 py-0.5 rounded font-bold">
                k = 2.00
              </span>
            </div>

            <div className="h-52 bg-[#f9f9fc] border border-[#c1c7ce] rounded p-4 flex items-end justify-between gap-4">
              {historyCycles.map((c) => (
                <div key={c.cycle} className="flex-1 flex flex-col items-center h-full justify-end group">
                  <div className="text-[9px] font-mono text-[#576065] mb-1">
                    {c.expandedUncertaintyPpm.toFixed(1)}
                  </div>
                  <div
                    className="w-full bg-[#00435f] hover:bg-[#245b78] rounded-t transition-all"
                    style={{ height: `${(c.expandedUncertaintyPpm / 5.0) * 100}%` }}
                  ></div>
                  <div className="text-[10px] font-mono font-semibold text-[#191c1e] mt-2">
                    {c.cycle}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Stability Comparison Matrix Table matching Image 15 */}
        <div className="bg-white border border-[#c1c7ce] rounded-lg overflow-hidden">
          <div className="p-3 bg-[#f3f4f2] border-b border-[#c1c7ce] flex justify-between items-center">
            <h3 className="font-bold text-xs text-[#00435f]">
              Stability Comparison Matrix (Multi-Voltage Points)
            </h3>
            <span className="font-mono text-[10px] text-[#576065]">
              Baseline: CY-18 | Current: CY-23
            </span>
          </div>

          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-[#e1e5e3] text-[#41484d] border-b border-[#c1c7ce]">
                <th className="py-2 px-3 font-semibold">TEST POINT</th>
                <th className="py-2 px-3 font-semibold">BASELINE (CY-18)</th>
                <th className="py-2 px-3 font-semibold">PREVIOUS (CY-22)</th>
                <th className="py-2 px-3 font-semibold">CURRENT (CY-23)</th>
                <th className="py-2 px-3 font-semibold">Δ vs PREV</th>
                <th className="py-2 px-3 font-semibold">Δ vs BASELINE</th>
                <th className="py-2 px-3 font-semibold">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#c1c7ce]">
              {stabilityMatrix.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#f3f4f2]">
                  <td className="py-2.5 px-3 font-bold text-[#191c1e]">{row.pointName}</td>
                  <td className="py-2.5 px-3 text-[#576065]">{row.baselineVal.toFixed(6)} V</td>
                  <td className="py-2.5 px-3 text-[#576065]">{row.prevVal.toFixed(6)} V</td>
                  <td className="py-2.5 px-3 font-bold text-[#00435f]">{row.currentVal.toFixed(6)} V</td>
                  <td className="py-2.5 px-3 text-[#576065]">
                    {row.deltaPrev >= 0 ? `+${row.deltaPrev.toFixed(6)}` : row.deltaPrev.toFixed(6)} V
                  </td>
                  <td className="py-2.5 px-3 text-[#576065]">
                    {row.deltaBaseline >= 0 ? `+${row.deltaBaseline.toFixed(6)}` : row.deltaBaseline.toFixed(6)} V
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 ${
                        row.status === 'DRIFT_WARNING'
                          ? 'bg-[#ffdad6] text-[#ba1a1a]'
                          : 'bg-[#dbe4ea] text-[#4a7c59]'
                      }`}
                    >
                      {row.status === 'DRIFT_WARNING' ? (
                        <>
                          <AlertTriangle className="w-2.5 h-2.5" />
                          <span>DRIFT WARNING</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-2.5 h-2.5" />
                          <span>STABLE</span>
                        </>
                      )}
                    </span>
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

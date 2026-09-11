import React, { useState } from 'react';
import {
  Activity,
  BarChart,
  CheckCircle2,
  HelpCircle,
  Lock,
  Plus,
  RotateCcw,
  Sparkles,
  Sliders,
  ShieldAlert,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';
import { DistributionType, UncertaintySource } from '../../types';

export const CalculationWorkspace: React.FC = () => {
  const {
    uncertaintySources,
    updateUncertaintySource,
    addUncertaintySource,
    combinedUc,
    expandedU,
    effectiveDof,
    selectedMeasurement,
    setActiveWorkspace,
  } = useMetrology();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<UncertaintySource | null>(null);

  const measuredVal = selectedMeasurement ? selectedMeasurement.measured : 10.0021;

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingSource) {
      updateUncertaintySource(editingSource.id, editingSource);
      setIsEditModalOpen(false);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#f4f5f3]">
      {/* Main Budget & Calculation Section */}
      <div className="flex-1 flex flex-col overflow-y-auto border-r border-[#c1c7ce]">
        {/* Canonical Result Banner matching Image 23 */}
        <div className="p-4 bg-white border-b border-[#c1c7ce]">
          <div className="flex justify-between items-center mb-3">
            <div>
              <span className="font-mono text-xs text-[#576065] uppercase">
                GUM Framework Uncertainty Analysis (JCGM 100:2008)
              </span>
              <h2 className="text-lg font-bold text-[#191c1e] tracking-tight">
                Canonical Calibration Result & Budget
              </h2>
            </div>
            <span className="font-mono text-xs px-2.5 py-1 bg-[#dbe4ea] text-[#00435f] font-semibold rounded border border-[#c1c7ce] flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" />
              <span>Computation Secure</span>
            </span>
          </div>

          {/* 5 Result Metric Cards */}
          <div className="grid grid-cols-5 gap-2.5">
            <div className="p-2.5 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="text-[10px] text-[#576065] font-mono uppercase">MEASURED VALUE</div>
              <div className="font-mono text-base font-bold text-[#191c1e] mt-0.5">
                {measuredVal.toFixed(4)} V
              </div>
            </div>

            <div className="p-2.5 bg-[#dbe4ea]/50 border border-[#00435f]/30 rounded">
              <div className="text-[10px] text-[#00435f] font-mono uppercase font-semibold">
                EXPANDED UNCERTAINTY (U)
              </div>
              <div className="font-mono text-base font-bold text-[#00435f] mt-0.5">
                ± {expandedU.toFixed(4)} V
              </div>
            </div>

            <div className="p-2.5 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="text-[10px] text-[#576065] font-mono uppercase">COVERAGE FACTOR</div>
              <div className="font-mono text-base font-bold text-[#191c1e] mt-0.5">
                k = 2.00
              </div>
            </div>

            <div className="p-2.5 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="text-[10px] text-[#576065] font-mono uppercase">CONFIDENCE LEVEL</div>
              <div className="font-mono text-base font-bold text-[#191c1e] mt-0.5">
                95.45 %
              </div>
            </div>

            <div className="p-2.5 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
              <div className="text-[10px] text-[#576065] font-mono uppercase">EFFECTIVE DOF</div>
              <div className="font-mono text-base font-bold text-[#191c1e] mt-0.5">
                {effectiveDof === 'inf' ? '∞' : effectiveDof}
              </div>
            </div>
          </div>
        </div>

        {/* Uncertainty Budget Table matching Image 23 */}
        <div className="p-4 space-y-4">
          <div className="bg-white border border-[#c1c7ce] rounded-lg overflow-hidden">
            <div className="p-3 bg-[#f3f4f2] border-b border-[#c1c7ce] flex justify-between items-center">
              <h3 className="font-bold text-xs text-[#00435f]">Uncertainty Budget Elements (X_i)</h3>
              <button
                onClick={() => {
                  setEditingSource({
                    id: '',
                    name: 'New Component',
                    symbol: 'δX',
                    estimate: 0,
                    estimateStr: '0.0000',
                    unit: 'V',
                    distribution: 'Normal',
                    stdUncertainty: 0.001,
                    degreesOfFreedom: 'inf',
                    sensitivityCoeff: 1.0,
                    contribution: 0.001,
                    type: 'B',
                  });
                  setIsEditModalOpen(true);
                }}
                className="px-2.5 py-1 text-xs font-semibold bg-white border border-[#c1c7ce] text-[#00435f] rounded hover:bg-[#e7e8e6] flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3 h-3" />
                <span>Add Source</span>
              </button>
            </div>

            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="bg-[#e1e5e3] text-[#41484d] border-b border-[#c1c7ce]">
                  <th className="py-2 px-3 font-semibold">SOURCE (X_i)</th>
                  <th className="py-2 px-3 font-semibold">ESTIMATE (x_i)</th>
                  <th className="py-2 px-3 font-semibold">DISTRIBUTION</th>
                  <th className="py-2 px-3 font-semibold">STD UNCERTAINTY u(x_i)</th>
                  <th className="py-2 px-3 font-semibold">SENSITIVITY (c_i)</th>
                  <th className="py-2 px-3 font-semibold">CONTRIBUTION u_i(y)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#c1c7ce]">
                {uncertaintySources.map((src) => (
                  <tr
                    key={src.id}
                    onClick={() => {
                      setEditingSource(src);
                      setIsEditModalOpen(true);
                    }}
                    className="hover:bg-[#f3f4f2] cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3">
                      <div className="font-bold text-[#191c1e]">{src.name}</div>
                      <div className="text-[10px] text-[#576065]">{src.symbol} (Type {src.type})</div>
                    </td>
                    <td className="py-2.5 px-3 text-[#191c1e]">
                      {src.estimateStr || `${src.estimate.toFixed(4)} ${src.unit}`}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#e1e2e5] text-[#41484d] border border-[#c1c7ce]">
                        {src.distribution}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[#191c1e]">
                      {src.stdUncertainty.toFixed(4)} {src.unit}
                    </td>
                    <td className="py-2.5 px-3 text-[#576065]">{src.sensitivityCoeff}</td>
                    <td className="py-2.5 px-3 font-bold text-[#00435f]">
                      {(src.contribution || 0).toFixed(4)} V
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-[#e1e5e3] text-[#191c1e] border-t-2 border-[#00435f] font-bold">
                  <td colSpan={5} className="py-2.5 px-3 text-right text-[#00435f]">
                    COMBINED STANDARD UNCERTAINTY u_c(y):
                  </td>
                  <td className="py-2.5 px-3 text-base text-[#00435f]">
                    {combinedUc.toFixed(4)} V
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      {/* Right Inspector Panel matching Image 23 */}
      <div className="w-[340px] bg-[#f3f4f2] flex flex-col shrink-0 select-none overflow-y-auto p-4 space-y-4 font-mono text-xs">
        {/* Pareto Variance Contributions */}
        <div>
          <div className="text-[10px] text-[#576065] uppercase font-bold tracking-wider mb-2">
            Variance Contributions (%)
          </div>
          <div className="bg-white border border-[#c1c7ce] rounded p-3 space-y-2.5">
            {uncertaintySources.map((src) => (
              <div key={src.id} className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-[#191c1e] truncate">{src.name}</span>
                  <span className="font-bold text-[#00435f]">{src.variancePercent || 0}%</span>
                </div>
                <div className="h-2 bg-[#e1e2e5] rounded overflow-hidden">
                  <div
                    className="h-full bg-[#00435f] rounded"
                    style={{ width: `${Math.min(100, Math.max(2, src.variancePercent || 0))}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Method Comparison: GUM vs MCM */}
        <div>
          <div className="text-[10px] text-[#576065] uppercase font-bold tracking-wider mb-2">
            Method Comparison
          </div>
          <div className="bg-white border border-[#c1c7ce] rounded overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#e1e5e3] text-[#576065] border-b border-[#c1c7ce]">
                  <th className="p-2">Param</th>
                  <th className="p-2">GUM</th>
                  <th className="p-2">MCM (10⁵)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#c1c7ce] text-[11px]">
                <tr>
                  <td className="p-2 text-[#576065]">Estimate</td>
                  <td className="p-2 font-bold">{measuredVal.toFixed(4)} V</td>
                  <td className="p-2">10.0020 V</td>
                </tr>
                <tr>
                  <td className="p-2 text-[#576065]">Uncertainty (u)</td>
                  <td className="p-2 font-bold">{combinedUc.toFixed(4)} V</td>
                  <td className="p-2">0.0041 V</td>
                </tr>
                <tr>
                  <td className="p-2 text-[#576065]">Coverage</td>
                  <td className="p-2">k=2.00</td>
                  <td className="p-2">Numeric 95%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Analysis Assistant Note */}
        <div className="bg-[#dbe4ea] border border-[#c1c7ce] rounded p-3 text-[11px] text-[#00435f] space-y-1 font-sans">
          <div className="font-bold flex items-center gap-1 font-mono text-xs">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Analysis Assistant</span>
          </div>
          <p className="leading-relaxed">
            The dominant contributor is <strong>Resolution (UUT)</strong> accounting for over 50% of the total budget variance. Consider increasing multi-slope integration cycles to reduce quantization error.
          </p>
        </div>

        <button
          onClick={() => setActiveWorkspace('monte-carlo')}
          className="w-full py-2 bg-[#00435f] text-white rounded font-semibold flex items-center justify-center gap-2 hover:bg-[#245b78] cursor-pointer"
        >
          <span>Run Monte Carlo Check</span>
        </button>
      </div>

      {/* Edit Component Modal */}
      {isEditModalOpen && editingSource && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleSaveEdit}
            className="bg-white border border-[#c1c7ce] rounded-lg shadow-xl w-full max-w-md overflow-hidden"
          >
            <div className="p-4 bg-[#f3f4f2] border-b border-[#c1c7ce] flex justify-between items-center">
              <h3 className="font-bold text-sm text-[#00435f]">Edit Uncertainty Element</h3>
              <button
                type="button"
                onClick={() => setIsEditModalOpen(false)}
                className="text-[#576065] hover:text-[#191c1e]"
              >
                ✕
              </button>
            </div>

            <div className="p-4 space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[#576065] mb-1">Source Name:</label>
                <input
                  type="text"
                  value={editingSource.name}
                  onChange={(e) => setEditingSource({ ...editingSource, name: e.target.value })}
                  className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[#576065] mb-1">Std Uncertainty (u_i):</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={editingSource.stdUncertainty}
                    onChange={(e) =>
                      setEditingSource({
                        ...editingSource,
                        stdUncertainty: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[#576065] mb-1">Sensitivity (c_i):</label>
                  <input
                    type="number"
                    step="0.001"
                    value={editingSource.sensitivityCoeff}
                    onChange={(e) =>
                      setEditingSource({
                        ...editingSource,
                        sensitivityCoeff: parseFloat(e.target.value) || 1.0,
                      })
                    }
                    className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-[#576065] mb-1">Probability Distribution:</label>
                <select
                  value={editingSource.distribution}
                  onChange={(e) =>
                    setEditingSource({
                      ...editingSource,
                      distribution: e.target.value as DistributionType,
                    })
                  }
                  className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
                >
                  <option value="Normal">Normal (Gaussian)</option>
                  <option value="Rectangular">Rectangular (Uniform)</option>
                  <option value="U-Shape">U-Shape (Sine)</option>
                  <option value="Triangular">Triangular</option>
                </select>
              </div>
            </div>

            <div className="p-3 bg-[#f3f4f2] border-t border-[#c1c7ce] flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsEditModalOpen(false)}
                className="px-3 py-1.5 text-xs text-[#576065] hover:bg-[#e1e2e5] rounded cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 text-xs font-semibold bg-[#00435f] text-white rounded hover:bg-[#245b78] cursor-pointer"
              >
                Apply Updates
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

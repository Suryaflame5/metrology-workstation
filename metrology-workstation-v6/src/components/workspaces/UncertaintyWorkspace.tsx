import React, { useState } from 'react';
import {
  Calculator,
  CheckCircle2,
  ArrowDown,
  Info,
  Layers,
  HelpCircle,
  Inbox,
  ArrowRight,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const UncertaintyWorkspace: React.FC = () => {
  const { selectedJob, uncertaintySources, combinedUc, expandedU, effectiveDof, setActiveWorkspace } = useMetrology();
  const [coverageFactorK, setCoverageFactorK] = useState(2.0);

  const budgetItems = selectedJob?.uncertainty_budget?.budget_breakdown?.length
    ? selectedJob.uncertainty_budget.budget_breakdown.map((b) => ({
        source: b.name,
        type: b.name.includes('Type A') || b.name.includes('Repeatability') ? 'A' : 'B',
        distribution: b.distribution || 'Normal',
        standard: `${b.standard_uncertainty.toFixed(6)} ${selectedJob?.unit || 'V'}`,
        sensitivity: (b.sensitivity_coefficient ?? 1.0).toFixed(2),
        contribution: `${(b.standard_uncertainty * (b.sensitivity_coefficient ?? 1.0)).toFixed(6)} ${selectedJob?.unit || 'V'}`,
        variancePct: b.variance_percent ?? 0,
      }))
    : uncertaintySources.map((s) => ({
        source: s.name,
        type: s.distribution === 'Normal' ? 'A' : 'B',
        distribution: s.distribution,
        standard: `${s.estimate.toFixed(6)} ${s.unit}`,
        sensitivity: s.sensitivity.toFixed(2),
        contribution: `${(s.estimate * s.sensitivity).toFixed(6)} ${s.unit}`,
        variancePct: (s as any).variancePercent ?? 0,
      }));

  const measurandTitle = selectedJob
    ? `${selectedJob.title || selectedJob.instrument_name} (${selectedJob.nominal_value} ${selectedJob.unit || 'V'})`
    : 'DC Voltage Standard (10 V Nominal)';

  const ucVal = selectedJob?.uncertainty_budget?.combined_uncertainty_uc ?? combinedUc;
  const expVal = selectedJob?.uncertainty_budget?.expanded_uncertainty_U95 ?? expandedU;
  const kVal = selectedJob?.uncertainty_budget?.coverage_factor_k ?? coverageFactorK;
  const dofVal = selectedJob?.uncertainty_budget?.effective_dof ?? effectiveDof;
  const meanVal = selectedJob?.statistics?.mean ?? (selectedJob?.nominal_value ?? 10.0);
  const devVal = selectedJob?.conformity?.error_of_indication ?? (meanVal - (selectedJob?.nominal_value ?? 10.0));
  const unitStr = selectedJob?.unit || 'V';

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-y-auto custom-scrollbar p-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-[#E2E5E9]">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
            ISO/IEC Guide 98-3 (GUM)
          </span>
          <span className="text-xs text-[#656B73]">Evaluation of Measurement Data</span>
        </div>
        <h1 className="text-xl font-bold text-[#17191C] mt-1 tracking-tight">
          Measurement Uncertainty &mdash; {selectedJob?.job_number || 'General Assessment'}
        </h1>
      </div>

      {/* Top Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider block">
            MEASURAND
          </span>
          <div className="text-base font-bold text-[#17191C] mt-1.5 truncate">
            {measurandTitle}
          </div>
          <div className="text-xs text-[#656B73] mt-0.5 font-mono">
            Model: y = x̄_DUT + δ_cal + δ_res + δ_temp
          </div>
        </div>

        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider block">
            CALIBRATED RESULT (MEAN)
          </span>
          <div className="text-2xl font-extrabold text-[#17191C] font-mono tabular-nums mt-1">
            {meanVal.toFixed(5)} <span className="text-sm font-semibold text-[#00435F]">{unitStr}</span>
          </div>
          <div className="text-xs text-[#656B73] mt-0.5 font-mono">
            Deviation: {devVal >= 0 ? `+${devVal.toFixed(6)}` : devVal.toFixed(6)} {unitStr}
          </div>
        </div>

        <div className="bg-white border border-[#E2E5E9] rounded-lg p-4 shadow-xs">
          <span className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider block">
            EXPANDED UNCERTAINTY (U₉₅)
          </span>
          <div className="text-2xl font-extrabold text-[#00435F] font-mono tabular-nums mt-1">
            &plusmn;{expVal.toFixed(5)} <span className="text-sm font-semibold text-[#656B73]">{unitStr}</span>
          </div>
          <div className="text-xs text-[#656B73] mt-0.5 font-mono">
            k = {typeof kVal === 'number' ? kVal.toFixed(2) : kVal} &bull; Level of Confidence: 95.45%
          </div>
        </div>
      </div>

      {/* Uncertainty Budget Table */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden mt-6">
        <div className="p-4 border-b border-[#E2E5E9] bg-[#FAFAFA] flex items-center justify-between">
          <div>
            <h2 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
              UNCERTAINTY BUDGET (GUM SECTION 4 & 5)
            </h2>
            <p className="text-[11px] text-[#656B73] mt-0.5">Component breakdown and variance contributions</p>
          </div>
          <span className="text-xs font-mono font-semibold text-[#00435F] bg-[#EBF3F6] px-2.5 py-1 rounded border border-[#CBD5E1]">
            Combined u_c = {ucVal.toFixed(6)} {unitStr}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#F7F8FA] border-b border-[#E2E5E9] text-[#656B73] font-semibold">
              <tr>
                <th className="py-2.5 px-3.5 font-medium">Uncertainty Source</th>
                <th className="py-2.5 px-3.5 font-medium">Type</th>
                <th className="py-2.5 px-3.5 font-medium">Distribution</th>
                <th className="py-2.5 px-3.5 font-medium">Standard Uncertainty u(xᵢ)</th>
                <th className="py-2.5 px-3.5 font-medium">Sensitivity cᵢ</th>
                <th className="py-2.5 px-3.5 font-medium">Contribution uᵢ(y)</th>
                <th className="py-2.5 px-3.5 font-medium text-right">Variance %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E5E9]">
              {budgetItems.map((item, idx) => (
                <tr key={idx} className="hover:bg-[#F9FAFB] transition-colors">
                  <td className="py-2.5 px-3.5 font-semibold text-[#17191C]">
                    {item.source}
                  </td>
                  <td className="py-2.5 px-3.5 font-mono font-bold text-[#00435F]">
                    {item.type}
                  </td>
                  <td className="py-2.5 px-3.5 text-[#656B73]">
                    {item.distribution}
                  </td>
                  <td className="py-2.5 px-3.5 font-mono tabular-nums text-[#17191C]">
                    {item.standard}
                  </td>
                  <td className="py-2.5 px-3.5 font-mono text-[#656B73]">
                    {item.sensitivity}
                  </td>
                  <td className="py-2.5 px-3.5 font-mono tabular-nums font-semibold text-[#17191C]">
                    {item.contribution}
                  </td>
                  <td className="py-2.5 px-3.5 text-right font-mono tabular-nums font-semibold text-[#00435F]">
                    {item.variancePct.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Calculation Chain Flow (21st.dev calculation chain representation) */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs mt-6">
        <h2 className="text-xs font-bold text-[#17191C] uppercase tracking-wider mb-4">
          MATHEMATICAL CALCULATION CHAIN
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs">
          <div className="p-2.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
            <span className="text-[10px] text-[#656B73] uppercase block font-semibold">1. Input</span>
            <span className="font-mono font-bold text-xs text-[#17191C] mt-1 block">5 Readings</span>
          </div>
          <div className="p-2.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
            <span className="text-[10px] text-[#656B73] uppercase block font-semibold">2. Std Unc</span>
            <span className="font-mono font-bold text-xs text-[#17191C] mt-1 block">u_i(x)</span>
          </div>
          <div className="p-2.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
            <span className="text-[10px] text-[#656B73] uppercase block font-semibold">3. Sensitivity</span>
            <span className="font-mono font-bold text-xs text-[#17191C] mt-1 block">c_i = 1.0</span>
          </div>
          <div className="p-2.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
            <span className="text-[10px] text-[#656B73] uppercase block font-semibold">4. Variance</span>
            <span className="font-mono font-bold text-xs text-[#17191C] mt-1 block">u_i²(y)</span>
          </div>
          <div className="p-2.5 bg-[#EBF3F6] border border-[#00435F] rounded">
            <span className="text-[10px] text-[#00435F] uppercase block font-semibold">5. Combined</span>
            <span className="font-mono font-bold text-xs text-[#00435F] mt-1 block">0.000155 V</span>
          </div>
          <div className="p-2.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
            <span className="text-[10px] text-[#656B73] uppercase block font-semibold">6. Welch-Sat</span>
            <span className="font-mono font-bold text-xs text-[#17191C] mt-1 block">ν_eff = 68</span>
          </div>
          <div className="p-2.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded">
            <span className="text-[10px] text-[#656B73] uppercase block font-semibold">7. Coverage</span>
            <span className="font-mono font-bold text-xs text-[#17191C] mt-1 block">k = 2.0</span>
          </div>
          <div className="p-2.5 bg-[#F0FDF4] border border-[#BBF7D0] rounded">
            <span className="text-[10px] text-[#16A34A] uppercase block font-semibold">8. Expanded</span>
            <span className="font-mono font-bold text-xs text-[#16A34A] mt-1 block">±0.00031 V</span>
          </div>
        </div>
      </div>
    </div>
  );
};

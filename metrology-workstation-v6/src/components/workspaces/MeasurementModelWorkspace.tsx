import React from 'react';
import { GitFork, Layers, Lock, Sparkles, Sliders } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const MeasurementModelWorkspace: React.FC = () => {
  const { uncertaintySources, selectedJob } = useMetrology();

  const unit = selectedJob?.unit || 'V';
  const measurandName = selectedJob?.title || 'Precision Calibration Transfer Model';
  const formula = `${unit}_meas = ${unit}_ref + δ${unit}_res + α·(T - T_0) + δ${unit}_drift + s_p`;

  const budgetComponents = selectedJob?.uncertainty_budget?.components || [];

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            TRANSFER FUNCTION MODEL
          </span>
          <span className="text-xs font-semibold text-[#576065]">
            JCGM 100:2008 Functional Relationship Y = f(X1, X2, ..., Xn)
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] tracking-tight">
          {measurandName}
        </h1>

        {/* Model Equation Display Card */}
        <div className="mt-4 p-4 bg-[#f9f9fc] border border-[#c1c7ce] rounded-lg font-mono text-center">
          <div className="text-xs text-[#576065] mb-1 uppercase tracking-wider">
            Canonical Transfer Equation
          </div>
          <div className="text-lg font-bold text-[#00435f]">
            {formula}
          </div>
        </div>
      </div>

      {/* Partial Derivatives Matrix */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg overflow-hidden">
        <div className="p-3 bg-[#f3f4f2] border-b border-[#c1c7ce] flex justify-between items-center">
          <h3 className="font-bold text-xs text-[#00435f]">
            First-Order Sensitivity Coefficients (c_i = ∂f / ∂X_i)
          </h3>
          <span className="font-mono text-[10px] text-[#576065]">Taylor Series First Order</span>
        </div>

        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="bg-[#e1e5e3] text-[#41484d] border-b border-[#c1c7ce]">
              <th className="py-2.5 px-3">INPUT QUANTITY (X_i)</th>
              <th className="py-2.5 px-3">PARTIAL DERIVATIVE (∂f/∂X_i)</th>
              <th className="py-2.5 px-3">SENSITIVITY VALUE (c_i)</th>
              <th className="py-2.5 px-3">EVALUATION BASELINE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#c1c7ce]">
            {budgetComponents.length > 0
              ? budgetComponents.map((src: any, idx: number) => (
                  <tr key={idx} className="hover:bg-[#f3f4f2]">
                    <td className="py-2.5 px-3 font-bold text-[#191c1e]">
                      {src.name || src.source} ({src.symbol || `X_${idx + 1}`})
                    </td>
                    <td className="py-2.5 px-3 text-[#00435f] font-semibold">
                      ∂{unit}_meas / ∂{src.symbol || `X_${idx + 1}`}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-[#191c1e]">
                      {src.sensitivity_coefficient ?? src.sensitivityCoeff ?? 1.0}
                    </td>
                    <td className="py-2.5 px-3 text-[#576065]">
                      {src.value ?? src.estimate ?? selectedJob?.nominal_value ?? 0} {unit}
                    </td>
                  </tr>
                ))
              : uncertaintySources.map((src) => (
                  <tr key={src.id} className="hover:bg-[#f3f4f2]">
                    <td className="py-2.5 px-3 font-bold text-[#191c1e]">
                      {src.name} ({src.symbol})
                    </td>
                    <td className="py-2.5 px-3 text-[#00435f] font-semibold">
                      ∂{unit}_meas / ∂{src.symbol}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-[#191c1e]">
                      {src.sensitivityCoeff}
                    </td>
                    <td className="py-2.5 px-3 text-[#576065]">
                      {src.estimateStr || `${src.estimate} ${src.unit}`}
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

import React from 'react';
import { GitCompare, Layers, TrendingUp } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const ComparisonWorkspace: React.FC = () => {
  const { stabilityMatrix } = useMetrology();

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-6xl mx-auto">
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            COMPARISON WORKSPACE
          </span>
          <span className="text-xs font-semibold text-[#576065]">
            Cross-Run Differential Analysis
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] tracking-tight">
          Run 41 (Previous) vs Run 42 (Current Active Run)
        </h1>
      </div>

      <div className="bg-white border border-[#c1c7ce] rounded-lg overflow-hidden font-mono text-xs">
        <div className="p-3 bg-[#f3f4f2] border-b border-[#c1c7ce] font-bold text-[#00435f]">
          Statistical Differences & Deviations
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#e1e5e3] text-[#41484d] border-b border-[#c1c7ce]">
              <th className="p-2.5">PARAMETER</th>
              <th className="p-2.5">RUN 41 (2023-05-12)</th>
              <th className="p-2.5">RUN 42 (2023-10-27)</th>
              <th className="p-2.5">DIFFERENCE (Δ)</th>
              <th className="p-2.5">DRIFT EVALUATION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#c1c7ce]">
            <tr className="hover:bg-[#f3f4f2]">
              <td className="p-2.5 font-bold">Mean Voltage (10V)</td>
              <td className="p-2.5 text-[#576065]">10.00004 V</td>
              <td className="p-2.5 font-bold text-[#00435f]">10.00015 V</td>
              <td className="p-2.5 text-[#ba1a1a]">+0.00011 V (+11 ppm)</td>
              <td className="p-2.5 text-[#ba1a1a] font-bold">DRIFT DETECTED</td>
            </tr>
            <tr className="hover:bg-[#f3f4f2]">
              <td className="p-2.5 font-bold">Standard Deviation (Type A)</td>
              <td className="p-2.5 text-[#576065]">0.00075 V</td>
              <td className="p-2.5 font-bold text-[#00435f]">0.00080 V</td>
              <td className="p-2.5 text-[#576065]">+0.00005 V</td>
              <td className="p-2.5 text-[#4a7c59] font-bold">CONSISTENT</td>
            </tr>
            <tr className="hover:bg-[#f3f4f2]">
              <td className="p-2.5 font-bold">Expanded Uncertainty (U)</td>
              <td className="p-2.5 text-[#576065]">0.0080 V</td>
              <td className="p-2.5 font-bold text-[#00435f]">0.0082 V</td>
              <td className="p-2.5 text-[#576065]">+0.0002 V</td>
              <td className="p-2.5 text-[#4a7c59] font-bold">COMPLIANT</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

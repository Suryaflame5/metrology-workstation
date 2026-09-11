import React from 'react';
import { Gauge, Shield, ShieldCheck, HelpCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const GuardbandTURWorkspace: React.FC = () => {
  const { conformityConfig, expandedU } = useMetrology();

  const turValue = conformityConfig.specTolerance / (expandedU || 0.0025);
  const isTurCompliant = turValue >= 4.0;

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-6xl mx-auto">
      {/* TUR Header */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            TUR & GUARDBAND ANALYSIS
          </span>
          <span className="text-xs font-semibold text-[#576065]">
            ANSI/NCSL Z540.3 & ILAC-G8:09 Risk Metrics
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] tracking-tight">
          Test Uncertainty Ratio (TUR) & Probability of False Acceptance (PFA)
        </h1>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="p-4 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
            <div className="text-[10px] text-[#576065] font-mono uppercase">Calculated TUR</div>
            <div className="font-mono text-2xl font-bold text-[#00435f] mt-1">
              {turValue.toFixed(2)} : 1
            </div>
            <div className="text-[11px] text-[#576065] font-mono mt-1">
              Formula: Specification Tolerance / Expanded U
            </div>
          </div>

          <div className="p-4 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
            <div className="text-[10px] text-[#576065] font-mono uppercase">4:1 Rule Compliance</div>
            <div
              className={`font-mono text-2xl font-bold mt-1 flex items-center gap-1.5 ${
                isTurCompliant ? 'text-[#4a7c59]' : 'text-[#ba1a1a]'
              }`}
            >
              {isTurCompliant ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
              <span>{isTurCompliant ? 'COMPLIANT' : 'MARGINAL'}</span>
            </div>
            <div className="text-[11px] text-[#576065] font-mono mt-1">
              ANSI/NCSL Z540.3 Standard
            </div>
          </div>

          <div className="p-4 bg-[#f3f4f2] border border-[#c1c7ce] rounded">
            <div className="text-[10px] text-[#576065] font-mono uppercase">Global Consumer Risk</div>
            <div className="font-mono text-2xl font-bold text-[#191c1e] mt-1">
              &lt; 0.05 %
            </div>
            <div className="text-[11px] text-[#4a7c59] font-mono mt-1">
              Probability of False Acceptance (PFA)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

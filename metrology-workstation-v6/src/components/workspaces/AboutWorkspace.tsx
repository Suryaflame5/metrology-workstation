import React from 'react';
import { Info, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const AboutWorkspace: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-4xl mx-auto font-mono text-xs">
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            METROLOGY WORKSTATION V6.0.42
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] font-sans tracking-tight">
          About Metrology Workstation V6
        </h1>
        <p className="text-[#576065] text-xs mt-1">
          Engineered for ISO/IEC 17025 accredited laboratories and precision calibration facilities.
        </p>
      </div>

      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5 space-y-3">
        <h3 className="font-bold text-xs text-[#00435f] uppercase tracking-wider font-sans">
          Supported International Standards & Mathematical Guides
        </h3>
        <ul className="space-y-2 text-[#191c1e]">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#4a7c59]" />
            <span><strong>JCGM 100:2008 (GUM)</strong> — Evaluation of measurement data — Guide to the expression of uncertainty in measurement</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#4a7c59]" />
            <span><strong>JCGM 101:2008</strong> — Propagation of distributions using a Monte Carlo method</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#4a7c59]" />
            <span><strong>ISO 14253-1:2017</strong> — Decision rules for proving conformity or non-conformity with specifications</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#4a7c59]" />
            <span><strong>ILAC-G8:09/2019</strong> — Guidelines on Decision Rules and Statements of Conformity</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#4a7c59]" />
            <span><strong>ANSI/NCSL Z540.3-2006</strong> — Requirements for the Calibration of Measuring and Test Equipment</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#4a7c59]" />
            <span><strong>ISO/IEC 17025:2017</strong> — General requirements for the competence of testing and calibration laboratories</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

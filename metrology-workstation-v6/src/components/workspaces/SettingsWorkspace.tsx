import React from 'react';
import { Save, Settings, Sliders } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const SettingsWorkspace: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-4xl mx-auto font-mono text-xs">
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            SYSTEM CONFIGURATION
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] font-sans tracking-tight">
          Metrology Workstation Engineering Preferences
        </h1>
      </div>

      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5 space-y-4">
        <div>
          <label className="block text-[#576065] mb-1">Default Units System:</label>
          <select className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none">
            <option value="SI">Metric SI (Volts, Ohms, Amperes, °C)</option>
            <option value="US">US Customary (°F, psi)</option>
          </select>
        </div>

        <div>
          <label className="block text-[#576065] mb-1">Numerical Precision Display (Digits):</label>
          <input
            type="number"
            defaultValue={5}
            min={3}
            max={8}
            className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none"
          />
        </div>

        <div>
          <label className="block text-[#576065] mb-1">Coverage Probability Default (k):</label>
          <select className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none">
            <option value="2.00">k = 2.00 (95.45% Normal)</option>
            <option value="1.96">k = 1.96 (95.00% Exact Normal)</option>
            <option value="3.00">k = 3.00 (99.73% 3-Sigma)</option>
          </select>
        </div>

        <div>
          <label className="block text-[#576065] mb-1">Cryptographic Audit Ledger Mode:</label>
          <select className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none">
            <option value="SHA256">SHA-256 Strict Immutable Hashing</option>
            <option value="FAST">Local Rapid Session Log</option>
          </select>
        </div>
      </div>
    </div>
  );
};

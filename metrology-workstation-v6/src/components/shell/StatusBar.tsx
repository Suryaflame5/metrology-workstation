import React, { useEffect, useState } from 'react';
import { Activity, Globe, RefreshCw, Cpu, CheckCircle } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const StatusBar: React.FC = () => {
  const { activeInstrument, setIsDiagnosticsOpen } = useMetrology();
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStr(d.toISOString().substring(11, 19) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="bg-[#e1e5e3] border-t border-[#c1c7ce] h-8 w-full flex justify-between items-center px-4 z-30 shrink-0 font-mono text-[11px] text-[#191c1e] select-none">
      {/* Left System Health */}
      <div className="flex items-center gap-3">
        <span className="text-[#4a7c59] font-medium flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#4a7c59] animate-pulse"></span>
          SYSTEM STATUS: OPTIMAL
        </span>
        <span className="text-[#c1c7ce]">|</span>
        <span className="text-[#00435f] font-semibold">{activeInstrument.id} ACTIVE</span>
        <span className="text-[#c1c7ce]">|</span>
        <span className="text-[#576065]">UNITS: METRIC (SI)</span>
      </div>

      {/* Right Telemetry Controls */}
      <div className="flex items-center gap-4 text-[#576065]">
        <button
          onClick={() => setIsDiagnosticsOpen(true)}
          className="hover:text-[#00435f] hover:underline flex items-center gap-1 cursor-pointer transition-colors"
        >
          <Activity className="w-3 h-3 text-[#4a7c59]" />
          <span>Diagnostics</span>
        </button>

        <span className="flex items-center gap-1">
          <Globe className="w-3 h-3 text-[#576065]" />
          <span>Network (0.8 ms)</span>
        </span>

        <span className="flex items-center gap-1 text-[#4a7c59]">
          <RefreshCw className="w-3 h-3 animate-spin-slow" />
          <span>Sync: Synced</span>
        </span>

        <span className="text-[#41484d] font-semibold border-l border-[#c1c7ce] pl-3">
          {timeStr}
        </span>
      </div>
    </footer>
  );
};

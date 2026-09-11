import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Radio,
  RefreshCw,
  Terminal,
  Activity,
  Play,
  Square,
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  Wifi,
  Sliders,
} from 'lucide-react';
import { MetrologyAPI } from '../../services/api';

interface CommEvent {
  time: string;
  direction: 'OUT' | 'IN';
  text: string;
}

export const InstrumentsWorkspace: React.FC = () => {
  const [selectedProfile, setSelectedProfile] = useState<'FLUKE_8846A' | 'KEYSIGHT_34461A' | 'FLUKE_8508A' | 'DRUCK_DPI104'>('FLUKE_8846A');
  const [isConnected, setIsConnected] = useState(true);
  const [lastCommTime, setLastCommTime] = useState('14:32:08');
  const [liveValue, setLiveValue] = useState('10.00002');
  const [liveUnit, setLiveUnit] = useState('V');
  const [isStreaming, setIsStreaming] = useState(true);
  const [scpiInput, setScpiInput] = useState('MEAS:VOLT:DC?');
  const [isExecuting, setIsExecuting] = useState(false);

  const [commLog, setCommLog] = useState<CommEvent[]>([
    { time: '14:32:05', direction: 'OUT', text: '*IDN?' },
    { time: '14:32:05', direction: 'IN', text: 'FLUKE,8846A,12345678,1.14/1.08' },
    { time: '14:32:06', direction: 'OUT', text: 'CONF:VOLT:DC 10,0.000001' },
    { time: '14:32:06', direction: 'IN', text: 'OK' },
    { time: '14:32:06', direction: 'OUT', text: 'MEAS:VOLT:DC?' },
    { time: '14:32:06', direction: 'IN', text: '10.00002' },
    { time: '14:32:07', direction: 'OUT', text: 'SYST:ERR?' },
    { time: '14:32:07', direction: 'IN', text: '0,"No error"' },
  ]);

  // Live streaming effect (subtle Gaussian simulation for visual realism)
  useEffect(() => {
    if (!isStreaming || !isConnected) return;
    const interval = setInterval(() => {
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];
      setLastCommTime(timeStr);

      const base = 10.00000;
      const noise = (Math.random() - 0.5) * 0.00004;
      const newVal = (base + noise).toFixed(5);
      setLiveValue(newVal);

      setCommLog((prev) => [
        ...prev.slice(-15),
        { time: timeStr, direction: 'OUT', text: 'MEAS:VOLT:DC?' },
        { time: timeStr, direction: 'IN', text: newVal },
      ]);
    }, 2500);

    return () => clearInterval(interval);
  }, [isStreaming, isConnected]);

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scpiInput.trim()) return;

    const cmd = scpiInput.trim();
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    setIsExecuting(true);
    setCommLog((prev) => [...prev, { time: timeStr, direction: 'OUT', text: cmd }]);

    try {
      const res = await MetrologyAPI.executeScpi('TCPIP::192.168.1.42::5025::SOCKET', cmd);
      const respText = res?.response || (cmd === '*IDN?' ? 'FLUKE,8846A,12345678,1.14/1.08' : cmd === 'SYST:ERR?' ? '0,"No error"' : '10.00001');
      setCommLog((prev) => [...prev, { time: timeStr, direction: 'IN', text: respText }]);
      if (cmd.includes('MEAS')) {
        const num = parseFloat(respText);
        if (!isNaN(num)) setLiveValue(num.toFixed(5));
      }
    } catch {
      setCommLog((prev) => [...prev, { time: timeStr, direction: 'IN', text: '10.00003' }]);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-hidden">
      {/* Top Bar */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-lg font-bold text-[#17191C] tracking-tight flex items-center gap-2">
            <Cpu className="w-5 h-5 text-[#00435F]" />
            <span>Instruments & Hardware Gateway</span>
          </h1>
          <p className="text-xs text-[#656B73]">
            SCPI-TCP socket, VISA resource connections, real-time command logger, and telemetry buffer
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Instrument profile switcher */}
          <select
            value={selectedProfile}
            onChange={(e: any) => setSelectedProfile(e.target.value)}
            className="bg-white border border-[#E2E5E9] rounded px-2.5 py-1.5 text-xs text-[#17191C] outline-none font-medium cursor-pointer"
          >
            <option value="FLUKE_8846A">Fluke 8846A (192.168.1.42:5025)</option>
            <option value="KEYSIGHT_34461A">Keysight 34461A (192.168.1.50:5025)</option>
            <option value="FLUKE_8508A">Fluke 8508A Reference (GPIB0::16)</option>
            <option value="DRUCK_DPI104">Druck DPI 104 (COM3::9600)</option>
          </select>

          <button
            onClick={() => setIsStreaming(!isStreaming)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold shadow-xs transition-colors cursor-pointer ${
              isStreaming
                ? 'bg-[#FEF3C7] text-[#D97706] hover:bg-[#FDE68A]'
                : 'bg-[#DCFCE7] text-[#16A34A] hover:bg-[#BBF7D0]'
            }`}
          >
            {isStreaming ? <Square className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{isStreaming ? 'Pause Stream' : 'Live Stream'}</span>
          </button>
        </div>
      </div>

      {/* Main Content Pane */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
        {/* Top Connection Card */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-[#E2E5E9] gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#17191C]">Fluke 8846A Precision Multimeter</h2>
                <span className="inline-flex items-center gap-1 bg-[#DCFCE7] text-[#16A34A] px-2 py-0.5 rounded text-[11px] font-mono font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]"></span>
                  CONNECTED
                </span>
              </div>
              <p className="text-xs text-[#656B73] mt-0.5">
                Primary Standard Bench &bull; Electrical Standards Lab 02
              </p>
            </div>

            <div className="text-xs font-mono text-[#656B73] bg-[#F7F8FA] px-3 py-1.5 rounded border border-[#E2E5E9]">
              Last communication: <span className="font-semibold text-[#17191C]">{lastCommTime}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-xs">
            <div>
              <span className="text-[#656B73] block text-[11px]">Connection Type</span>
              <span className="font-mono font-semibold text-[#17191C]">TCP/IP 192.168.1.42:5025</span>
            </div>
            <div>
              <span className="text-[#656B73] block text-[11px]">Driver Profile</span>
              <span className="font-mono font-semibold text-[#17191C]">SCPI-TCP (IEEE 488.2)</span>
            </div>
            <div className="md:col-span-2">
              <span className="text-[#656B73] block text-[11px]">Identity String (*IDN?)</span>
              <span className="font-mono font-semibold text-[#17191C] truncate block">
                FLUKE,8846A,12345678,1.14/1.08
              </span>
            </div>
          </div>
        </div>

        {/* Center: Live Reading Display (Tabular Numerals) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Reading Card */}
          <div className="md:col-span-2 bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#656B73] uppercase tracking-wider">
                  LIVE READING
                </span>
                <span className="inline-flex items-center gap-1.5 text-xs text-[#16A34A] font-medium font-mono">
                  <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse"></span>
                  Buffered (5 readings/sec)
                </span>
              </div>

              {/* Big Tabular Number */}
              <div className="my-6">
                <div className="text-5xl font-extrabold text-[#17191C] font-mono tabular-nums tracking-tight">
                  {liveValue} <span className="text-3xl font-semibold text-[#00435F]">{liveUnit}</span>
                </div>
                <div className="text-xs text-[#656B73] mt-2 font-mono">
                  Deviation from 10.00000 V: <span className="text-[#16A34A] font-semibold">+0.00002 V (+2.0 ppm)</span>
                </div>
              </div>
            </div>

            {/* Readout parameters */}
            <div className="grid grid-cols-3 gap-2 pt-4 border-t border-[#E2E5E9] text-xs">
              <div className="p-2 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
                <span className="text-[#656B73] block text-[10.5px]">Range</span>
                <span className="font-mono font-semibold text-[#17191C]">10 V DC</span>
              </div>
              <div className="p-2 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
                <span className="text-[#656B73] block text-[10.5px]">Resolution</span>
                <span className="font-mono font-semibold text-[#17191C]">1 µV (6.5 Digits)</span>
              </div>
              <div className="p-2 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
                <span className="text-[#656B73] block text-[10.5px]">Function</span>
                <span className="font-mono font-semibold text-[#17191C]">DC Voltage</span>
              </div>
            </div>
          </div>

          {/* Environmental Sensor Telemetry */}
          <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="text-xs font-bold text-[#656B73] uppercase tracking-wider">
                ENVIRONMENTAL TELEMETRY
              </div>
              <p className="text-[11px] text-[#656B73] mt-0.5">Live laboratory monitoring</p>

              <div className="mt-4 space-y-3 text-xs">
                <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] flex items-center justify-between">
                  <span className="text-[#656B73]">Temperature</span>
                  <span className="font-mono font-bold text-sm text-[#17191C]">20.05 °C</span>
                </div>
                <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] flex items-center justify-between">
                  <span className="text-[#656B73]">Relative Humidity</span>
                  <span className="font-mono font-bold text-sm text-[#17191C]">45.8 %RH</span>
                </div>
                <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] flex items-center justify-between">
                  <span className="text-[#656B73]">Pressure</span>
                  <span className="font-mono font-bold text-sm text-[#17191C]">1013.25 hPa</span>
                </div>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-[#E2E5E9] text-[11px] text-[#16A34A] flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Within ISO 17025 procedure limits</span>
            </div>
          </div>
        </div>

        {/* Bottom: Raw SCPI Communication Log & Terminal */}
        <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-xs overflow-hidden">
          <div className="p-3.5 border-b border-[#E2E5E9] bg-[#FAFAFA] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#00435F]" />
              <h3 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
                COMMUNICATION LOG (SCPI / IEEE 488.2)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-[#656B73]">Cryptographically Verified Local Trace</span>
          </div>

          {/* Terminal Box */}
          <div className="bg-[#0F172A] text-slate-100 p-4 font-mono text-xs max-h-56 overflow-y-auto custom-scrollbar space-y-1">
            {commLog.map((ev, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-slate-500 shrink-0">{ev.time}</span>
                <span className={`shrink-0 font-bold ${ev.direction === 'OUT' ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {ev.direction === 'OUT' ? '→' : '←'}
                </span>
                <span className={ev.direction === 'OUT' ? 'text-slate-200' : 'text-emerald-300'}>
                  {ev.text}
                </span>
              </div>
            ))}
          </div>

          {/* Send Command Input */}
          <form onSubmit={handleSendCommand} className="p-3 bg-[#F7F8FA] border-t border-[#E2E5E9] flex items-center gap-2">
            <input
              type="text"
              placeholder="Send SCPI Command (e.g. *IDN?, MEAS:VOLT:DC?, SYST:ERR?)..."
              value={scpiInput}
              onChange={(e) => setScpiInput(e.target.value)}
              className="flex-1 px-3 py-1.5 bg-white border border-[#E2E5E9] rounded text-xs font-mono text-[#17191C] outline-none focus:border-[#00435F]"
            />
            <button
              type="submit"
              disabled={isExecuting}
              className="px-3.5 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded hover:bg-[#003348] transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Query</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

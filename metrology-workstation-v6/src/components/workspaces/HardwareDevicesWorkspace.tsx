import React, { useState, useEffect } from "react";
import {
  Radio,
  Cpu,
  Terminal,
  Send,
  Play,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Zap,
  Activity,
  ArrowRight,
  Database,
} from "lucide-react";
import { useMetrology } from "../../context/MetrologyContext";

interface ConnectedDevice {
  id: string;
  name: string;
  device_type: string;
  protocol: string;
  connection_string: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  is_connected: boolean;
  last_seen?: string;
}

export const HardwareDevicesWorkspace: React.FC = () => {
  const { setActiveWorkspace } = useMetrology();
  const [devices, setDevices] = useState<ConnectedDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<ConnectedDevice | null>(null);
  const [loading, setLoading] = useState(false);

  // SCPI Terminal
  const [scpiCommand, setScpiCommand] = useState("*IDN?");
  const [terminalLog, setTerminalLog] = useState<Array<{ cmd: string; resp: string; time: string; ms: number }>>([]);
  const [cmdRunning, setCmdRunning] = useState(false);

  // Streaming Panel
  const [streamCount, setStreamCount] = useState(5);
  const [streamResults, setStreamResults] = useState<any | null>(null);
  const [streaming, setStreaming] = useState(false);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v8/hardware").then((r) => r.json());
      if (res && res.devices) {
        setDevices(res.devices);
        if (!selectedDevice && res.devices.length > 0) {
          setSelectedDevice(res.devices[0]);
        }
      }
    } catch (e) {
      console.error("Error fetching devices:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleSendCommand = async (cmdToSend?: string) => {
    if (!selectedDevice) return;
    const cmd = cmdToSend || scpiCommand;
    if (!cmd) return;

    setCmdRunning(true);
    try {
      const res = await fetch(`/api/v8/hardware/${selectedDevice.id}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      }).then((r) => r.json());

      if (res && res.response) {
        setTerminalLog((prev) => [
          {
            cmd,
            resp: res.response,
            time: new Date().toLocaleTimeString(),
            ms: res.execution_time_ms || 4.2,
          },
          ...prev.slice(0, 19),
        ]);
      }
    } catch (e) {
      console.error("Error sending SCPI command:", e);
    } finally {
      setCmdRunning(false);
    }
  };

  const handleStreamReadings = async () => {
    if (!selectedDevice) return;
    setStreaming(true);
    try {
      const res = await fetch(`/api/v8/hardware/${selectedDevice.id}/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count: streamCount }),
      }).then((r) => r.json());

      if (res && res.readings) {
        setStreamResults(res);
      }
    } catch (e) {
      console.error("Error streaming readings:", e);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto custom-scrollbar">
      {/* Top Banner */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                Hardware Connectivity Adapter (SCPI / VISA / Serial)
              </h1>
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full font-mono">
                LIVE HARDWARE BUS
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Direct bench instrument control, live command streaming, and automated reading acquisition.
            </p>
          </div>
        </div>

        <button
          onClick={fetchDevices}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-300 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Scan Interfaces
        </button>
      </div>

      {/* Main Grid */}
      <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Device Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {devices.map((d) => (
            <div
              key={d.id}
              onClick={() => setSelectedDevice(d)}
              className={`bg-white rounded-xl border p-4 transition shadow-xs cursor-pointer flex flex-col justify-between ${
                selectedDevice?.id === d.id
                  ? "border-indigo-600 ring-2 ring-indigo-500/20 bg-indigo-50/20"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {d.protocol}
                  </span>
                  <span className={`w-2 h-2 rounded-full ${d.is_connected ? "bg-emerald-500" : "bg-slate-300"}`} />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-900 leading-snug">{d.name}</h3>
                  <div className="text-[11px] text-slate-500 mt-0.5">{d.manufacturer} • {d.model}</div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 text-[10px] font-mono text-slate-400 truncate mt-3">
                {d.connection_string}
              </div>
            </div>
          ))}
        </div>

        {/* Selected Device Workstation Grid */}
        {selectedDevice && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Live SCPI Terminal */}
            <div className="bg-slate-950 rounded-xl border border-slate-800 p-5 shadow-lg flex flex-col justify-between h-[440px]">
              <div className="space-y-3 flex-1 flex flex-col min-h-0">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2 text-slate-200 text-xs font-mono font-bold">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    <span>SCPI Command Terminal — {selectedDevice.model}</span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400">STATUS: READY</span>
                </div>

                {/* Quick SCPI Macros */}
                <div className="flex items-center gap-1.5 text-[10px] font-mono">
                  {["*IDN?", "MEAS:VOLT:DC?", "READ?", "*RST", "*CLS"].map((macro) => (
                    <button
                      key={macro}
                      onClick={() => handleSendCommand(macro)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                    >
                      {macro}
                    </button>
                  ))}
                </div>

                {/* Terminal Log Output */}
                <div className="flex-1 bg-black/60 rounded-lg p-3 font-mono text-xs overflow-y-auto space-y-1.5 custom-scrollbar border border-slate-800/80">
                  {terminalLog.length === 0 ? (
                    <div className="text-slate-600 text-[11px]">
                      Type an IEEE 488.2 / SCPI command below (e.g. *IDN? or READ?) and press Enter...
                    </div>
                  ) : (
                    terminalLog.map((entry, idx) => (
                      <div key={idx} className="space-y-0.5">
                        <div className="text-slate-400 text-[11px] flex justify-between">
                          <span>&gt; {entry.cmd}</span>
                          <span className="text-[10px] text-slate-600">{entry.ms} ms</span>
                        </div>
                        <div className="text-emerald-400 font-bold pl-2 text-xs">
                          {entry.resp}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Command Input Box */}
              <div className="pt-3 border-t border-slate-800 flex items-center gap-2 mt-3">
                <input
                  type="text"
                  value={scpiCommand}
                  onChange={(e) => setScpiCommand(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendCommand()}
                  placeholder="Enter SCPI command (e.g. MEAS:VOLT:DC?)..."
                  className="flex-1 bg-slate-900 border border-slate-700 text-slate-100 px-3 py-2 rounded-md font-mono text-xs focus:ring-1 focus:ring-emerald-500 focus:outline-hidden"
                />
                <button
                  onClick={() => handleSendCommand()}
                  disabled={cmdRunning}
                  className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-bold font-mono transition cursor-pointer disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send</span>
                </button>
              </div>
            </div>

            {/* Live Streaming Acquisition Panel */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between h-[440px]">
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2 text-slate-800 text-xs font-bold uppercase tracking-wider">
                    <Activity className="w-4 h-4 text-blue-600" />
                    <span>Continuous Reading Streaming</span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    Buffer: 5–20 Samples
                  </span>
                </div>

                <div className="flex items-center justify-between gap-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-700">Sample Count:</span>
                    {[5, 10, 20].map((c) => (
                      <button
                        key={c}
                        onClick={() => setStreamCount(c)}
                        className={`px-3 py-1 rounded text-xs font-bold border transition cursor-pointer ${
                          streamCount === c
                            ? "bg-blue-600 text-white border-blue-600"
                            : "bg-white text-slate-700 border-slate-300"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={handleStreamReadings}
                    disabled={streaming}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5" />
                    {streaming ? "Acquiring Bus..." : "Acquire Readings"}
                  </button>
                </div>

                {/* Stream Output Display */}
                {streamResults ? (
                  <div className="p-4 rounded-lg bg-blue-50/50 border border-blue-200 space-y-3">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs text-slate-600 font-semibold">
                        Acquired {streamResults.count} observations ({streamResults.unit}):
                      </span>
                      <span className="text-sm font-mono font-bold text-blue-700">
                        Mean: {streamResults.mean} {streamResults.unit}
                      </span>
                    </div>

                    <div className="grid grid-cols-5 gap-2 font-mono text-xs">
                      {streamResults.readings.map((r: number, idx: number) => (
                        <div key={idx} className="bg-white p-2 rounded border border-blue-100 text-center">
                          <div className="text-[10px] text-slate-400">#{idx + 1}</div>
                          <div className="font-bold text-slate-800 mt-0.5">{r}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-10 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-lg">
                    Click "Acquire Readings" to stream live measurements directly across the hardware bus.
                  </div>
                )}
              </div>

              {/* Action: Transfer to New Job */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Ready to calibrate using streamed data?
                </span>
                <button
                  onClick={() => setActiveWorkspace("jobs")}
                  className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-lg transition cursor-pointer"
                >
                  <span>Transfer to Calibration Job</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  Search,
  Bell,
  Menu,
  ChevronDown,
  Minimize2,
  Maximize2,
  Activity,
  HelpCircle,
  Thermometer,
  MapPin,
  User,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const TopBar: React.FC = () => {
  const {
    setIsCommandPaletteOpen,
    setIsDiagnosticsOpen,
    setIsOnboardingOpen,
    setActiveWorkspace,
  } = useMetrology();

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [operatorMenuOpen, setOperatorMenuOpen] = useState(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  return (
    <header className="bg-[#FFFFFF] border-b border-[#E2E5E9] h-12 px-3.5 w-full flex justify-between items-center z-30 shrink-0 select-none">
      {/* Left: Brand & Menu */}
      <div className="flex items-center gap-3">
        <button
          className="p-1 hover:bg-[#F7F8FA] rounded text-[#656B73] hover:text-[#17191C] cursor-pointer"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2">
          <span className="font-bold text-[15px] tracking-tight text-[#00435F]">
            METROLOGY WORKSTATION
          </span>
          <span className="text-[9.5px] uppercase font-mono px-1.5 py-0.5 bg-[#EBF3F6] text-[#00435F] font-semibold rounded border border-[#CBD5E1]">
            ISO 17025
          </span>
        </div>
      </div>

      {/* Center: Command Palette Trigger */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsCommandPaletteOpen(true)}
          className="relative flex items-center bg-[#F7F8FA] border border-[#E2E5E9] rounded px-3 py-1 text-xs text-[#17191C] hover:border-[#00435F] hover:bg-white transition-all w-80 text-left group cursor-pointer shadow-xs"
        >
          <Search className="w-3.5 h-3.5 text-[#656B73] mr-2 group-hover:text-[#00435F]" />
          <span className="text-[#656B73] font-sans flex-1 text-[11.5px]">
            Search jobs, assets, instruments...
          </span>
          <kbd className="hidden sm:inline-block font-mono text-[10px] bg-[#E2E8F0] px-1.5 py-0.5 text-[#475569] rounded border border-[#CBD5E1]">
            Ctrl K
          </kbd>
        </button>
      </div>

      {/* Right: Operational Status, Lab, Environment, Operator */}
      <div className="flex items-center gap-3">
        {/* Lab Location */}
        <div className="hidden md:flex items-center gap-1.5 text-[11.5px] text-[#656B73] bg-[#F7F8FA] px-2.5 py-1 rounded border border-[#E2E5E9]">
          <MapPin className="w-3.5 h-3.5 text-[#00435F]" />
          <span className="font-medium text-[#17191C]">Lab:</span>
          <span>Chennai Calibration Lab</span>
        </div>

        {/* Environmental Telemetry */}
        <div
          title="Ambient conditions: 20.05 °C, 45.8% RH, 1013.25 hPa"
          className="flex items-center gap-1.5 text-[11px] font-mono bg-[#F7F8FA] px-2.5 py-1 rounded border border-[#E2E5E9]"
        >
          <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse"></span>
          <span className="text-[#17191C] font-semibold">Environment:</span>
          <span className="text-[#16A34A] font-medium">Stable</span>
          <span className="text-[#656B73] hidden lg:inline">(20.1°C / 46% RH)</span>
        </div>

        {/* Exception Notifications */}
        <button
          onClick={() => setActiveWorkspace('exception-center')}
          title="2 Quality Exceptions Active"
          className="relative p-1.5 hover:bg-[#F7F8FA] text-[#656B73] hover:text-[#17191C] rounded transition-colors cursor-pointer border border-transparent hover:border-[#E2E5E9]"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-[#DC2626] rounded-full"></span>
        </button>

        {/* Operator Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOperatorMenuOpen(!operatorMenuOpen)}
            className="flex items-center gap-1.5 text-[12px] bg-[#F7F8FA] hover:bg-[#EBF3F6] px-2.5 py-1 rounded border border-[#E2E5E9] text-[#17191C] font-medium transition-colors cursor-pointer"
          >
            <User className="w-3.5 h-3.5 text-[#00435F]" />
            <span className="truncate max-w-[120px]">Marcus Brody</span>
            <ChevronDown className="w-3.5 h-3.5 text-[#656B73]" />
          </button>

          {operatorMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-52 bg-white border border-[#E2E5E9] rounded-md shadow-lg py-1 z-50 text-xs">
              <div className="px-3 py-2 border-b border-[#E2E5E9] bg-[#F7F8FA]">
                <div className="font-semibold text-[#17191C]">Marcus Brody</div>
                <div className="text-[10px] text-[#656B73]">Lead Metrologist (Admin)</div>
                <div className="text-[9.5px] font-mono text-[#00435F] mt-0.5">Role: Sign-Off Authorized</div>
              </div>
              <button
                onClick={() => {
                  setActiveWorkspace('customers');
                  setOperatorMenuOpen(false);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-[#F7F8FA] text-[#17191C]"
              >
                Users & Roles Management
              </button>
              <button
                onClick={() => {
                  setActiveWorkspace('settings');
                  setOperatorMenuOpen(false);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-[#F7F8FA] text-[#17191C]"
              >
                Laboratory Settings
              </button>
              <div className="border-t border-[#E2E5E9] my-1"></div>
              <button
                onClick={() => {
                  setIsDiagnosticsOpen(true);
                  setOperatorMenuOpen(false);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-[#F7F8FA] text-[#17191C]"
              >
                Hardware Diagnostics
              </button>
            </div>
          )}
        </div>

        {/* Window Chrome */}
        <div className="flex items-center gap-1 border-l border-[#E2E5E9] pl-2 text-[#656B73]">
          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            className="p-1 hover:bg-[#F7F8FA] hover:text-[#17191C] rounded transition-colors cursor-pointer"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
    </header>
  );
};

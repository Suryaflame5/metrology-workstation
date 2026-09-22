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
  CheckCircle2,
  Sparkles,
  Zap,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const TopBar: React.FC = () => {
  const {
    setIsCommandPaletteOpen,
    setIsDiagnosticsOpen,
    setIsOnboardingOpen,
    setActiveWorkspace,
    isCommercial,
    isDemo,
    setIsUpgradeModalOpen,
  } = useMetrology();

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [operatorMenuOpen, setOperatorMenuOpen] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  const [labName, setLabName] = useState<string>(() => {
    return localStorage.getItem('calibra_lab_name') || 'Standards & Calibration Facility';
  });
  const [operatorName, setOperatorName] = useState<string>(() => {
    return localStorage.getItem('calibra_operator_name') || 'Lead Metrologist';
  });
  const [operatorRole, setOperatorRole] = useState<string>(() => {
    return localStorage.getItem('calibra_operator_role') || 'QA / Sign-Off Authorized';
  });

  const saveProfile = (newLab: string, newOp: string) => {
    setLabName(newLab);
    setOperatorName(newOp);
    localStorage.setItem('calibra_lab_name', newLab);
    localStorage.setItem('calibra_operator_name', newOp);
    setIsEditingProfile(false);
  };

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
          {isCommercial ? (
            <button
              onClick={() => setIsUpgradeModalOpen(true)}
              className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 font-mono text-[10px] font-bold rounded border border-emerald-300 transition-colors cursor-pointer"
              title="Commercial License Active — Click to view details"
            >
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              <span>ISO 17025 PRO</span>
            </button>
          ) : (
            <button
              onClick={() => setIsUpgradeModalOpen(true)}
              className="flex items-center gap-1.5 px-2.5 py-0.5 bg-amber-50 hover:bg-amber-100 text-amber-900 font-mono text-[10px] font-bold rounded border border-amber-300 transition-colors cursor-pointer group shadow-2xs"
              title="Click to Compare Editions & Upgrade to Professional"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
              <span>DEMO EVALUATION</span>
              <span className="text-amber-700 font-sans font-semibold text-[9.5px] hidden sm:inline ml-1 underline group-hover:text-amber-900">
                Compare &amp; Upgrade ↗
              </span>
            </button>
          )}
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
          <span>{labName}</span>
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
            <span className="truncate max-w-[120px]">{operatorName}</span>
            <ChevronDown className="w-3.5 h-3.5 text-[#656B73]" />
          </button>

          {operatorMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-56 bg-white border border-[#E2E5E9] rounded-md shadow-lg py-1 z-50 text-xs">
              <div className="px-3 py-2 border-b border-[#E2E5E9] bg-[#F7F8FA]">
                <div className="font-semibold text-[#17191C]">{operatorName}</div>
                <div className="text-[10px] text-[#656B73] truncate">{labName}</div>
                <div className="text-[9.5px] font-mono text-[#00435F] mt-0.5">{operatorRole}</div>
              </div>
              <button
                onClick={() => {
                  const newLab = prompt('Enter Facility / Laboratory Name:', labName);
                  if (newLab !== null && newLab.trim()) {
                    const newOp = prompt('Enter Lead Metrologist / Operator Name:', operatorName);
                    if (newOp !== null && newOp.trim()) {
                      saveProfile(newLab.trim(), newOp.trim());
                    }
                  }
                  setOperatorMenuOpen(false);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-[#F7F8FA] text-[#00435F] font-semibold"
              >
                ✎ Configure Facility Profile...
              </button>
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

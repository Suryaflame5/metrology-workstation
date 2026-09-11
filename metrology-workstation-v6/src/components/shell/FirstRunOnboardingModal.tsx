import React, { useState } from 'react';
import { 
  X, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft, 
  ShieldCheck, 
  Calculator, 
  Cpu, 
  Lock, 
  FileText, 
  Sparkles,
  Zap
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const FirstRunOnboardingModal: React.FC = () => {
  const { isOnboardingOpen, setIsOnboardingOpen, setActiveWorkspace } = useMetrology();
  const [currentStep, setCurrentStep] = useState(1);
  const [dontShowAgain, setDontShowAgain] = useState(true);

  if (!isOnboardingOpen) return null;

  const handleClose = () => {
    if (dontShowAgain) {
      localStorage.setItem('has_completed_onboarding', 'true');
    }
    setIsOnboardingOpen(false);
  };

  const handleStartTour = () => {
    handleClose();
    setActiveWorkspace('uncertainty');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 select-none">
      <div className="bg-white border border-[#c1c7ce] rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-4 bg-[#00435f] text-white flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center border border-white/20">
              <Sparkles className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-bold text-sm tracking-tight">
                Metrology Workstation V6 — Quick Start & Tour
              </h3>
              <p className="text-[11px] text-[#dbe4ea] font-mono">
                Precision Measurement Analysis & ISO 17025 Conformity System
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-white/70 hover:text-white p-1 rounded transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Progress Step Indicator */}
        <div className="px-6 pt-4 pb-2 bg-[#f9f9fc] border-b border-[#c1c7ce] flex justify-between items-center">
          <span className="font-mono text-xs font-bold text-[#00435f]">
            STEP {currentStep} OF 4
          </span>
          <div className="flex gap-1.5">
            {[1, 2, 3, 4].map((step) => (
              <div
                key={step}
                className={`h-1.5 rounded-full transition-all ${
                  step === currentStep 
                    ? 'w-8 bg-[#00435f]' 
                    : step < currentStep 
                    ? 'w-4 bg-[#4a7c59]' 
                    : 'w-4 bg-[#c1c7ce]'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="p-6 overflow-y-auto min-h-[290px] space-y-4">
          {currentStep === 1 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-[#00435f]">
                <Calculator className="w-5 h-5" />
                <h4 className="font-bold text-base text-[#191c1e]">
                  Exact 50-Digit Sovereign Metrology Kernel
                </h4>
              </div>
              <p className="text-xs text-[#576065] leading-relaxed">
                Metrology Workstation eliminates IEEE 754 floating-point cancellation errors entirely. 
                Every mean, variance, covariance, and probability integral is calculated using arbitrary-precision 
                decimal arithmetic accurate to 50 significant digits.
              </p>
              <div className="grid grid-cols-2 gap-3 pt-1 font-mono text-xs">
                <div className="p-3 bg-[#f3f4f2] border border-[#c1c7ce] rounded-lg">
                  <strong className="text-[#00435f] block text-[11px] uppercase">100% Air-Gapped Ready</strong>
                  <span className="text-[#576065] text-[11px]">Zero telemetry or external calls. Runs entirely within your secure sovereign facility.</span>
                </div>
                <div className="p-3 bg-[#f3f4f2] border border-[#c1c7ce] rounded-lg">
                  <strong className="text-[#00435f] block text-[11px] uppercase">Commercial Professional Tier</strong>
                  <span className="text-[#576065] text-[11px]">Priced at $599/year ($50/mo equivalent) with all 22 engineering workspaces included.</span>
                </div>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-[#00435f]">
                <Cpu className="w-5 h-5" />
                <h4 className="font-bold text-base text-[#191c1e]">
                  Hardware Studio & Unbroken Traceability Chain
                </h4>
              </div>
              <p className="text-xs text-[#576065] leading-relaxed">
                Seamlessly interface with laboratory instrumentation via GPIB IEEE-488.2 and USB VISA using standard SCPI commands. 
                Ingest multi-run batch datasets from Excel or CSV files with automated column mapping.
              </p>
              <div className="p-3 bg-[#f9f9fc] border border-[#c1c7ce] rounded-lg font-mono text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-[#576065]">Primary Standard:</span>
                  <strong className="text-[#191c1e]">NIST / BIPM SI Realization</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#576065]">Accredited Calibration:</span>
                  <strong className="text-[#191c1e]">NVLAP Accredited Laboratory</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#576065]">Instrument Bus:</span>
                  <strong className="text-[#00435f]">SCPI / VISA / RS-232 / CSV Ingestion</strong>
                </div>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-[#00435f]">
                <ShieldCheck className="w-5 h-5 text-[#4a7c59]" />
                <h4 className="font-bold text-base text-[#191c1e]">
                  GUM Uncertainty & ANSI Z540.3 Guardbanding
                </h4>
              </div>
              <p className="text-xs text-[#576065] leading-relaxed">
                Execute complete JCGM 100:2008 uncertainty budgets with Type A repeatability and Type B sensitivity coefficients. 
                Apply ANSI/NCSL Z540.3 Method 6 root guardbanding to mathematically ensure consumer risk remains under 2.0%.
              </p>
              <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-xs text-center">
                <div className="p-2.5 bg-[#e8f0fe] border border-[#00435f]/30 rounded">
                  <span className="text-[10px] text-[#576065] block">EXPANDED UNC</span>
                  <strong className="text-[#00435f] text-sm">U95 (k=2.00)</strong>
                </div>
                <div className="p-2.5 bg-[#e8f5e9] border border-[#2e7d32]/30 rounded">
                  <span className="text-[10px] text-[#2e7d32] block">CONSUMER RISK</span>
                  <strong className="text-[#1b5e20] text-sm">P_CR = 2.0%</strong>
                </div>
                <div className="p-2.5 bg-[#e8f0fe] border border-[#00435f]/30 rounded">
                  <span className="text-[10px] text-[#576065] block">MONTE CARLO</span>
                  <strong className="text-[#00435f] text-sm">10k Draws</strong>
                </div>
              </div>
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-[#00435f]">
                <Lock className="w-5 h-5 text-[#00435f]" />
                <h4 className="font-bold text-base text-[#191c1e]">
                  12-Stage Mathematical Replay & ISO 17025 Certificates
                </h4>
              </div>
              <p className="text-xs text-[#576065] leading-relaxed">
                Every calculation is recorded into an append-only cryptographic ledger with SHA-256 hash chains. 
                Replay every derivation stage on demand, seal records with FDA 21 CFR Part 11 electronic signatures, 
                and export formal ReportLab PDF certificates and machine-verifiable evidence ZIP packages.
              </p>
              <div className="p-3 bg-[#e8f5e9] border border-[#2e7d32]/30 rounded-lg flex items-center justify-between font-mono text-xs">
                <div className="flex items-center gap-2 text-[#2e7d32] font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Audit Ready for ISO/IEC 17025 Assessment</span>
                </div>
                <span className="text-[11px] text-[#1b5e20]">Zero Unsaved Drift</span>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#f3f4f2] border-t border-[#c1c7ce] flex justify-between items-center">
          <label className="flex items-center gap-2 text-xs font-mono text-[#576065] cursor-pointer">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              className="rounded text-[#00435f]"
            />
            <span>Don't show on startup</span>
          </label>

          <div className="flex items-center gap-2">
            {currentStep > 1 && (
              <button
                onClick={() => setCurrentStep((prev) => prev - 1)}
                className="px-3 py-1.5 border border-[#c1c7ce] rounded text-xs font-semibold text-[#191c1e] hover:bg-white flex items-center gap-1 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>
            )}

            {currentStep < 4 ? (
              <button
                onClick={() => setCurrentStep((prev) => prev + 1)}
                className="px-4 py-1.5 bg-[#00435f] text-white rounded text-xs font-semibold hover:bg-[#245b78] flex items-center gap-1 cursor-pointer shadow-xs"
              >
                <span>Next</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleStartTour}
                className="px-4 py-1.5 bg-[#4a7c59] text-white rounded text-xs font-semibold hover:bg-[#3b6347] flex items-center gap-1 cursor-pointer shadow-xs"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Launch Calibration Tour</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

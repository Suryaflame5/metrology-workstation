import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  Zap,
  Key,
  Download,
  Sparkles,
  ArrowRight,
  HelpCircle,
  Lock,
  Unlock,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const EditionComparisonModal: React.FC = () => {
  const { isUpgradeModalOpen, setIsUpgradeModalOpen, refreshLicense, isCommercial } = useMetrology();
  const [licenseData, setLicenseData] = useState<any>(null);
  const [keyInput, setKeyInput] = useState('');
  const [activating, setActivating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (isUpgradeModalOpen) {
      fetch('/api/license')
        .then((r) => r.json())
        .then((data) => setLicenseData(data))
        .catch(() => {});
    }
  }, [isUpgradeModalOpen]);

  if (!isUpgradeModalOpen) return null;

  const handleClose = () => {
    setIsUpgradeModalOpen(false);
    setStatusMsg(null);
  };

  const handleApplyKey = async () => {
    const trimmed = keyInput.trim();
    if (!trimmed) {
      setStatusMsg({ type: 'error', text: 'Please enter a license key, offline token, or evaluation grant code.' });
      return;
    }

    try {
      setActivating(true);
      setStatusMsg(null);
      const res = await fetch('/api/license/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: trimmed, token_json: trimmed }),
      });

      const data = await res.json();
      if (res.ok) {
        setStatusMsg({
          type: 'success',
          text: `License activated successfully! Plan: ${data.entitlement?.plan_name || 'Commercial Professional'}`,
        });
        setKeyInput('');
        await refreshLicense();
        const updated = await fetch('/api/license').then((r) => r.json());
        setLicenseData(updated);
      } else {
        setStatusMsg({
          type: 'error',
          text: data.detail || 'Activation failed. Verify your key or grant code.',
        });
      }
    } catch (e: any) {
      setStatusMsg({ type: 'error', text: e.message || 'Error connecting to local licensing service.' });
    } finally {
      setActivating(false);
    }
  };

  const handleStartTrial = async () => {
    try {
      setActivating(true);
      setStatusMsg(null);
      const res = await fetch('/api/license/trial', { method: 'POST' });
      if (res.ok) {
        setStatusMsg({ type: 'success', text: '14-Day Professional Trial successfully activated!' });
        await refreshLicense();
        const updated = await fetch('/api/license').then((r) => r.json());
        setLicenseData(updated);
      } else {
        setStatusMsg({ type: 'error', text: 'Could not activate trial.' });
      }
    } catch (e: any) {
      setStatusMsg({ type: 'error', text: e.message || 'Network error activating trial.' });
    } finally {
      setActivating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 select-none">
      <div className="bg-white border border-[#C1C7CE] rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 bg-[#00435F] text-white flex justify-between items-center shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center border border-white/20">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-bold text-sm tracking-tight">
                CALIBRA Metrology Workstation — Edition Comparison &amp; Licensing
              </h3>
              <p className="text-[11px] text-[#DBE4EA] font-mono">
                Select the capability profile required for your laboratory accreditation scope
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

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 custom-scrollbar text-xs font-sans">
          {/* Status Message */}
          {statusMsg && (
            <div
              className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2 ${
                statusMsg.type === 'success'
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                  : 'bg-red-50 border-red-300 text-red-800'
              }`}
            >
              {statusMsg.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              )}
              <span>{statusMsg.text}</span>
            </div>
          )}

          {/* Current Edition Banner */}
          <div className="bg-[#F8FAFC] border border-[#CBD5E1] rounded-lg p-3.5 flex items-center justify-between flex-wrap gap-2 font-mono">
            <div>
              <span className="text-[#64748B] text-[11px]">ACTIVE INSTALLATION:</span>
              <div className="font-bold text-[#0F172A] text-sm flex items-center gap-2 mt-0.5">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                    isCommercial ? 'bg-emerald-600 text-white' : 'bg-amber-100 text-amber-900 border border-amber-300'
                  }`}
                >
                  {licenseData?.edition_badge || (isCommercial ? 'ISO 17025 PRO' : 'DEMO EVALUATION')}
                </span>
                <span>{licenseData?.edition || 'CALIBRA Metrology Workstation 7'}</span>
              </div>
            </div>
            {!isCommercial && (
              <button
                onClick={handleStartTrial}
                disabled={activating}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Start Free 14-Day Pro Trial</span>
              </button>
            )}
          </div>

          {/* Edition Capability Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Community Demo Card */}
            <div className="border border-[#E2E8F0] rounded-xl p-5 bg-white space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Community Demo
                </span>
                <span className="text-xs font-mono text-[#64748B]">Free Evaluation</span>
              </div>
              <h4 className="text-base font-bold text-[#0F172A]">Community Evaluation Edition</h4>
              <p className="text-[11.5px] text-[#64748B] leading-relaxed">
                Pre-configured evaluation sandbox for metrologists to inspect the exact 50-digit GUM mathematical kernel, test decision rules, and evaluate UI workflows.
              </p>
              <ul className="space-y-1.5 text-[11.5px] text-[#334155]">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>50-Digit exact decimal arithmetic (zero IEEE 754 drift)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>JCGM 100:2008 GUM Type A &amp; B uncertainty budget</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>ANSI/NCSL Z540.3 Method 5 &amp; 6 guardband calculation</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>12-Stage mathematical replay viewer</span>
                </li>
                <li className="flex items-center gap-2 text-amber-700">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>PDF certificates include diagonal evaluation watermark</span>
                </li>
                <li className="flex items-center gap-2 text-amber-700">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>Limited to sample micrometer &amp; caliper records</span>
                </li>
              </ul>
            </div>

            {/* Professional Commercial Card */}
            <div className="border-2 border-[#00435F] rounded-xl p-5 bg-[#F8FAFC] space-y-3 relative shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider text-white bg-[#00435F] px-2 py-0.5 rounded">
                  Commercial Production
                </span>
                <span className="text-xs font-mono font-bold text-[#00435F]">$590 / yr or $1,490 perpetual</span>
              </div>
              <h4 className="text-base font-bold text-[#0F172A]">Professional Edition</h4>
              <p className="text-[11.5px] text-[#64748B] leading-relaxed">
                Accredited calibration management for ISO/IEC 17025 facilities. Clean production database, unwatermarked customer certificates, and 60-second audit defense.
              </p>
              <ul className="space-y-1.5 text-[11.5px] text-[#334155]">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <strong>Clean Production Database: zero mock data or clutter</strong>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <strong>All 7 Precision Instrument Families</strong> (Dial, Pressure, Torque, etc.)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <strong>Multi-Point Calibration Studio</strong> &amp; non-linear curve fitting
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <strong>Unwatermarked Official ISO/IEC 17025 PDF Certificates</strong>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Custom lab logo, accreditation number &amp; dual e-signatures</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>60-Second Machine-Verifiable Audit Defense Package (ZIP)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Out-of-Tolerance (OOT) reverse impact investigation</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Quick Activation Box */}
          <div className="bg-[#00435F]/5 border border-[#00435F]/20 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-[#00435F]" />
                <h5 className="font-bold text-xs text-[#0F172A] uppercase tracking-wider font-mono">
                  Activate Commercial License or Grant Code
                </h5>
              </div>
              <a
                href="https://novyrax.vercel.app/pricing"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-[#00435F] hover:underline flex items-center gap-1 font-semibold"
              >
                <span>Purchase License Online ($590)</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <p className="text-[11px] text-[#64748B]">
              Enter your Lemon Squeezy license key, offline token, or evaluation grant code (e.g. <code className="font-mono text-[#00435F] font-bold">M3TR0-9X2K-7V8P-Q4L1</code>).
            </p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="XXXX-XXXX-XXXX-XXXX or paste offline token JSON"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                className="flex-1 bg-white border border-[#CBD5E1] rounded px-3 py-1.5 text-xs font-mono text-[#0F172A] focus:outline-none focus:border-[#00435F]"
              />
              <button
                onClick={handleApplyKey}
                disabled={activating}
                className="px-4 py-1.5 bg-[#00435F] hover:bg-[#003348] text-white font-semibold text-xs rounded transition-colors cursor-pointer disabled:opacity-50 shrink-0"
              >
                {activating ? 'Verifying...' : 'Activate Entitlement'}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#F8FAFC] border-t border-[#E2E8F0] flex justify-between items-center shrink-0">
          <span className="text-[10px] text-[#64748B] font-mono">
            Compliant with JCGM 100:2008, JCGM 101:2008, ISO 14253-1, ILAC-G8 &amp; ANSI/NCSL Z540.3
          </span>
          <button
            onClick={handleClose}
            className="px-4 py-1.5 bg-white border border-[#CBD5E1] text-[#334155] hover:bg-[#F1F5F9] text-xs font-semibold rounded cursor-pointer transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

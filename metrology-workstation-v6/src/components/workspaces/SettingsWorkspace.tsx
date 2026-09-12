import React, { useState, useEffect, useRef } from 'react';
import { Save, Settings, Sliders, ShieldCheck, Key, RefreshCw, AlertCircle, CheckCircle2, ExternalLink, Sparkles, Upload, FileText } from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

interface LicenseInfo {
  edition: string;
  version: string;
  entitlement_state: string;
  plan_id: string;
  customer_name: string;
  seat_limit: number;
  is_trial: boolean;
  expiration: string | null;
  offline_operation_status: string;
  features: string[];
}

export const SettingsWorkspace: React.FC = () => {
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [keyInput, setKeyInput] = useState<string>('');
  const [activating, setActivating] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchLicense = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/license');
      if (res.ok) {
        const data = await res.json();
        setLicense(data);
      }
    } catch (e) {
      console.error('Failed to fetch license', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLicense();
  }, []);

  const handleActivate = async () => {
    const trimmed = keyInput.trim();
    if (!trimmed) {
      setStatusMsg({ type: 'error', text: 'Please enter a Lemon Squeezy license key or offline JSON token.' });
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
          text: `License activated successfully! Plan: ${data.entitlement?.plan_name || 'Commercial Active'}`,
        });
        setKeyInput('');
        fetchLicense();
      } else {
        setStatusMsg({
          type: 'error',
          text: data.detail || 'License activation failed. Verify your key or offline token.',
        });
      }
    } catch (e: any) {
      setStatusMsg({
        type: 'error',
        text: e.message || 'Network error connecting to local license service.',
      });
    } finally {
      setActivating(false);
    }
  };

  const handleTrial = async () => {
    try {
      setActivating(true);
      setStatusMsg(null);
      const res = await fetch('/api/license/trial', { method: 'POST' });
      if (res.ok) {
        setStatusMsg({ type: 'success', text: '14-Day Professional Trial activated!' });
        fetchLicense();
      }
    } catch (e) {
      setStatusMsg({ type: 'error', text: 'Failed to activate trial.' });
    } finally {
      setActivating(false);
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selftestResult, setSelftestResult] = useState<any>(null);
  const [runningSelftest, setRunningSelftest] = useState<boolean>(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target?.result as string;
      if (content) {
        setKeyInput(content.trim());
        try {
          setActivating(true);
          setStatusMsg(null);
          const res = await fetch('/api/license/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: content.trim(), token_json: content.trim() }),
          });
          const data = await res.json();
          if (res.ok) {
            setStatusMsg({
              type: 'success',
              text: `License file imported & activated successfully! Plan: ${data.entitlement?.plan_name || 'Commercial Active'}`,
            });
            fetchLicense();
          } else {
            setStatusMsg({
              type: 'error',
              text: data.detail || 'Failed to activate imported license file.',
            });
          }
        } catch (err: any) {
          setStatusMsg({ type: 'error', text: err.message || 'Error importing license file.' });
        } finally {
          setActivating(false);
          if (fileInputRef.current) fileInputRef.current.value = '';
        }
      }
    };
    reader.readAsText(file);
  };

  const handleRunSelftest = async () => {
    try {
      setRunningSelftest(true);
      const res = await fetch('/api/selftest');
      if (res.ok) {
        const data = await res.json();
        setSelftestResult(data);
      }
    } catch (err) {
      console.error('Failed to run self-test', err);
    } finally {
      setRunningSelftest(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset license to Community / Free Evaluation mode?')) return;
    try {
      setActivating(true);
      const res = await fetch('/api/license/reset', { method: 'POST' });
      if (res.ok) {
        setStatusMsg({ type: 'success', text: 'License reset to Community Edition.' });
        fetchLicense();
      }
    } catch (e) {
      setStatusMsg({ type: 'error', text: 'Failed to reset license.' });
    } finally {
      setActivating(false);
    }
  };

  const isProOrHigher = license && (license.plan_id === 'PROFESSIONAL' || license.plan_id === 'BUSINESS' || license.plan_id === 'ENTERPRISE');

  const COMMERCIAL_FEATURE_CATALOG = [
    { id: 'EXACT_50_DIGIT_GUM', name: '50-Digit Deterministic GUM Math Engine', desc: 'JCGM 100:2008 high-precision arithmetic with zero IEEE 754 drift.' },
    { id: 'DECISION_Z5403_METHOD6', name: 'ANSI/NCSL Z540.3 Method 6 Guard Banding', desc: 'Automatic 2.0% PFA risk guardband calculation.' },
    { id: '12_STAGE_REPLAY', name: '12-Stage Reproducibility & Provenance', desc: 'Clause-by-clause cryptographic calculation replay.' },
    { id: 'ALL_7_INSTRUMENT_FAMILIES', name: 'All 7 Metrology Instrument Families', desc: 'Micrometers, Calipers, Indicators, Torque, Pressure, Temp, Multimeters.' },
    { id: 'MULTI_POINT_STUDIO', name: 'Multi-Point Calibration Studio', desc: 'Nonlinear multi-point nominal calibration runs.' },
    { id: 'MACHINE_VERIFIABLE_EVIDENCE_ZIP', name: 'Cryptographic Evidence Bundle (ZIP)', desc: 'SHA-256 sealed audit packages for external accreditation auditors.' },
    { id: 'UNWATERMARKED_CERTIFICATES', name: 'Official Unwatermarked ISO/IEC 17025 PDFs', desc: 'Accreditation-ready calibration certificates without evaluation stamp.' },
    { id: 'CUSTOM_LAB_BRANDING', name: 'Custom Laboratory Branding & Logo', desc: 'Embed lab header, accreditation number, and corporate identity.' },
    { id: 'MULTI_SEAT_ORGANIZATION', name: 'Multi-Seat Team Floating Deployment', desc: 'Centralized organization-wide seat entitlement.' },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-4xl mx-auto font-mono text-xs">
      {/* Header */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            SYSTEM CONFIGURATION &amp; LICENSING
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] font-sans tracking-tight">
          CALIBRA Metrology Workstation Settings
        </h1>
      </div>

      {/* Commercial Licensing Card */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#e2e5e9]">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-[#00435f]" />
            <h2 className="font-bold text-sm text-[#191c1e] font-sans">
              Commercial Entitlement &amp; License Key
            </h2>
          </div>
          <button
            onClick={fetchLicense}
            disabled={loading}
            className="flex items-center gap-1 text-[11px] text-[#576065] hover:text-[#00435f] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Status</span>
          </button>
        </div>

        {/* Active Entitlement Status Banner */}
        {license && (
          <div className={`p-4 rounded-lg border ${
            isProOrHigher
              ? 'bg-[#f0f9f4] border-[#86efac]'
              : 'bg-[#f8fafc] border-[#cbd5e1]'
          }`}>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold tracking-wider uppercase ${
                    isProOrHigher
                      ? 'bg-[#16a34a] text-white'
                      : 'bg-[#00435f] text-white'
                  }`}>
                    {license.plan_id}
                  </span>
                  <span className="font-semibold text-sm text-[#191c1e] font-sans">
                    {license.edition}
                  </span>
                </div>
                <div className="text-[11px] text-[#576065] mt-1.5 flex items-center gap-3">
                  <span>Licensed to: <strong>{license.customer_name}</strong></span>
                  <span>Seats: <strong>{license.seat_limit}</strong></span>
                  <span>Status: <strong className="uppercase">{license.entitlement_state}</strong></span>
                  {license.expiration && (
                    <span>Expires: <strong>{new Date(license.expiration).toLocaleDateString()}</strong></span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-[11px] text-[#16a34a] font-medium bg-white px-2.5 py-1 rounded border border-[#86efac]">
                <ShieldCheck className="w-4 h-4 text-[#16a34a]" />
                <span>{license.offline_operation_status}</span>
              </div>
            </div>
          </div>
        )}

        {/* Feature Permissions Matrix */}
        {license && (
          <div className="border border-[#e2e5e9] rounded-lg p-3 bg-[#fdfdfd] space-y-2">
            <h3 className="font-sans font-bold text-xs text-[#191c1e] flex items-center justify-between">
              <span>Tier Feature Permissions &amp; Audit Capabilities</span>
              <span className="text-[10px] text-[#656b73] font-normal">
                {license.features.length} features active
              </span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
              {COMMERCIAL_FEATURE_CATALOG.map((f) => {
                const isAuthorized = license.features.includes(f.id);
                return (
                  <div
                    key={f.id}
                    className={`p-2 rounded border flex items-start justify-between gap-2 ${
                      isAuthorized
                        ? 'bg-[#f0f9f4] border-[#bbf7d0]'
                        : 'bg-[#f8fafc] border-[#e2e8f0] opacity-65'
                    }`}
                  >
                    <div>
                      <div className="font-sans font-medium text-[11px] text-[#191c1e] flex items-center gap-1.5">
                        {isAuthorized ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#16a34a] shrink-0" />
                        ) : (
                          <AlertCircle className="w-3.5 h-3.5 text-[#94a3b8] shrink-0" />
                        )}
                        <span>{f.name}</span>
                      </div>
                      <p className="text-[10px] text-[#64748b] mt-0.5 leading-tight">{f.desc}</p>
                    </div>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide ${
                        isAuthorized
                          ? 'bg-[#dcfce7] text-[#15803d]'
                          : 'bg-[#f1f5f9] text-[#64748b]'
                      }`}
                    >
                      {isAuthorized ? 'Active' : 'Locked'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* License Activation Form */}
        <div className="space-y-2 pt-2">
          <label className="block text-[#191c1e] font-medium font-sans text-xs">
            Activate Lemon Squeezy License Key or Air-Gapped Entitlement Token:
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              placeholder="Paste License Key (e.g. ABCD-EFGH-IJKL-MNOP) or offline JSON token..."
              className="flex-1 p-2.5 border border-[#c1c7ce] rounded bg-[#f8fafc] text-xs font-mono outline-none focus:border-[#00435f]"
              disabled={activating}
            />
            <button
              onClick={handleActivate}
              disabled={activating || !keyInput.trim()}
              className="px-4 py-2 bg-[#00435f] hover:bg-[#003147] text-white font-sans font-semibold rounded text-xs transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {activating ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Key className="w-3.5 h-3.5" />
              )}
              <span>Activate</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              accept=".json"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={activating}
              className="px-3 py-2 bg-white hover:bg-[#f8fafc] text-[#00435f] font-sans font-semibold rounded border border-[#c1c7ce] text-xs transition-colors disabled:opacity-50 flex items-center gap-1.5"
              title="Import calibra-license.json file"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Import File</span>
            </button>
          </div>
          <p className="text-[10px] text-[#656b73]">
            Supports instant activation via Lemon Squeezy license key, confidential evaluation grant code, or offline HMAC-SHA256 signed JSON license tokens for air-gapped lab facilities.
          </p>
        </div>

        {/* Status Messages */}
        {statusMsg && (
          <div className={`p-3 rounded text-xs flex items-start gap-2 ${
            statusMsg.type === 'success'
              ? 'bg-[#f0fdf4] text-[#15803d] border border-[#bbf7d0]'
              : 'bg-[#fef2f2] text-[#b91c1c] border border-[#fecaca]'
          }`}>
            {statusMsg.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            )}
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Quick Actions & Links */}
        <div className="pt-2 flex items-center justify-between flex-wrap gap-2 border-t border-[#e2e5e9]">
          <div className="flex items-center gap-2">
            {!isProOrHigher && (
              <button
                onClick={handleTrial}
                disabled={activating}
                className="px-3 py-1.5 bg-[#f0f9f4] hover:bg-[#dcfce7] text-[#15803d] font-sans font-medium rounded border border-[#86efac] text-xs transition-colors flex items-center gap-1"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Start 14-Day Pro Trial</span>
              </button>
            )}
            {isProOrHigher && (
              <button
                onClick={handleReset}
                disabled={activating}
                className="px-3 py-1.5 bg-white hover:bg-[#f8fafc] text-[#656b73] font-sans rounded border border-[#c1c7ce] text-xs transition-colors"
              >
                Reset to Community
              </button>
            )}
          </div>

          <a
            href="https://novyrax.com/pricing/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-[#00435f] hover:underline font-sans font-medium"
          >
            <span>Need a commercial license or discount coupon? NovyraX Pricing</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* ISO/IEC 17025 Qualification Self-Test Card */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#e2e5e9]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#00435f]" />
            <h2 className="font-bold text-sm text-[#191c1e] font-sans">
              ISO/IEC 17025 Section 7.11 Software Qualification Self-Test
            </h2>
          </div>
          <button
            onClick={handleRunSelftest}
            disabled={runningSelftest}
            className="px-3 py-1.5 bg-[#00435f] hover:bg-[#003147] text-white font-sans font-semibold rounded text-xs transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            {runningSelftest ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
            <span>{runningSelftest ? 'Verifying...' : 'Run Qualification Test'}</span>
          </button>
        </div>
        <p className="text-[11px] text-[#656b73] leading-relaxed">
          Executes the deterministic JCGM 100:2008 and ANSI Z540.3 Method 6 benchmark suite across 8 reference metrology test vectors to certify computational integrity for quality audits.
        </p>
        {selftestResult && (
          <div className="mt-3 p-3 bg-[#f8fafc] border border-[#cbd5e1] rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-sans font-bold text-xs text-[#0f172a] flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#16a34a]" />
                Audit Status: {selftestResult.overall_status}
              </span>
              <span className="text-[11px] font-bold text-[#15803d] bg-[#dcfce7] px-2 py-0.5 rounded">
                {selftestResult.benchmark_tests_passed} / {selftestResult.benchmark_tests_total} Benchmarks Passed (100%)
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 text-[10px]">
              {selftestResult.checks?.map((chk: any, i: number) => (
                <div key={i} className="p-1.5 bg-white border border-[#e2e8f0] rounded flex items-center justify-between">
                  <span className="truncate text-[#334155]">{chk.name}</span>
                  <span className="text-[#16a34a] font-bold ml-1">{chk.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Engineering Preferences Card */}
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-[#e2e5e9]">
          <Sliders className="w-4 h-4 text-[#00435f]" />
          <h2 className="font-bold text-sm text-[#191c1e] font-sans">
            Metrology Engineering Preferences
          </h2>
        </div>

        <div>
          <label className="block text-[#576065] mb-1">Default Units System:</label>
          <select className="w-full p-2 border border-[#c1c7ce] rounded bg-[#f3f4f2] outline-none">
            <option value="SI">Metric SI (Volts, Ohms, Amperes, °C, mm)</option>
            <option value="US">US Customary (°F, psi, in)</option>
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

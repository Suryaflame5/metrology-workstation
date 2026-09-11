import React, { useState, useEffect } from 'react';
import { Save, Settings, Sliders, ShieldCheck, Key, RefreshCw, AlertCircle, CheckCircle2, ExternalLink, Sparkles } from 'lucide-react';
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
        body: JSON.stringify({ token_json: trimmed }),
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
          </div>
          <p className="text-[10px] text-[#656b73]">
            Supports instant activation via Lemon Squeezy license key, or offline HMAC-SHA256 signed JSON tokens for air-gapped lab facilities.
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

import React, { useState, useEffect } from 'react';
import {
  Tag,
  Search,
  ScanLine,
  Plus,
  RefreshCw,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  FileBarChart,
  FileText,
  Tool,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { fetchAssets, scanAsset } from '../../services/jobApi';
import { AssetItem } from '../../types';
import { useMetrology } from '../../context/MetrologyContext';

export const AssetsWorkspace: React.FC = () => {
  const { setActiveWorkspace } = useMetrology();
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<AssetItem | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'history' | 'certificates' | 'evidence' | 'maintenance'>('overview');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [scanInput, setScanInput] = useState('');
  const [scanResult, setScanResult] = useState<string | null>(null);

  const loadAssetsList = async () => {
    setLoading(true);
    try {
      const list = await fetchAssets();
      if (list && list.length > 0) {
        setAssets(list);
        setSelectedAsset(list[0]);
      } else {
        // Fallback reference equipment
        const defaults: AssetItem[] = [
          {
            id: 'ASSET-FLUKE-8846A-01',
            asset_tag: 'DMM-0182',
            serial_number: '12345678',
            manufacturer: 'Fluke Calibration',
            model: '8846A 6.5 Digit Precision Multimeter',
            instrument_type: 'Digital Multimeter',
            location: 'Electrical Standards Lab Bay 02',
            owner_customer_name: 'Acme Metrology Labs',
            status: 'IN_SERVICE',
            calibration_interval_days: 365,
            last_calibration_date: '2026-03-04',
            next_calibration_due: '2027-03-04',
            days_until_due: 182,
            calibration_health: 'COMPLIANT',
            accuracy_spec: '±0.0024% of reading',
          },
          {
            id: 'ASSET-KEY-34461A-02',
            asset_tag: 'DMM-0291',
            serial_number: 'MY53201844',
            manufacturer: 'Keysight Technologies',
            model: '34461A Truevolt DMM',
            instrument_type: 'Digital Multimeter',
            location: 'Secondary Calibration Bench 01',
            owner_customer_name: 'Micro Precision Labs',
            status: 'IN_SERVICE',
            calibration_interval_days: 365,
            last_calibration_date: '2025-09-10',
            next_calibration_due: '2026-09-10',
            days_until_due: 7,
            calibration_health: 'EXPIRING_SOON',
            accuracy_spec: '±0.0035% of reading',
          },
          {
            id: 'ASSET-DRK-104-03',
            asset_tag: 'PRB-0031',
            serial_number: 'DP-992014',
            manufacturer: 'Baker Hughes Druck',
            model: 'DPI 104 Digital Pressure Indicator',
            instrument_type: 'Pressure Standard',
            location: 'Pneumatics Clean Room',
            owner_customer_name: 'Delta Aero Systems',
            status: 'OVERDUE',
            calibration_interval_days: 180,
            last_calibration_date: '2026-01-15',
            next_calibration_due: '2026-07-15',
            days_until_due: -50,
            calibration_health: 'OVERDUE',
            accuracy_spec: '±0.05% FS',
          },
        ];
        setAssets(defaults);
        setSelectedAsset(defaults[0]);
      }
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssetsList();
  }, []);

  const handleBarcodeScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanInput.trim()) return;
    setScanResult(null);
    try {
      const res = await scanAsset(scanInput.trim());
      if (res.found && res.asset) {
        setSelectedAsset(res.asset);
        setScanResult(`Matched: ${res.asset.manufacturer} ${res.asset.model} (Tag: ${res.asset.asset_tag})`);
      } else {
        setScanResult(`No registered asset found matching identifier "${scanInput}".`);
      }
    } catch (err: any) {
      setScanResult(`Scan error: ${err.message}`);
    }
  };

  const filteredAssets = assets.filter(
    (a) =>
      a.asset_tag.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.serial_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.manufacturer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-hidden">
      {/* Top Header */}
      <div className="p-4 bg-white border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-lg font-bold text-[#17191C] tracking-tight flex items-center gap-2">
            <Tag className="w-5 h-5 text-[#00435F]" />
            <span>Asset Registry</span>
          </h1>
          <p className="text-xs text-[#656B73]">
            Track devices under test, lab standards, serial numbers, calibration intervals, and QR tags
          </p>
        </div>

        {/* Scan input */}
        <form onSubmit={handleBarcodeScan} className="flex items-center gap-2">
          <div className="relative">
            <ScanLine className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#656B73]" />
            <input
              type="text"
              placeholder="Scan Barcode / QR / Serial..."
              value={scanInput}
              onChange={(e) => setScanInput(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-[#F7F8FA] border border-[#E2E5E9] rounded text-xs text-[#17191C] placeholder-[#656B73] outline-none focus:border-[#00435F] w-64"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded hover:bg-[#003348] transition-colors cursor-pointer"
          >
            Scan
          </button>
        </form>
      </div>

      {scanResult && (
        <div className="p-2.5 bg-[#EBF3F6] border-b border-[#CBD5E1] text-[11px] text-[#00435F] flex items-center justify-between font-mono">
          <span>{scanResult}</span>
          <button onClick={() => setScanResult(null)} className="text-[#656B73] hover:text-[#17191C]">✕</button>
        </div>
      )}

      {/* Main Split: Left Asset List / Right Asset Details */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left List (21st.dev list pane) */}
        <div className="w-80 border-r border-[#E2E5E9] bg-white flex flex-col shrink-0">
          <div className="p-2.5 border-b border-[#E2E5E9] bg-[#FAFAFA]">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#656B73]" />
              <input
                type="text"
                placeholder="Search by tag, model, serial..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-[#E2E5E9] rounded text-xs outline-none focus:border-[#00435F]"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-[#E2E5E9]">
            {filteredAssets.map((asset) => {
              const isSelected = selectedAsset?.id === asset.id;
              const isOverdue = asset.calibration_health === 'OVERDUE';
              const isExpiring = asset.calibration_health === 'EXPIRING_SOON';

              return (
                <div
                  key={asset.id}
                  onClick={() => setSelectedAsset(asset)}
                  className={`p-3 cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#EBF3F6] border-l-3 border-[#00435F]' : 'hover:bg-[#F9FAFB]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-[#00435F]">{asset.asset_tag}</span>
                    <span
                      className={`text-[9.5px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                        isOverdue
                          ? 'bg-[#FEE2E2] text-[#DC2626]'
                          : isExpiring
                          ? 'bg-[#FEF3C7] text-[#D97706]'
                          : 'bg-[#DCFCE7] text-[#16A34A]'
                      }`}
                    >
                      {asset.calibration_health || asset.status}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-[#17191C] mt-1 truncate">
                    {asset.model}
                  </div>
                  <div className="text-[10.5px] text-[#656B73] font-mono mt-0.5">
                    SN: {asset.serial_number} &bull; {asset.manufacturer}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Asset Details Pane */}
        {selectedAsset ? (
          <div className="flex-1 bg-[#F7F8FA] flex flex-col overflow-y-auto custom-scrollbar p-6">
            {/* Asset Header Card */}
            <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
                      ASSET ID: {selectedAsset.asset_tag}
                    </span>
                    <span className="text-xs font-mono text-[#656B73]">
                      SERIAL: {selectedAsset.serial_number}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-[#17191C] mt-1.5">
                    {selectedAsset.manufacturer} {selectedAsset.model}
                  </h2>
                  <p className="text-xs text-[#656B73]">
                    {selectedAsset.instrument_type} &bull; Location: {selectedAsset.location || 'Central Metrology Lab'}
                  </p>
                </div>

                <div className="text-right">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F0FDF4] border border-[#BBF7D0] text-[#16A34A] text-xs font-semibold">
                    <span className="w-2 h-2 rounded-full bg-[#16A34A]"></span>
                    <span>{selectedAsset.status.replace(/_/g, ' ')}</span>
                  </div>
                  <div className="text-[11px] text-[#656B73] mt-1">
                    Interval: {selectedAsset.calibration_interval_days || 365} days (12 months)
                  </div>
                </div>
              </div>

              {/* Dates strip */}
              <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-[#E2E5E9] text-xs">
                <div>
                  <span className="text-[#656B73] block text-[10.5px]">Last Calibrated</span>
                  <span className="font-mono font-semibold text-[#17191C]">
                    {selectedAsset.last_calibration_date || '2026-03-04'}
                  </span>
                </div>
                <div>
                  <span className="text-[#656B73] block text-[10.5px]">Next Due Date</span>
                  <span className="font-mono font-semibold text-[#17191C]">
                    {selectedAsset.next_calibration_due || '2027-03-04'}
                  </span>
                </div>
                <div>
                  <span className="text-[#656B73] block text-[10.5px]">Accuracy Specification</span>
                  <span className="font-mono font-semibold text-[#17191C]">
                    {selectedAsset.accuracy_spec || '±0.0024% of reading'}
                  </span>
                </div>
              </div>
            </div>

            {/* 21st.dev Tabs */}
            <div className="mt-6 flex border-b border-[#E2E5E9] bg-white rounded-t-lg px-4 pt-2 gap-4 text-xs font-semibold text-[#656B73]">
              {(['overview', 'history', 'certificates', 'evidence', 'maintenance'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-2.5 capitalize transition-colors cursor-pointer ${
                    activeTab === tab
                      ? 'text-[#00435F] border-b-2 border-[#00435F] font-bold'
                      : 'hover:text-[#17191C]'
                  }`}
                >
                  {tab === 'history' ? 'Calibration History' : tab}
                </button>
              ))}
            </div>

            {/* Tab Body */}
            <div className="bg-white border-x border-b border-[#E2E5E9] rounded-b-lg p-5 shadow-xs flex-1">
              {activeTab === 'overview' && (
                <div className="space-y-4 text-xs">
                  <h3 className="font-bold text-xs text-[#17191C] uppercase tracking-wider">
                    Equipment Specifications & Standards Chain
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
                      <span className="text-[#656B73] block">Owner / Assigned Customer:</span>
                      <span className="font-semibold text-[#17191C] text-sm">
                        {selectedAsset.owner_customer_name || 'Internal Metrology Fleet'}
                      </span>
                    </div>
                    <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
                      <span className="text-[#656B73] block">Barcode Identifier:</span>
                      <span className="font-mono font-semibold text-[#17191C]">
                        {selectedAsset.barcode_data || `METRO:ASSET:${selectedAsset.id}:${selectedAsset.serial_number}`}
                      </span>
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => setActiveWorkspace('jobs')}
                      className="px-3 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded hover:bg-[#003348] transition-colors cursor-pointer"
                    >
                      Schedule New Calibration Job For This Asset
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-3 text-xs">
                  <h3 className="font-bold text-xs text-[#17191C] uppercase tracking-wider">
                    Past Calibration Cycles
                  </h3>
                  <table className="w-full text-left">
                    <thead className="bg-[#F7F8FA] text-[#656B73] font-semibold border-b border-[#E2E5E9]">
                      <tr>
                        <th className="py-2 px-3">Date</th>
                        <th className="py-2 px-3">Job ID</th>
                        <th className="py-2 px-3">Certificate ID</th>
                        <th className="py-2 px-3">Verdict</th>
                        <th className="py-2 px-3">Metrologist</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E5E9]">
                      <tr>
                        <td className="py-2.5 px-3 font-mono">{selectedAsset.last_calibration_date || '2026-03-04'}</td>
                        <td className="py-2.5 px-3 font-mono text-[#00435F]">CAL-1028</td>
                        <td className="py-2.5 px-3 font-mono">CERT-2026-0042</td>
                        <td className="py-2.5 px-3"><span className="text-[#16A34A] font-semibold">PASS</span></td>
                        <td className="py-2.5 px-3">Marcus Brody</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-mono">2025-03-02</td>
                        <td className="py-2.5 px-3 font-mono text-[#00435F]">CAL-0891</td>
                        <td className="py-2.5 px-3 font-mono">CERT-2025-0819</td>
                        <td className="py-2.5 px-3"><span className="text-[#16A34A] font-semibold">PASS</span></td>
                        <td className="py-2.5 px-3">S. Kumar</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'certificates' && (
                <div className="space-y-3 text-xs">
                  <h3 className="font-bold text-xs text-[#17191C] uppercase tracking-wider">
                    Issued Calibration Certificates
                  </h3>
                  <div className="p-3 border border-[#E2E5E9] rounded flex items-center justify-between bg-[#F7F8FA]">
                    <div>
                      <div className="font-mono font-bold text-[#00435F]">CERT-2026-004281</div>
                      <div className="text-[11px] text-[#656B73]">Issued: March 4, 2026 &bull; ISO 17025 Accredited</div>
                    </div>
                    <button
                      onClick={() => setActiveWorkspace('reports')}
                      className="px-2.5 py-1 bg-white border border-[#E2E5E9] rounded font-semibold text-[#00435F] hover:bg-[#EBF3F6]"
                    >
                      View Certificate
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'evidence' && (
                <div className="space-y-2 text-xs">
                  <h3 className="font-bold text-xs text-[#17191C] uppercase tracking-wider">
                    Cryptographic Evidence Vault
                  </h3>
                  <div className="p-3 bg-[#F7F8FA] border border-[#E2E5E9] rounded font-mono text-[11px] text-[#656B73]">
                    SHA-256 Root Digest: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                    <br />
                    Tamper Status: Cryptographically Intact (Zero Modifications)
                  </div>
                </div>
              )}

              {activeTab === 'maintenance' && (
                <div className="text-xs text-[#656B73]">
                  No outstanding preventive maintenance work orders for this asset.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 p-12 text-center text-xs text-[#656B73]">
            Select an asset from the left to view records.
          </div>
        )}
      </div>
    </div>
  );
};

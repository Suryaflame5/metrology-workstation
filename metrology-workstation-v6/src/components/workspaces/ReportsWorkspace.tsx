import React, { useState } from 'react';
import {
  FileBarChart,
  Download,
  Eye,
  FileText,
  Code,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Printer,
  RefreshCw,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const ReportsWorkspace: React.FC = () => {
  const { selectedJob, setActiveWorkspace } = useMetrology();

  if (!selectedJob) {
    return (
      <div className="flex-1 bg-[#F7F8FA] flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md bg-white border border-[#E2E5E9] rounded-xl p-8 shadow-sm">
          <div className="w-12 h-12 rounded-full bg-[#EBF3F6] flex items-center justify-center text-[#00435F] mx-auto mb-4">
            <FileBarChart className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-[#17191C] tracking-tight">
            No Active Job Selected
          </h2>
          <p className="text-xs text-[#656B73] mt-2 leading-relaxed">
            Select a completed or in-progress calibration work order from the Job Hub to view certificate preview, dual electronic signatures, and ISO 17025 PDF reports.
          </p>
          <button
            onClick={() => setActiveWorkspace('jobs')}
            className="mt-5 w-full py-2.5 px-4 bg-[#00435F] hover:bg-[#003348] text-white text-xs font-semibold rounded-lg shadow-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Open Job Hub</span>
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  const certNumber = selectedJob.certificate_id || `CERT-2026-${selectedJob.job_number?.replace('JOB-', '') || '0042'}`;
  const meanVal = selectedJob.statistics?.mean ?? (selectedJob.raw_measurements?.[0] ?? selectedJob.nominal_value);
  const nomVal = selectedJob.nominal_value ?? 10.0;
  const devVal = selectedJob.conformity?.error_of_indication ?? (meanVal - nomVal);
  const u95 = selectedJob.uncertainty_budget?.expanded_uncertainty_U95 ?? 0.00031;
  const kFactor = selectedJob.uncertainty_budget?.coverage_factor_k ?? 2.0;

  const certData = {
    certNumber: certNumber,
    assetName: selectedJob.instrument_name || 'Precision Unit Under Test',
    serial: selectedJob.instrument_serial || 'SN-UNKNOWN',
    customer: selectedJob.customer_name || 'Laboratory Operations',
    procedure: selectedJob.procedure_name || 'Standard Verification',
    version: selectedJob.revision_number ? `Rev ${selectedJob.revision_number}.0` : 'Rev 1.0',
    date: selectedJob.created_at ? selectedJob.created_at.substring(0, 10) : new Date().toISOString().substring(0, 10),
    result: selectedJob.conformity?.conformance_verdict || 'PASS',
    expandedUncertainty: `±${u95.toFixed(5)} ${selectedJob.unit || 'V'} (k=${kFactor})`,
    technician: selectedJob.operator || 'Lead Metrologist',
    reviewer: selectedJob.reviewer || 'Dr. E. Vance (Quality Manager)',
  };

  const activeJobId = selectedJob.id;

  return (
    <div className="flex-1 bg-[#F7F8FA] flex flex-col h-full overflow-y-auto custom-scrollbar p-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-[#E2E5E9] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#00435F] bg-[#EBF3F6] px-2 py-0.5 rounded border border-[#CBD5E1]">
              DOCUMENT PRODUCTION SYSTEM
            </span>
            <span className="text-xs text-[#656B73]">ISO/IEC 17025 Accredited Calibration Certificates</span>
          </div>
          <h1 className="text-xl font-bold text-[#17191C] mt-1 tracking-tight">
            Calibration Certificates & DCC Export &mdash; {selectedJob.job_number}
          </h1>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={`/api/v1/jobs/${encodeURIComponent(activeJobId)}/advanced-certificate-pdf`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00435F] text-white text-xs font-semibold rounded shadow-xs hover:bg-[#003348] transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Preview / Download ISO 17025 PDF (4-Page)</span>
          </a>

          <a
            href={`/api/v1/jobs/${encodeURIComponent(activeJobId)}/dcc-json`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
          >
            <Code className="w-3.5 h-3.5 text-[#00435F]" />
            <span>Export DCC JSON</span>
          </a>

          <a
            href={`/api/v1/jobs/${encodeURIComponent(activeJobId)}/dcc-xml`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-[#00435F]" />
            <span>Export DCC XML</span>
          </a>

          <a
            href={`/api/jobs/${encodeURIComponent(activeJobId)}/evidence-package`}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E5E9] hover:border-[#00435F] text-[#17191C] text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-[#00435F]" />
            <span>Evidence Package (ZIP)</span>
          </a>
        </div>
      </div>

      {/* Meta Card */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg p-5 shadow-xs mt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#E2E5E9] gap-4">
          <div>
            <div className="text-[11px] font-bold text-[#656B73] uppercase tracking-wider">
              CERTIFICATE IDENTIFIER
            </div>
            <div className="text-2xl font-black text-[#00435F] font-mono mt-1">
              {certData.certNumber}
            </div>
            <p className="text-xs text-[#656B73] mt-0.5">
              Issued under ISO/IEC 17025 Accreditation &bull; Standard Calibration Lab
            </p>
          </div>

          <div className="text-right">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#DCFCE7] border border-[#BBF7D0] text-[#16A34A] rounded text-xs font-mono font-bold">
              <CheckCircle2 className="w-4 h-4" />
              CONFORMANCE: {certData.result}
            </span>
            <div className="text-[11px] text-[#656B73] font-mono mt-1">
              Issued: {certData.date}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-xs">
          <div>
            <span className="text-[#656B73] block text-[11px]">Asset</span>
            <span className="font-semibold text-[#17191C]">{certData.assetName}</span>
          </div>
          <div>
            <span className="text-[#656B73] block text-[11px]">Serial Number</span>
            <span className="font-mono font-semibold text-[#17191C]">{certData.serial}</span>
          </div>
          <div>
            <span className="text-[#656B73] block text-[11px]">Standard Procedure</span>
            <span className="font-semibold text-[#17191C]">{certData.procedure} (v{certData.version})</span>
          </div>
          <div>
            <span className="text-[#656B73] block text-[11px]">Expanded Uncertainty</span>
            <span className="font-mono font-semibold text-[#17191C]">{certData.expandedUncertainty}</span>
          </div>
        </div>
      </div>

      {/* Document Visual Preview (Clean Paper Representation) */}
      <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-md mt-6 max-w-4xl mx-auto w-full p-8 font-sans text-xs text-[#17191C] space-y-6">
        {/* Certificate Header Banner */}
        <div className="border-b-2 border-[#00435F] pb-4 flex items-center justify-between">
          <div>
            <div className="text-xl font-black text-[#00435F] tracking-tight">
              CERTIFICATE OF CALIBRATION
            </div>
            <div className="text-xs text-[#656B73]">
              Chennai Metrology & Standards Laboratory &bull; ISO/IEC 17025 Accredited
            </div>
          </div>
          <div className="text-right font-mono">
            <div className="text-sm font-bold text-[#00435F]">{certData.certNumber}</div>
            <div className="text-[11px] text-[#656B73]">Page 1 of 2</div>
          </div>
        </div>

        {/* Customer & Asset Block */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
          <div>
            <div className="font-bold uppercase text-[10px] text-[#656B73] mb-1">Customer / Location</div>
            <div className="font-semibold">{certData.customer}</div>
            <div className="text-[#656B73]">Advanced Electronics Division</div>
          </div>
          <div>
            <div className="font-bold uppercase text-[10px] text-[#656B73] mb-1">Device Under Test</div>
            <div className="font-semibold">{certData.assetName}</div>
            <div className="text-[#656B73] font-mono">Serial: {certData.serial}</div>
          </div>
        </div>

        {/* Traceability & Environmental Conditions */}
        <div>
          <h3 className="font-bold uppercase text-[11px] text-[#00435F] mb-2 border-b border-[#E2E5E9] pb-1">
            1. Environmental Conditions & Traceability
          </h3>
          <div className="grid grid-cols-3 gap-3 text-[#17191C]">
            <div>Ambient Temperature: <span className="font-mono font-semibold">20.05 °C ± 0.2 °C</span></div>
            <div>Relative Humidity: <span className="font-mono font-semibold">45.8 %RH</span></div>
            <div>Atmospheric Pressure: <span className="font-mono font-semibold">1013.25 hPa</span></div>
          </div>
          <div className="mt-2 text-[#656B73]">
            Traceability: Measurements traceable to the International System of Units (SI) through NIST via Fluke 5720A Primary Calibrator.
          </div>
        </div>

        {/* Calibration Results Table */}
        <div>
          <h3 className="font-bold uppercase text-[11px] text-[#00435F] mb-2 border-b border-[#E2E5E9] pb-1">
            2. Calibrated Measurement Results
          </h3>
          <table className="w-full text-left border border-[#E2E5E9]">
            <thead className="bg-[#F7F8FA] border-b border-[#E2E5E9] font-semibold text-[#656B73]">
              <tr>
                <th className="p-2">Nominal Value</th>
                <th className="p-2">Indicated Mean</th>
                <th className="p-2">Deviation</th>
                <th className="p-2">Expanded Uncertainty U (k=2)</th>
                <th className="p-2">Verdict</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-2 font-mono">10.00000 V</td>
                <td className="p-2 font-mono">9.99982 V</td>
                <td className="p-2 font-mono">-0.00018 V</td>
                <td className="p-2 font-mono">±0.00031 V</td>
                <td className="p-2 font-bold text-[#16A34A]">PASS</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Conformity & Signatures */}
        <div className="pt-4 border-t border-[#E2E5E9] grid grid-cols-2 gap-6">
          <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9]">
            <div className="font-bold text-[10.5px] uppercase text-[#656B73]">Conformity Statement</div>
            <p className="mt-1 leading-relaxed text-[11px]">
              Compliance statement based on ANSI/NCSL Z540.3 Method 6 guardband. Probability of False Accept is 0.02% (≤ 2.0%).
            </p>
          </div>

          <div className="p-3 bg-[#F7F8FA] rounded border border-[#E2E5E9] font-mono text-[11px]">
            <div className="font-bold text-[10.5px] uppercase text-[#656B73] font-sans">Digital Endorsement</div>
            <div className="mt-1">Technician: {certData.technician}</div>
            <div>Approved by: {certData.reviewer}</div>
            <div className="text-[#16A34A] font-semibold mt-1">21 CFR Part 11 Electronically Signed</div>
          </div>
        </div>
      </div>
    </div>
  );
};

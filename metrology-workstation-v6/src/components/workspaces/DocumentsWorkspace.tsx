import React from 'react';
import { Download, FileText, Lock, Plus } from 'lucide-react';

export const DocumentsWorkspace: React.FC = () => {
  const docs = [
    {
      id: 'DOC-01',
      title: 'ISO/IEC 17025 Quality Manual Section 7.6 (Uncertainty)',
      size: '2.4 MB',
      type: 'PDF',
      date: '2023-01-15',
    },
    {
      id: 'DOC-02',
      title: 'Fluke 8508A Service & Calibration Manual Rev D',
      size: '18.1 MB',
      type: 'PDF',
      date: '2022-11-04',
    },
    {
      id: 'DOC-03',
      title: 'Primary Standard Resistor Oil Bath Calibration Certificate',
      size: '1.1 MB',
      type: 'PDF',
      date: '2023-05-12',
    },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-[#f4f5f3] select-none p-6 space-y-6 max-w-5xl mx-auto">
      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-xs font-bold text-[#00435f] bg-[#dbe4ea] px-2 py-0.5 rounded border border-[#c1c7ce]">
            DOCUMENT REPOSITORY
          </span>
          <span className="text-xs font-semibold text-[#576065]">
            Laboratory Procedures & Quality Artifacts
          </span>
        </div>
        <h1 className="text-xl font-bold text-[#191c1e] tracking-tight">
          Governing Documents & Standards Repository
        </h1>
      </div>

      <div className="bg-white border border-[#c1c7ce] rounded-lg p-5 space-y-3 font-mono text-xs">
        {docs.map((d) => (
          <div key={d.id} className="p-3 bg-[#f9f9fc] border border-[#c1c7ce] rounded flex justify-between items-center hover:bg-[#f3f4f2]">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-[#00435f]" />
              <div>
                <div className="font-bold text-[#191c1e] font-sans text-sm">{d.title}</div>
                <div className="text-[11px] text-[#576065]">
                  {d.id} • {d.size} • {d.date}
                </div>
              </div>
            </div>
            <button className="px-3 py-1 bg-white border border-[#c1c7ce] rounded hover:bg-[#e7e8e6] text-[#00435f] font-semibold flex items-center gap-1 cursor-pointer">
              <Download className="w-3.5 h-3.5" />
              <span>Download</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Inbox,
  Tag,
  Cpu,
  PlayCircle,
  PlusCircle,
  ListOrdered,
  AlertTriangle,
  FileBarChart,
  ScanLine,
  Ruler,
  Calculator,
  ShieldCheck,
  CheckCheck,
  ScrollText,
  X,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';

export const CommandPalette: React.FC = () => {
  const {
    isCommandPaletteOpen,
    setIsCommandPaletteOpen,
    setActiveWorkspace,
  } = useMetrology();

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isCommandPaletteOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
      setQuery('');
    }
  }, [isCommandPaletteOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen(!isCommandPaletteOpen);
      }
      if (e.key === 'Escape' && isCommandPaletteOpen) {
        setIsCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, setIsCommandPaletteOpen]);

  if (!isCommandPaletteOpen) return null;

  const allCommands = [
    {
      id: 'cmd-search-job',
      title: 'Search Job',
      subtitle: 'Find calibration work orders by ID or customer',
      category: 'Operations',
      icon: Inbox,
      action: () => {
        setActiveWorkspace('jobs');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-search-asset',
      title: 'Search Asset',
      subtitle: 'Locate equipment by serial number or asset tag',
      category: 'Operations',
      icon: Tag,
      action: () => {
        setActiveWorkspace('assets');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-search-instrument',
      title: 'Search Instrument',
      subtitle: 'Inspect bench measurement standards and SCPI links',
      category: 'Operations',
      icon: Cpu,
      action: () => {
        setActiveWorkspace('instrument');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-active-run',
      title: 'Open Active Run',
      subtitle: 'Launch real-time calibration execution cockpit',
      category: 'Execution',
      icon: PlayCircle,
      action: () => {
        setActiveWorkspace('job-workflow');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-create-job',
      title: 'Create Job',
      subtitle: 'Create a new calibration work order from procedure',
      category: 'Operations',
      icon: PlusCircle,
      action: () => {
        setActiveWorkspace('jobs');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-start-procedure',
      title: 'Start Procedure',
      subtitle: 'Select SOP and initialize calibration run',
      category: 'Execution',
      icon: ListOrdered,
      action: () => {
        setActiveWorkspace('procedure');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-view-exceptions',
      title: 'View Exceptions',
      subtitle: 'Inspect out-of-tolerance and communication errors',
      category: 'Execution',
      icon: AlertTriangle,
      action: () => {
        setActiveWorkspace('exception-center');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-open-certificate',
      title: 'Open Certificate',
      subtitle: 'Preview ISO 17025 PDF and export DCC JSON/XML',
      category: 'Results',
      icon: FileBarChart,
      action: () => {
        setActiveWorkspace('reports');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-scan-asset',
      title: 'Scan Asset Barcode / QR',
      subtitle: 'Quick lookup via METRO:ASSET barcode payload',
      category: 'Operations',
      icon: ScanLine,
      action: () => {
        setActiveWorkspace('assets');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-measurements',
      title: 'View Measurements Table',
      subtitle: 'Dense aligned measurement dataset',
      category: 'Results',
      icon: Ruler,
      action: () => {
        setActiveWorkspace('measurements');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-uncertainty',
      title: 'Inspect Uncertainty Budget',
      subtitle: 'GUM Type A & B standard uncertainties & DOF',
      category: 'Results',
      icon: Calculator,
      action: () => {
        setActiveWorkspace('uncertainty');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-conformity',
      title: 'Inspect Conformity Decision',
      subtitle: 'Guard-banded ISO 17025 statement & PFA/PFR risk',
      category: 'Results',
      icon: ShieldCheck,
      action: () => {
        setActiveWorkspace('conformity');
        setIsCommandPaletteOpen(false);
      },
    },
    {
      id: 'cmd-evidence',
      title: 'Audit & Evidence Chain',
      subtitle: 'Cryptographic SHA-256 integrity verification',
      category: 'Evidence',
      icon: CheckCheck,
      action: () => {
        setActiveWorkspace('evidence');
        setIsCommandPaletteOpen(false);
      },
    },
  ];

  const filteredCommands = allCommands.filter(
    (c) =>
      c.title.toLowerCase().includes(query.toLowerCase()) ||
      c.subtitle.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filteredCommands.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % (filteredCommands.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        filteredCommands[selectedIndex].action();
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-start justify-center pt-24 z-50 p-4">
      <div className="bg-white border border-[#E2E5E9] rounded-lg shadow-2xl w-full max-w-xl overflow-hidden flex flex-col">
        {/* Search Header */}
        <div className="flex items-center px-3.5 py-2.5 border-b border-[#E2E5E9] bg-[#F7F8FA] gap-2">
          <Search className="w-4 h-4 text-[#656B73] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search (Job, Asset, Instrument, Action)..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent border-none text-xs text-[#17191C] placeholder-[#656B73] outline-none"
          />
          <button
            onClick={() => setIsCommandPaletteOpen(false)}
            className="text-[#656B73] hover:text-[#17191C] p-1 rounded hover:bg-[#E2E5E9] transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-1.5 custom-scrollbar">
          {filteredCommands.length === 0 ? (
            <div className="p-6 text-center text-xs text-[#656B73]">
              No matching commands or resources found for "{query}".
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  onClick={cmd.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center gap-3 px-3 py-2 rounded text-xs cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#EBF3F6] text-[#00435F]' : 'hover:bg-[#F7F8FA] text-[#17191C]'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded flex items-center justify-center shrink-0 ${
                      isSelected ? 'bg-[#00435F] text-white' : 'bg-[#F1F5F9] text-[#656B73]'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium flex items-center gap-2">
                      <span>{cmd.title}</span>
                      <span className="text-[10px] text-[#656B73] font-mono uppercase bg-[#F1F5F9] px-1.5 py-0.2 rounded border border-[#E2E5E9]">
                        {cmd.category}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#656B73] truncate">{cmd.subtitle}</div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="px-3 py-2 border-t border-[#E2E5E9] bg-[#F7F8FA] flex items-center justify-between text-[10.5px] text-[#656B73] font-mono">
          <span>Use ↑ / ↓ to navigate, Enter to select</span>
          <span>Esc to dismiss</span>
        </div>
      </div>
    </div>
  );
};

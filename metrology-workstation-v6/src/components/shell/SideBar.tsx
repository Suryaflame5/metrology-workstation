import React from 'react';
import {
  LayoutDashboard,
  FolderGit2,
  Inbox,
  Tag,
  Cpu,
  ListOrdered,
  PlayCircle,
  Layers,
  AlertTriangle,
  Ruler,
  Calculator,
  ShieldCheck,
  FileBarChart,
  CheckCheck,
  ScrollText,
  Users,
  Settings,
  User,
} from 'lucide-react';
import { useMetrology } from '../../context/MetrologyContext';
import { WorkspaceId } from '../../types';

interface NavItem {
  id: WorkspaceId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  isAlert?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'WORKSPACE',
    items: [
      { id: 'overview', label: 'Overview', icon: LayoutDashboard },
      { id: 'projects', label: 'Projects', icon: FolderGit2 },
      { id: 'jobs', label: 'Jobs', icon: Inbox },
      { id: 'assets', label: 'Assets', icon: Tag },
      { id: 'instrument', label: 'Instruments', icon: Cpu },
    ],
  },
  {
    title: 'EXECUTION',
    items: [
      { id: 'procedure', label: 'Procedures', icon: ListOrdered },
      { id: 'job-workflow', label: 'Active Runs', icon: PlayCircle, badge: 'Live' },
      { id: 'batch-processing', label: 'Batch Runs', icon: Layers },
      { id: 'exception-center', label: 'Exceptions', icon: AlertTriangle, isAlert: true },
    ],
  },
  {
    title: 'RESULTS',
    items: [
      { id: 'measurements', label: 'Measurements', icon: Ruler },
      { id: 'uncertainty', label: 'Uncertainty', icon: Calculator },
      { id: 'conformity', label: 'Conformity', icon: ShieldCheck },
      { id: 'reports', label: 'Certificates', icon: FileBarChart },
    ],
  },
  {
    title: 'EVIDENCE',
    items: [
      { id: 'evidence', label: 'Evidence', icon: CheckCheck },
      { id: 'audit', label: 'Audit Trail', icon: ScrollText },
    ],
  },
  {
    title: 'ADMIN',
    items: [
      { id: 'customers', label: 'Users & Roles', icon: Users },
      { id: 'settings', label: 'Settings', icon: Settings },
    ],
  },
];

export const SideBar: React.FC = () => {
  const { activeWorkspace, setActiveWorkspace } = useMetrology();

  return (
    <aside className="bg-[#FFFFFF] w-[240px] h-full border-r border-[#E2E5E9] flex flex-col shrink-0 select-none z-20">
      {/* Session Operator Header */}
      <div className="p-3 border-b border-[#E2E5E9] bg-[#F7F8FA] flex items-center gap-2.5">
        <div className="w-7 h-7 rounded bg-[#00435F] flex items-center justify-center text-white shrink-0 shadow-xs">
          <User className="w-3.5 h-3.5" />
        </div>
        <div className="min-w-0">
          <div className="font-semibold text-[13px] leading-tight text-[#17191C] truncate">
            Marcus Brody
          </div>
          <div className="text-[10px] text-[#656B73] flex items-center gap-1 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]"></span>
            <span>Lead Metrologist</span>
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-3.5 custom-scrollbar">
        {NAV_SECTIONS.map((section, sIdx) => (
          <div key={sIdx} className="space-y-0.5">
            <div className="px-2.5 py-1 text-[10px] font-bold text-[#656B73] tracking-widest uppercase">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeWorkspace === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveWorkspace(item.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[12.5px] font-medium transition-colors ${
                      isActive
                        ? 'bg-[#EBF3F6] text-[#00435F] font-semibold border-l-2 border-[#00435F]'
                        : 'text-[#17191C] hover:bg-[#F7F8FA] hover:text-[#00435F]'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Icon
                        className={`w-4 h-4 shrink-0 ${
                          isActive ? 'text-[#00435F]' : 'text-[#656B73]'
                        }`}
                      />
                      <span className="truncate">{item.label}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={`text-[9.5px] px-1.5 py-0.5 rounded font-mono font-semibold uppercase tracking-wider ${
                          item.isAlert
                            ? 'bg-[#FEE2E2] text-[#DC2626] border border-[#FCA5A5]'
                            : isActive
                            ? 'bg-[#00435F] text-white'
                            : 'bg-[#F1F5F9] text-[#656B73]'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer System Status */}
      <div className="p-2.5 border-t border-[#E2E5E9] bg-[#F7F8FA] text-[10.5px] text-[#656B73]">
        <div className="flex items-center justify-between font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]"></span>
            <span>SYSTEM READY</span>
          </span>
          <span className="text-[#8C939D]">v7.0.0</span>
        </div>
      </div>
    </aside>
  );
};

import React from 'react';
import { MetrologyProvider, useMetrology } from './context/MetrologyContext';
import { TopBar } from './components/shell/TopBar';
import { SideBar } from './components/shell/SideBar';
import { StatusBar } from './components/shell/StatusBar';
import { CommandPalette } from './components/shell/CommandPalette';
import { DiagnosticsModal } from './components/shell/DiagnosticsModal';
import { FirstRunOnboardingModal } from './components/shell/FirstRunOnboardingModal';
import { EditionComparisonModal } from './components/shell/EditionComparisonModal';

// Workspaces
import { OverviewWorkspace } from './components/workspaces/OverviewWorkspace';
import { ProjectsWorkspace } from './components/workspaces/ProjectsWorkspace';
import { AssetsWorkspace } from './components/workspaces/AssetsWorkspace';
import { ActiveRunWorkspace } from './components/workspaces/ActiveRunWorkspace';
import { MeasurementsWorkspace } from './components/workspaces/MeasurementsWorkspace';
import { InstrumentsWorkspace } from './components/workspaces/InstrumentsWorkspace';
import { ProceduresWorkspace } from './components/workspaces/ProceduresWorkspace';
import { ValidationWorkspace } from './components/workspaces/ValidationWorkspace';
import { CalculationWorkspace } from './components/workspaces/CalculationWorkspace';
import { CalculationChainWorkspace } from './components/workspaces/CalculationChainWorkspace';
import { MeasurementModelWorkspace } from './components/workspaces/MeasurementModelWorkspace';
import { UncertaintyWorkspace } from './components/workspaces/UncertaintyWorkspace';
import { MonteCarloWorkspace } from './components/workspaces/MonteCarloWorkspace';
import { ConformityWorkspace } from './components/workspaces/ConformityWorkspace';
import { GuardbandTURWorkspace } from './components/workspaces/GuardbandTURWorkspace';
import { CalibrationHistoryWorkspace } from './components/workspaces/CalibrationHistoryWorkspace';
import { ComparisonWorkspace } from './components/workspaces/ComparisonWorkspace';
import { EvidenceWorkspace } from './components/workspaces/EvidenceWorkspace';
import { DocumentsWorkspace } from './components/workspaces/DocumentsWorkspace';
import { AuditTrailWorkspace } from './components/workspaces/AuditTrailWorkspace';
import { ReportsWorkspace } from './components/workspaces/ReportsWorkspace';
import { SettingsWorkspace } from './components/workspaces/SettingsWorkspace';
import { JobInboxWorkspace } from './components/jobs/JobInboxWorkspace';
import { JobWorkflowCockpit } from './components/jobs/JobWorkflowCockpit';
import { BatchProcessingWorkspace } from './components/workspaces/BatchProcessingWorkspace';
import { ExceptionCenterWorkspace } from './components/workspaces/ExceptionCenterWorkspace';
import { ReviewCockpitWorkspace } from './components/workspaces/ReviewCockpitWorkspace';
import { CustomersWorkspace } from './components/workspaces/CustomersWorkspace';
import { HardwareDevicesWorkspace } from './components/workspaces/HardwareDevicesWorkspace';
import { AboutWorkspace } from './components/workspaces/AboutWorkspace';

const MainWorkspaceRouter: React.FC = () => {
  const { activeWorkspace, setActiveWorkspace, selectedJob, setSelectedJob } = useMetrology();

  switch (activeWorkspace) {
    case 'overview':
      return <OverviewWorkspace />;
    case 'projects':
      return <ProjectsWorkspace />;
    case 'jobs':
      return (
        <JobInboxWorkspace
          onSelectJob={(job) => {
            setSelectedJob(job);
            setActiveWorkspace('job-workflow');
          }}
        />
      );
    case 'assets':
      return <AssetsWorkspace />;
    case 'instrument':
      return <InstrumentsWorkspace />;
    case 'procedure':
      return <ProceduresWorkspace />;
    case 'active-runs':
      return <ActiveRunWorkspace />;
    case 'job-workflow':
      return selectedJob ? (
        <JobWorkflowCockpit
          job={selectedJob}
          onBack={() => setActiveWorkspace('jobs')}
          onUpdateJob={(updated) => setSelectedJob(updated)}
        />
      ) : (
        <ActiveRunWorkspace />
      );
    case 'batch-processing':
      return <BatchProcessingWorkspace />;
    case 'exception-center':
      return <ExceptionCenterWorkspace />;
    case 'measurements':
      return <MeasurementsWorkspace />;
    case 'uncertainty':
      return <UncertaintyWorkspace />;
    case 'conformity':
      return <ConformityWorkspace />;
    case 'reports':
    case 'certificates':
      return <ReportsWorkspace />;
    case 'evidence':
      return <EvidenceWorkspace />;
    case 'audit':
      return <AuditTrailWorkspace />;
    case 'review-cockpit':
      return <ReviewCockpitWorkspace />;
    case 'customers':
    case 'users-roles':
      return <CustomersWorkspace />;
    case 'settings':
      return <SettingsWorkspace />;
    case 'hardware':
      return <HardwareDevicesWorkspace />;
    case 'validation':
      return <ValidationWorkspace />;
    case 'calculation':
      return <CalculationWorkspace />;
    case 'calculation-chain':
      return <CalculationChainWorkspace />;
    case 'model':
      return <MeasurementModelWorkspace />;
    case 'monte-carlo':
      return <MonteCarloWorkspace />;
    case 'guardband':
    case 'tur':
      return <GuardbandTURWorkspace />;
    case 'calibration-history':
      return <CalibrationHistoryWorkspace />;
    case 'comparison':
      return <ComparisonWorkspace />;
    case 'documents':
      return <DocumentsWorkspace />;
    case 'about':
      return <AboutWorkspace />;
    default:
      return <OverviewWorkspace />;
  }
};

export default function App() {
  return (
    <MetrologyProvider>
      <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#F7F8FA] text-[#17191C]">
        {/* Top Header Chrome */}
        <TopBar />

        {/* Central Workspace (Sidebar + Dynamic Router View) */}
        <div className="flex-1 flex overflow-hidden">
          <SideBar />
          <main className="flex-1 flex flex-col overflow-hidden relative">
            <MainWorkspaceRouter />
          </main>
        </div>

        {/* Bottom Hardware Status & Sync Chrome */}
        <StatusBar />

        {/* Global Modals */}
        <CommandPalette />
        <DiagnosticsModal />
        <FirstRunOnboardingModal />
        <EditionComparisonModal />
      </div>
    </MetrologyProvider>
  );
}

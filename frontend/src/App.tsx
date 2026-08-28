import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { AppShell } from './components/shell/AppShell';

import { OverviewPage } from './pages/OverviewPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { PerceptionPage } from './pages/PerceptionPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { ActivityPage } from './pages/ActivityPage';
import { PerformancePage } from './pages/PerformancePage';
import { DemoLabPage } from './pages/DemoLabPage';
import { JudgeModePage } from './pages/JudgeModePage';
import { SettingsPage } from './pages/SettingsPage';

const AppContent: React.FC = () => {
  const { activePage } = useApp();

  const renderPage = () => {
    switch (activePage) {
      case 'overview':
        return <OverviewPage />;
      case 'workspace':
        return <WorkspacePage />;
      case 'perception':
        return <PerceptionPage />;
      case 'privacy':
        return <PrivacyPage />;
      case 'activity':
        return <ActivityPage />;
      case 'performance':
        return <PerformancePage />;
      case 'demolab':
        return <DemoLabPage />;
      case 'judge':
        return <JudgeModePage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage />;
    }
  };


  return <AppShell>{renderPage()}</AppShell>;
};

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

import React from 'react';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { ConfirmDialog } from '../common/ConfirmDialog';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="app-shell">
      <TopBar />
      <div className="app-body">
        <Sidebar />
        <main className="main-view-container" role="main">
          {children}
        </main>
      </div>
      <ConfirmDialog />
    </div>
  );
};

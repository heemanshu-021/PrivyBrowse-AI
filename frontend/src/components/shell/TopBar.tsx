import React from 'react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';

export const TopBar: React.FC = () => {
  const {
    backendConnected,
    extensionConnected,
    privacyStatus,
    currentScenario,
    setActivePage,
    refreshHealth,
    isProcessing
  } = useApp();

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="topbar-brand" onClick={() => setActivePage('overview')}>
          <div className="brand-icon">🛡️</div>
          <div className="brand-text-wrapper">
            <span className="brand-title">PRIVYBROWSE AI</span>
            <span className="brand-tagline">See. Understand. Protect. Act.</span>
          </div>
        </div>
      </div>

      <div className="topbar-center">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <StatusBadge
            status={backendConnected ? 'LOCAL ENGINE ONLINE' : 'SANDBOX SIMULATOR'}
            variant={backendConnected ? 'green' : 'amber'}
            dot
          />
          <StatusBadge
            status={extensionConnected ? 'BROWSER CONNECTED' : backendConnected ? 'DAEMON READY' : 'STANDALONE SANDBOX'}
            variant={extensionConnected ? 'green' : backendConnected ? 'cyan' : 'muted'}
            dot
          />
          <StatusBadge
            status={`PRIVACY ${privacyStatus}`}
            variant="green"
            dot
          />
        </div>
      </div>

      <div className="topbar-right">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Target:</span>
          <span
            style={{
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--accent-cyan)',
              backgroundColor: 'var(--bg-card-subtle)',
              padding: '3px 8px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)'
            }}
          >
            {currentScenario.name}
          </span>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={refreshHealth}
          title="Re-check local perception engine connection"
          disabled={isProcessing}
        >
          <span>↻</span>
          <span>Sync Engine</span>
        </button>

        <button
          className="btn btn-cyan btn-sm"
          onClick={() => setActivePage('demolab')}
        >
          <span>🧪</span>
          <span>Demo Lab</span>
        </button>

        <button
          className="btn btn-primary btn-sm"
          onClick={() => setActivePage('judge')}
          style={{ backgroundColor: 'var(--accent-amber)', color: '#04101e', fontWeight: 700 }}
        >
          <span>⚖️</span>
          <span>Judge Mode</span>
        </button>
      </div>
    </header>

  );
};

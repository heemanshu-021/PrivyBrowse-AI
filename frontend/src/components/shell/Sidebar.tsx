import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import type { PageId } from '../../types';

interface NavItemDef {
  id: PageId;
  label: string;
  icon: string;
  badge?: string;
}

const PRIMARY_NAV: NavItemDef[] = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'workspace', label: 'Agent Workspace', icon: '🎯' },
  { id: 'perception', label: 'Perception Inspector', icon: '👁️' },
  { id: 'privacy', label: 'Privacy Center', icon: '🛡️' },
  { id: 'activity', label: 'Activity & Logs', icon: '📜' },
  { id: 'performance', label: 'Performance', icon: '⚡' }
];

const SECONDARY_NAV: NavItemDef[] = [
  { id: 'judge', label: 'Judge Mode', icon: '⚖️', badge: 'SIH26171' },
  { id: 'demolab', label: 'Demo Lab', icon: '🧪', badge: '5 LABS' },
  { id: 'settings', label: 'Settings', icon: '⚙️' }
];


export const Sidebar: React.FC = () => {
  const {
    activePage,
    setActivePage,
    backendConnected,
    privacyStatus,
    metrics
  } = useApp();

  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} aria-label="Sidebar Navigation">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 8px' }}>
          {!collapsed && <span className="sidebar-heading">Navigation</span>}
          <button
            className="btn btn-secondary btn-icon-only btn-sm"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            style={{ marginLeft: collapsed ? 'auto' : undefined, marginRight: collapsed ? 'auto' : undefined }}
          >
            {collapsed ? '→' : '←'}
          </button>
        </div>

        <nav className="sidebar-nav">
          {PRIMARY_NAV.map(item => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActivePage(item.id)}
                title={item.label}
              >
                <span className="nav-item-icon">{item.icon}</span>
                {!collapsed && <span className="nav-item-text">{item.label}</span>}
                {!collapsed && item.badge && (
                  <span className="badge badge-cyan" style={{ marginLeft: 'auto', fontSize: '9px' }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {!collapsed && <span className="sidebar-heading">Evaluation</span>}
        <nav className="sidebar-nav">
          {SECONDARY_NAV.map(item => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActivePage(item.id)}
                title={item.label}
              >
                <span className="nav-item-icon">{item.icon}</span>
                {!collapsed && <span className="nav-item-text">{item.label}</span>}
                {!collapsed && item.badge && (
                  <span className="badge badge-purple" style={{ marginLeft: 'auto', fontSize: '9px' }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-footer">
        {!collapsed && (
          <div className="sidebar-status-box">
            <div className="status-row">
              <span className="status-label">Perception</span>
              <span className="status-pill" style={{ color: backendConnected ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
                <span className={`status-dot ${backendConnected ? 'online' : 'warning'}`} />
                {backendConnected ? 'ON-DEVICE' : 'SANDBOX'}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label">Privacy Shield</span>
              <span className="status-pill" style={{ color: 'var(--accent-green)' }}>
                <span className="status-dot online" />
                {privacyStatus}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label">Loop Latency</span>
              <span className="status-pill" style={{ color: 'var(--accent-cyan)' }}>
                {metrics.total_task_latency_ms > 0 ? `${metrics.total_task_latency_ms} ms` : 'Idle'}
              </span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

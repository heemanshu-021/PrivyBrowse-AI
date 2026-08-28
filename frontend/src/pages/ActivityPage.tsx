import React from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';
import { EmptyState } from '../components/common/EmptyState';

export const ActivityPage: React.FC = () => {
  const { logs, actionHistory, resetState } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Activity & Execution Logs</h1>
          <p className="page-subtitle">
            Trace the complete lifecycle of observation frames, PII filter events, action planning queries, and browser state transitions.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={resetState}>
          <span>🗑️</span>
          <span>Clear Logs</span>
        </button>
      </div>

      {/* 2. Action History Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">🚀</span>
            <span>Executed Actions History ({actionHistory.length})</span>
          </span>
          <span className="badge badge-cyan">{actionHistory.length} ACTIONS RECORDED</span>
        </div>

        {actionHistory.length > 0 ? (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Action Verb</th>
                  <th>Target Descriptor</th>
                  <th>Coordinates</th>
                  <th>Payload</th>
                  <th>Confidence</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {actionHistory.map((act, idx) => (
                  <tr key={idx}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      #{idx + 1}
                    </td>
                    <td>
                      <StatusBadge status={act.action} />
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {act.target_description}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
                        ({act.target.x}, {act.target.y})
                      </span>
                    </td>
                    <td>
                      {act.text ? (
                        <code style={{ color: 'var(--accent-green)' }}>"{act.text}"</code>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>
                    <td>
                      <ConfidenceBadge confidence={act.confidence} />
                    </td>
                    <td>
                      <span className="badge badge-green">VERIFIED</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon="📜"
            title="No Actions Executed Yet"
            description="Run a mission and click 'Execute Action Safely' in the workspace to populate the execution trace."
          />
        )}
      </div>

      {/* 3. System Console Terminal */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">💻</span>
            <span>Real-Time System Log Stream</span>
          </span>
          <span className="badge badge-muted">{logs.length} EVENTS</span>
        </div>

        <div className="console" style={{ height: '360px' }}>
          {logs.map((log) => (
            <div key={log.id} className="console-line">
              <span className="console-time">[{log.time}]</span>
              <span className={`console-tag ${log.tag}`}>{log.tag.toUpperCase()}:</span>
              <span style={{ color: log.tag === 'sec' ? '#fca5a5' : log.tag === 'err' ? '#f87171' : '#e2e8f0' }}>
                {log.text}
              </span>
            </div>
          ))}
          {logs.length === 0 && (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
              No system log entries recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

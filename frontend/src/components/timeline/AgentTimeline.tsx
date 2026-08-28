import React from 'react';
import { useApp } from '../../context/AppContext';

export const AgentTimeline: React.FC = () => {
  const { timelineSteps } = useApp();

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">⏱️</span>
          <span>Agent Activity Pipeline</span>
        </span>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          8 Stages
        </span>
      </div>

      <div className="timeline-vertical">
        {timelineSteps.map((step) => {
          return (
            <div key={step.id} className={`timeline-item ${step.status}`}>
              <div className="timeline-node" />
              <div className="timeline-title-row">
                <span className="timeline-title">
                  {step.name}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {step.durationMs !== undefined && (
                    <span className="timeline-meta">
                      {step.durationMs} ms
                    </span>
                  )}
                  <span
                    className={`badge ${
                      step.status === 'SUCCESS'
                        ? 'badge-green'
                        : step.status === 'RUNNING'
                        ? 'badge-cyan'
                        : step.status === 'FAILED'
                        ? 'badge-red'
                        : 'badge-muted'
                    }`}
                    style={{ fontSize: '9px', padding: '1px 5px' }}
                  >
                    {step.status}
                  </span>
                </div>
              </div>
              <span className="timeline-desc">{step.description}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

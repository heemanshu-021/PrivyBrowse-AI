import React from 'react';
import { useApp } from '../context/AppContext';
import { BrowserPreview } from '../components/workspace/BrowserPreview';
import { ElementInspector } from '../components/workspace/ElementInspector';
import { AgentTimeline } from '../components/timeline/AgentTimeline';
import { StatusBadge } from '../components/common/StatusBadge';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';

export const WorkspacePage: React.FC = () => {
  const {
    taskText,
    setTaskText,
    runPipeline,
    plannedAction,
    executePlannedAction,
    isProcessing,
    currentScenario,
    selectScenario,
    scenarios
  } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Mission Assignment Bar */}
      <div className="card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ minWidth: '180px' }}>
            <label style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
              Target Environment
            </label>
            <select
              className="input-control select-control"
              value={currentScenario.id}
              onChange={(e) => selectScenario(e.target.value)}
              disabled={isProcessing}
              style={{ fontSize: '12px', padding: '7px 10px' }}
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.number} {sc.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1, minWidth: '280px' }}>
            <label style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
              Task Objective
            </label>
            <input
              type="text"
              className="input-control"
              value={taskText}
              onChange={(e) => setTaskText(e.target.value)}
              placeholder="E.g. Fill out the checkout billing form securely and confirm order..."
              disabled={isProcessing}
              style={{ fontSize: '13px' }}
            />
          </div>

          <div style={{ alignSelf: 'flex-end' }}>
            <button
              className="btn btn-cyan"
              onClick={runPipeline}
              disabled={isProcessing}
              style={{ height: '38px', padding: '0 20px' }}
            >
              <span>{isProcessing ? '⏳' : '⚡'}</span>
              <span>{isProcessing ? 'Running Pipeline...' : 'Run Local Pipeline'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Three-Panel Grid: Browser Preview (Left) vs Agent Reasoning & Inspector (Right) */}
      <div className="workspace-grid">
        {/* Left Column: Live Browser & Perception Scanner */}
        <div className="workspace-left-center">
          <BrowserPreview />
        </div>

        {/* Right Column: Planned Action & Deep Inspector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Planned Action Card */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                <span className="card-title-icon">⚡</span>
                <span>Planned Action</span>
              </span>
              {plannedAction && (
                <StatusBadge status={plannedAction.action} />
              )}
            </div>

            {plannedAction ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Target:</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {plannedAction.target_description}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Coordinates:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
                    ({plannedAction.target.x}, {plannedAction.target.y})
                  </span>
                </div>

                {plannedAction.text && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Payload:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-green)' }}>
                      "{plannedAction.text}"
                    </span>
                  </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Confidence:</span>
                  <ConfidenceBadge confidence={plannedAction.confidence} />
                </div>

                {plannedAction.requires_confirmation && (
                  <div
                    style={{
                      padding: '8px 10px',
                      backgroundColor: 'var(--accent-red-subtle)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '11px',
                      color: 'var(--accent-red)'
                    }}
                  >
                    ⚠️ High-impact action requires safety gatekeeper confirmation.
                  </div>
                )}

                <button
                  className="btn btn-primary"
                  onClick={executePlannedAction}
                  disabled={isProcessing}
                  style={{ marginTop: '4px', width: '100%' }}
                >
                  <span>▶</span>
                  <span>Execute Action Safely</span>
                </button>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px 12px' }}>
                <div style={{ fontSize: '20px', marginBottom: '4px' }}>⏳</div>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>No Action Planned</div>
                <div style={{ fontSize: '11px', marginTop: '2px' }}>
                  Run the pipeline to formulate the next browser automation step.
                </div>
              </div>
            )}
          </div>

          {/* Deep Element & PII Inspector Card */}
          <ElementInspector />
        </div>
      </div>

      {/* 3. Bottom Timeline Stepper */}
      <AgentTimeline />
    </div>
  );
};

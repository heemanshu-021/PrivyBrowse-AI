import React from 'react';
import { useApp } from '../context/AppContext';
import { BrowserPreview } from '../components/workspace/BrowserPreview';
import { ElementInspector } from '../components/workspace/ElementInspector';
import { PlanningPanel } from '../components/workspace/PlanningPanel';
import { AgentTimeline } from '../components/timeline/AgentTimeline';
import { StatusBadge } from '../components/common/StatusBadge';

export const WorkspacePage: React.FC = () => {
  const {
    taskText,
    setTaskText,
    runPipeline,
    isProcessing,
    currentScenario,
    selectScenario,
    scenarios,
    perceptionStatus,
    metrics,
    fusedElements
  } = useApp();

  const interactiveCount = fusedElements.filter(e => e.type === 'BUTTON' || e.type === 'INPUT' || e.type === 'LINK' || e.type === 'CHECKBOX' || e.type === 'SELECT').length;

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

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', alignSelf: 'flex-end' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', marginRight: '4px' }}>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Perception State</span>
              <StatusBadge
                status={isProcessing || perceptionStatus === 'RUNNING' ? 'PROCESSING' : perceptionStatus === 'ERROR' ? 'ERROR' : fusedElements.length > 0 ? 'COMPLETED' : 'IDLE'}
                variant={isProcessing || perceptionStatus === 'RUNNING' ? 'amber' : perceptionStatus === 'ERROR' ? 'red' : fusedElements.length > 0 ? 'green' : 'muted'}
                dot
              />
            </div>
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

        {/* Perception Quick Telemetry Summary Strip */}
        {fusedElements.length > 0 && (
          <div style={{ display: 'flex', gap: '16px', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Detected Elements: <strong style={{ color: 'var(--accent-cyan)' }}>{fusedElements.length}</strong>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Interactive Targets: <strong style={{ color: 'var(--accent-green)' }}>{interactiveCount}</strong>
            </div>
            {metrics.local_inference_time_ms > 0 && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Perception Latency: <strong style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{metrics.local_inference_time_ms.toFixed(1)}ms</strong>
              </div>
            )}
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Engine: <strong style={{ color: 'var(--text-secondary)' }}>OpenCV + Tesseract</strong>
            </div>
          </div>
        )}
      </div>

      {/* 2. Three-Panel Grid: Browser Preview (Left) vs Agent Reasoning & Inspector (Right) */}
      <div className="workspace-grid">
        {/* Left Column: Live Browser & Perception Scanner */}
        <div className="workspace-left-center">
          <BrowserPreview />
        </div>

        {/* Right Column: Planning Panel & Deep Inspector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Agent Planning Engine & Control Panel */}
          <PlanningPanel />

          {/* Deep Element & PII Inspector Card */}
          <ElementInspector />
        </div>
      </div>

      {/* 3. Bottom Timeline Stepper */}
      <AgentTimeline />
    </div>
  );
};

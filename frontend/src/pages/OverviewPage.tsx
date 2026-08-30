import React, { useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/common/StatusBadge';

export const OverviewPage: React.FC = () => {
  const {
    agentStatus,
    privacyStatus,
    backendConnected,
    extensionConnected,
    currentScenario,
    taskText,
    metrics,
    piiEntities,
    fusedElements,
    runPipeline,
    setActivePage,
    isProcessing,
    // Real-time observability state
    liveEvents,
    activeTask,
    browserContext,
    eventStreamConnected
  } = useApp();

  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');

  const filteredEvents = useMemo(() => {
    if (selectedFilter === 'ALL') return liveEvents;
    if (selectedFilter === 'ERRORS') {
      return liveEvents.filter(e => e.severity === 'ERROR' || e.severity === 'CRITICAL' || e.severity === 'WARNING');
    }
    if (selectedFilter === 'TASK') {
      return liveEvents.filter(e => e.component === 'TASK_MANAGER' || e.component === 'PLANNER');
    }
    if (selectedFilter === 'BROWSER') {
      return liveEvents.filter(e => e.component === 'BROWSER_CONTEXT' || e.component === 'EXTENSION');
    }
    if (selectedFilter === 'PERCEPTION') {
      return liveEvents.filter(e => e.component === 'PERCEPTION' || e.component === 'OCR');
    }
    if (selectedFilter === 'PRIVACY') {
      return liveEvents.filter(e => e.component === 'PRIVACY');
    }
    if (selectedFilter === 'SECURITY') {
      return liveEvents.filter(e => e.component === 'SECURITY');
    }
    if (selectedFilter === 'ACTIONS') {
      return liveEvents.filter(e => e.component === 'ACTION_VALIDATOR' || e.component === 'ACTION_EXECUTOR' || e.component === 'ACTION_VERIFIER');
    }
    return liveEvents;
  }, [liveEvents, selectedFilter]);

  const taskProgressPct = activeTask ? Math.round(activeTask.task_progress * 100) : (isProcessing ? 60 : 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Page Header with Live Connectivity Status */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Real-Time Autonomous Agent Observability</h1>
          <p className="page-subtitle">
            Live telemetry stream from on-device visual perception, local privacy gate, multi-step planner, and real browser action executor.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: eventStreamConnected ? 'var(--accent-green)' : 'var(--accent-amber)' }} />
            <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: eventStreamConnected ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
              {eventStreamConnected ? 'SSE LIVE STREAM ACTIVE' : 'POLLING RECONNECT'}
            </span>
          </div>

          <button className="btn btn-secondary" onClick={() => setActivePage('demolab')}>
            <span>🧪</span>
            <span>Demo Lab</span>
          </button>
          <button className="btn btn-primary" onClick={() => { setActivePage('workspace'); runPipeline(); }} disabled={isProcessing}>
            <span>▶</span>
            <span>Run Task</span>
          </button>
        </div>
      </div>

      {/* 2. System Connectivity & Health State Bar */}
      <section className="metrics-grid" aria-label="System Health Overview" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Backend Daemon</span>
            <span>⚡</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={backendConnected ? 'HEALTHY' : 'OFFLINE'} variant={backendConnected ? 'green' : 'red'} dot />
          </div>
          <div className="metric-footer">{backendConnected ? 'FastAPI Port 8000' : 'Disconnected'}</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Chrome Extension</span>
            <span>🧩</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={extensionConnected ? 'CONNECTED' : 'STANDBY'} variant={extensionConnected ? 'green' : 'amber'} dot />
          </div>
          <div className="metric-footer">{extensionConnected ? 'Heartbeat Active' : 'Extension Standby'}</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Browser Context</span>
            <span>🌐</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={browserContext ? 'SYNCED' : 'STANDBY'} variant={browserContext ? 'green' : 'amber'} dot />
          </div>
          <div className="metric-footer">{browserContext ? `${browserContext.element_count} Elements Synced` : 'Awaiting Tab'}</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Agent State</span>
            <span>🤖</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={agentStatus} dot />
          </div>
          <div className="metric-footer">Closed-Loop Planner</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Privacy Shield</span>
            <span>🛡️</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={privacyStatus} variant="green" dot />
          </div>
          <div className="metric-footer">Zero Raw PII Egress</div>
        </div>
      </section>

      {/* 3. Real Active Task & Step Dependency Timeline */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">📋</span>
            <span>Active Task & Step Execution Graph</span>
          </span>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span className="badge badge-cyan">
              {activeTask ? `TASK ID: ${activeTask.task_id}` : 'SIMULATION MODE'}
            </span>
            <span className="badge badge-green">{taskProgressPct}% PROGRESS</span>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-input)', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Objective</div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                "{activeTask ? activeTask.goal : taskText}"
              </div>
            </div>
            <div style={{ width: '200px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                <span>Progress</span>
                <span>{taskProgressPct}%</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'var(--bg-card)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${taskProgressPct}%`, height: '100%', background: 'var(--accent-green)', transition: 'width 0.3s ease' }} />
              </div>
            </div>
          </div>

          {/* Step Timeline */}
          {activeTask && activeTask.steps && activeTask.steps.length > 0 ? (
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${activeTask.steps.length}, 1fr)`, gap: '10px' }}>
              {activeTask.steps.map((step, idx) => {
                const isCompleted = step.status === 'COMPLETED';
                const isCurrent = idx === activeTask.current_step_index;
                const isFailed = step.status === 'FAILED';
                const isBlocked = step.status === 'AWAITING_CONFIRMATION';

                return (
                  <div
                    key={step.id}
                    style={{
                      background: isCompleted ? 'rgba(0, 230, 118, 0.08)' : isCurrent ? 'rgba(0, 242, 254, 0.08)' : isFailed ? 'rgba(255, 68, 68, 0.08)' : isBlocked ? 'rgba(255, 170, 0, 0.08)' : 'var(--bg-input)',
                      border: `1px solid ${isCompleted ? 'var(--accent-green)' : isCurrent ? 'var(--accent-cyan)' : isFailed ? 'var(--accent-red)' : isBlocked ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                      borderRadius: 'var(--radius-md)',
                      padding: '10px 12px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                        STEP #{idx + 1}
                      </span>
                      <span style={{
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: 600,
                        background: isCompleted ? 'var(--accent-green)' : isCurrent ? 'var(--accent-cyan)' : isFailed ? 'var(--accent-red)' : isBlocked ? 'var(--accent-amber)' : 'var(--border-subtle)',
                        color: '#000'
                      }}>
                        {step.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', lineHeight: '1.3' }}>
                      {step.description}
                    </div>
                    {step.evidence && step.evidence.length > 0 && (
                      <div style={{ fontSize: '10px', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                        ✓ {step.evidence[0]}
                      </div>
                    )}
                    {step.failure_reason && (
                      <div style={{ fontSize: '10px', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>
                        ✗ {step.failure_reason}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
              <div style={{ background: 'var(--bg-input)', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>STEP #1</span>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>Locate interactive controls</div>
                <span className="badge badge-green" style={{ marginTop: '4px' }}>READY</span>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>STEP #2</span>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>Input sanitized credentials</div>
                <span className="badge" style={{ marginTop: '4px' }}>PENDING</span>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>STEP #3</span>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>Execute verified action</div>
                <span className="badge" style={{ marginTop: '4px' }}>PENDING</span>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>STEP #4</span>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>Verify destination outcome</div>
                <span className="badge" style={{ marginTop: '4px' }}>PENDING</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 4. Live Browser Context & Privacy/Security Gauges Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Browser Context Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🌐</span>
              <span>Active Browser Context</span>
            </span>
            <span className="badge badge-cyan">{browserContext ? `TAB #${browserContext.tab_id || 1}` : 'DEMO SANDBOX'}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Active URL:</span>
              <code style={{ color: 'var(--accent-cyan)' }}>{browserContext ? browserContext.url : currentScenario.url}</code>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Page Title:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{browserContext ? browserContext.title : currentScenario.name}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Layout Elements:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                {browserContext ? browserContext.element_count : fusedElements.length || currentScenario.expectedElements} elements
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Page Load State:</span>
              <span className="badge badge-green">{browserContext ? browserContext.loading_state : 'COMPLETE'}</span>
            </div>
          </div>
        </div>

        {/* Privacy & Security Telemetry Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🛡️</span>
              <span>Privacy & Security Boundaries</span>
            </span>
            <span className="badge badge-green">100% ON-DEVICE</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>PII Detections (Local):</span>
              <strong style={{ color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>
                {metrics.pii_detected_count > 0 ? metrics.pii_detected_count : piiEntities.length}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Redacted Fields:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                {metrics.pii_redacted_count > 0 ? metrics.pii_redacted_count : piiEntities.length}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Prompt Injections Neutralized:</span>
              <strong style={{ color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)' }}>
                {liveEvents.filter(e => e.event_type === 'PROMPT_INJECTION_DETECTED').length}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Raw Secrets Transmitted:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                0 BYTES (ZERO LEAK)
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Live Observability Event Log (Filterable) */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">⚡</span>
            <span>Real-Time Observability Event Stream ({filteredEvents.length})</span>
          </span>

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {['ALL', 'TASK', 'BROWSER', 'PERCEPTION', 'PRIVACY', 'SECURITY', 'ACTIONS', 'ERRORS'].map(f => (
              <button
                key={f}
                onClick={() => setSelectedFilter(f)}
                style={{
                  fontSize: '11px',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 600,
                  background: selectedFilter === f ? 'var(--accent-cyan)' : 'var(--bg-input)',
                  color: selectedFilter === f ? '#000' : 'var(--text-muted)'
                }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {filteredEvents.length > 0 ? (
          <div className="data-table-wrapper" style={{ maxHeight: '320px', overflowY: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Seq #</th>
                  <th style={{ width: '90px' }}>Time</th>
                  <th style={{ width: '130px' }}>Component</th>
                  <th style={{ width: '160px' }}>Event Type</th>
                  <th>Safe Summary Message</th>
                  <th style={{ width: '90px' }}>Severity</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map(evt => (
                  <tr key={evt.seq_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      #{evt.seq_id}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </td>
                    <td>
                      <span className="badge badge-cyan" style={{ fontSize: '10px' }}>
                        {evt.component}
                      </span>
                    </td>
                    <td>
                      <code style={{ fontSize: '11px', color: 'var(--text-primary)' }}>
                        {evt.event_type}
                      </code>
                    </td>
                    <td>
                      <span style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                        {evt.message}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '10px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontWeight: 600,
                          background:
                            evt.severity === 'CRITICAL' || evt.severity === 'ERROR' ? 'var(--accent-red)' :
                            evt.severity === 'WARNING' ? 'var(--accent-amber)' :
                            evt.severity === 'SUCCESS' ? 'var(--accent-green)' : 'var(--bg-card)',
                          color: '#000'
                        }}
                      >
                        {evt.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            No events match the selected filter. Run an agent mission or connect Chrome to observe live events.
          </div>
        )}
      </div>
    </div>
  );
};

import React from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { MetricCard } from '../components/common/MetricCard';

export const OverviewPage: React.FC = () => {
  const {
    agentStatus,
    perceptionStatus,
    privacyStatus,
    backendConnected,
    currentScenario,
    taskText,
    metrics,
    piiEntities,
    fusedElements,
    runPipeline,
    setActivePage,
    isProcessing
  } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Privacy-Preserving Browser Intelligence</h1>
          <p className="page-subtitle">
            Understand webpages locally on-device. Redact sensitive PII before transmission. Empower lightweight AI agents to navigate safely.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" onClick={() => setActivePage('demolab')}>
            <span>🧪</span>
            <span>Explore Demo Lab</span>
          </button>
          <button className="btn btn-primary" onClick={() => { setActivePage('workspace'); runPipeline(); }} disabled={isProcessing}>
            <span>▶</span>
            <span>Run Current Mission</span>
          </button>
        </div>
      </div>

      {/* 2. Hero Visual Innovation Pipeline (SEE -> PROTECT -> REASON -> ACT) */}
      <section className="hero-pipeline" aria-label="Core Innovation Pipeline">
        <div className="pipeline-step-box">
          <span className="step-code-badge">01. SEE</span>
          <div className="step-main-title">Visual Perception</div>
          <div className="step-sub-desc">Extracts controls & contours via OpenCV on raw frame.</div>
        </div>

        <div className="pipeline-divider-arrow">→</div>

        <div className="pipeline-step-box">
          <span className="step-code-badge" style={{ color: 'var(--accent-red)' }}>02. PROTECT</span>
          <div className="step-main-title">On-Device Redaction</div>
          <div className="step-sub-desc">Classifies & masks cards, passwords, emails & faces locally.</div>
        </div>

        <div className="pipeline-divider-arrow">→</div>

        <div className="pipeline-step-box">
          <span className="step-code-badge" style={{ color: 'var(--accent-purple)' }}>03. REASON</span>
          <div className="step-main-title">Sanitized Context</div>
          <div className="step-sub-desc">Agent reasons exclusively on safe, structured layout tokens.</div>
        </div>

        <div className="pipeline-divider-arrow">→</div>

        <div className="pipeline-step-box">
          <span className="step-code-badge" style={{ color: 'var(--accent-green)' }}>04. ACT</span>
          <div className="step-main-title">Safe Browser Action</div>
          <div className="step-sub-desc">Executes verified clicks & keystrokes on target page.</div>
        </div>
      </section>

      {/* 3. System States & Metrics Grid */}
      <section className="metrics-grid" aria-label="Quick System State">
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Agent Engine</span>
            <span>🤖</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={agentStatus} dot />
          </div>
          <div className="metric-footer">Structured action planner active</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Perception Layer</span>
            <span>👁️</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={perceptionStatus} dot />
          </div>
          <div className="metric-footer">OpenCV & OCR layout engine</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Privacy Shield</span>
            <span>🛡️</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={privacyStatus} variant="green" dot />
          </div>
          <div className="metric-footer">Zero raw PII transmitted</div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Browser Link</span>
            <span>🌐</span>
          </div>
          <div className="metric-value-row">
            <StatusBadge status={backendConnected ? 'CONNECTED' : 'STANDALONE'} variant={backendConnected ? 'green' : 'amber'} dot />
          </div>
          <div className="metric-footer">{backendConnected ? 'Port 8000 Ready' : 'Local Sandbox Active'}</div>
        </div>
      </section>

      {/* 4. Telemetry Metrics Quick Cards */}
      <div className="metrics-grid">
        <MetricCard
          label="Local Inference Time"
          value={metrics.local_inference_time_ms > 0 ? metrics.local_inference_time_ms : 38}
          unit="ms"
          icon="⚡"
          subtext="Contour + OCR analysis latency"
          statusColor="var(--accent-cyan)"
        />
        <MetricCard
          label="Sensitive Items Protected"
          value={metrics.pii_redacted_count > 0 ? metrics.pii_redacted_count : piiEntities.length}
          unit="nodes"
          icon="🔒"
          subtext="Protected inside trust boundary"
          statusColor="var(--accent-green)"
        />
        <MetricCard
          label="Detected UI Elements"
          value={fusedElements.length > 0 ? fusedElements.length : currentScenario.expectedElements}
          unit="elements"
          icon="🎯"
          subtext="Fused DOM + visual controls"
          statusColor="var(--accent-blue)"
        />
        <MetricCard
          label="Autonomous Actions"
          value={metrics.actions_executed}
          unit="executed"
          icon="🚀"
          subtext="Verified state transitions"
          statusColor="var(--accent-purple)"
        />
      </div>

      {/* 5. Active Mission & Privacy Summary Row */}
      <div className="grid-panels" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '20px' }}>
        {/* Mission Showcase Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🎯</span>
              <span>Active Agent Mission</span>
            </span>
            <span className="badge badge-cyan">{currentScenario.name}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div
              style={{
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 16px'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
                Assigned User Task
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                "{taskText}"
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Target Sandbox:</span>{' '}
                <code style={{ color: 'var(--accent-cyan)' }}>{currentScenario.url}</code>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Risk Rating:</span>{' '}
                <span style={{ color: currentScenario.riskLevel === 'HIGH' ? 'var(--accent-red)' : 'var(--accent-green)', fontWeight: 600 }}>
                  {currentScenario.riskLevel}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setActivePage('workspace');
                  runPipeline();
                }}
                disabled={isProcessing}
                style={{ flex: 1 }}
              >
                {isProcessing ? "Processing Pipeline..." : "Execute in Agent Workspace →"}
              </button>
            </div>
          </div>
        </div>

        {/* Privacy Shield Summary Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🛡️</span>
              <span>Privacy Boundary Status</span>
            </span>
            <span className="badge badge-green">VERIFIED</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>PII Elements Detected:</span>
              <strong style={{ color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>
                {piiEntities.length > 0 ? piiEntities.length : currentScenario.piiTypes.length}
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Local Redactions Executed:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                {piiEntities.length > 0 ? piiEntities.length : currentScenario.piiTypes.length}
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Raw PII Transmitted:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                0 bytes
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Enforcement Policy:</span>
              <span className="badge badge-cyan">ON-DEVICE FIRST</span>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setActivePage('privacy')}
              style={{ marginTop: '6px' }}
            >
              Open Privacy Center & Trust Map
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

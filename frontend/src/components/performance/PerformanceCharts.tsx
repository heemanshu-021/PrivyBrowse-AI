import React from 'react';
import { useApp } from '../../context/AppContext';

export const PerformanceCharts: React.FC = () => {
  const { metrics } = useApp();

  const stages = [
    { name: 'Visual Contours (CV)', ms: metrics.local_inference_time_ms, color: 'var(--accent-blue)' },
    { name: 'OCR Layout Parsing', ms: metrics.ocr_latency_ms, color: 'var(--accent-purple)' },
    { name: 'PII Detection', ms: metrics.pii_detection_latency_ms, color: 'var(--accent-amber)' },
    { name: 'Local Redaction', ms: metrics.redaction_latency_ms, color: 'var(--accent-green)' },
    { name: 'Agent Reasoning', ms: metrics.agent_planning_latency_ms, color: 'var(--accent-cyan)' }
  ];

  const maxMs = Math.max(...stages.map(s => s.ms), 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Latency Breakdown Bars */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">⚡</span>
            <span>Pipeline Stage Latency Breakdown</span>
          </span>
          <span className="badge badge-cyan">
            TOTAL: {metrics.total_task_latency_ms} MS
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {stages.map((stage) => {
            const pct = Math.max(4, Math.round((stage.ms / maxMs) * 100));
            return (
              <div key={stage.name} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{stage.name}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: stage.color }}>
                    {stage.ms > 0 ? `${stage.ms} ms` : 'Waiting'}
                  </span>
                </div>
                <div
                  style={{
                    height: '8px',
                    backgroundColor: 'var(--bg-input)',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)'
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${stage.ms > 0 ? pct : 0}%`,
                      backgroundColor: stage.color,
                      borderRadius: '4px',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. System Footprint & Counters */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">💻</span>
              <span>Memory & CPU Footprint</span>
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>RAM Footprint:</span>
              <strong style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {metrics.memory_usage_mb} MB
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Avg CPU Utilization:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                {metrics.cpu_utilization_pct}%
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Inference Mode:</span>
              <span className="badge badge-green">LOCAL PROCESS</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🎯</span>
              <span>Action Throughput</span>
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Pipeline Runs:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>{metrics.runs_count}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Actions Executed:</span>
              <strong style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {metrics.actions_executed}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>PII Redactions Count:</span>
              <strong style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                {metrics.pii_redacted_count}
              </strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { useApp } from '../context/AppContext';
import { DemoCard } from '../components/demo/DemoCard';

export const DemoLabPage: React.FC = () => {
  const { scenarios, currentScenario, backendConnected } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Demo Lab — Controlled Evaluation Sandbox</h1>
          <p className="page-subtitle">
            Controlled test environments containing synthetic credit cards, passwords, phone numbers, addresses, and human portraits to demonstrate on-device redaction and agent autonomy.
          </p>
        </div>
      </div>

      {/* 2. Pipeline Sequence Diagram */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          overflowX: 'auto',
          padding: '12px 16px',
          backgroundColor: 'var(--bg-card-subtle)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)'
        }}
      >
        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>EVALUATION PIPELINE:</span>
        <span className="badge badge-muted">TASK</span> →
        <span className="badge badge-muted">OBSERVE</span> →
        <span className="badge badge-blue">PERCEIVE</span> →
        <span className="badge badge-amber">DETECT PII</span> →
        <span className="badge badge-green">LOCAL REDACT</span> →
        <span className="badge badge-purple">PLAN ACTION</span> →
        <span className="badge badge-green">EXECUTE</span> →
        <span className="badge badge-cyan">VERIFY</span>
      </div>

      {/* 3. Five Scenario Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {scenarios.map((sc) => (
          <DemoCard key={sc.id} scenario={sc} />
        ))}
      </div>

      {/* 4. Sandbox Webpage Live Iframe Preview */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">🌐</span>
            <span>Target Sandbox Live Render ({currentScenario.name})</span>
          </span>
          <span className="badge badge-cyan">{currentScenario.url}</span>
        </div>

        <div
          style={{
            height: '380px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            border: '1px solid var(--border-medium)'
          }}
        >
          {backendConnected ? (
            <iframe
              src={`http://127.0.0.1:8000${currentScenario.url}`}
              title="Demo Sandbox Frame"
              style={{ width: '100%', height: '100%', border: 'none' }}
            />
          ) : (
            <div
              style={{
                height: '100%',
                backgroundColor: '#0f172a',
                color: 'var(--text-secondary)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '20px',
                textAlign: 'center'
              }}
            >
              <div style={{ fontSize: '28px' }}>🧪</div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Synthetic Page Ready
              </div>
              <div style={{ fontSize: '11px', maxWidth: '380px' }}>
                Local FastAPI server serves raw HTML from <code style={{ color: 'var(--accent-cyan)' }}>demo-pages/{currentScenario.id}.html</code>.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

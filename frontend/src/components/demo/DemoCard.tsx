import React from 'react';
import type { DemoScenario } from '../../types';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';

interface DemoCardProps {
  scenario: DemoScenario;
}

export const DemoCard: React.FC<DemoCardProps> = ({ scenario }) => {
  const { currentScenario, selectScenario, runPipeline, setActivePage, isProcessing } = useApp();

  const isCurrent = currentScenario.id === scenario.id;

  const handleLaunch = async () => {
    selectScenario(scenario.id);
    setActivePage('workspace');
    await runPipeline();
  };

  return (
    <div
      className="card"
      style={{
        border: isCurrent ? '1.5px solid var(--accent-cyan)' : undefined,
        boxShadow: isCurrent ? 'var(--shadow-cyan-glow)' : undefined,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '16px'
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '13px',
              fontWeight: 800,
              color: 'var(--accent-cyan)',
              backgroundColor: 'var(--bg-input)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)'
            }}
          >
            {scenario.number}
          </span>
          <StatusBadge status={scenario.riskLevel} />
        </div>

        <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
          {scenario.name}
        </h3>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
          {scenario.subtitle}
        </div>

        <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4', marginBottom: '12px' }}>
          {scenario.description}
        </p>

        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          <strong>Expected Behavior:</strong> {scenario.expectedBehavior}
        </div>

        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {scenario.piiTypes.length > 0 ? (
            scenario.piiTypes.map((type: string) => (
              <span key={type} className="badge badge-red" style={{ fontSize: '9px' }}>
                🔒 {type}
              </span>
            ))
          ) : (
            <span className="badge badge-muted" style={{ fontSize: '9px' }}>
              NO PII INVOLVED
            </span>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => {
            selectScenario(scenario.id);
            setActivePage('workspace');
          }}
          style={{ flex: 1 }}
        >
          Load Sandbox
        </button>
        <button
          className="btn btn-primary btn-sm"
          onClick={handleLaunch}
          disabled={isProcessing}
          style={{ flex: 1.2 }}
        >
          <span>▶</span>
          <span>Run Demo</span>
        </button>
      </div>
    </div>
  );
};

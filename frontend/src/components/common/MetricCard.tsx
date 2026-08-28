import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: string;
  subtext?: string;
  statusColor?: string;
  empty?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit = '',
  icon = '⚡',
  subtext,
  statusColor,
  empty = false
}) => {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        <span className="metric-icon">{icon}</span>
      </div>

      <div className="metric-value-row">
        {empty ? (
          <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 500 }}>
            Waiting for data
          </span>
        ) : (
          <>
            <span className="metric-value" style={{ color: statusColor || 'var(--text-primary)' }}>
              {value}
            </span>
            {unit && <span className="metric-unit">{unit}</span>}
          </>
        )}
      </div>

      {subtext && <div className="metric-footer">{subtext}</div>}
    </div>
  );
};

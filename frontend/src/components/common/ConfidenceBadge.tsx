import React from 'react';

interface ConfidenceBadgeProps {
  confidence: number; // 0.0 to 1.0 or 0 to 100
  showPercent?: boolean;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence, showPercent = true }) => {
  const norm = confidence > 1 ? confidence : Math.round(confidence * 100);
  
  let colorVar = 'var(--accent-green)';
  let bgVar = 'var(--accent-green-subtle)';
  if (norm < 70) {
    colorVar = 'var(--accent-red)';
    bgVar = 'var(--accent-red-subtle)';
  } else if (norm < 88) {
    colorVar = 'var(--accent-amber)';
    bgVar = 'var(--accent-amber-subtle)';
  }

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: bgVar,
        color: colorVar,
        padding: '2px 7px',
        borderRadius: 'var(--radius-sm)',
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        fontWeight: 600,
        border: `1px solid ${colorVar}40`
      }}
    >
      <div
        style={{
          width: '28px',
          height: '4px',
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '2px',
          overflow: 'hidden'
        }}
      >
        <div
          style={{
            width: `${norm}%`,
            height: '100%',
            backgroundColor: colorVar
          }}
        />
      </div>
      {showPercent && <span>{norm}%</span>}
    </div>
  );
};

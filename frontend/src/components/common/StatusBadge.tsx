import React from 'react';

interface StatusBadgeProps {
  status: string;
  variant?: 'cyan' | 'green' | 'blue' | 'amber' | 'red' | 'purple' | 'muted';
  dot?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'cyan',
  dot = false,
  className = ''
}) => {
  let badgeVariant = variant;
  const s = status.toUpperCase();

  if (s === 'PROTECTED' || s === 'SUCCESS' || s === 'ONLINE' || s === 'SAFE' || s === 'ON-DEVICE' || s === 'VERIFIED') {
    badgeVariant = 'green';
  } else if (s === 'RUNNING' || s === 'PERCEIVING' || s === 'PLANNING' || s === 'ACTING' || s === 'FUSED') {
    badgeVariant = 'cyan';
  } else if (s === 'WARNING' || s === 'PAUSED' || s === 'STANDBY' || s === 'HIGH_RISK') {
    badgeVariant = 'amber';
  } else if (s === 'ERROR' || s === 'FAILED' || s === 'OFFLINE' || s === 'DISCONNECTED' || s === 'HIGH') {
    badgeVariant = 'red';
  } else if (s === 'DOM' || s === 'LINK' || s === 'OCR') {
    badgeVariant = 'purple';
  } else if (s === 'VISION' || s === 'BUTTON') {
    badgeVariant = 'blue';
  }

  return (
    <span className={`badge badge-${badgeVariant} ${className}`}>
      {dot && (
        <span
          className={`status-dot ${
            badgeVariant === 'green' ? 'online' : badgeVariant === 'red' ? 'offline' : badgeVariant === 'amber' ? 'warning' : 'standby'
          }`}
        />
      )}
      {status}
    </span>
  );
};

import React from 'react';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '🔍',
  title,
  description,
  actionLabel,
  onAction
}) => {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <div className="empty-title">{title}</div>
      <div className="empty-desc">{description}</div>
      {actionLabel && onAction && (
        <button className="btn btn-secondary btn-sm" onClick={onAction} style={{ marginTop: '8px' }}>
          {actionLabel}
        </button>
      )}
    </div>
  );
};

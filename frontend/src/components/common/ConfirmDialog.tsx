import React from 'react';
import { useApp } from '../../context/AppContext';

export const ConfirmDialog: React.FC = () => {
  const { confirmDialog, dismissConfirmDialog, approveConfirmAction } = useApp();

  if (!confirmDialog.open) return null;

  return (
    <div className="dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <div className="dialog-box">
        <div className="dialog-header" id="dialog-title">
          <span>⚠️</span>
          <span>SAFETY GATEKEEPER INTERCEPTION</span>
        </div>

        <div className="dialog-body">
          <p>{confirmDialog.message}</p>
          {confirmDialog.action && (
            <div
              style={{
                marginTop: '12px',
                padding: '10px 12px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                border: '1px solid var(--border-subtle)'
              }}
            >
              <div><strong>Action Verb:</strong> {confirmDialog.action.action}</div>
              <div><strong>Target:</strong> {confirmDialog.action.target_description}</div>
              <div><strong>Coordinates:</strong> ({confirmDialog.action.target.x}, {confirmDialog.action.target.y})</div>
              {confirmDialog.action.text && <div><strong>Payload:</strong> "{confirmDialog.action.text}"</div>}
            </div>
          )}
        </div>

        <div className="dialog-footer">
          <button className="btn btn-secondary" onClick={dismissConfirmDialog}>
            Reject / Abort
          </button>
          <button className="btn btn-danger" onClick={approveConfirmAction}>
            Authorize & Execute
          </button>
        </div>
      </div>
    </div>
  );
};

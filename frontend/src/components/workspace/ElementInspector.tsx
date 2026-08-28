import React from 'react';
import { useApp } from '../../context/AppContext';
import { ConfidenceBadge } from '../common/ConfidenceBadge';
import { StatusBadge } from '../common/StatusBadge';

export const ElementInspector: React.FC = () => {
  const {
    fusedElements,
    piiEntities,
    selectedElementId,
    selectedPiiId,
    setSelectedElementId,
    setSelectedPiiId
  } = useApp();

  const selectedElement = fusedElements.find(e => e.id === selectedElementId);
  const selectedPii = piiEntities.find((p, idx) => (p.id || `pii_${idx}`) === selectedPiiId);

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">🔍</span>
          <span>Element & PII Inspector</span>
        </span>
        {(selectedElement || selectedPii) && (
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              setSelectedElementId(null);
              setSelectedPiiId(null);
            }}
          >
            Clear Selection
          </button>
        )}
      </div>

      {selectedPii ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Type:</span>
            <StatusBadge status={selectedPii.type} variant="red" />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Confidence:</span>
            <ConfidenceBadge confidence={selectedPii.confidence} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Detection Source:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-primary)' }}>
              {selectedPii.source}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Bounding Box:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
              [{selectedPii.bbox.join(', ')}]
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Dimensions:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
              {selectedPii.bbox[2] - selectedPii.bbox[0]}px × {selectedPii.bbox[3] - selectedPii.bbox[1]}px
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Status:</span>
            <span className="badge badge-green">PROTECTED ON-DEVICE</span>
          </div>

          <div
            style={{
              padding: '10px',
              backgroundColor: 'var(--bg-input)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              fontSize: '11px',
              color: 'var(--text-secondary)'
            }}
          >
            <div style={{ color: 'var(--accent-red)', fontWeight: 600, marginBottom: '2px' }}>
              🔒 Trust Boundary Enforcement
            </div>
            <div>Raw value protected on-device. The sanitized replacement label is provided to the agent planner.</div>
          </div>
        </div>
      ) : selectedElement ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Element ID:</span>
            <code style={{ color: 'var(--accent-cyan)', fontSize: '12px' }}>{selectedElement.id}</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Control Type:</span>
            <StatusBadge status={selectedElement.type} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Confidence:</span>
            <ConfidenceBadge confidence={selectedElement.confidence} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Perception Source:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-primary)' }}>
              {selectedElement.source}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Bounding Box:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
              [{selectedElement.bbox.join(', ')}]
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Dimensions:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
              {selectedElement.bbox[2] - selectedElement.bbox[0]}px × {selectedElement.bbox[3] - selectedElement.bbox[1]}px
            </span>
          </div>

          {selectedElement.text && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Sanitized Label / Content:</span>
              <div
                style={{
                  padding: '8px 10px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-primary)'
                }}
              >
                {selectedElement.text}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px 12px' }}>
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>🎯</div>
          <div style={{ fontSize: '12px', fontWeight: 600 }}>No Element Selected</div>
          <div style={{ fontSize: '11px', marginTop: '2px' }}>
            Click on any contour box in the preview to inspect coordinates and visual confidence.
          </div>
        </div>
      )}
    </div>
  );
};

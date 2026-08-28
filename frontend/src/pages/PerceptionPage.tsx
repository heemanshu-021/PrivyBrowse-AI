import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';
import { EmptyState } from '../components/common/EmptyState';
import { BrowserPreview } from '../components/workspace/BrowserPreview';
import { ElementInspector } from '../components/workspace/ElementInspector';

export const PerceptionPage: React.FC = () => {
  const { fusedElements, selectedElementId, setSelectedElementId, setSelectedPiiId, runPipeline, isProcessing } = useApp();
  const [filterType, setFilterType] = useState<string>('ALL');

  const filters = ['ALL', 'BUTTON', 'INPUT', 'LINK', 'IMAGE', 'FUSED'];

  const filteredElements = fusedElements.filter((el) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'FUSED') return el.source === 'FUSED';
    return el.type === filterType;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Visual Perception Inspector</h1>
          <p className="page-subtitle">
            Debug and inspect OpenCV visual contours, OCR layout blocks, and DOM elements fused via bounding box IoU alignment.
          </p>
        </div>

        <button className="btn btn-cyan" onClick={runPipeline} disabled={isProcessing}>
          <span>{isProcessing ? '⏳' : '⚡'}</span>
          <span>{isProcessing ? 'Processing...' : 'Run Perception Scan'}</span>
        </button>
      </div>

      {/* 2. Top Preview & Inspector Row */}
      <div className="workspace-grid">
        <BrowserPreview />
        <ElementInspector />
      </div>

      {/* 3. Coordinate Map & Elements Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">🗺️</span>
            <span>Fused Interactive Elements Matrix ({filteredElements.length})</span>
          </span>

          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {filters.map((f) => (
              <button
                key={f}
                className={`btn btn-secondary btn-sm ${filterType === f ? 'btn-cyan' : ''}`}
                onClick={() => setFilterType(f)}
                style={{ fontSize: '10px', padding: '3px 8px' }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {filteredElements.length > 0 ? (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Element ID</th>
                  <th>Control Type</th>
                  <th>Sanitized Label / Value</th>
                  <th>Bounding Box [x1, y1, x2, y2]</th>
                  <th>Dimensions</th>
                  <th>Confidence</th>
                  <th>Inference Source</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredElements.map((el) => {
                  const isSelected = selectedElementId === el.id;
                  const [x1, y1, x2, y2] = el.bbox;
                  return (
                    <tr
                      key={el.id}
                      style={{
                        backgroundColor: isSelected ? 'rgba(0, 242, 254, 0.08)' : undefined
                      }}
                    >
                      <td>
                        <code style={{ color: 'var(--accent-cyan)' }}>{el.id}</code>
                      </td>
                      <td>
                        <StatusBadge status={el.type} />
                      </td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
                          {el.text || el.value || el.attributes.placeholder || <em style={{ color: 'var(--text-muted)' }}>None</em>}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
                          [{x1}, {y1}, {x2}, {y2}]
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {x2 - x1} × {y2 - y1} px
                        </span>
                      </td>
                      <td>
                        <ConfidenceBadge confidence={el.confidence} />
                      </td>
                      <td>
                        <span className="badge badge-muted" style={{ fontSize: '10px' }}>
                          {el.source}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => {
                            setSelectedElementId(el.id);
                            setSelectedPiiId(null);
                          }}
                          style={{ fontSize: '10px', padding: '2px 8px' }}
                        >
                          {isSelected ? 'Selected' : 'Inspect'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon="👁️"
            title="No Elements Detected"
            description="Run the visual perception engine on an active webpage to populate the coordinate matrix."
            actionLabel="Run Perception Scan"
            onAction={runPipeline}
          />
        )}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';
import { EmptyState } from '../components/common/EmptyState';
import { BrowserPreview } from '../components/workspace/BrowserPreview';
import { ElementInspector } from '../components/workspace/ElementInspector';

export const PerceptionPage: React.FC = () => {
  const { fusedElements, selectedElementId, setSelectedElementId, setSelectedPiiId, runPipeline, isProcessing, perceptionStatus, metrics, backendConnected } = useApp();
  const [filterType, setFilterType] = useState<string>('ALL');

  const filters = ['ALL', 'BUTTON', 'INPUT', 'LINK', 'IMAGE', 'HEADING', 'TEXT', 'FUSED'];

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
            On-device visual perception pipeline: OpenCV contour detection, Tesseract OCR, DOM accessibility fusion, and multi-source confidence scoring.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <StatusBadge
            status={perceptionStatus === 'RUNNING' ? 'PROCESSING' : perceptionStatus === 'ERROR' ? 'ERROR' : 'READY'}
            variant={perceptionStatus === 'RUNNING' ? 'amber' : perceptionStatus === 'ERROR' ? 'red' : 'green'}
            dot
          />
          <button className="btn btn-cyan" onClick={runPipeline} disabled={isProcessing}>
            <span>{isProcessing ? '⏳' : '⚡'}</span>
            <span>{isProcessing ? 'Processing...' : 'Run Perception Scan'}</span>
          </button>
        </div>
      </div>

      {/* 2. Latency Breakdown */}
      {backendConnected && metrics.local_inference_time_ms > 0 && (
        <div className="card" style={{ padding: '14px 18px' }}>
          <div className="card-header" style={{ marginBottom: '8px' }}>
            <span className="card-title">
              <span className="card-title-icon">⏱️</span>
              <span>Perception Latency Breakdown</span>
            </span>
            <StatusBadge status="LOCAL / UNSANITIZED" variant="amber" />
          </div>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {[
              { label: 'CV Detection', value: metrics.local_inference_time_ms, color: 'var(--accent-cyan)' },
              { label: 'OCR', value: metrics.ocr_latency_ms, color: 'var(--accent-green)' },
              { label: 'Total Pipeline', value: metrics.total_task_latency_ms, color: 'var(--accent-cyan)' },
            ].map((m) => (
              <div key={m.label} style={{ textAlign: 'center', minWidth: '80px' }}>
                <div style={{ fontSize: '18px', fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>
                  {m.value.toFixed(1)}
                </div>
                <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{m.label} (ms)</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Top Preview & Inspector Row */}
      <div className="workspace-grid">
        <BrowserPreview />
        <ElementInspector />
      </div>

      {/* 4. Coordinate Map & Elements Table */}
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

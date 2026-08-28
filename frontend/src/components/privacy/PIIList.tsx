import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { ConfidenceBadge } from '../common/ConfidenceBadge';
import { EmptyState } from '../common/EmptyState';

export const PIIList: React.FC = () => {
  const { piiEntities, setSelectedPiiId, setSelectedElementId } = useApp();
  const [filterType, setFilterType] = useState<string>('ALL');

  const categories = ['ALL', 'EMAIL', 'PASSWORD', 'CARD', 'NAME', 'ADDRESS', 'ID_NUM', 'FACE'];

  const filteredEntities = piiEntities.filter((item) => {
    if (filterType === 'ALL') return true;
    return item.type.toUpperCase() === filterType;
  });

  const maskValue = (text: string, type: string) => {
    if (type === 'PASSWORD') return '••••••••';
    if (type === 'CARD') return '•••• •••• •••• ' + text.slice(-4);
    if (type === 'EMAIL') {
      const parts = text.split('@');
      if (parts.length === 2) return `${parts[0].slice(0, 2)}***@${parts[1]}`;
    }
    if (type === 'FACE') return '[FACE DETECTED]';
    return text.length > 4 ? `${text.slice(0, 2)}***${text.slice(-2)}` : '***';
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">📋</span>
          <span>Protected Sensitive Records</span>
        </span>
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`btn btn-secondary btn-sm ${filterType === cat ? 'btn-cyan' : ''}`}
              onClick={() => setFilterType(cat)}
              style={{ fontSize: '10px', padding: '3px 8px' }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {filteredEntities.length > 0 ? (
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Masked Value</th>
                <th>Confidence</th>
                <th>Source</th>
                <th>Coordinates</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntities.map((pii, idx) => (
                <tr key={pii.id || idx}>
                  <td>
                    <StatusBadge status={pii.type} variant="red" />
                  </td>
                  <td>
                    <code style={{ color: 'var(--text-secondary)' }}>
                      {maskValue(pii.text, pii.type)}
                    </code>
                  </td>
                  <td>
                    <ConfidenceBadge confidence={pii.confidence} />
                  </td>
                  <td>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {pii.source}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '11px', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                      [{pii.bbox.join(', ')}]
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        setSelectedPiiId(pii.id || `pii_${idx}`);
                        setSelectedElementId(null);
                      }}
                      style={{ fontSize: '10px', padding: '2px 8px' }}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          icon="🛡️"
          title="No Sensitive Elements in Current View"
          description={
            filterType === 'ALL'
              ? 'Run observation on a page with credentials, payment forms, or profiles to see protected PII records.'
              : `No PII detected matching filter "${filterType}".`
          }
        />
      )}
    </div>
  );
};

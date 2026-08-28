import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { ConfidenceBadge } from '../common/ConfidenceBadge';
import { EmptyState } from '../common/EmptyState';

export const PIIList: React.FC = () => {
  const { piiEntities, setSelectedPiiId, setSelectedElementId } = useApp();
  const [filterType, setFilterType] = useState<string>('ALL');

  const categories = ['ALL', 'PAN', 'AADHAAR', 'CARD', 'PASSWORD', 'OTP', 'SECRET_TOKEN', 'EMAIL', 'PHONE', 'NAME', 'FACE'];

  const filteredEntities = piiEntities.filter((item) => {
    if (filterType === 'ALL') return true;
    return item.type.toUpperCase() === filterType;
  });

  const maskValue = (text: string, type: string) => {
    if (type === 'PASSWORD') return '••••••••';
    if (type === 'CARD') {
      const clean = text.replace(/\D/g, '');
      return '•••• •••• •••• ' + (clean.slice(-4) || '****');
    }
    if (type === 'PAN') {
      if (text.length === 10) return `${text.slice(0, 2)}***${text.slice(-2)}`;
      return 'PAN_CARD_NUMBER';
    }
    if (type === 'AADHAAR') {
      const clean = text.replace(/\D/g, '');
      return 'XXXX XXXX ' + (clean.slice(-4) || '****');
    }
    if (type === 'OTP') return '••••••';
    if (type === 'SECRET_TOKEN') return `${text.slice(0, 4)}...[REDACTED_SECRET]`;
    if (type === 'EMAIL') {
      const parts = text.split('@');
      if (parts.length === 2) return `${parts[0].slice(0, 2)}***@${parts[1]}`;
    }
    if (type === 'PHONE') {
      const clean = text.replace(/\D/g, '');
      return `+**-***-***-${clean.slice(-4) || '****'}`;
    }
    if (type === 'FACE') return '[FACE DETECTED]';
    return text.length > 4 ? `${text.slice(0, 2)}***${text.slice(-2)}` : '***';
  };

  const renderSources = (src: string | string[]) => {
    if (Array.isArray(src)) {
      return src.join(', ');
    }
    return src;
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">📋</span>
          <span>Protected Sensitive Records ({filteredEntities.length})</span>
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
                <th>Classification</th>
                <th>Masked Value</th>
                <th>Confidence</th>
                <th>Source Signals</th>
                <th>Coordinates</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntities.map((pii, idx) => {
                const isHighlySensitive = pii.classification === 'HIGHLY_SENSITIVE' || ['PASSWORD', 'CARD', 'PAN', 'AADHAAR', 'OTP', 'SECRET_TOKEN'].includes(pii.type);
                return (
                  <tr key={pii.id || idx}>
                    <td>
                      <StatusBadge status={pii.type} variant={isHighlySensitive ? 'red' : 'amber'} />
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '9px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: isHighlySensitive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          color: isHighlySensitive ? 'var(--accent-red)' : 'var(--accent-amber)',
                          border: `1px solid ${isHighlySensitive ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                        }}
                      >
                        {isHighlySensitive ? 'HIGHLY SENSITIVE' : 'SENSITIVE'}
                      </span>
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
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {renderSources(pii.source)}
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
                );
              })}
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

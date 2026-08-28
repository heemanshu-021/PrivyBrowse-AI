import React from 'react';
import { useApp } from '../../context/AppContext';

export const PerceptionOverlay: React.FC = () => {
  const {
    viewMode,
    fusedElements,
    piiEntities,
    selectedElementId,
    setSelectedElementId,
    selectedPiiId,
    setSelectedPiiId
  } = useApp();

  const showVision = viewMode === 'perception' || viewMode === 'overlay';
  const showPii = viewMode === 'sanitized' || viewMode === 'overlay';

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 10 }}>
      {/* 1. Vision & Fused Element Bounding Boxes */}
      {showVision &&
        fusedElements.map((el) => {
          const isSelected = selectedElementId === el.id;
          const [x1, y1, x2, y2] = el.bbox;
          const w = x2 - x1;
          const h = y2 - y1;

          if (w <= 0 || h <= 0) return null;

          return (
            <div
              key={el.id}
              className={`bbox-box ${el.type} ${isSelected ? 'selected' : ''}`}
              style={{
                left: `${x1}px`,
                top: `${y1}px`,
                width: `${w}px`,
                height: `${h}px`
              }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedElementId(el.id);
                setSelectedPiiId(null);
              }}
              title={`${el.type}: ${el.text || el.value || el.attributes.placeholder || el.id} (${Math.round(el.confidence * 100)}%)`}
            >
              <span className="bbox-tag">
                {el.type} {Math.round(el.confidence * 100)}%
              </span>
            </div>
          );
        })}

      {/* 2. PII / Sensitive Bounding Boxes */}
      {showPii &&
        piiEntities.map((pii, idx) => {
          const isSelected = selectedPiiId === (pii.id || `pii_${idx}`);
          const [x1, y1, x2, y2] = pii.bbox;
          const w = x2 - x1;
          const h = y2 - y1;

          if (w <= 0 || h <= 0) return null;

          return (
            <div
              key={pii.id || `pii_${idx}`}
              className={`bbox-box PII ${isSelected ? 'selected' : ''}`}
              style={{
                left: `${x1}px`,
                top: `${y1}px`,
                width: `${w}px`,
                height: `${h}px`
              }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedPiiId(pii.id || `pii_${idx}`);
                setSelectedElementId(null);
              }}
              title={`PII [${pii.type}]: ${pii.text} (${Math.round(pii.confidence * 100)}%)`}
            >
              <span className="bbox-tag">
                🔒 {pii.type}
              </span>
            </div>
          );
        })}
    </div>
  );
};

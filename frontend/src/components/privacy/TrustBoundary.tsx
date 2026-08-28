import React from 'react';

export const TrustBoundary: React.FC = () => {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">🛡️</span>
          <span>Architectural Trust Boundary</span>
        </span>
        <span className="badge badge-green">STRICT LOCAL ENFORCEMENT</span>
      </div>

      <div className="trust-boundary-container">
        {/* Left: Trusted Local Zone */}
        <div className="trust-zone local">
          <div className="trust-zone-header">
            <span className="trust-zone-title">
              <span>💻</span>
              <span>Trusted Local Zone (On-Device)</span>
            </span>
            <span className="badge badge-green" style={{ fontSize: '9px' }}>100% PRIVATE</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>📷</span>
              <div>
                <strong>Raw Screenshot & DOM Tree</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Never leaves device memory</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>👁️</span>
              <div>
                <strong>OpenCV Visual Contour Extraction</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Local shape & control classification</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>🔍</span>
              <div>
                <strong>PII Heuristics & Haar Face Classifier</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Identifies emails, cards, passwords, faces</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>🎨</span>
              <div>
                <strong>Local Visual & DOM Redactor</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Blurs/masks coordinates before transmission</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Untrusted Remote Reasoning Zone */}
        <div className="trust-zone remote">
          <div className="trust-zone-header">
            <span className="trust-zone-title">
              <span>🤖</span>
              <span>Reasoning / Planning Zone</span>
            </span>
            <span className="badge badge-purple" style={{ fontSize: '9px' }}>SANITIZED CONTEXT ONLY</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>🖼️</span>
              <div>
                <strong>Sanitized Visual Frame</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>All sensitive regions masked/blurred</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>📄</span>
              <div>
                <strong>Redacted Element Hierarchy</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Values scrubbed with `[CARD REDACTED]` tokens</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>⚡</span>
              <div>
                <strong>Structured Browser Action Output</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Outputs JSON: `CLICK`, `TYPE`, `WAIT`</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
              <span>🛡️</span>
              <div>
                <strong>Safety Gatekeeper Check</strong>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Blocks unverified high-impact actions</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

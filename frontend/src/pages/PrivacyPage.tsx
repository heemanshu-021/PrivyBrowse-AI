import React from 'react';
import { useApp } from '../context/AppContext';
import { MetricCard } from '../components/common/MetricCard';
import { TrustBoundary } from '../components/privacy/TrustBoundary';
import { PIIList } from '../components/privacy/PIIList';

export const PrivacyPage: React.FC = () => {
  const {
    piiEntities,
    privacyStatus,
    settings,
    updateSettings,
    runPipeline,
    isProcessing,
    rawScreenshot,
    currentScenario
  } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Privacy Center & Trust Boundary</h1>
          <p className="page-subtitle">
            All raw screenshots, passwords, emails, card numbers, and facial coordinates are processed on-device. The reasoning agent only receives scrubbed tokens.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" onClick={runPipeline} disabled={isProcessing}>
            <span>{isProcessing ? '⏳' : '↻'}</span>
            <span>Re-Scan Privacy</span>
          </button>
        </div>
      </div>

      {/* 2. Privacy Quick Metrics */}
      <div className="metrics-grid">
        <MetricCard
          label="Sensitive Items Detected"
          value={piiEntities.length}
          icon="🔍"
          subtext="Categorized via regex + DOM semantics"
          statusColor="var(--accent-amber)"
        />
        <MetricCard
          label="Local Redactions Executed"
          value={piiEntities.length}
          icon="🛡️"
          subtext={`Rendered using ${settings.redactionStyle} style`}
          statusColor="var(--accent-green)"
        />
        <MetricCard
          label="Raw PII Transmitted"
          value="0"
          unit="bytes"
          icon="🔒"
          subtext="Strict zero-leak trust boundary"
          statusColor="var(--accent-green)"
        />
        <MetricCard
          label="Privacy Shield State"
          value={privacyStatus}
          icon="⚡"
          subtext="Local enforcement active"
          statusColor="var(--accent-cyan)"
        />
      </div>

      {/* 3. Architectural Trust Boundary Diagram */}
      <TrustBoundary />

      {/* 4. Side-by-Side Before vs After Comparison */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">🔄</span>
            <span>Before & After Redaction Comparison</span>
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Style:</span>
            <select
              className="input-control select-control"
              value={settings.redactionStyle}
              onChange={(e) => updateSettings({ redactionStyle: e.target.value as any })}
              style={{ fontSize: '11px', padding: '4px 8px', width: '130px' }}
            >
              <option value="opaque">Opaque Mask</option>
              <option value="blur">Gaussian Blur</option>
              <option value="pixelate">Pixelation</option>
            </select>
          </div>
        </div>

        {rawScreenshot ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Raw Frame (Unsanitized) */}
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-red)', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>⚠️</span>
                <span>Raw Frame (Trusted Local Zone Only)</span>
              </div>
              <div
                style={{
                  backgroundColor: '#1e293b',
                  border: '1.5px solid var(--accent-red)',
                  borderRadius: 'var(--radius-md)',
                  padding: '20px',
                  minHeight: '360px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#38bdf8', textAlign: 'center' }}>
                  {currentScenario.name} (Unsanitized Raw Data)
                </div>
                {currentScenario.id === 'checkout' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Name:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>Amit Sharma</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Billing Email:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>amit.sharma@example.com</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>PAN Card Number:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>4111 2222 3333 4444</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>CVV & Expiry:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>CVV: 899 | EXP: 12/28</div>
                    </div>
                  </div>
                )}
                {currentScenario.id === 'login' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Account Email:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>user@sih2026.gov.in</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Plaintext Password:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>PrivySafePassword123!</div>
                    </div>
                  </div>
                )}
                {currentScenario.id === 'profile' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', overflow: 'hidden', margin: '0 auto', border: '2px solid #ef4444' }}>
                      <img src="/demo/face.jpg" alt="Raw Face" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Full Name:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>Johnathan Doe</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Employee Identification:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>987-65-4321</div>
                    </div>
                  </div>
                )}
                {currentScenario.id === 'search' && (
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    No personal data on public query page.
                  </div>
                )}
                {currentScenario.id === 'privacy_eval' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Indian PAN:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>ABCDE1234F</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Indian Aadhaar:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>9876 5432 1098</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Payment Card:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>4111 2222 3333 4444</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Password & OTP:</span>
                      <div style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>SecretAdminKey!2026 / 593821</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Non-PII Content (Public):</span>
                      <div style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>2026, ₹999, Order #12345</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Sanitized Frame (Safe for Reasoning) */}
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-green)', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🔒</span>
                <span>Sanitized Layout (Safe for Reasoning)</span>
              </div>
              <div
                style={{
                  backgroundColor: '#1e293b',
                  border: '1.5px solid var(--accent-green)',
                  borderRadius: 'var(--radius-md)',
                  padding: '20px',
                  minHeight: '360px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#38bdf8', textAlign: 'center' }}>
                  {currentScenario.name} (Sanitized)
                </div>
                {currentScenario.id === 'checkout' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Name:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[NAME REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Billing Email:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[EMAIL REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>PAN Card Number:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[CARD REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>CVV & Expiry:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>CVV: [MASKED] | EXP: 12/28</div>
                    </div>
                  </div>
                )}
                {currentScenario.id === 'login' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Account Email:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[EMAIL REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Plaintext Password:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[PASSWORD REDACTED]</div>
                    </div>
                  </div>
                )}
                {currentScenario.id === 'profile' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', overflow: 'hidden', margin: '0 auto', border: '2px solid #10b981', position: 'relative' }}>
                      <img
                        src="/demo/face.jpg"
                        alt="Blurred Face"
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          filter: settings.redactionStyle === 'blur' ? `blur(${settings.blurStrength}px)` : settings.redactionStyle === 'pixelate' ? 'contrast(0.2)' : 'none'
                        }}
                      />
                      {settings.redactionStyle === 'opaque' && (
                        <div style={{ position: 'absolute', inset: 0, backgroundColor: '#262626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '8px', color: 'white' }}>
                          [FACE MASKED]
                        </div>
                      )}
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Full Name:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[NAME REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Employee Identification:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[ID_NUM REDACTED]</div>
                    </div>
                  </div>
                )}
                {currentScenario.id === 'search' && (
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Layout verified. No PII tokens required.
                  </div>
                )}
                {currentScenario.id === 'privacy_eval' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Indian PAN:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[PAN REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Indian Aadhaar:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[AADHAAR REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Payment Card:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[CARD REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Password & OTP:</span>
                      <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>[PASSWORD REDACTED] / [OTP REDACTED]</div>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8', fontSize: '10px' }}>Preserved Public Numbers:</span>
                      <div style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>2026, ₹999, Order #12345 (UNTOUCHED)</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '36px' }}>
            Run the pipeline on an active scenario to compare raw vs sanitized states.
          </div>
        )}
      </div>

      {/* 5. Detected PII Records Table */}
      <PIIList />
    </div>
  );
};

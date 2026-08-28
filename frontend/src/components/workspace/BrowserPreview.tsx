import React from 'react';
import { useApp } from '../../context/AppContext';
import { PerceptionOverlay } from './PerceptionOverlay';

export const BrowserPreview: React.FC = () => {
  const {
    currentScenario,
    viewMode,
    setViewMode,
    settings,
    agentStatus,
    pauseAgent,
    resumeAgent,
    stopAgent,
    rawScreenshot,
    backendConnected
  } = useApp();

  const isSanitized = viewMode === 'sanitized' || viewMode === 'overlay';

  return (
    <div className="card" style={{ padding: '16px' }}>
      <div className="card-header" style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="card-title">
            <span className="card-title-icon">🌐</span>
            <span>Live Browser Preview</span>
          </span>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              backgroundColor: 'var(--bg-input)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)'
            }}
          >
            480 x 540 px
          </span>
        </div>

        <div className="view-mode-bar">
          <button
            className={`view-mode-btn ${viewMode === 'original' ? 'active' : ''}`}
            onClick={() => setViewMode('original')}
            title="Show raw unredacted webpage"
          >
            Raw
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'perception' ? 'active' : ''}`}
            onClick={() => setViewMode('perception')}
            title="Show visual contour & element bounding boxes"
          >
            Contours
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'sanitized' ? 'active' : ''}`}
            onClick={() => setViewMode('sanitized')}
            title="Show on-device redacted layout"
          >
            Redacted
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'overlay' ? 'active' : ''}`}
            onClick={() => setViewMode('overlay')}
            title="Show unified overlay"
          >
            Fused Overlay
          </button>
        </div>
      </div>

      {/* Browser URL Navigation Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '6px 10px',
          marginBottom: '12px',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)'
        }}
      >
        <span style={{ color: 'var(--accent-green)' }}>🔒 https://</span>
        <span style={{ color: 'var(--text-secondary)' }}>
          {backendConnected ? `127.0.0.1:8000${currentScenario.url}` : `sandbox.local${currentScenario.url}`}
        </span>
      </div>

      {/* Visual Canvas Area */}
      <div className="canvas-wrapper">
        {rawScreenshot ? (
          <div className="preview-frame">
            {/* Scenario 1: Login Form */}
            {currentScenario.id === 'login' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', padding: '40px 30px' }}>
                <div style={{ textAlign: 'center', color: 'var(--accent-green)', fontWeight: 700, fontSize: '15px' }}>
                  Secure Gatekeeper
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>Email Address</div>
                  <div style={{ height: '34px', backgroundColor: '#121214', border: '1px solid #323238', borderRadius: '4px', padding: '7px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[EMAIL REDACTED]' : 'user@sih2026.gov.in'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>Password</div>
                  <div style={{ height: '34px', backgroundColor: '#121214', border: '1px solid #323238', borderRadius: '4px', padding: '7px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[PASSWORD REDACTED]' : 'PrivySafePassword123!'}
                  </div>
                </div>
                <button style={{ height: '36px', backgroundColor: '#00b37e', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}>
                  Sign In
                </button>
              </div>
            )}

            {/* Scenario 2: Search Page */}
            {currentScenario.id === 'search' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', padding: '24px 20px' }}>
                <div style={{ textAlign: 'center', color: 'var(--accent-blue)', fontWeight: 700, fontSize: '18px' }}>
                  IndiSearch
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ flex: 1, height: '34px', backgroundColor: '#1a1a1e', border: '1px solid #2e2e33', borderRadius: '17px', padding: '8px 14px', fontSize: '12px', color: '#fff' }}>
                    Chandrayaan-3
                  </div>
                  <button style={{ height: '34px', padding: '0 14px', backgroundColor: 'var(--accent-blue)', border: 'none', borderRadius: '17px', color: 'white', fontSize: '11px', fontWeight: 'bold' }}>
                    Search
                  </button>
                </div>
                <div style={{ borderTop: '1px solid #2e2e33', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ backgroundColor: '#1a1a1e', border: '1px solid #2e2e33', borderRadius: '6px', padding: '10px' }}>
                    <div style={{ fontSize: '12px', color: '#60a5fa', fontWeight: 'bold' }}>Chandrayaan-3 - Wikipedia</div>
                    <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '4px' }}>
                      India's third lunar exploration mission soft-landed Vikram lander on lunar south pole...
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Scenario 3: Checkout Form */}
            {currentScenario.id === 'checkout' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '20px' }}>
                <div style={{ textAlign: 'center', color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '14px' }}>
                  Secure Order Checkout
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Cardholder Name</div>
                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[NAME REDACTED]' : 'Amit Sharma'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Billing Email</div>
                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[EMAIL REDACTED]' : 'amit.sharma@example.com'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Credit Card Number</div>
                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[CARD REDACTED]' : '4111 2222 3333 4444'}
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Expiry</div>
                    <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>12/28</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>CVV</div>
                    <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>•••</div>
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Delivery Address</div>
                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[ADDRESS REDACTED]' : '12, MG Road, Bangalore, KA'}
                  </div>
                </div>
                <button style={{ height: '36px', backgroundColor: '#0284c7', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginTop: '6px' }}>
                  Confirm & Pay Order
                </button>
              </div>
            )}

            {/* Scenario 4: Complex Webpage (reuses dense checkout layout) */}
            {currentScenario.id === 'complex' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '20px' }}>
                <div style={{ textAlign: 'center', color: 'var(--accent-purple)', fontWeight: 700, fontSize: '14px' }}>
                  Multi-Column Control Matrix
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>First Name</div>
                    <div style={{ height: '30px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '5px 8px', fontSize: '11px', color: '#fff' }}>
                      {isSanitized ? '[NAME REDACTED]' : 'Amit'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Last Name</div>
                    <div style={{ height: '30px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '5px 8px', fontSize: '11px', color: '#fff' }}>
                      {isSanitized ? '[NAME REDACTED]' : 'Sharma'}
                    </div>
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Primary Contact Email</div>
                  <div style={{ height: '30px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '5px 8px', fontSize: '11px', color: '#fff' }}>
                    {isSanitized ? '[EMAIL REDACTED]' : 'amit.sharma@example.com'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Payment Instrument (Card)</div>
                  <div style={{ height: '30px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '5px 8px', fontSize: '11px', color: '#fff' }}>
                    {isSanitized ? '[CARD REDACTED]' : '4111 2222 3333 4444'}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '6px', marginTop: '10px' }}>
                  <button style={{ flex: 1, height: '32px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 600, fontSize: '11px', cursor: 'pointer' }}>Apply Filters</button>
                  <button style={{ flex: 1, height: '32px', backgroundColor: '#0284c7', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 600, fontSize: '11px', cursor: 'pointer' }}>Submit Matrix</button>
                </div>
              </div>
            )}

            {/* Scenario 5: Profile & Face Redaction */}
            {currentScenario.id === 'profile' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', padding: '24px 20px', alignItems: 'center' }}>
                <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '14px' }}>
                  Secure Profile Management
                </div>
                <div
                  style={{
                    position: 'relative',
                    width: '110px',
                    height: '110px',
                    borderRadius: '50%',
                    overflow: 'hidden',
                    border: '2.5px solid var(--accent-cyan)',
                    backgroundColor: '#0f172a'
                  }}
                >
                  <img
                    src="/demo/face.jpg"
                    alt="Face"
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      filter:
                        isSanitized && settings.redactionStyle === 'blur'
                          ? `blur(${settings.blurStrength}px)`
                          : isSanitized && settings.redactionStyle === 'pixelate'
                          ? 'contrast(0.2)'
                          : 'none'
                    }}
                  />
                  {isSanitized && settings.redactionStyle === 'opaque' && (
                    <div
                      style={{
                        position: 'absolute',
                        inset: 0,
                        backgroundColor: '#262626',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '9px',
                        fontWeight: 'bold',
                        color: 'white'
                      }}
                    >
                      [FACE MASKED]
                    </div>
                  )}
                </div>
                <div style={{ width: '100%', textAlign: 'left' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Full Name</div>
                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[NAME REDACTED]' : 'Johnathan Doe'}
                  </div>
                </div>
                <div style={{ width: '100%', textAlign: 'left' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Employee ID (Sensitive)</div>
                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', color: '#fff' }}>
                    {isSanitized ? '[ID_NUM REDACTED]' : '987-65-4321'}
                  </div>
                </div>
                <button style={{ width: '100%', height: '34px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginTop: '6px' }}>
                  Save Profile Settings
                </button>
              </div>
            )}

            {/* Projected Perception Overlay */}
            <PerceptionOverlay />
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
            <div style={{ fontSize: '28px', marginBottom: '8px' }}>📷</div>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>No Active Screen Observation</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Click "Run Local Pipeline" to observe and perceive the current webpage frame.</div>
          </div>
        )}
      </div>

      {/* Viewport Control Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          {agentStatus === 'RUNNING' ? (
            <button className="btn btn-secondary btn-sm" onClick={pauseAgent}>
              <span>⏸</span>
              <span>Pause</span>
            </button>
          ) : agentStatus === 'PAUSED' ? (
            <button className="btn btn-cyan btn-sm" onClick={resumeAgent}>
              <span>▶</span>
              <span>Resume</span>
            </button>
          ) : (
            <button className="btn btn-secondary btn-sm" onClick={stopAgent}>
              <span>⏹</span>
              <span>Reset View</span>
            </button>
          )}
        </div>

        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          State: <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{agentStatus}</span>
        </div>
      </div>
    </div>
  );
};

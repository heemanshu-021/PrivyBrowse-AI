import React from 'react';
import { useApp } from '../context/AppContext';

export const SettingsPage: React.FC = () => {
  const { settings, updateSettings, refreshHealth } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Agent & Privacy Settings</h1>
          <p className="page-subtitle">
            Configure local computer vision inference parameters, visual redaction styling, and safety gatekeeper enforcement policies.
          </p>
        </div>

        <button
          className="btn btn-secondary"
          onClick={() => {
            updateSettings({
              redactionStyle: 'opaque',
              confidenceThreshold: 0.85,
              confirmationMode: 'high_risk',
              maxActionsPerTask: 6,
              localProcessingPreference: 'always_local',
              blurStrength: 15
            });
          }}
        >
          Reset to Safe Defaults
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Section A: Privacy & Redaction Parameters */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🛡️</span>
              <span>Visual Redaction Styling</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Visual Masking Method
              </label>
              <select
                className="input-control select-control"
                value={settings.redactionStyle}
                onChange={(e) => updateSettings({ redactionStyle: e.target.value as any })}
              >
                <option value="opaque">Opaque Solid Fill Overlay (Default)</option>
                <option value="blur">Gaussian Blur Filter</option>
                <option value="pixelate">Pixelation Block Filter</option>
              </select>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Rendered directly over raw pixels on-device before screen context is exported.
              </span>
            </div>

            {settings.redactionStyle === 'blur' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Gaussian Blur Radius ({settings.blurStrength}px)
                  </label>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={settings.blurStrength}
                  onChange={(e) => updateSettings({ blurStrength: Number(e.target.value) })}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Processing Trust Boundary
              </label>
              <select
                className="input-control select-control"
                value={settings.localProcessingPreference}
                onChange={(e) => updateSettings({ localProcessingPreference: e.target.value as any })}
              >
                <option value="always_local">Always Local (Strict On-Device Only)</option>
                <option value="hybrid">Hybrid (Local CV + Isolated Sandbox)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section B: Agent & Decision Gatekeeper */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <span className="card-title-icon">🤖</span>
              <span>Agent Autonomy & Safety Gatekeeper</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Safety Confirmation Policy
              </label>
              <select
                className="input-control select-control"
                value={settings.confirmationMode}
                onChange={(e) => updateSettings({ confirmationMode: e.target.value as any })}
              >
                <option value="high_risk">Prompt for High-Impact Actions (Payments/Deletions)</option>
                <option value="always">Always Require User Confirmation Before Action</option>
                <option value="never">Full Autonomous Execution (Demo Mode)</option>
              </select>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Prevents accidental form submissions or monetary transactions during browser automation.
              </span>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Minimum Action Confidence Threshold ({Math.round(settings.confidenceThreshold * 100)}%)
                </label>
              </div>
              <input
                type="range"
                min="0.6"
                max="0.99"
                step="0.05"
                value={settings.confidenceThreshold}
                onChange={(e) => updateSettings({ confidenceThreshold: Number(e.target.value) })}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', display: 'block' }}>
                Actions with confidence lower than threshold are automatically paused.
              </span>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Max Actions per Task Loop
              </label>
              <input
                type="number"
                min="1"
                max="20"
                className="input-control"
                value={settings.maxActionsPerTask}
                onChange={(e) => updateSettings({ maxActionsPerTask: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Section C: Connection & Health Sync */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">🔌</span>
            <span>Local Engine & API Endpoints</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              FastAPI Local Perception Daemon
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              http://127.0.0.1:8000/api
            </div>
          </div>

          <button className="btn btn-secondary btn-sm" onClick={refreshHealth}>
            <span>↻</span>
            <span>Check Daemon Status</span>
          </button>
        </div>
      </div>
    </div>
  );
};

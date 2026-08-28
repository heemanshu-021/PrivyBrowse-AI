import React from 'react';
import { useApp } from '../context/AppContext';
import { MetricCard } from '../components/common/MetricCard';
import { PerformanceCharts } from '../components/performance/PerformanceCharts';

export const PerformancePage: React.FC = () => {
  const { metrics, refreshHealth, isProcessing } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Performance & Latency Telemetry</h1>
          <p className="page-subtitle">
            Measured latencies across on-device visual contour detection, OCR text extraction, regex PII filters, OpenCV redactions, and agent planning.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={refreshHealth} disabled={isProcessing}>
          <span>↻</span>
          <span>Refresh Measurements</span>
        </button>
      </div>

      {/* 2. Top Metric Cards */}
      <div className="metrics-grid">
        <MetricCard
          label="OCR Latency"
          value={metrics.ocr_latency_ms}
          unit="ms"
          icon="📝"
          subtext="Layout text extraction"
          statusColor="var(--accent-purple)"
        />
        <MetricCard
          label="PII Detection"
          value={metrics.pii_detection_latency_ms}
          unit="ms"
          icon="🔍"
          subtext="Regex & Haar Cascade face scan"
          statusColor="var(--accent-amber)"
        />
        <MetricCard
          label="Visual Redaction"
          value={metrics.redaction_latency_ms}
          unit="ms"
          icon="🎨"
          subtext="OpenCV Gaussian & mask rendering"
          statusColor="var(--accent-green)"
        />
        <MetricCard
          label="Agent Planning"
          value={metrics.agent_planning_latency_ms}
          unit="ms"
          icon="🤖"
          subtext="Structured JSON action formation"
          statusColor="var(--accent-cyan)"
        />
      </div>

      {/* 3. Detailed Performance Charts */}
      <PerformanceCharts />

      {/* 4. On-Device Optimization Strategy Card */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">⚙️</span>
            <span>On-Device Optimization Principles</span>
          </span>
          <span className="badge badge-green">LIGHTWEIGHT DESIGN</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', fontSize: '12px' }}>
          <div style={{ padding: '12px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>1. Region of Interest (ROI)</strong>
            <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
              Limits computer vision filters to active viewport bounds, reducing unnecessary pixel operations.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <strong style={{ color: 'var(--accent-green)' }}>2. IoU Bounding Box Merging</strong>
            <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
              Resolves overlapping DOM rects and visual contours into a single deduplicated token representation.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <strong style={{ color: 'var(--accent-purple)' }}>3. Zero Remote Overhead</strong>
            <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
              Zero high-bandwidth raw images sent over WAN; transmission payload is strictly tiny sanitized JSON.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

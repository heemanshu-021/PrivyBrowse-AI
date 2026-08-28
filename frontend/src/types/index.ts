export type PageId =
  | 'overview'
  | 'workspace'
  | 'perception'
  | 'privacy'
  | 'activity'
  | 'performance'
  | 'demolab'
  | 'settings';

export type ViewMode = 'original' | 'perception' | 'sanitized' | 'overlay';
export type RedactionStyle = 'opaque' | 'blur' | 'pixelate';
export type ActionType = 'CLICK' | 'TYPE' | 'SCROLL' | 'PRESS_KEY' | 'NAVIGATE' | 'WAIT' | 'GO_BACK' | 'GO_FORWARD' | 'FINISH';

export type StepStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'WARNING' | 'FAILED';

export interface DOMNode {
  id: string;
  tag_name: string;
  text?: string;
  value?: string;
  placeholder?: string;
  type?: string;
  id_attr?: string;
  class_attr?: string;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
}

export interface PiiEntity {
  id?: string;
  type: 'EMAIL' | 'PHONE' | 'NAME' | 'PASSWORD' | 'ADDRESS' | 'CARD' | 'BANK_ACCOUNT' | 'AADHAAR' | 'PAN' | 'OTP' | 'SECRET_TOKEN' | 'ID_NUM' | 'DOB' | 'FACE' | string;
  text: string;
  confidence: number;
  bbox: [number, number, number, number];
  source: 'OCR_REGEX' | 'DOM_SEMANTICS' | 'VISION_HAAR' | string | string[];
  classification?: 'PUBLIC' | 'SENSITIVE' | 'HIGHLY_SENSITIVE';
  element_id?: string;
  timestamp?: string;
  protectionMethod?: RedactionStyle;
}

export interface RedactionItem {
  id: string;
  pii_type: string;
  bbox: [number, number, number, number];
  replacement: string;
  confidence: number;
  classification: string;
  element_id?: string;
}

export interface RedactionMap {
  redactions: RedactionItem[];
  total_redacted: number;
  highly_sensitive_count: number;
  sensitive_count: number;
  style: string;
  timestamp: string;
}

export interface PrivacyAuditLogEntry {
  id: string;
  event: string;
  type?: string;
  classification?: string;
  confidence?: number;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface PrivacyPolicy {
  process_locally: boolean;
  redact_pii: boolean;
  allow_raw_remote_transmission: boolean;
  allow_sanitized_remote_transmission: boolean;
  min_confidence_threshold: number;
  default_redaction_style: string;
}


export interface FusedElement {
  id: string;
  type: 'BUTTON' | 'INPUT' | 'CHECKBOX' | 'LINK' | 'SELECT' | 'TEXTAREA' | 'IMAGE' | 'ELEMENT';
  bbox: [number, number, number, number];
  text: string;
  value: string;
  attributes: {
    tag_name?: string;
    placeholder?: string;
    type?: string;
    id?: string;
    class?: string;
  };
  confidence: number;
  source: 'DOM' | 'VISION' | 'OCR' | 'FUSED';
}

export interface OCRBlock {
  id: string;
  text: string;
  bbox: [number, number, number, number];
  confidence: number;
  element_id?: string;
  tag_name?: string;
}

export interface AgentAction {
  action: ActionType;
  target: { x: number; y: number };
  target_description: string;
  text?: string;
  confidence: number;
  element_id?: string;
  requires_confirmation?: boolean;
}

export interface TimelineStep {
  id: string;
  name: string;
  code: 'OBSERVE' | 'PERCEIVE' | 'DETECT' | 'REDACT' | 'FUSION' | 'PLAN' | 'ACT' | 'VERIFY';
  status: StepStatus;
  description: string;
  durationMs?: number;
  timestamp?: string;
}

export interface PerformanceMetrics {
  local_inference_time_ms: number;
  ocr_latency_ms: number;
  pii_detection_latency_ms: number;
  redaction_latency_ms: number;
  agent_planning_latency_ms: number;
  total_task_latency_ms: number;
  pii_detected_count: number;
  pii_redacted_count: number;
  actions_executed: number;
  runs_count: number;
  memory_usage_mb: number;
  cpu_utilization_pct: number;
  historicalLatencies?: { timestamp: string; latency: number; type: string }[];
}

export interface DemoScenario {
  id: string;
  number: string;
  name: string;
  subtitle: string;
  task: string;
  url: string;
  piiTypes: string[];
  expectedElements: number;
  description: string;
  expectedBehavior: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface AppSettings {
  redactionStyle: RedactionStyle;
  confidenceThreshold: number; // 0.0 to 1.0
  confirmationMode: 'always' | 'high_risk' | 'never';
  maxActionsPerTask: number;
  localProcessingPreference: 'always_local' | 'hybrid';
  telemetryEnabled: boolean;
  blurStrength: number;
  theme: 'dark';
}

export interface LogEntry {
  id: string;
  time: string;
  tag: 'sys' | 'act' | 'sec' | 'warn' | 'err';
  text: string;
  metadata?: Record<string, unknown>;
}

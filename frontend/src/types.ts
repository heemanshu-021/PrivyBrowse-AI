export interface DOMNode {
  id: string;
  tag_name: string;
  text?: string;
  value?: string;
  placeholder?: string;
  type?: string;
  id_attr?: string;
  class_attr?: string;
  bbox: number[]; // [x1, y1, x2, y2]
}

export interface PiiEntity {
  type: string;
  text: string;
  confidence: number;
  bbox: number[];
  source: string;
  element_id?: string;
}

export interface FusedElement {
  id: string;
  type: string;
  bbox: number[];
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
  source: string;
}

export interface AgentAction {
  action: 'CLICK' | 'TYPE' | 'SCROLL' | 'PRESS_KEY' | 'NAVIGATE' | 'WAIT' | 'GO_BACK' | 'GO_FORWARD' | 'FINISH';
  target: { x: number; y: number };
  target_description: string;
  text?: string;
  confidence: number;
  element_id?: string;
  requires_confirmation?: boolean;
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
}

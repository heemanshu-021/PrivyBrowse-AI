export type ElementType =
  | 'button'
  | 'input'
  | 'select'
  | 'textarea'
  | 'link'
  | 'checkbox'
  | 'radio'
  | 'form'
  | 'text'
  | 'image'
  | 'element';

export type ActionVerb =
  | 'CLICK'
  | 'TYPE'
  | 'SCROLL'
  | 'PRESS_KEY'
  | 'NAVIGATE'
  | 'WAIT';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  top?: number;
  left?: number;
  right?: number;
  bottom?: number;
}

export interface NormalizedElement {
  id: string; // e.g. "pb-element-001"
  type: ElementType;
  tag: string;
  text: string;
  ariaLabel: string | null;
  placeholder: string | null;
  role: string | null;
  name: string | null;
  inputType?: string | null;
  sensitive?: boolean; // True for passwords, credit cards, CVVs, etc.
  bbox: BoundingBox;
  visible: boolean;
  enabled: boolean;
  selector?: string;
  xpath?: string;
}

export interface PageMetadata {
  url: string;
  hostname: string;
  title: string;
  viewport: {
    width: number;
    height: number;
  };
  devicePixelRatio: number;
  timestamp: string;
}

export interface BrowserContext {
  page: PageMetadata;
  screenshot: {
    available: boolean;
    dataUrl?: string;
    timestamp: string;
  };
  elements: NormalizedElement[];
  capture: {
    timestamp: string;
    source: 'chrome-extension';
    elementCount: number;
  };
}

export interface ActionTarget {
  elementId?: string;
  selector?: string;
  x?: number;
  y?: number;
  description?: string;
}

export interface AgentActionRequest {
  action: ActionVerb;
  target: ActionTarget;
  text?: string;
  key?: string;
  scrollDelta?: { x: number; y: number };
  confidence: number;
  requiresConfirmation?: boolean;
}

export interface ActionResult {
  success: boolean;
  action: ActionVerb;
  target?: string;
  detail?: string;
  error?: 'TARGET_NOT_FOUND' | 'TARGET_NOT_VISIBLE' | 'TARGET_DISABLED' | 'ACTION_FAILED' | 'INVALID_ACTION' | string;
  timestamp: string;
}

export type ExtensionMessageType =
  | 'GET_PAGE_CONTEXT'
  | 'CAPTURE_SCREENSHOT'
  | 'ANALYZE_PAGE'
  | 'CONNECTION_STATUS'
  | 'EXECUTE_ACTION'
  | 'ACTION_RESULT'
  | 'AGENT_STATUS'
  | 'HIGHLIGHT_ELEMENT'
  | 'CLEAR_HIGHLIGHTS';

export interface ExtensionMessage<T = unknown> {
  type: ExtensionMessageType;
  payload?: T;
  source?: 'popup' | 'background' | 'content' | 'frontend';
}

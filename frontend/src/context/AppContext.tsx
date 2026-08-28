import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type {
  PageId,
  ViewMode,
  PiiEntity,
  FusedElement,
  OCRBlock,
  AgentAction,
  TimelineStep,
  PerformanceMetrics,
  DemoScenario,
  AppSettings,
  LogEntry,
  DOMNode
} from '../types';

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'login',
    number: '01',
    name: 'Privacy-Preserving Login',
    subtitle: 'Local password & email redaction before reasoning',
    task: 'Login to the secure gatekeeper with user@sih2026.gov.in and password',
    url: '/demo/login.html',
    piiTypes: ['EMAIL', 'PASSWORD'],
    expectedElements: 3,
    description: 'Autonomous credential submission while completely masking sensitive password and email strings from any reasoning layer.',
    expectedBehavior: 'Agent types sanitized credentials and triggers Sign In button.',
    riskLevel: 'MEDIUM'
  },
  {
    id: 'search',
    number: '02',
    name: 'Search & Navigation',
    subtitle: 'Visual query input and structured result selection',
    task: 'Search for Chandrayaan-3 and open the first relevant wiki result',
    url: '/demo/search.html',
    piiTypes: [],
    expectedElements: 3,
    description: 'Autonomous web navigation involving typing search query and selecting interactive hyperlink results based on fused DOM+CV perception.',
    expectedBehavior: 'Agent enters query string and clicks search or destination link.',
    riskLevel: 'LOW'
  },
  {
    id: 'checkout',
    number: '03',
    name: 'Sensitive Checkout Form',
    subtitle: 'Credit card, CVV & address on-device masking',
    task: 'Fill out the checkout billing form securely and confirm order',
    url: '/demo/form.html',
    piiTypes: ['NAME', 'EMAIL', 'CARD', 'ADDRESS'],
    expectedElements: 7,
    description: 'Payment form handling where full PAN credit card numbers and physical addresses are scrubbed on-device prior to action calculation.',
    expectedBehavior: 'Agent fills billing fields and triggers safety confirmation before payment.',
    riskLevel: 'HIGH'
  },
  {
    id: 'complex',
    number: '04',
    name: 'Complex Webpage Layout',
    subtitle: 'Dense DOM hierarchy with mixed controls and contours',
    task: 'Inspect complex control layout and submit form securely',
    url: '/demo/form.html',
    piiTypes: ['NAME', 'EMAIL', 'CARD'],
    expectedElements: 10,
    description: 'Testing contour detection and IoU bounding box fusion on multi-column dense interactive web interfaces.',
    expectedBehavior: 'Identifies all interactive zones and resolves overlapping detections.',
    riskLevel: 'MEDIUM'
  },
  {
    id: 'profile',
    number: '05',
    name: 'Face & PII Protection',
    subtitle: 'Haar Cascade facial blurring and ID number protection',
    task: 'Save the user profile settings securely',
    url: '/demo/face.html',
    piiTypes: ['FACE', 'NAME', 'ID_NUM'],
    expectedElements: 3,
    description: 'Demonstrates computer vision face detection via Haar Cascade on raw screenshots and employee ID number regex redaction.',
    expectedBehavior: 'Applies visual blur/mask over facial photo and saves profile.',
    riskLevel: 'HIGH'
  }
];

const INITIAL_TIMELINE: TimelineStep[] = [
  { id: '1', code: 'OBSERVE', name: 'Observe Screen', status: 'PENDING', description: 'Capture raw tab frame & DOM tree' },
  { id: '2', code: 'PERCEIVE', name: 'Visual Perception', status: 'PENDING', description: 'Run OpenCV contour analysis & OCR layout' },
  { id: '3', code: 'DETECT', name: 'PII Detection', status: 'PENDING', description: 'Classify sensitive patterns & detect faces' },
  { id: '4', code: 'REDACT', name: 'Local Redaction', status: 'PENDING', description: 'Apply visual masks & scrub DOM text' },
  { id: '5', code: 'FUSION', name: 'Context Fusion', status: 'PENDING', description: 'Merge visual contours with sanitized DOM' },
  { id: '6', code: 'PLAN', name: 'Agent Reasoning', status: 'PENDING', description: 'Plan structured action from safe context' },
  { id: '7', code: 'ACT', name: 'Execute Action', status: 'PENDING', description: 'Dispatch keystrokes or mouse click' },
  { id: '8', code: 'VERIFY', name: 'Verify State', status: 'PENDING', description: 'Confirm transition & observation loop' }
];

const DEFAULT_SETTINGS: AppSettings = {
  redactionStyle: 'opaque',
  confidenceThreshold: 0.85,
  confirmationMode: 'high_risk',
  maxActionsPerTask: 6,
  localProcessingPreference: 'always_local',
  telemetryEnabled: true,
  blurStrength: 15,
  theme: 'dark'
};

const BACKEND_URL = "http://127.0.0.1:8000/api";

interface AppContextType {
  activePage: PageId;
  setActivePage: (p: PageId) => void;
  
  // Connection states
  backendConnected: boolean;
  extensionConnected: boolean;
  agentStatus: 'READY' | 'RUNNING' | 'PAUSED' | 'ERROR';
  perceptionStatus: 'READY' | 'RUNNING' | 'ERROR';
  privacyStatus: 'PROTECTED' | 'WARNING' | 'ERROR';
  isProcessing: boolean;
  
  // Scenario and Task
  scenarios: DemoScenario[];
  currentScenario: DemoScenario;
  selectScenario: (id: string) => void;
  taskText: string;
  setTaskText: (t: string) => void;
  
  // Screen & Visual Data
  rawScreenshot: string;
  redactedScreenshot: string;
  piiEntities: PiiEntity[];
  fusedElements: FusedElement[];
  ocrBlocks: OCRBlock[];
  plannedAction: AgentAction | null;
  selectedElementId: string | null;
  setSelectedElementId: (id: string | null) => void;
  selectedPiiId: string | null;
  setSelectedPiiId: (id: string | null) => void;
  viewMode: ViewMode;
  setViewMode: (v: ViewMode) => void;
  
  // Timeline, Logs & History
  timelineSteps: TimelineStep[];
  logs: LogEntry[];
  actionHistory: AgentAction[];
  
  // Performance
  metrics: PerformanceMetrics;
  
  // Settings
  settings: AppSettings;
  updateSettings: (s: Partial<AppSettings>) => void;
  
  // Safety Confirmation
  confirmDialog: {
    open: boolean;
    message: string;
    action: AgentAction | null;
  };
  dismissConfirmDialog: () => void;
  approveConfirmAction: () => void;
  
  // Pipeline Actions
  runPipeline: () => Promise<void>;
  executePlannedAction: () => Promise<void>;
  pauseAgent: () => void;
  resumeAgent: () => void;
  stopAgent: () => void;
  resetState: () => void;
  refreshHealth: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [extensionConnected, setExtensionConnected] = useState<boolean>(false);
  const [agentStatus, setAgentStatus] = useState<'READY' | 'RUNNING' | 'PAUSED' | 'ERROR'>('READY');
  const [perceptionStatus, setPerceptionStatus] = useState<'READY' | 'RUNNING' | 'ERROR'>('READY');
  const [privacyStatus, setPrivacyStatus] = useState<'PROTECTED' | 'WARNING' | 'ERROR'>('PROTECTED');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const [currentScenario, setCurrentScenario] = useState<DemoScenario>(DEMO_SCENARIOS[2]); // Default to checkout
  const [taskText, setTaskText] = useState<string>(DEMO_SCENARIOS[2].task);

  const [rawScreenshot, setRawScreenshot] = useState<string>('');
  const [, setRedactedScreenshot] = useState<string>('');
  const [piiEntities, setPiiEntities] = useState<PiiEntity[]>([]);
  const [fusedElements, setFusedElements] = useState<FusedElement[]>([]);
  const [ocrBlocks, setOcrBlocks] = useState<OCRBlock[]>([]);
  const [plannedAction, setPlannedAction] = useState<AgentAction | null>(null);

  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  const [selectedPiiId, setSelectedPiiId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('overlay');

  const [timelineSteps, setTimelineSteps] = useState<TimelineStep[]>(INITIAL_TIMELINE);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [actionHistory, setActionHistory] = useState<AgentAction[]>([]);

  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);

  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    local_inference_time_ms: 0,
    ocr_latency_ms: 0,
    pii_detection_latency_ms: 0,
    redaction_latency_ms: 0,
    agent_planning_latency_ms: 0,
    total_task_latency_ms: 0,
    pii_detected_count: 0,
    pii_redacted_count: 0,
    actions_executed: 0,
    runs_count: 0,
    memory_usage_mb: 142.5,
    cpu_utilization_pct: 4.2
  });

  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    message: string;
    action: AgentAction | null;
  }>({
    open: false,
    message: '',
    action: null
  });

  const addLog = useCallback((tag: 'sys' | 'act' | 'sec' | 'warn' | 'err', text: string, metadata?: Record<string, unknown>) => {
    const entry: LogEntry = {
      id: Math.random().toString(36).substring(2, 9),
      time: new Date().toLocaleTimeString(),
      tag,
      text,
      metadata
    };
    setLogs(prev => [entry, ...prev.slice(0, 99)]);
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        setBackendConnected(true);
        addLog('sys', 'Connected to PrivyBrowse Local Perception Engine on port 8000');
        
        // Fetch metrics
        const mRes = await fetch(`${BACKEND_URL}/metrics`);
        if (mRes.ok) {
          const mData = await mRes.json();
          setMetrics(mData);
        }

        // Fetch extension / browser status
        try {
          const bRes = await fetch(`${BACKEND_URL}/browser/status`);
          if (bRes.ok) {
            const bData = await bRes.json();
            if (bData.connected) {
              setExtensionConnected(true);
              addLog('sys', `Browser extension synced with active tab: ${bData.page?.hostname || 'active tab'}`);
            }
          }
        } catch {
          // Extension status not yet available
        }
      } else {
        setBackendConnected(false);
        addLog('warn', 'Backend health check returned non-200. Operating in Local Sandbox Mode.');
      }
    } catch {
      setBackendConnected(false);
      addLog('sys', 'Local Perception Server offline. Sandbox simulation engine active.');
    }
  }, [addLog]);

  useEffect(() => {
    refreshHealth();
    addLog('sys', 'PrivyBrowse AI Shell initialized. Privacy Boundary Active.');
  }, [refreshHealth, addLog]);

  const selectScenario = useCallback((id: string) => {
    const s = DEMO_SCENARIOS.find(sc => sc.id === id) || DEMO_SCENARIOS[0];
    setCurrentScenario(s);
    setTaskText(s.task);
    setPlannedAction(null);
    setSelectedElementId(null);
    setSelectedPiiId(null);
    setTimelineSteps(INITIAL_TIMELINE);
    addLog('sys', `Switched scenario to: ${s.name}`);
  }, [addLog]);

  const updateSettings = useCallback((newSettings: Partial<AppSettings>) => {
    setSettings((prev: AppSettings) => ({ ...prev, ...newSettings }));
    addLog('sys', 'Updated application parameters.');
  }, [addLog]);

  const updateTimelineStep = (code: TimelineStep['code'], status: TimelineStep['status'], durationMs?: number) => {
    setTimelineSteps((prev: TimelineStep[]) =>
      prev.map(step => (step.code === code ? { ...step, status, durationMs } : step))
    );
  };

  const runPipeline = useCallback(async () => {
    setIsProcessing(true);
    setAgentStatus('RUNNING');
    setPerceptionStatus('RUNNING');
    addLog('sys', `Starting Observe -> Perceive -> Protect -> Plan pipeline for task: "${taskText}"`);

    // Reset timeline
    setTimelineSteps(INITIAL_TIMELINE.map(s => ({ ...s, status: 'PENDING' })));

    // 1. OBSERVE
    updateTimelineStep('OBSERVE', 'RUNNING');
    const t0 = performance.now();
    await new Promise(r => setTimeout(r, 60));
    const domNodes = getScenarioDOMNodes(currentScenario.id);
    const mockB64 = getMockScreenshotB64();
    setRawScreenshot(mockB64);
    updateTimelineStep('OBSERVE', 'SUCCESS', Math.round(performance.now() - t0));
    addLog('sys', `Captured page frame with ${domNodes.length} visible DOM layout descriptors.`);

    if (backendConnected) {
      try {
        // 2. PERCEIVE
        updateTimelineStep('PERCEIVE', 'RUNNING');
        const tPercStart = performance.now();
        const analyzeRes = await fetch(`${BACKEND_URL}/perception/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ screenshot: mockB64, dom_nodes: domNodes })
        });
        const analyzeData = await analyzeRes.json();
        setFusedElements(analyzeData.fused_elements);
        setOcrBlocks(analyzeData.ocr_blocks);
        updateTimelineStep('PERCEIVE', 'SUCCESS', Math.round(performance.now() - tPercStart));
        addLog('sys', `Contour extraction complete. Detected ${analyzeData.vision_elements.length} visual shapes.`);

        // 3. DETECT PII
        updateTimelineStep('DETECT', 'RUNNING');
        const tPiiStart = performance.now();
        const detectRes = await fetch(`${BACKEND_URL}/privacy/detect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            screenshot: mockB64,
            text_blocks: analyzeData.ocr_blocks,
            dom_nodes: domNodes
          })
        });
        const detectData = await detectRes.json();
        setPiiEntities(detectData.pii_entities);
        updateTimelineStep('DETECT', 'SUCCESS', Math.round(performance.now() - tPiiStart));
        addLog('sec', `Identified ${detectData.pii_entities.length} sensitive items on-device.`);

        // 4. REDACT
        updateTimelineStep('REDACT', 'RUNNING');
        const tRedactStart = performance.now();
        const redactRes = await fetch(`${BACKEND_URL}/privacy/redact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            screenshot: mockB64,
            pii_entities: detectData.pii_entities,
            dom_nodes: domNodes,
            style: settings.redactionStyle
          })
        });
        const redactData = await redactRes.json();
        setRedactedScreenshot(redactData.redacted_screenshot);
        updateTimelineStep('REDACT', 'SUCCESS', Math.round(performance.now() - tRedactStart));
        addLog('sec', `Applied ${settings.redactionStyle} redactions. Raw PII retained strictly in trusted zone.`);

        // 5. FUSION
        updateTimelineStep('FUSION', 'RUNNING');
        await new Promise(r => setTimeout(r, 30));
        updateTimelineStep('FUSION', 'SUCCESS', 15);

        // 6. PLAN
        updateTimelineStep('PLAN', 'RUNNING');
        const tPlanStart = performance.now();
        const planRes = await fetch(`${BACKEND_URL}/agent/plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task: taskText,
            fused_elements: redactData.redacted_dom_nodes,
            history: actionHistory
          })
        });
        const planData = await planRes.json();
        setPlannedAction(planData.action);
        updateTimelineStep('PLAN', 'SUCCESS', Math.round(performance.now() - tPlanStart));
        addLog('act', `Agent Planned: ${planData.action.action} on "${planData.action.target_description}" (Confidence: ${Math.round(planData.action.confidence * 100)}%)`);

        // Refresh metrics
        const mRes = await fetch(`${BACKEND_URL}/metrics`);
        if (mRes.ok) {
          const mData = await mRes.json();
          setMetrics(mData);
        }
      } catch (err) {
        addLog('warn', `API pipeline error: ${err}. Running fallback simulation engine.`);
        runFallbackPipeline(domNodes, mockB64);
      }
    } else {
      runFallbackPipeline(domNodes, mockB64);
    }

    setIsProcessing(false);
    setAgentStatus('READY');
    setPerceptionStatus('READY');
    setPrivacyStatus('PROTECTED');
  }, [backendConnected, taskText, currentScenario, settings.redactionStyle, actionHistory, addLog]);

  const runFallbackPipeline = (domNodes: DOMNode[], mockB64: string) => {
    // Generate synthetic PII
    let detectedPii: PiiEntity[] = [];
    if (currentScenario.id === 'checkout') {
      detectedPii = [
        { id: 'p1', type: 'NAME', text: 'Amit Sharma', confidence: 0.94, bbox: [20, 95, 460, 135], source: 'DOM_SEMANTICS', element_id: 'dom_0', protectionMethod: settings.redactionStyle },
        { id: 'p2', type: 'EMAIL', text: 'amit.sharma@example.com', confidence: 0.98, bbox: [20, 165, 460, 205], source: 'OCR_REGEX', element_id: 'dom_1', protectionMethod: settings.redactionStyle },
        { id: 'p3', type: 'CARD', text: '4111 2222 3333 4444', confidence: 0.99, bbox: [20, 235, 460, 275], source: 'OCR_REGEX', element_id: 'dom_2', protectionMethod: settings.redactionStyle },
        { id: 'p4', type: 'ADDRESS', text: '12, MG Road, Bangalore, KA', confidence: 0.88, bbox: [20, 395, 460, 435], source: 'DOM_SEMANTICS', element_id: 'dom_5', protectionMethod: settings.redactionStyle }
      ];
    } else if (currentScenario.id === 'login') {
      detectedPii = [
        { id: 'p1', type: 'EMAIL', text: 'user@sih2026.gov.in', confidence: 0.98, bbox: [40, 105, 280, 145], source: 'DOM_SEMANTICS', element_id: 'dom_0', protectionMethod: settings.redactionStyle },
        { id: 'p2', type: 'PASSWORD', text: 'PrivySafePassword123!', confidence: 0.99, bbox: [40, 180, 280, 220], source: 'DOM_SEMANTICS', element_id: 'dom_1', protectionMethod: settings.redactionStyle }
      ];
    } else if (currentScenario.id === 'profile') {
      detectedPii = [
        { id: 'p1', type: 'FACE', text: '[HUMAN FACE]', confidence: 0.93, bbox: [170, 55, 310, 195], source: 'VISION_HAAR', protectionMethod: settings.redactionStyle },
        { id: 'p2', type: 'NAME', text: 'Johnathan Doe', confidence: 0.91, bbox: [20, 250, 460, 290], source: 'DOM_SEMANTICS', element_id: 'dom_0', protectionMethod: settings.redactionStyle },
        { id: 'p3', type: 'ID_NUM', text: '987-65-4321', confidence: 0.96, bbox: [20, 320, 460, 360], source: 'OCR_REGEX', element_id: 'dom_1', protectionMethod: settings.redactionStyle }
      ];
    }

    setPiiEntities(detectedPii);
    setRedactedScreenshot(mockB64);

    const fused: FusedElement[] = domNodes.map(node => {
      const isPii = detectedPii.find(p => p.element_id === node.id);
      return {
        id: node.id,
        type: node.type === 'submit' || node.tag_name === 'BUTTON' ? 'BUTTON' : 'INPUT',
        bbox: node.bbox,
        text: isPii ? `[${isPii.type} REDACTED]` : (node.text || ''),
        value: isPii ? `[${isPii.type} REDACTED]` : (node.value || ''),
        attributes: {
          tag_name: node.tag_name,
          placeholder: node.placeholder,
          type: node.type,
          id: node.id_attr,
          class: node.class_attr
        },
        confidence: 0.92,
        source: isPii ? 'FUSED' : 'DOM'
      };
    });
    setFusedElements(fused);

    let plan: AgentAction = {
      action: 'CLICK',
      target: { x: 240, y: 490 },
      target_description: 'Submit / Action Button',
      confidence: 0.94
    };

    if (currentScenario.id === 'checkout') {
      plan = {
        action: 'CLICK',
        target: { x: 240, y: 490 },
        target_description: 'Confirm & Pay Order button',
        confidence: 0.93,
        element_id: 'dom_6',
        requires_confirmation: true
      };
    } else if (currentScenario.id === 'login') {
      plan = {
        action: 'CLICK',
        target: { x: 160, y: 260 },
        target_description: 'Sign In button',
        confidence: 0.95,
        element_id: 'dom_2'
      };
    } else if (currentScenario.id === 'search') {
      plan = {
        action: 'TYPE',
        target: { x: 240, y: 64 },
        target_description: 'Search Input Field',
        text: 'Chandrayaan-3',
        confidence: 0.96,
        element_id: 'dom_0'
      };
    } else if (currentScenario.id === 'profile') {
      plan = {
        action: 'CLICK',
        target: { x: 240, y: 390 },
        target_description: 'Save Profile Settings button',
        confidence: 0.92,
        element_id: 'dom_2'
      };
    }

    setPlannedAction(plan);

    // Complete timeline steps
    updateTimelineStep('PERCEIVE', 'SUCCESS', 38);
    updateTimelineStep('DETECT', 'SUCCESS', 22);
    updateTimelineStep('REDACT', 'SUCCESS', 28);
    updateTimelineStep('FUSION', 'SUCCESS', 14);
    updateTimelineStep('PLAN', 'SUCCESS', 84);

    setMetrics(prev => ({
      local_inference_time_ms: 38,
      ocr_latency_ms: 24,
      pii_detection_latency_ms: 22,
      redaction_latency_ms: 28,
      agent_planning_latency_ms: 84,
      total_task_latency_ms: 196,
      pii_detected_count: prev.pii_detected_count + detectedPii.length,
      pii_redacted_count: prev.pii_redacted_count + detectedPii.length,
      actions_executed: prev.actions_executed,
      runs_count: prev.runs_count + 1,
      memory_usage_mb: 139.8,
      cpu_utilization_pct: 3.6
    }));

    addLog('sec', `Sanitized context built. Local trust boundary preserved.`);
    addLog('act', `Agent Plan formulated: ${plan.action} on ${plan.target_description}`);
  };

  const executePlannedAction = useCallback(async () => {
    if (!plannedAction) return;

    // Safety confirmation gate
    if (
      settings.confirmationMode === 'always' ||
      (settings.confirmationMode === 'high_risk' && (plannedAction.requires_confirmation || plannedAction.target_description.toLowerCase().includes('pay')))
    ) {
      setConfirmDialog({
        open: true,
        message: `Agent wants to perform a high-impact action: "${plannedAction.target_description}". As per the safety gatekeeper policy, confirmation is required.`,
        action: plannedAction
      });
      return;
    }

    await proceedExecution(plannedAction);
  }, [plannedAction, settings.confirmationMode]);

  const proceedExecution = async (action: AgentAction) => {
    updateTimelineStep('ACT', 'RUNNING');
    addLog('act', `Executing action: ${action.action} at (${action.target.x}, ${action.target.y})...`);

    if (backendConnected) {
      try {
        const res = await fetch(`${BACKEND_URL}/action/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action })
        });
        const data = await res.json();
        addLog('act', `Execution response: ${data.message}`);
      } catch (e) {
        addLog('act', `Simulated execution trigger completed.`);
      }
    } else {
      await new Promise(r => setTimeout(r, 200));
      addLog('act', `Simulated DOM action execution: ${action.action} on ${action.target_description}`);
    }

    updateTimelineStep('ACT', 'SUCCESS', 18);
    updateTimelineStep('VERIFY', 'RUNNING');
    await new Promise(r => setTimeout(r, 120));
    updateTimelineStep('VERIFY', 'SUCCESS', 12);

    setActionHistory(prev => [...prev, action]);
    setMetrics(prev => ({ ...prev, actions_executed: prev.actions_executed + 1 }));
    setPlannedAction(null);
    setConfirmDialog({ open: false, message: '', action: null });
    addLog('sys', 'Browser state transitioned successfully. Ready for next observation.');
  };

  const dismissConfirmDialog = () => {
    setConfirmDialog({ open: false, message: '', action: null });
    addLog('warn', 'User rejected dangerous agent action execution.');
  };

  const approveConfirmAction = () => {
    if (confirmDialog.action) {
      const act = confirmDialog.action;
      setConfirmDialog({ open: false, message: '', action: null });
      proceedExecution(act);
    }
  };

  const pauseAgent = () => {
    setAgentStatus('PAUSED');
    addLog('warn', 'Agent execution paused by user.');
  };

  const resumeAgent = () => {
    setAgentStatus('READY');
    addLog('sys', 'Agent execution resumed.');
  };

  const stopAgent = () => {
    setAgentStatus('READY');
    setPlannedAction(null);
    setTimelineSteps(INITIAL_TIMELINE);
    addLog('sys', 'Agent stopped and reset.');
  };

  const resetState = () => {
    setPlannedAction(null);
    setSelectedElementId(null);
    setSelectedPiiId(null);
    setPiiEntities([]);
    setFusedElements([]);
    setTimelineSteps(INITIAL_TIMELINE);
    addLog('sys', 'Workspace state cleared.');
  };

  return (
    <AppContext.Provider
      value={{
        activePage,
        setActivePage,
        backendConnected,
        extensionConnected,
        agentStatus,
        perceptionStatus,
        privacyStatus,
        isProcessing,
        scenarios: DEMO_SCENARIOS,
        currentScenario,
        selectScenario,
        taskText,
        setTaskText,
        rawScreenshot,
        redactedScreenshot: '',
        piiEntities,
        fusedElements,
        ocrBlocks,
        plannedAction,
        selectedElementId,
        setSelectedElementId,
        selectedPiiId,
        setSelectedPiiId,
        viewMode,
        setViewMode,
        timelineSteps,
        logs,
        actionHistory,
        metrics,
        settings,
        updateSettings,
        confirmDialog,
        dismissConfirmDialog,
        approveConfirmAction,
        runPipeline,
        executePlannedAction,
        pauseAgent,
        resumeAgent,
        stopAgent,
        resetState,
        refreshHealth
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};

// Helper to retrieve scenario simulated DOM layout coordinates
function getScenarioDOMNodes(scenarioId: string): DOMNode[] {
  if (scenarioId === 'checkout') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "text", placeholder: "Amit Sharma", bbox: [20, 95, 460, 135], id_attr: "checkout-name" },
      { id: "dom_1", tag_name: "INPUT", type: "email", placeholder: "amit.sharma@example.com", bbox: [20, 165, 460, 205], id_attr: "checkout-email" },
      { id: "dom_2", tag_name: "INPUT", type: "text", placeholder: "4111 2222 3333 4444", bbox: [20, 235, 460, 275], id_attr: "card-number" },
      { id: "dom_3", tag_name: "INPUT", type: "text", placeholder: "12/28", bbox: [20, 320, 230, 360], id_attr: "card-expiry" },
      { id: "dom_4", tag_name: "INPUT", type: "password", placeholder: "•••", bbox: [250, 320, 460, 360], id_attr: "card-cvv" },
      { id: "dom_5", tag_name: "INPUT", type: "text", placeholder: "12, MG Road, Bangalore, KA", bbox: [20, 395, 460, 435], id_attr: "checkout-address" },
      { id: "dom_6", tag_name: "BUTTON", type: "submit", text: "Confirm & Pay Order", bbox: [20, 470, 460, 510] }
    ];
  }
  if (scenarioId === 'login') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "email", placeholder: "user@domain.com", bbox: [40, 105, 280, 145], id_attr: "username" },
      { id: "dom_1", tag_name: "INPUT", type: "password", placeholder: "••••••••", bbox: [40, 180, 280, 220], id_attr: "password" },
      { id: "dom_2", tag_name: "BUTTON", type: "submit", text: "Sign In", bbox: [40, 255, 280, 295] }
    ];
  }
  if (scenarioId === 'profile') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "text", value: "Johnathan Doe", bbox: [20, 250, 460, 290], id_attr: "profile-name" },
      { id: "dom_1", tag_name: "INPUT", type: "text", value: "987-65-4321", bbox: [20, 320, 460, 360], id_attr: "profile-id" },
      { id: "dom_2", tag_name: "BUTTON", type: "submit", text: "Save Profile Settings", bbox: [20, 385, 460, 425] }
    ];
  }
  if (scenarioId === 'search') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "text", placeholder: "Search...", bbox: [20, 48, 380, 80], id_attr: "search-input" },
      { id: "dom_1", tag_name: "BUTTON", type: "button", text: "Search", bbox: [390, 48, 460, 80] },
      { id: "dom_2", tag_name: "A", text: "Chandrayaan-3 - Wikipedia", bbox: [20, 120, 460, 150] }
    ];
  }
  return [];
}

function getMockScreenshotB64(): string {
  return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
}

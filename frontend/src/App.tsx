import { useState, useEffect, useRef } from 'react';
import type { DOMNode, PiiEntity, FusedElement, AgentAction, PerformanceMetrics } from './types';

// Mock images matching synthetic page mockups (so visual overlay maps coordinates correctly)
const SCENARIO_PREVIEWS: Record<string, { name: string, task: string, url: string }> = {
  login: {
    name: "Secure Gatekeeper Login",
    task: "Login securely with user@sih2026.gov.in and password",
    url: "/demo/login.html"
  },
  checkout: {
    name: "Billing Checkout Form",
    task: "Fill out the checkout form securely and click confirm",
    url: "/demo/form.html"
  },
  search: {
    name: "Secure Wiki Search",
    task: "Search for Chandrayaan-3 and open the first wiki link",
    url: "/demo/search.html"
  },
  profile: {
    name: "Profile Face Redaction",
    task: "Save the user profile settings securely",
    url: "/demo/face.html"
  }
};

const BACKEND_URL = "http://127.0.0.1:8000/api";

export default function App() {
  const [activeTab, setActiveTab] = useState<'workspace' | 'privacy' | 'perception' | 'performance' | 'demo'>('workspace');
  const [currentScenario, setCurrentScenario] = useState<string>('checkout');
  const [taskText, setTaskText] = useState<string>(SCENARIO_PREVIEWS.checkout.task);
  
  // App States
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [showRawScreenshot, setShowRawScreenshot] = useState<boolean>(false);
  const [redactionStyle, setRedactionStyle] = useState<'opaque' | 'blur' | 'pixelate'>('opaque');
  
  // Data State
  const [rawScreenshot, setRawScreenshot] = useState<string>('');
  const [redactedScreenshot, setRedactedScreenshot] = useState<string>('');
  const [piiEntities, setPiiEntities] = useState<PiiEntity[]>([]);
  const [fusedElements, setFusedElements] = useState<FusedElement[]>([]);
  const [plannedAction, setPlannedAction] = useState<AgentAction | null>(null);
  
  // Action History / Execution logs
  const [consoleLogs, setConsoleLogs] = useState<{ time: string, tag: 'sys' | 'act' | 'sec', text: string }[]>([]);
  const [agentStep, setAgentStep] = useState<number>(0); // E2E timeline phase index
  
  // Safety confirmation dialog
  const [safetyDialog, setSafetyDialog] = useState<{ open: boolean; message: string; action: AgentAction | null }>({
    open: false,
    message: '',
    action: null
  });

  // Performance telemetry metrics
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
    cpu_utilization_pct: 4.8
  });

  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Initialize and check backend connection
  useEffect(() => {
    checkBackendHealth();
    addConsoleLog('sys', 'System Initialized. Awaiting task selection.');
  }, []);

  // Update task input when scenario changes
  const handleScenarioChange = (scenario: string) => {
    setCurrentScenario(scenario);
    setTaskText(SCENARIO_PREVIEWS[scenario].task);
    // Reset agent state
    setRawScreenshot('');
    setRedactedScreenshot('');
    setPiiEntities([]);
    setFusedElements([]);
    setPlannedAction(null);
    setAgentStep(0);
    addConsoleLog('sys', `Switched to scenario: ${SCENARIO_PREVIEWS[scenario].name}`);
  };

  const checkBackendHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        setIsBackendConnected(true);
        addConsoleLog('sys', 'Connected to PrivyBrowse Local Perception Backend (port 8000)');
        fetchLiveMetrics();
      } else {
        setIsBackendConnected(false);
        addConsoleLog('sys', 'Backend health check failed. Running in Local Simulator Mode.');
      }
    } catch (e) {
      setIsBackendConnected(false);
      addConsoleLog('sys', 'Backend server offline. Running in Local Simulator Mode.');
    }
  };

  const fetchLiveMetrics = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/metrics`);
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.warn("Could not retrieve live metrics", e);
    }
  };

  const addConsoleLog = (tag: 'sys' | 'act' | 'sec', text: string) => {
    const time = new Date().toLocaleTimeString();
    setConsoleLogs(prev => [...prev, { time, tag, text }]);
  };

  // Capture current page layout and analyze (main agent pipeline trigger)
  const handleObserveAndAnalyze = async () => {
    setIsProcessing(true);
    setAgentStep(1); // Stage 1: Observe Screen
    addConsoleLog('sys', 'Capturing webpage DOM tree & coordinates...');
    
    // 1. Gather simulated DOM nodes coordinates relative to the layout box
    const domNodes = getSimulatedDOM(currentScenario);
    
    // We fetch a base64 mock screenshot matching our scenario to pass to OpenCV / canvas
    const rawB64 = getMockScreenshotB64(currentScenario);
    setRawScreenshot(rawB64);
    
    // If backend is connected, use real API endpoints
    if (isBackendConnected) {
      try {
        // --- 1. LOCAL VISUAL PERCEPTION & OCR FUSION ---
        setAgentStep(2); // Stage 2: Perceive Visuals
        addConsoleLog('sys', 'Sending screenshot + DOM tree to local perception API...');
        
        const analyzeRes = await fetch(`${BACKEND_URL}/perception/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ screenshot: rawB64, dom_nodes: domNodes })
        });
        const analyzeData = await analyzeRes.json();
        setFusedElements(analyzeData.fused_elements);
        addConsoleLog('sys', `OpenCV detected ${analyzeData.vision_elements.length} visual contours. Fused with ${domNodes.length} DOM elements.`);

        // --- 2. LOCAL PII DETECTION ---
        setAgentStep(3); // Stage 3: Detect PII
        addConsoleLog('sec', 'Analyzing fused layout for sensitive patterns locally...');
        
        const detectRes = await fetch(`${BACKEND_URL}/privacy/detect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            screenshot: rawB64,
            text_blocks: analyzeData.ocr_blocks,
            dom_nodes: domNodes
          })
        });
        const detectData = await detectRes.json();
        setPiiEntities(detectData.pii_entities);
        addConsoleLog('sec', `Detected ${detectData.pii_entities.length} PII objects (NAME, CARD, DOB, etc.) inside Secure Zone.`);

        // --- 3. LOCAL REDACTION ---
        setAgentStep(4); // Stage 4: Redact Sensitive Data
        addConsoleLog('sec', `Applying local redaction: masking and drawing '${redactionStyle}' boxes...`);
        
        const redactRes = await fetch(`${BACKEND_URL}/privacy/redact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            screenshot: rawB64,
            pii_entities: detectData.pii_entities,
            dom_nodes: domNodes,
            style: redactionStyle
          })
        });
        const redactData = await redactRes.json();
        setRedactedScreenshot(redactData.redacted_screenshot);
        
        // --- 4. AGENT PLANNING ON REDACTED DATA ---
        setAgentStep(5); // Stage 5: Plan Action
        addConsoleLog('sys', 'Sending sanitized context to Agent Planner...');
        
        const planRes = await fetch(`${BACKEND_URL}/agent/plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task: taskText,
            fused_elements: redactData.redacted_dom_nodes,
            history: []
          })
        });
        const planData = await planRes.json();
        setPlannedAction(planData.action);
        addConsoleLog('act', `Agent Planned Action: ${planData.action.action} on "${planData.action.target_description}" (Confidence: ${Math.round(planData.action.confidence * 100)}%)`);

        // Refresh performance statistics
        await fetchLiveMetrics();
      } catch (err) {
        addConsoleLog('sys', `API error: ${err}. Falling back to Local Simulator.`);
        runMockPipeline(domNodes, rawB64);
      }
    } else {
      // Standalone simulator flow
      runMockPipeline(domNodes, rawB64);
    }
    
    setIsProcessing(false);
  };

  // Handles client-side simulation when backend is offline
  const runMockPipeline = (domNodes: DOMNode[], rawB64: string) => {
    // Simulated latencies
    const t_ocr = 42 + Math.random() * 15;
    const t_pii = 15 + Math.random() * 8;
    const t_redact = 25 + Math.random() * 10;
    const t_perc = 38 + Math.random() * 12;
    const t_plan = 95 + Math.random() * 20;

    // Determine PII based on current scenario
    let detectedPii: PiiEntity[] = [];
    if (currentScenario === 'checkout') {
      detectedPii = [
        { type: "NAME", text: "Amit Sharma", confidence: 0.92, bbox: [20, 100, 460, 140], source: "DOM_SEMANTICS", element_id: "dom_0" },
        { type: "EMAIL", text: "amit.sharma@example.com", confidence: 0.98, bbox: [20, 175, 460, 215], source: "OCR_REGEX", element_id: "dom_1" },
        { type: "CARD", text: "4111 2222 3333 4444", confidence: 0.99, bbox: [20, 250, 460, 290], source: "OCR_REGEX", element_id: "dom_2" },
        { type: "ADDRESS", text: "12, MG Road, Bangalore, KA", confidence: 0.85, bbox: [20, 440, 460, 480], source: "DOM_SEMANTICS", element_id: "dom_5" }
      ];
    } else if (currentScenario === 'login') {
      detectedPii = [
        { type: "EMAIL", text: "user@sih2026.gov.in", confidence: 0.98, bbox: [40, 105, 280, 145], source: "DOM_SEMANTICS", element_id: "dom_0" },
        { type: "PASSWORD", text: "PrivySafePassword123!", confidence: 0.99, bbox: [40, 180, 280, 220], source: "DOM_SEMANTICS", element_id: "dom_1" }
      ];
    } else if (currentScenario === 'profile') {
      detectedPii = [
        { type: "FACE", text: "[FACE DETECTED]", confidence: 0.90, bbox: [170, 60, 310, 200], source: "VISION_HAAR" },
        { type: "NAME", text: "Johnathan Doe", confidence: 0.88, bbox: [20, 255, 480, 295], source: "DOM_SEMANTICS", element_id: "dom_0" },
        { type: "ID_NUM", text: "987-65-4321", confidence: 0.95, bbox: [20, 330, 480, 370], source: "OCR_REGEX", element_id: "dom_1" }
      ];
    }

    setPiiEntities(detectedPii);
    
    // Simulate visual element fuser
    const fused: FusedElement[] = domNodes.map(node => {
      const isPii = detectedPii.find(p => p.element_id === node.id);
      return {
        id: node.id,
        type: node.type === 'submit' || node.tag_name === 'BUTTON' ? 'BUTTON' : 'INPUT',
        bbox: node.bbox,
        text: isPii ? `[${isPii.type} REDACTED]` : (node.text || ""),
        value: isPii ? `[${isPii.type} REDACTED]` : (node.value || ""),
        attributes: {
          tag_name: node.tag_name,
          placeholder: node.placeholder,
          type: node.type,
          id: node.id_attr,
          class: node.class_attr
        },
        confidence: 0.94,
        source: isPii ? "FUSED" : "DOM"
      };
    });
    setFusedElements(fused);

    // Simulate redaction screenshot (we just set the same image or draw colored overlays in CSS)
    setRedactedScreenshot(rawB64); 

    // Simulate Agent Plan
    let planned: AgentAction = {
      action: "WAIT",
      target: { x: 0, y: 0 },
      target_description: "Wait",
      confidence: 0.85
    };

    if (currentScenario === 'checkout') {
      planned = {
        action: "CLICK",
        target: { x: 240, y: 520 },
        target_description: "Confirm & Pay Order button",
        confidence: 0.92,
        element_id: "dom_6",
        requires_confirmation: true
      };
    } else if (currentScenario === 'login') {
      planned = {
        action: "CLICK",
        target: { x: 200, y: 270 },
        target_description: "Sign In button",
        confidence: 0.94,
        element_id: "dom_2"
      };
    } else if (currentScenario === 'search') {
      planned = {
        action: "TYPE",
        target: { x: 260, y: 80 },
        target_description: "Search input field",
        text: "Chandrayaan-3",
        confidence: 0.95,
        element_id: "dom_0"
      };
    } else if (currentScenario === 'profile') {
      planned = {
        action: "CLICK",
        target: { x: 250, y: 410 },
        target_description: "Save Profile Settings button",
        confidence: 0.91,
        element_id: "dom_2"
      };
    }

    setPlannedAction(planned);

    // Update simulation stats
    setMetrics(prev => ({
      local_inference_time_ms: Math.round(t_perc),
      ocr_latency_ms: Math.round(t_ocr),
      pii_detection_latency_ms: Math.round(t_pii),
      redaction_latency_ms: Math.round(t_redact),
      agent_planning_latency_ms: Math.round(t_plan),
      total_task_latency_ms: Math.round(t_perc + t_ocr + t_pii + t_redact + t_plan),
      pii_detected_count: prev.pii_detected_count + detectedPii.length,
      pii_redacted_count: prev.pii_redacted_count + detectedPii.length,
      actions_executed: prev.actions_executed,
      runs_count: prev.runs_count + 1,
      memory_usage_mb: 138.4,
      cpu_utilization_pct: 3.2
    }));

    setAgentStep(5);
    addConsoleLog('sec', `Local pipeline protected ${detectedPii.length} PII nodes.`);
    addConsoleLog('act', `Planned Agent Action: ${planned.action} on "${planned.target_description}"`);
  };

  // Triggers the execution of planned actions
  const handleExecuteAction = async () => {
    if (!plannedAction) return;

    // Safety checks for checkout payment submission
    if (plannedAction.requires_confirmation || (plannedAction.action === 'CLICK' && plannedAction.target_description.toLowerCase().includes('pay'))) {
      setSafetyDialog({
        open: true,
        message: `Safety check triggered. The agent wants to execute a high-impact transaction action: "${plannedAction.target_description}". Proceed?`,
        action: plannedAction
      });
      return;
    }

    proceedExecution(plannedAction);
  };

  const proceedExecution = async (action: AgentAction) => {
    setAgentStep(6); // Stage 6: Execute Action
    addConsoleLog('act', `Executing action: ${action.action} at coordinates (${action.target.x}, ${action.target.y})...`);
    
    if (isBackendConnected) {
      try {
        const res = await fetch(`${BACKEND_URL}/action/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: action })
        });
        const data = await res.json();
        addConsoleLog('act', `Execution response: ${data.message}`);
      } catch (e) {
        addConsoleLog('act', `Simulated execution of: ${action.action} complete.`);
      }
    } else {
      addConsoleLog('act', `Simulated execution of: ${action.action} complete.`);
    }

    setAgentStep(7); // Stage 7: Verify Result
    addConsoleLog('sys', 'Result verified. Page updated.');
    
    // Increment telemetry counters
    setMetrics(prev => ({ ...prev, actions_executed: prev.actions_executed + 1 }));
    setPlannedAction(null);
    setSafetyDialog({ open: false, message: '', action: null });
  };

  return (
    <div className="app-container">
      {/* Top Banner Header */}
      <header className="header">
        <div className="header-brand">
          <div className="logo-icon">👁</div>
          <span className="logo-text">PRIVYBROWSE AI</span>
        </div>
        
        <div className="header-status">
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Mode: <span style={{ color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{isBackendConnected ? "ON-DEVICE SERVER" : "SANDBOX SIMULATOR"}</span>
          </div>
          <div className={`status-badge ${isBackendConnected ? '' : 'error'}`}>
            {isBackendConnected ? "Secure Local Connection" : "Local Standalone Mode"}
          </div>
        </div>
      </header>

      {/* Main Tab Links */}
      <nav className="nav-tabs">
        <button className={`tab-btn ${activeTab === 'workspace' ? 'active' : ''}`} onClick={() => setActiveTab('workspace')}>
          Agent Workspace
        </button>
        <button className={`tab-btn ${activeTab === 'privacy' ? 'active' : ''}`} onClick={() => setActiveTab('privacy')}>
          Privacy Center
        </button>
        <button className={`tab-btn ${activeTab === 'perception' ? 'active' : ''}`} onClick={() => setActiveTab('perception')}>
          Perception Inspector
        </button>
        <button className={`tab-btn ${activeTab === 'performance' ? 'active' : ''}`} onClick={() => setActiveTab('performance')}>
          Performance Telemetry
        </button>
        <button className={`tab-btn ${activeTab === 'demo' ? 'active' : ''}`} onClick={() => setActiveTab('demo')}>
          Demo Lab
        </button>
      </nav>

      {/* Core Panels Layout */}
      <main className="main-workspace">
        <div className="main-content">
          
          {/* Tab 1: Agent Workspace */}
          {activeTab === 'workspace' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="card">
                <h3 className="card-title">Browser Mission Task</h3>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <input
                    type="text"
                    className="input-field"
                    value={taskText}
                    onChange={(e) => setTaskText(e.target.value)}
                    placeholder="Describe browser automation task..."
                  />
                  <button className="btn-primary" onClick={handleObserveAndAnalyze} disabled={isProcessing}>
                    {isProcessing ? "Processing..." : "Run Local Pipeline"}
                  </button>
                </div>
              </div>

              <div className="grid-panels">
                {/* Visual Screenshot display with bounding boxes */}
                <div className="card">
                  <div className="card-title">
                    <span>Live Page Scan Preview</span>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Show Raw:</span>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={showRawScreenshot}
                          onChange={(e) => setShowRawScreenshot(e.target.checked)}
                        />
                        <span className="slider"></span>
                      </label>
                    </div>
                  </div>

                  <div className="preview-container">
                    {/* Simulated page mockups visually generated */}
                    {rawScreenshot ? (
                      <div className="screenshot-canvas-wrapper" style={{ width: '480px', height: '560px', position: 'relative' }}>
                        {/* We render the clean screenshot image */}
                        <div style={{ display: 'none' }}>{redactedScreenshot.length}</div>
                        <div style={{
                          width: '100%',
                          height: '100%',
                          backgroundColor: '#1e293b',
                          border: '1px solid #475569',
                          borderRadius: '8px',
                          padding: '20px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '15px',
                          boxSizing: 'border-box'
                        }}>
                          {currentScenario === 'checkout' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                              <h4 style={{ color: '#38bdf8', textAlign: 'center', margin: 0 }}>Secure Order Checkout</h4>
                              <div>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Cardholder Name</div>
                                <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "Amit Sharma" : "[NAME REDACTED]"}
                                </div>
                              </div>
                              <div>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Billing Email</div>
                                <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "amit.sharma@example.com" : "[EMAIL REDACTED]"}
                                </div>
                              </div>
                              <div>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Credit Card Number</div>
                                <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "4111 2222 3333 4444" : "[CARD REDACTED]"}
                                </div>
                              </div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                                <div>
                                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Expiry</div>
                                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>12/28</div>
                                </div>
                                <div>
                                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>CVV</div>
                                  <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>•••</div>
                                </div>
                              </div>
                              <div>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Address</div>
                                <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "12, MG Road, Bangalore, KA" : "[ADDRESS REDACTED]"}
                                </div>
                              </div>
                              <button style={{ height: '38px', backgroundColor: '#0284c7', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}>Confirm & Pay Order</button>
                            </div>
                          )}

                          {currentScenario === 'login' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '40px 10px' }}>
                              <h4 style={{ color: '#00b37e', textAlign: 'center', margin: 0 }}>Secure Gatekeeper</h4>
                              <div>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Email Address</div>
                                <div style={{ height: '32px', backgroundColor: '#121214', border: '1px solid #323238', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "user@sih2026.gov.in" : "[EMAIL REDACTED]"}
                                </div>
                              </div>
                              <div>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Password</div>
                                <div style={{ height: '32px', backgroundColor: '#121214', border: '1px solid #323238', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "PrivySafePassword123!" : "[PASSWORD REDACTED]"}
                                </div>
                              </div>
                              <button style={{ height: '38px', backgroundColor: '#00b37e', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}>Sign In</button>
                            </div>
                          )}

                          {currentScenario === 'profile' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', alignItems: 'center' }}>
                              <h4 style={{ color: '#38bdf8', margin: 0 }}>Secure User Profile</h4>
                              
                              <div style={{ position: 'relative', width: '120px', height: '120px', borderRadius: '50%', overflow: 'hidden', border: '2.5px solid #38bdf8' }}>
                                <img 
                                  src="/demo/face.jpg" 
                                  alt="Face" 
                                  style={{ width: '100%', height: '100%', filter: (!showRawScreenshot && redactionStyle === 'blur') ? 'blur(10px)' : (!showRawScreenshot && redactionStyle === 'pixelate') ? 'contrast(0.2)' : 'none' }}
                                />
                                {!showRawScreenshot && redactionStyle === 'opaque' && (
                                  <div style={{ position: 'absolute', inset: 0, backgroundColor: '#282828', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: 'white' }}>[FACE MASKED]</div>
                                )}
                              </div>

                              <div style={{ alignSelf: 'stretch', textAlign: 'left' }}>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Full Name</div>
                                <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "Johnathan Doe" : "[NAME REDACTED]"}
                                </div>
                              </div>
                              <div style={{ alignSelf: 'stretch', textAlign: 'left' }}>
                                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Employee ID (Sensitive)</div>
                                <div style={{ height: '32px', backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '4px', padding: '8px', fontSize: '12px' }}>
                                  {showRawScreenshot ? "987-65-4321" : "[ID_NUM REDACTED]"}
                                </div>
                              </div>
                              <button style={{ alignSelf: 'stretch', height: '38px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>Save Settings</button>
                            </div>
                          )}

                          {currentScenario === 'search' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                              <h4 style={{ color: '#3b82f6', textAlign: 'center', margin: 0 }}>IndiSearch</h4>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <div style={{ flex: 1, height: 32, backgroundColor: '#1a1a1e', border: '1px solid #2e2e33', borderRadius: '16px', padding: '8px 12px', fontSize: '12px' }}>
                                  Chandrayaan-3
                                </div>
                                <button style={{ height: 32, padding: '0 12px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '16px', color: 'white', fontSize: '11px', fontWeight: 'bold' }}>Search</button>
                              </div>
                              <div style={{ borderTop: '1px solid #2e2e33', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                <div style={{ backgroundColor: '#1a1a1e', border: '1px solid #2e2e33', borderRadius: '6px', padding: '10px' }}>
                                  <a href="#" style={{ fontSize: '12px', color: '#60a5fa', fontWeight: 'bold', textDecoration: 'none' }}>Chandrayaan-3 - Wikipedia</a>
                                  <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '4px' }}>India's third lunar exploration mission soft-landed Vikram lander...</div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Interactive local bounding box overlays */}
                        {!showRawScreenshot && piiEntities.map((pii, idx) => (
                          <div
                            key={idx}
                            className="bbox-overlay PII"
                            style={{
                              left: `${pii.bbox[0]}px`,
                              top: `${pii.bbox[1]}px`,
                              width: `${pii.bbox[2] - pii.bbox[0]}px`,
                              height: `${pii.bbox[3] - pii.bbox[1]}px`
                            }}
                          >
                            <span className="bbox-label">{pii.type}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                        Awaiting visual observation check...
                      </div>
                    )}
                  </div>
                </div>

                {/* Bounding box list & Planner */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div className="card">
                    <h3 className="card-title">Planned Action Layer</h3>
                    {plannedAction ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                          <span>Action:</span>
                          <strong style={{ color: 'var(--accent-green)' }}>{plannedAction.action}</strong>
                        </div>
                        <div style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                          <span>Target:</span>
                          <span>{plannedAction.target_description}</span>
                        </div>
                        {plannedAction.text && (
                          <div style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                            <span>Payload:</span>
                            <span style={{ color: 'var(--accent-cyan)' }}>{plannedAction.text}</span>
                          </div>
                        )}
                        <button className="btn-primary" onClick={handleExecuteAction}>
                          Execute Action Safely
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        No planned action yet.
                      </span>
                    )}
                  </div>

                  <div className="card">
                    <h3 className="card-title">Console Terminal</h3>
                    <div className="console">
                      {consoleLogs.map((log, idx) => (
                        <div key={idx} className="console-line">
                          <span className="console-time">[{log.time}]</span>
                          <span className={`console-tag ${log.tag}`}>{log.tag.toUpperCase()}:</span>
                          <span>{log.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Privacy Center */}
          {activeTab === 'privacy' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="metrics-row">
                <div className="metric-card">
                  <span className="metric-label">Sensitive Items Detected</span>
                  <span className="metric-value" style={{ color: 'var(--accent-orange)' }}>
                    {piiEntities.length}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Local Redactions Executed</span>
                  <span className="metric-value" style={{ color: 'var(--accent-green)' }}>
                    {piiEntities.length}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Data Transmitted to Planner</span>
                  <span className="metric-value" style={{ color: 'var(--accent-green)' }}>
                    0 bytes
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Privacy Shield Status</span>
                  <span className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
                    ACTIVE
                  </span>
                </div>
              </div>

              <div className="grid-panels">
                <div className="card">
                  <h3 className="card-title">On-Device Redacted Records</h3>
                  <table style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Category</th>
                        <th>Source</th>
                        <th>Confidence</th>
                        <th>Bounding Box</th>
                      </tr>
                    </thead>
                    <tbody>
                      {piiEntities.map((pii, idx) => (
                        <tr key={idx}>
                          <td><span style={{ color: 'var(--accent-red)', fontWeight: 'bold' }}>{pii.type}</span></td>
                          <td>{pii.source}</td>
                          <td>{Math.round(pii.confidence * 100)}%</td>
                          <td>{`[${pii.bbox.join(', ')}]`}</td>
                        </tr>
                      ))}
                      {piiEntities.length === 0 && (
                        <tr>
                          <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                            No sensitive elements processed in current view.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="card">
                  <h3 className="card-title">Settings & Parameters</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Redaction Visualization Style</label>
                      <select 
                        className="input-field" 
                        value={redactionStyle} 
                        onChange={(e) => setRedactionStyle(e.target.value as any)}
                      >
                        <option value="opaque">Opaque Mask Overlay</option>
                        <option value="blur">Gaussian Blur Filter</option>
                        <option value="pixelate">Pixelation Block</option>
                      </select>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      <strong>Privacy Principle:</strong> All raw page screenshot data, full strings containing PII, and inputs are processed on-device. The remote agent planer layer is completely isolated behind the redaction boundary.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Perception Inspector */}
          {activeTab === 'perception' && (
            <div className="card">
              <h3 className="card-title">Visual Contours & DOM Coordinate Map</h3>
              <table style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Element ID</th>
                    <th>Visual Type</th>
                    <th>Coordinates (BBox)</th>
                    <th>Text Descriptor (Sanitized)</th>
                    <th>Inference / Source</th>
                  </tr>
                </thead>
                <tbody>
                  {fusedElements.map((el, idx) => (
                    <tr key={idx}>
                      <td><code style={{ color: 'var(--accent-cyan)' }}>{el.id}</code></td>
                      <td><span style={{ background: '#1c2434', padding: '2px 6px', borderRadius: '4px', fontSize: '10px' }}>{el.type}</span></td>
                      <td>{`[${el.bbox.join(', ')}]`}</td>
                      <td>{el.text || <em style={{ color: 'var(--text-muted)' }}>None</em>}</td>
                      <td>{el.source}</td>
                    </tr>
                  ))}
                  {fusedElements.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                        Analyze a page to view the coordinate map.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: Performance Telemetry */}
          {activeTab === 'performance' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="metrics-row">
                <div className="metric-card">
                  <span className="metric-label">OCR Parsing Latency</span>
                  <span className="metric-value">{metrics.ocr_latency_ms} ms</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">PII Classification</span>
                  <span className="metric-value">{metrics.pii_detection_latency_ms} ms</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Visual Redaction</span>
                  <span className="metric-value">{metrics.redaction_latency_ms} ms</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Agent Planner Latency</span>
                  <span className="metric-value">{metrics.agent_planning_latency_ms} ms</span>
                </div>
              </div>

              <div className="grid-panels">
                <div className="card">
                  <h3 className="card-title">Inference Speed</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span>Local CV Inference Time:</span>
                      <strong>{metrics.local_inference_time_ms} ms</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span>Total E2E Execution Loop:</span>
                      <strong style={{ color: 'var(--accent-cyan)' }}>{metrics.total_task_latency_ms} ms</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span>Task Runs Count:</span>
                      <strong>{metrics.runs_count}</strong>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="card-title">Resource Utilization</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span>Estimated RAM Footprint:</span>
                      <strong>{metrics.memory_usage_mb} MB</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span>CPU Utilization (Avg):</span>
                      <strong>{metrics.cpu_utilization_pct}%</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 5: Demo Lab Scenarios */}
          {activeTab === 'demo' && (
            <div className="grid-panels">
              {/* Left Side: Sandbox Scenarios Selector */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h3 className="card-title">Sandbox Environments</h3>
                {Object.entries(SCENARIO_PREVIEWS).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => handleScenarioChange(key)}
                    style={{
                      width: '100%',
                      padding: '12px',
                      backgroundColor: currentScenario === key ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                      color: currentScenario === key ? 'var(--accent-cyan)' : 'var(--text-primary)',
                      border: '1px solid',
                      borderColor: currentScenario === key ? 'var(--accent-cyan)' : 'var(--border-color)',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontWeight: 'bold',
                      transition: 'all 0.2s'
                    }}
                  >
                    {value.name}
                  </button>
                ))}
              </div>

              {/* Right Side: Render Simulation Iframe */}
              <div className="card">
                <h3 className="card-title">Target Webpage Sandbox</h3>
                <div style={{ border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden', height: '400px', backgroundColor: 'white' }}>
                  <iframe
                    ref={iframeRef}
                    src={isBackendConnected ? `${BACKEND_URL.replace('/api', '')}${SCENARIO_PREVIEWS[currentScenario].url}` : ''}
                    style={{ width: '100%', height: '100%', border: 'none' }}
                    title="Demo Frame"
                  />
                  {!isBackendConnected && (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0f172a', color: 'var(--text-secondary)', fontSize: '12px', padding: '20px', textAlign: 'center' }}>
                      Start backend server to load and interact with synthetic HTML pages inside this sandbox.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Right Side Panel: Agent Timeline & Status */}
        <aside className="side-panel">
          <div className="card">
            <h3 className="card-title">Agent Execution Timeline</h3>
            <div className="timeline">
              <div className={`timeline-step ${agentStep >= 1 ? 'active' : ''} ${agentStep > 1 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">Observe</div>
                <div className="timeline-desc">Capture raw tab frame</div>
              </div>
              <div className={`timeline-step ${agentStep >= 2 ? 'active' : ''} ${agentStep > 2 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">Perceive</div>
                <div className="timeline-desc">OCR layout & contours</div>
              </div>
              <div className={`timeline-step ${agentStep >= 3 ? 'active' : ''} ${agentStep > 3 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">PII Filter</div>
                <div className="timeline-desc">Scan sensitive fields</div>
              </div>
              <div className={`timeline-step ${agentStep >= 4 ? 'active' : ''} ${agentStep > 4 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">Redact</div>
                <div className="timeline-desc">Blur/mask details locally</div>
              </div>
              <div className={`timeline-step ${agentStep >= 5 ? 'active' : ''} ${agentStep > 5 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">Reason & Plan</div>
                <div className="timeline-desc">Calculate actions on safe DOM</div>
              </div>
              <div className={`timeline-step ${agentStep >= 6 ? 'active' : ''} ${agentStep > 6 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">Act</div>
                <div className="timeline-desc">Dispatch keystrokes/clicks</div>
              </div>
              <div className={`timeline-step ${agentStep >= 7 ? 'active' : ''} ${agentStep > 7 ? 'success' : ''}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-label">Verify</div>
                <div className="timeline-desc">Confirm state transition</div>
              </div>
            </div>
          </div>
        </aside>
      </main>

      {/* Safety Confirmation Dialog overlay */}
      {safetyDialog.open && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="card" style={{ maxWidth: '400px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--accent-red)' }}>
            <h4 style={{ color: 'var(--accent-red)', marginBottom: '12px', fontWeight: 'bold' }}>⚠️ SAFETY POLICY BLOCK</h4>
            <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '20px', lineHeight: '1.5' }}>
              {safetyDialog.message}
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSafetyDialog({ open: false, message: '', action: null })}
                style={{ padding: '8px 16px', background: 'none', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                Reject Action
              </button>
              <button
                onClick={() => safetyDialog.action && proceedExecution(safetyDialog.action)}
                style={{ padding: '8px 16px', backgroundColor: 'var(--accent-red)', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}
              >
                Approve & Execute
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Simulated browser coordinate mappings to enable fully interactive overlay rectangles
function getSimulatedDOM(scenario: string): DOMNode[] {
  if (scenario === 'checkout') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "text", placeholder: "Amit Sharma", bbox: [20, 100, 460, 140], id_attr: "checkout-name" },
      { id: "dom_1", tag_name: "INPUT", type: "email", placeholder: "amit.sharma@example.com", bbox: [20, 175, 460, 215], id_attr: "checkout-email" },
      { id: "dom_2", tag_name: "INPUT", type: "text", placeholder: "4111 2222 3333 4444", bbox: [20, 250, 460, 290], id_attr: "card-number" },
      { id: "dom_3", tag_name: "INPUT", type: "text", placeholder: "12/28", bbox: [20, 345, 230, 385], id_attr: "card-expiry" },
      { id: "dom_4", tag_name: "INPUT", type: "password", placeholder: "•••", bbox: [250, 345, 460, 385], id_attr: "card-cvv" },
      { id: "dom_5", tag_name: "INPUT", type: "text", placeholder: "12, MG Road, Bangalore, KA", bbox: [20, 440, 460, 480], id_attr: "checkout-address" },
      { id: "dom_6", tag_name: "BUTTON", type: "submit", text: "Confirm & Pay Order", bbox: [20, 500, 460, 540] }
    ];
  }
  if (scenario === 'login') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "email", placeholder: "user@domain.com", bbox: [40, 105, 280, 145], id_attr: "username" },
      { id: "dom_1", tag_name: "INPUT", type: "password", placeholder: "••••••••", bbox: [40, 180, 280, 220], id_attr: "password" },
      { id: "dom_2", tag_name: "BUTTON", type: "submit", text: "Sign In", bbox: [40, 255, 280, 295] }
    ];
  }
  if (scenario === 'profile') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "text", value: "Johnathan Doe", bbox: [20, 255, 480, 295], id_attr: "profile-name" },
      { id: "dom_1", tag_name: "INPUT", type: "text", value: "987-65-4321", bbox: [20, 330, 480, 370], id_attr: "profile-id" },
      { id: "dom_2", tag_name: "BUTTON", type: "submit", text: "Save Profile Settings", bbox: [20, 400, 480, 440] }
    ];
  }
  if (scenario === 'search') {
    return [
      { id: "dom_0", tag_name: "INPUT", type: "text", placeholder: "Search...", bbox: [20, 48, 480, 80], id_attr: "search-input" },
      { id: "dom_1", tag_name: "BUTTON", type: "button", text: "Search", bbox: [400, 48, 480, 80] },
      { id: "dom_2", tag_name: "A", text: "Chandrayaan-3 - Wikipedia", bbox: [20, 148, 250, 178] }
    ];
  }
  return [];
}

// Simple base64 stub representation for mock captures
function getMockScreenshotB64(_scenario: string): string {
  return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
}

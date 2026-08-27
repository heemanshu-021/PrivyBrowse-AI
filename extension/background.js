const BACKEND_URL = "http://127.0.0.1:8000/api";

// Listen for commands from popups or context scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "CAPTURE_AND_PROCESS") {
    captureAndProcess(message.task)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep channel open for async response
  }

  if (message.type === "EXECUTE_ACTION") {
    executeActionOnTab(message.action)
      .then(result => sendResponse({ success: true, result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

async function captureAndProcess(task) {
  // 1. Get current active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) throw new Error("No active tab found");

  // 2. Request DOM elements parsing from Content Script
  let domNodes = [];
  try {
    domNodes = await chrome.tabs.sendMessage(tab.id, { type: "PARSE_DOM" });
  } catch (e) {
    console.warn("Content script not responding. Attempting injection...", e);
    // Inject content script if not active
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
    // Try again
    domNodes = await chrome.tabs.sendMessage(tab.id, { type: "PARSE_DOM" });
  }

  // 3. Capture screenshot of the tab
  const screenshotBase64 = await chrome.tabs.captureVisibleTab(null, { format: "png" });

  // 4. Send to Backend Local Perception Engine
  const analyzeRes = await fetch(`${BACKEND_URL}/perception/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      screenshot: screenshotBase64,
      dom_nodes: domNodes
    })
  });
  if (!analyzeRes.ok) throw new Error("Backend perception analysis failed.");
  const analyzeData = await analyzeRes.json();

  // 5. Send to Privacy Engine to Detect PII
  const detectRes = await fetch(`${BACKEND_URL}/privacy/detect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      screenshot: screenshotBase64,
      text_blocks: analyzeData.ocr_blocks,
      dom_nodes: domNodes
    })
  });
  if (!detectRes.ok) throw new Error("PII detection failed.");
  const detectData = await detectRes.json();

  // 6. Send to Redactor to sanitize screenshot + DOM nodes
  const redactRes = await fetch(`${BACKEND_URL}/privacy/redact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      screenshot: screenshotBase64,
      pii_entities: detectData.pii_entities,
      dom_nodes: domNodes,
      style: "opaque"
    })
  });
  if (!redactRes.ok) throw new Error("Redaction failed.");
  const redactData = await redactRes.json();

  // 7. Plan the agent action based on redacted context
  let planData = { action: { action: "WAIT", target_description: "Failed to plan" } };
  if (task) {
    const planRes = await fetch(`${BACKEND_URL}/agent/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task: task,
        fused_elements: analyzeData.fused_elements,
        history: []
      })
    });
    if (planRes.ok) {
      planData = await planRes.json();
    }
  }

  // Combine local results to present to UI (trust boundary preserved)
  return {
    rawScreenshot: screenshotBase64,
    redactedScreenshot: redactData.redacted_screenshot,
    piiEntities: detectData.pii_entities,
    fusedElements: analyzeData.fused_elements,
    plannedAction: planData.action,
    rawDomCount: domNodes.length
  };
}

async function executeActionOnTab(action) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) throw new Error("No active tab");

  // Send action execution parameters to content script
  return await chrome.tabs.sendMessage(tab.id, {
    type: "EXECUTE_DOM_ACTION",
    action: action
  });
}

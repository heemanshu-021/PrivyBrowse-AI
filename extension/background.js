// PrivyBrowse AI - Manifest V3 Background Service Worker
const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000/api";

const RESTRICTED_PREFIXES = [
  "chrome://",
  "chrome-extension://",
  "devtools://",
  "edge://",
  "about:",
  "view-source:",
  "https://chromewebstore.google.com"
];

// Action polling state
let pollingIntervalId = null;
const POLL_INTERVAL_MS = 500;

function isRestrictedUrl(url) {
  if (!url) return true;
  return RESTRICTED_PREFIXES.some(prefix => url.startsWith(prefix));
}

chrome.runtime.onInstalled.addListener(() => {
  console.log("[PrivyBrowse AI] Service Worker successfully installed.");
  startPolling();
});

// Also start polling when the service worker wakes up
startPolling();

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "CONNECTION_STATUS") {
    checkHealth()
      .then(status => sendResponse({ success: true, ...status }))
      .catch(err => sendResponse({ success: false, connected: false, error: err.message }));
    return true; // Async channel
  }

  if (message.type === "CAPTURE_SCREENSHOT") {
    captureActiveTab()
      .then(dataUrl => sendResponse({ success: true, dataUrl }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === "ANALYZE_PAGE") {
    orchestrateAnalysis()
      .then(context => sendResponse({ success: true, context }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === "EXECUTE_ACTION") {
    dispatchAction(message.payload)
      .then(result => sendResponse({ success: true, result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === "START_POLLING") {
    startPolling();
    sendResponse({ success: true, message: "Polling started" });
    return false;
  }

  if (message.type === "STOP_POLLING") {
    stopPolling();
    sendResponse({ success: true, message: "Polling stopped" });
    return false;
  }
});

async function checkHealth() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);
  try {
    const res = await fetch(`${DEFAULT_BACKEND_URL}/health`, { method: "GET", signal: controller.signal });
    clearTimeout(timeoutId);
    return { connected: res.ok, status: res.ok ? "ONLINE" : "ERROR" };
  } catch {
    clearTimeout(timeoutId);
    return { connected: false, status: "OFFLINE" };
  }
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || tab.id === undefined) {
    throw new Error("No active browser tab found.");
  }
  if (tab.url && isRestrictedUrl(tab.url)) {
    throw new Error("This page is restricted (e.g. chrome://, Web Store) and cannot be analyzed by extensions.");
  }
  return tab;
}

async function captureActiveTab() {
  await getActiveTab();
  try {
    return await chrome.tabs.captureVisibleTab(chrome.windows.WINDOW_ID_CURRENT, { format: "png" });
  } catch (err) {
    throw new Error(`Screenshot capture failed: ${err.message || "Permission denied"}`);
  }
}

async function orchestrateAnalysis() {
  const tab = await getActiveTab();
  const tabId = tab.id;

  // 1. Capture viewport screenshot
  let screenshotDataUrl = "";
  try {
    screenshotDataUrl = await chrome.tabs.captureVisibleTab(chrome.windows.WINDOW_ID_CURRENT, { format: "png" });
  } catch (e) {
    console.warn("[PrivyBrowse] Screenshot capture note:", e);
  }

  // 2. Query DOM extraction from content script
  let domResponse = null;
  try {
    domResponse = await chrome.tabs.sendMessage(tabId, { type: "GET_PAGE_CONTEXT" });
  } catch {
    // Incase tab was loaded before extension
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ["content.js"]
      });
      domResponse = await chrome.tabs.sendMessage(tabId, { type: "GET_PAGE_CONTEXT" });
    } catch (e) {
      throw new Error(`Content script communication failure: ${e.message}`);
    }
  }

  if (!domResponse || !domResponse.success) {
    throw new Error(domResponse?.error || "Failed to extract DOM elements.");
  }

  const { page, elements } = domResponse.data;

  // 3. Assemble Unified Browser Context
  const browserContext = {
    page: {
      url: tab.url || page.url,
      hostname: page.hostname,
      title: tab.title || page.title,
      viewport: page.viewport,
      devicePixelRatio: page.devicePixelRatio,
      timestamp: new Date().toISOString()
    },
    screenshot: {
      available: !!screenshotDataUrl,
      dataUrl: screenshotDataUrl,
      timestamp: new Date().toISOString()
    },
    elements: elements || [],
    capture: {
      timestamp: new Date().toISOString(),
      source: "chrome-extension",
      elementCount: (elements || []).length
    }
  };

  // 4. Send to Local Backend Daemon
  try {
    const res = await fetch(`${DEFAULT_BACKEND_URL}/browser/context`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(browserContext)
    });
    if (!res.ok) {
      console.warn("[PrivyBrowse] Backend returned non-200 for browser context sync.");
    }
  } catch (err) {
    console.warn("[PrivyBrowse] Local backend daemon offline for context sync:", err);
  }

  return browserContext;
}

async function dispatchAction(actionPayload) {
  const tab = await getActiveTab();
  return await chrome.tabs.sendMessage(tab.id, {
    type: "EXECUTE_ACTION",
    payload: actionPayload
  });
}

// --- BROWSER ACTION BRIDGE POLLING ---

/**
 * Polls the backend for pending actions and dispatches them to the active tab's content script.
 * This is the core communication loop for the real browser action execution bridge.
 *
 * Flow:
 *   1. GET /api/action/pending → retrieve next queued action
 *   2. Forward action to content.js via chrome.tabs.sendMessage
 *   3. POST /api/action/ack → report execution result back to backend
 */
async function pollPendingActions() {
  try {
    const response = await fetch(`${DEFAULT_BACKEND_URL}/action/pending`, {
      method: "GET",
      headers: { "Accept": "application/json" }
    });

    if (!response.ok) {
      return; // Backend unavailable, skip this poll cycle
    }

    const data = await response.json();

    if (!data.has_action || !data.action) {
      return; // No pending actions
    }

    const action = data.action;
    const actionId = action.action_id;
    const actionType = action.action_type;

    console.log(`[PrivyBrowse Bridge] Received action: ${actionType} (${actionId})`);

    // Get active tab for execution
    let tab;
    try {
      tab = await getActiveTab();
    } catch (tabErr) {
      // No valid tab available — report failure
      await postAcknowledgement(actionId, {
        success: false,
        action_type: actionType,
        error: tabErr.message,
        error_code: "NO_ACTIVE_TAB"
      });
      return;
    }

    // Build the payload for content.js executeSafeAction()
    const contentPayload = {
      action: actionType,
      action_id: actionId,
      target: {
        elementId: action.target_id,
        x: action.target?.x,
        y: action.target?.y,
        description: action.description,
        selector: action.metadata?.selector
      },
      text: action.text,
      key: action.key,
      scrollDelta: action.scroll_delta
    };

    // Send to content script
    let result;
    try {
      result = await chrome.tabs.sendMessage(tab.id, {
        type: "EXECUTE_ACTION",
        payload: contentPayload
      });
    } catch (msgErr) {
      // Content script not loaded — try injecting it first
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"]
        });
        result = await chrome.tabs.sendMessage(tab.id, {
          type: "EXECUTE_ACTION",
          payload: contentPayload
        });
      } catch (retryErr) {
        await postAcknowledgement(actionId, {
          success: false,
          action_type: actionType,
          error: `Content script unavailable: ${retryErr.message}`,
          error_code: "CONTENT_SCRIPT_UNAVAILABLE"
        });
        return;
      }
    }

    // Post acknowledgement back to backend
    const ackPayload = {
      action_id: actionId,
      success: result?.success || result?.result?.success || false,
      action_type: actionType,
      target_id: action.target_id,
      error: result?.error || result?.result?.error || null,
      error_code: result?.result?.error || null,
      execution_timestamp: new Date().toISOString(),
      detail: result?.result?.detail || result?.detail || null,
      metadata: result?.result || result || {}
    };

    await postAcknowledgement(actionId, ackPayload);

    console.log(`[PrivyBrowse Bridge] Action ${actionId} completed: ${ackPayload.success ? 'SUCCESS' : 'FAILED'}`);

  } catch (err) {
    // Silently handle polling errors (backend offline, network issues)
    // The bridge will naturally recover on the next poll cycle
    console.debug("[PrivyBrowse Bridge] Poll cycle error:", err.message);
  }
}

/**
 * Posts an action acknowledgement to the backend bridge.
 */
async function postAcknowledgement(actionId, payload) {
  try {
    const body = {
      action_id: actionId,
      success: payload.success,
      action_type: payload.action_type || null,
      target_id: payload.target_id || null,
      error: payload.error || null,
      error_code: payload.error_code || null,
      execution_timestamp: payload.execution_timestamp || new Date().toISOString(),
      detail: payload.detail || null,
      metadata: payload.metadata || {}
    };

    await fetch(`${DEFAULT_BACKEND_URL}/action/ack`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
  } catch (ackErr) {
    console.warn(`[PrivyBrowse Bridge] Failed to post ack for ${actionId}:`, ackErr.message);
  }
}

/**
 * Starts the action polling loop.
 */
function startPolling() {
  if (pollingIntervalId !== null) {
    return; // Already polling
  }
  pollingIntervalId = setInterval(pollPendingActions, POLL_INTERVAL_MS);
  console.log("[PrivyBrowse Bridge] Action polling started (every " + POLL_INTERVAL_MS + "ms)");
}

/**
 * Stops the action polling loop.
 */
function stopPolling() {
  if (pollingIntervalId !== null) {
    clearInterval(pollingIntervalId);
    pollingIntervalId = null;
    console.log("[PrivyBrowse Bridge] Action polling stopped");
  }
}

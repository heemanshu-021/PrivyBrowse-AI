// PrivyBrowse AI — Production-Grade Manifest V3 Background Service Worker
// Reliable Browser Context, Navigation Lifecycle, Heartbeat & Action Execution Bridge

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

// -------------------------------------------------------------
// 1. EXTENSION CONNECTION STATE MACHINE
// -------------------------------------------------------------

const ExtensionState = Object.freeze({
  INITIALIZING: "INITIALIZING",
  READY: "READY",
  CONNECTING: "CONNECTING",
  CONNECTED: "CONNECTED",
  DISCONNECTED: "DISCONNECTED",
  RECONNECTING: "RECONNECTING",
  DEGRADED: "DEGRADED",
  STOPPING: "STOPPING",
  ERROR: "ERROR"
});

let currentState = ExtensionState.INITIALIZING;
let stateListeners = [];

function setExtensionState(newState, reason = "") {
  if (currentState !== newState) {
    const prevState = currentState;
    currentState = newState;
    console.log(`[PrivyBrowse State] ${prevState} -> ${newState}${reason ? ` (${reason})` : ""}`);

    // Persist to storage for service worker restarts
    chrome.storage?.local?.set({
      "privybrowse_extension_state": newState,
      "privybrowse_last_state_change": new Date().toISOString()
    }).catch(() => {});

    stateListeners.forEach(listener => {
      try { listener(newState, prevState, reason); } catch (e) {}
    });

    // Notify backend of extension state change if not disconnecting
    if (newState === ExtensionState.CONNECTED || newState === ExtensionState.DEGRADED) {
      notifyBrowserEvent("EXTENSION_STATE_CHANGED", {
        previousState: prevState,
        currentState: newState,
        reason
      });
    }
  }
}

function getExtensionState() {
  return currentState;
}

// -------------------------------------------------------------
// 2. TIMEOUTS, BACKOFF & ACTION POLLING STATE
// -------------------------------------------------------------

let pollingIntervalId = null;
let heartbeatIntervalId = null;

const BASE_POLL_INTERVAL_MS = 500;
const MAX_POLL_INTERVAL_MS = 10000;
const HEARTBEAT_INTERVAL_MS = 5000;
const FETCH_TIMEOUT_MS = 3000;

let currentPollInterval = BASE_POLL_INTERVAL_MS;
let consecutiveConnectionFailures = 0;
let isPollingActive = false;

// Action Deduplication Cache (60 second TTL)
const executedActionIds = new Map(); // action_id -> timestamp

function pruneActionCache() {
  const now = Date.now();
  for (const [id, ts] of executedActionIds.entries()) {
    if (now - ts > 60000) {
      executedActionIds.delete(id);
    }
  }
}

// -------------------------------------------------------------
// 3. SECURITY & URL VALIDATION
// -------------------------------------------------------------

function isRestrictedUrl(url) {
  if (!url) return true;
  return RESTRICTED_PREFIXES.some(prefix => url.startsWith(prefix));
}

function isTrustedMessageSender(sender) {
  // Only accept messages originating from the extension itself (popup or content scripts in tabs)
  if (!sender) return false;
  return sender.id === chrome.runtime.id;
}

// -------------------------------------------------------------
// 4. STRUCTURED MESSAGE PROTOCOL & VALIDATION
// -------------------------------------------------------------

function validateMessage(message) {
  if (!message || typeof message !== "object") {
    return { valid: false, reason: "Message must be a valid object" };
  }
  if (!message.type || typeof message.type !== "string") {
    return { valid: false, reason: "Message must include a valid 'type' string" };
  }
  return { valid: true };
}

// -------------------------------------------------------------
// 5. EVENT-DRIVEN TAB & NAVIGATION TRACKING
// -------------------------------------------------------------

async function notifyBrowserEvent(eventType, data) {
  if (currentState === ExtensionState.STOPPING) return;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const payload = {
      event: eventType,
      timestamp: new Date().toISOString(),
      extensionState: currentState,
      ...data
    };
    await fetch(`${DEFAULT_BACKEND_URL}/browser/event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
  } catch (err) {
    clearTimeout(timeoutId);
    console.debug(`[PrivyBrowse Event] Could not dispatch ${eventType} (backend unreachable)`);
  }
}

// 1. Tab Created
chrome.tabs.onCreated.addListener((tab) => {
  notifyBrowserEvent("TAB_CREATED", {
    tabId: tab.id,
    windowId: tab.windowId,
    url: tab.url || ""
  });
});

// 2. Tab Activation (Switching tabs)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  console.log(`[PrivyBrowse] Tab activated: ${activeInfo.tabId} in window ${activeInfo.windowId}`);
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    await notifyBrowserEvent("TAB_SWITCHED", {
      tabId: activeInfo.tabId,
      windowId: activeInfo.windowId,
      url: tab.url,
      title: tab.title
    });
  } catch (e) {
    await notifyBrowserEvent("TAB_SWITCHED", {
      tabId: activeInfo.tabId,
      windowId: activeInfo.windowId
    });
  }
});

// 3. Tab Navigation & Loading State Updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url) {
    console.log(`[PrivyBrowse] Tab ${tabId} navigated to: ${changeInfo.url}`);
    notifyBrowserEvent("NAVIGATED", {
      tabId,
      url: changeInfo.url,
      title: tab.title,
      status: changeInfo.status || tab.status
    });
  } else if (changeInfo.status) {
    notifyBrowserEvent("STATUS_CHANGED", {
      tabId,
      url: tab.url,
      status: changeInfo.status
    });
  }

  // Automatic initial browser context extraction on completed navigation
  if (changeInfo.status === "complete" && tab && tab.url && !isRestrictedUrl(tab.url)) {
    chrome.tabs.query({ active: true, currentWindow: true }).then(([activeTab]) => {
      if (activeTab && activeTab.id === tabId) {
        orchestrateAnalysis().catch((err) => {
          console.debug("[PrivyBrowse Auto-Analysis]", err.message);
        });
      }
    }).catch(() => {});
  }
});

// 4. Tab Closed
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  console.log(`[PrivyBrowse] Tab removed: ${tabId}`);
  notifyBrowserEvent("TAB_CLOSED", {
    tabId,
    windowId: removeInfo.windowId,
    isWindowClosing: removeInfo.isWindowClosing
  });
});

// 5. Window Focus Changed
chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    notifyBrowserEvent("WINDOW_BLURRED", {});
  } else {
    notifyBrowserEvent("WINDOW_FOCUSED", { windowId });
  }
});

// -------------------------------------------------------------
// 6. SERVICE WORKER LIFECYCLE RE-HYDRATION
// -------------------------------------------------------------

chrome.runtime.onInstalled.addListener(async (details) => {
  console.log(`[PrivyBrowse AI] Extension installed (${details.reason}). Initializing state...`);
  setExtensionState(ExtensionState.READY, "Installation/Update complete");
  await initializeExtension();
});

chrome.runtime.onStartup.addListener(async () => {
  console.log("[PrivyBrowse AI] Chrome browser startup detected. Restoring session...");
  setExtensionState(ExtensionState.READY, "Browser startup");
  await initializeExtension();
});

async function initializeExtension() {
  setExtensionState(ExtensionState.CONNECTING, "Starting connection cycle");
  startHeartbeat();
  startPolling();
}

// Auto-initialize on worker wake-up
initializeExtension();

// -------------------------------------------------------------
// 7. EXTENSION MESSAGE HANDLER (SECURE DISPATCH)
// -------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Verify message trust boundary
  if (!isTrustedMessageSender(sender)) {
    console.warn("[PrivyBrowse Security] Rejected message from untrusted sender:", sender);
    sendResponse({ success: false, error: "UNAUTHORIZED_MESSAGE_ORIGIN" });
    return false;
  }

  const validation = validateMessage(message);
  if (!validation.valid) {
    console.warn("[PrivyBrowse Protocol] Rejected malformed message:", validation.reason);
    sendResponse({ success: false, error: "MALFORMED_MESSAGE", detail: validation.reason });
    return false;
  }

  // 1. Connection Status Query
  if (message.type === "CONNECTION_STATUS" || message.type === "GET_STATE") {
    checkHealth()
      .then(status => sendResponse({ success: true, extensionState: currentState, ...status }))
      .catch(err => sendResponse({ success: false, extensionState: currentState, connected: false, error: err.message }));
    return true; // Keep channel open for async response
  }

  // 2. Viewport Screenshot Capture
  if (message.type === "CAPTURE_SCREENSHOT") {
    captureActiveTab()
      .then(dataUrl => sendResponse({ success: true, dataUrl }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  // 3. Unified DOM & Visual Page Analysis
  if (message.type === "ANALYZE_PAGE") {
    orchestrateAnalysis()
      .then(context => sendResponse({ success: true, context }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  // 4. Action Execution Request
  if (message.type === "EXECUTE_ACTION") {
    dispatchAction(message.payload)
      .then(result => sendResponse({ success: true, result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  // 5. DOM Mutation Event Notification
  if (message.type === "DOM_MUTATED") {
    notifyBrowserEvent("DOM_MUTATED", message.payload || {});
    sendResponse({ success: true });
    return false;
  }

  // 6. SPA Route Event Notification
  if (message.type === "SPA_ROUTED") {
    notifyBrowserEvent("SPA_ROUTED", message.payload || {});
    sendResponse({ success: true });
    return false;
  }

  // 7. Polling Control
  if (message.type === "START_POLLING") {
    startPolling();
    sendResponse({ success: true, message: "Polling loop activated" });
    return false;
  }

  if (message.type === "STOP_POLLING") {
    stopPolling();
    sendResponse({ success: true, message: "Polling loop paused" });
    return false;
  }

  // Unknown message type rejection
  sendResponse({ success: false, error: "UNKNOWN_MESSAGE_TYPE", detail: `Type '${message.type}' is not recognized.` });
  return false;
});

// -------------------------------------------------------------
// 8. BACKEND HEALTH & HEARTBEAT
// -------------------------------------------------------------

async function checkHealth() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(`${DEFAULT_BACKEND_URL}/health`, { method: "GET", signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      if (consecutiveConnectionFailures > 0) {
        console.log("[PrivyBrowse Backend] Reconnection established successfully.");
        consecutiveConnectionFailures = 0;
        currentPollInterval = BASE_POLL_INTERVAL_MS;
      }
      setExtensionState(ExtensionState.CONNECTED, "Health check passed");
      return { connected: true, status: "ONLINE" };
    } else {
      setExtensionState(ExtensionState.DEGRADED, `Backend returned HTTP ${res.status}`);
      return { connected: false, status: "DEGRADED" };
    }
  } catch (err) {
    clearTimeout(timeoutId);
    consecutiveConnectionFailures++;
    // Exponential backoff up to max
    currentPollInterval = Math.min(BASE_POLL_INTERVAL_MS * Math.pow(1.5, consecutiveConnectionFailures), MAX_POLL_INTERVAL_MS);
    setExtensionState(ExtensionState.DISCONNECTED, `Backend unreachable: ${err.message}`);
    return { connected: false, status: "OFFLINE", error: err.message };
  }
}

function startHeartbeat() {
  if (heartbeatIntervalId !== null) clearInterval(heartbeatIntervalId);
  heartbeatIntervalId = setInterval(async () => {
    await checkHealth();
  }, HEARTBEAT_INTERVAL_MS);
}

// -------------------------------------------------------------
// 9. BROWSER TAB OPERATIONS
// -------------------------------------------------------------

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || tab.id === undefined) {
    throw new Error("No active browser tab found.");
  }
  if (tab.url && isRestrictedUrl(tab.url)) {
    throw new Error("This page is restricted (e.g. chrome://, Web Store) and cannot be modified by extensions.");
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

  // 2. Query DOM extraction from content script with injection recovery
  let domResponse = null;
  try {
    domResponse = await chrome.tabs.sendMessage(tabId, { type: "GET_PAGE_CONTEXT" });
  } catch {
    // Content script missing (e.g., loaded before extension or newly refreshed tab)
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ["content.js"]
      });
      domResponse = await chrome.tabs.sendMessage(tabId, { type: "GET_PAGE_CONTEXT" });
    } catch (e) {
      throw new Error(`Content script communication failure on Tab ${tabId}: ${e.message}`);
    }
  }

  if (!domResponse || !domResponse.success) {
    throw new Error(domResponse?.error || "Failed to extract DOM elements from active page.");
  }

  const { page, elements } = domResponse.data;

  // 3. Assemble Unified Browser Context
  const browserContext = {
    tabId,
    windowId: tab.windowId,
    page: {
      tabId,
      windowId: tab.windowId,
      url: tab.url || page.url,
      hostname: page.hostname,
      title: tab.title || page.title,
      viewport: page.viewport,
      scroll: page.scroll,
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

// -------------------------------------------------------------
// 10. ACTION BRIDGE POLLING, TIMEOUT & DEDUPLICATION GUARDS
// -------------------------------------------------------------

async function pollPendingActions() {
  if (!isPollingActive) return;

  pruneActionCache();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(`${DEFAULT_BACKEND_URL}/action/pending`, {
      method: "GET",
      headers: { "Accept": "application/json" },
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      consecutiveConnectionFailures++;
      return;
    }

    consecutiveConnectionFailures = 0;
    currentPollInterval = BASE_POLL_INTERVAL_MS;

    const data = await response.json();
    if (!data.has_action || !data.action) {
      return; // No pending action
    }

    const action = data.action;
    const actionId = action.action_id;
    const actionType = action.action_type;

    console.log(`[PrivyBrowse Bridge] Received action: ${actionType} (${actionId})`);

    // 1. Duplicate Message / Action Guard
    if (executedActionIds.has(actionId)) {
      console.warn(`[PrivyBrowse Guard] Duplicate action '${actionId}' received. Rejecting duplicate execution.`);
      await postAcknowledgement(actionId, {
        success: false,
        action_type: actionType,
        error: `Duplicate action ID '${actionId}' was already executed. Rejected to prevent double submission.`,
        error_code: "DUPLICATE_ACTION_REJECTED"
      });
      return;
    }

    // 2. Active Tab Retrieval & Safety Check
    let tab;
    try {
      tab = await getActiveTab();
    } catch (tabErr) {
      await postAcknowledgement(actionId, {
        success: false,
        action_type: actionType,
        error: tabErr.message,
        error_code: "NO_ACTIVE_TAB"
      });
      return;
    }

    // 3. Stale Context & Tab Mismatch Verification
    if (action.tab_id !== undefined && action.tab_id !== null && action.tab_id !== tab.id) {
      console.warn(`[PrivyBrowse Guard] Tab mismatch: action targeting tab ${action.tab_id} but active is ${tab.id}`);
      await postAcknowledgement(actionId, {
        success: false,
        action_type: actionType,
        error: `Action targeted tab ${action.tab_id}, but current active tab is ${tab.id}`,
        error_code: "TAB_MISMATCH"
      });
      return;
    }

    if (action.expected_url && tab.url && !tab.url.includes(action.expected_url) && !action.expected_url.includes(tab.url)) {
      console.warn(`[PrivyBrowse Guard] URL mismatch / stale action: expected '${action.expected_url}' vs actual '${tab.url}'`);
      await postAcknowledgement(actionId, {
        success: false,
        action_type: actionType,
        error: `Stale action: expected URL '${action.expected_url}' does not match current URL '${tab.url}'`,
        error_code: "STALE_CONTEXT_URL_MISMATCH"
      });
      return;
    }

    // Mark action as in-flight / seen
    executedActionIds.set(actionId, Date.now());

    // 4. Build Content Script Payload
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

    // 5. Dispatch to Content Script with 5000ms Timeout
    let result;
    const actionTimeoutMs = action.timeout_ms || 5000;

    const executePromise = (async () => {
      try {
        return await chrome.tabs.sendMessage(tab.id, {
          type: "EXECUTE_ACTION",
          payload: contentPayload
        });
      } catch (msgErr) {
        // Try re-injecting content script once if unavailable
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"]
        });
        return await chrome.tabs.sendMessage(tab.id, {
          type: "EXECUTE_ACTION",
          payload: contentPayload
        });
      }
    })();

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Action execution timed out after ${actionTimeoutMs}ms`)), actionTimeoutMs)
    );

    try {
      result = await Promise.race([executePromise, timeoutPromise]);
    } catch (execErr) {
      const isTimeout = execErr.message.includes("timed out");
      await postAcknowledgement(actionId, {
        success: false,
        action_type: actionType,
        target_id: action.target_id,
        error: execErr.message,
        error_code: isTimeout ? "ACTION_TIMEOUT" : "CONTENT_SCRIPT_UNAVAILABLE"
      });
      return;
    }

    // 6. Post Formal Acknowledgement Back to Backend
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
    clearTimeout(timeoutId);
    console.debug("[PrivyBrowse Bridge] Poll cycle error:", err.message);
  }
}

// -------------------------------------------------------------
// 11. ACTION ACKNOWLEDGEMENT POSTING
// -------------------------------------------------------------

async function postAcknowledgement(actionId, payload) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

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
      body: JSON.stringify(body),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
  } catch (ackErr) {
    clearTimeout(timeoutId);
    console.warn(`[PrivyBrowse Bridge] Failed to post ack for ${actionId}:`, ackErr.message);
  }
}

// -------------------------------------------------------------
// 12. POLLING LIFECYCLE MANAGEMENT
// -------------------------------------------------------------

function startPolling() {
  if (isPollingActive) return;
  isPollingActive = true;

  const pollLoop = async () => {
    if (!isPollingActive) return;
    await pollPendingActions();
    if (isPollingActive) {
      pollingIntervalId = setTimeout(pollLoop, currentPollInterval);
    }
  };

  pollingIntervalId = setTimeout(pollLoop, currentPollInterval);
  console.log("[PrivyBrowse Bridge] Dynamic action polling activated.");
}

function stopPolling() {
  isPollingActive = false;
  if (pollingIntervalId !== null) {
    clearTimeout(pollingIntervalId);
    pollingIntervalId = null;
  }
  console.log("[PrivyBrowse Bridge] Action polling paused.");
}

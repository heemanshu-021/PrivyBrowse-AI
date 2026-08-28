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

function isRestrictedUrl(url) {
  if (!url) return true;
  return RESTRICTED_PREFIXES.some(prefix => url.startsWith(prefix));
}

chrome.runtime.onInstalled.addListener(() => {
  console.log("[PrivyBrowse AI] Service Worker successfully installed.");
});

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

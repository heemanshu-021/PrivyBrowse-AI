import { ExtensionMessage, BrowserContext } from '../types';
import { browserContextService } from '../services/browserContextService';

// Background Service Worker for PrivyBrowse AI Manifest V3
chrome.runtime.onInstalled.addListener(() => {
  console.log('[PrivyBrowse AI] Extension Service Worker Initialized.');
});

chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender, sendResponse) => {
  if (message.type === 'CONNECTION_STATUS') {
    browserContextService.checkEngineHealth()
      .then(status => sendResponse({ success: true, ...status }))
      .catch(err => sendResponse({ success: false, connected: false, error: err.message }));
    return true; // Async channel
  }

  if (message.type === 'CAPTURE_SCREENSHOT') {
    captureActiveTabScreenshot()
      .then(dataUrl => sendResponse({ success: true, dataUrl }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'ANALYZE_PAGE') {
    orchestratePageAnalysis()
      .then(context => sendResponse({ success: true, context }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'EXECUTE_ACTION') {
    dispatchActionToTab(message.payload)
      .then(result => sendResponse({ success: true, result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

async function getActiveTab(): Promise<chrome.tabs.Tab> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || tab.id === undefined) {
    throw new Error('No active browser tab found.');
  }

  if (tab.url && browserContextService.isRestrictedUrl(tab.url)) {
    throw new Error('This page is restricted (e.g. chrome://, Web Store) and cannot be analyzed by extensions.');
  }

  return tab;
}

async function captureActiveTabScreenshot(): Promise<string> {
  await getActiveTab();
  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(chrome.windows.WINDOW_ID_CURRENT, { format: 'png' });
    return dataUrl;
  } catch (err: any) {
    throw new Error(`Failed to capture tab screenshot: ${err.message || 'Permission denied'}`);
  }
}

async function orchestratePageAnalysis(): Promise<BrowserContext> {
  const tab = await getActiveTab();
  const tabId = tab.id!;

  // 1. Capture screenshot of visible viewport
  let screenshotDataUrl = '';
  try {
    screenshotDataUrl = await chrome.tabs.captureVisibleTab(chrome.windows.WINDOW_ID_CURRENT, { format: 'png' });
  } catch (e: any) {
    console.warn('[PrivyBrowse] Screenshot capture failed:', e);
  }

  // 2. Request normalized safe DOM & page metadata from content script
  let domResponse: any = null;
  try {
    domResponse = await chrome.tabs.sendMessage(tabId, { type: 'GET_PAGE_CONTEXT' });
  } catch {
    // Attempt programmatic re-injection of content script if tab was opened before extension was loaded
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['content.js']
      });
      domResponse = await chrome.tabs.sendMessage(tabId, { type: 'GET_PAGE_CONTEXT' });
    } catch (e: any) {
      throw new Error(`Could not establish communication with content script: ${e.message}`);
    }
  }

  if (!domResponse || !domResponse.success) {
    throw new Error(domResponse?.error || 'Failed to extract DOM layout.');
  }

  const { page, elements } = domResponse.data;

  // 3. Assemble Unified Browser Context Object
  const browserContext: BrowserContext = {
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
      source: 'chrome-extension',
      elementCount: (elements || []).length
    }
  };

  // 4. Send Context to Local Backend Daemon
  const backendResult = await browserContextService.sendBrowserContext(browserContext);
  if (!backendResult.success) {
    console.warn('[PrivyBrowse] Backend transmission note:', backendResult.error);
  }

  return browserContext;
}

async function dispatchActionToTab(actionPayload: any): Promise<any> {
  const tab = await getActiveTab();
  const response = await chrome.tabs.sendMessage(tab.id!, {
    type: 'EXECUTE_ACTION',
    payload: actionPayload
  });
  return response;
}

import { ExtensionMessage } from '../types';
import { extractNormalizedDOM, getPageMetadata } from '../utils/dom';
import { executeSafeAction } from '../utils/action';

// Register Chrome message listeners
chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender, sendResponse) => {
  if (message.type === 'GET_PAGE_CONTEXT') {
    try {
      const elements = extractNormalizedDOM();
      const page = getPageMetadata();
      sendResponse({
        success: true,
        data: { page, elements }
      });
    } catch (err: any) {
      sendResponse({
        success: false,
        error: err.message || 'Failed to extract DOM elements'
      });
    }
    return false;
  }

  if (message.type === 'EXECUTE_ACTION') {
    executeSafeAction(message.payload as any)
      .then((result) => {
        sendResponse({ success: result.success, result });
      })
      .catch((err: any) => {
        sendResponse({
          success: false,
          error: err.message || 'Action execution crashed'
        });
      });
    return true; // Async response
  }

  if (message.type === 'HIGHLIGHT_ELEMENT') {
    const { elementId } = (message.payload as any) || {};
    const el = document.querySelector<HTMLElement>(`[data-pb-id="${elementId}"]`);
    if (el) {
      el.style.outline = '3px solid #00f2fe';
      el.style.boxShadow = '0 0 12px rgba(0, 242, 254, 0.8)';
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      sendResponse({ success: true });
    } else {
      sendResponse({ success: false, error: 'Element not found' });
    }
    return false;
  }

  if (message.type === 'CLEAR_HIGHLIGHTS') {
    const highlighted = document.querySelectorAll<HTMLElement>('[data-pb-id]');
    highlighted.forEach((el) => {
      el.style.outline = '';
      el.style.boxShadow = '';
    });
    sendResponse({ success: true });
    return false;
  }
});

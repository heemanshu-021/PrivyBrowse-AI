// PrivyBrowse AI - Content Script
// Real DOM extraction, MutationObserver, SPA Navigation & Action Execution

if (window.__PRIVYBROWSE_LOADED__) {
  // Already initialized in this browsing context
  console.debug("[PrivyBrowse Content] Content script already active in frame.");
} else {
window.__PRIVYBROWSE_LOADED__ = true;

const SENSITIVE_PATTERNS = [
  /password/i,
  /passwd/i,
  /passcode/i,
  /credit[-_]?card/i,
  /card[-_]?number/i,
  /cvv/i,
  /cvc/i,
  /ssn/i,
  /social[-_]?security/i,
  /pin/i,
  /otp/i,
  /secret/i,
  /security[-_]?code/i
];

function isElementVisible(el) {
  if (!el || !(el instanceof HTMLElement)) return false;
  const style = window.getComputedStyle(el);
  if (
    style.display === 'none' ||
    style.visibility === 'hidden' ||
    style.visibility === 'collapse' ||
    parseFloat(style.opacity || '1') <= 0.05
  ) {
    return false;
  }
  const rect = el.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return false;
  if (
    rect.bottom < 0 ||
    rect.right < 0 ||
    rect.left > (window.innerWidth || document.documentElement.clientWidth) ||
    rect.top > (window.innerHeight || document.documentElement.clientHeight)
  ) {
    return false;
  }
  return true;
}

function isSensitiveField(el) {
  if (el instanceof HTMLInputElement && el.type === 'password') return true;
  const attrStr = [
    el.getAttribute('name') || '',
    el.id || '',
    el.getAttribute('placeholder') || '',
    el.getAttribute('autocomplete') || '',
    el.getAttribute('aria-label') || '',
    el.className || ''
  ].join(' ');
  return SENSITIVE_PATTERNS.some(pattern => pattern.test(attrStr));
}

function classifyElementType(el) {
  const tagName = el.tagName.toLowerCase();
  const role = (el.getAttribute('role') || '').toLowerCase();
  const inputType = el instanceof HTMLInputElement ? el.type.toLowerCase() : '';

  if (tagName === 'button' || role === 'button') return 'button';
  if (tagName === 'a' || role === 'link') return 'link';
  if (tagName === 'select') return 'select';
  if (tagName === 'textarea') return 'textarea';
  if (tagName === 'form') return 'form';
  if (tagName === 'img') return 'image';

  if (tagName === 'input') {
    if (inputType === 'button' || inputType === 'submit' || inputType === 'reset') return 'button';
    if (inputType === 'checkbox' || role === 'checkbox') return 'checkbox';
    if (inputType === 'radio' || role === 'radio') return 'radio';
    return 'input';
  }

  if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'label'].includes(tagName)) {
    return 'text';
  }

  return 'element';
}

function findFormLabel(el) {
  if (!el) return '';
  // 1. Check for explicit <label for="el.id">
  if (el.id) {
    const labelEl = document.querySelector(`label[for="${el.id}"]`);
    if (labelEl) {
      return (labelEl.innerText || labelEl.textContent || '').trim();
    }
  }
  // 2. Check for enclosing <label> parent
  const parentLabel = el.closest('label');
  if (parentLabel) {
    const clone = parentLabel.cloneNode(true);
    // Remove the input itself from text extraction
    clone.querySelectorAll('input, select, textarea').forEach(n => n.remove());
    return (clone.innerText || clone.textContent || '').trim();
  }
  // 3. Check for aria-labelledby
  const labelledBy = el.getAttribute('aria-labelledby');
  if (labelledBy) {
    const targetEl = document.getElementById(labelledBy);
    if (targetEl) {
      return (targetEl.innerText || targetEl.textContent || '').trim();
    }
  }
  return '';
}

function extractNormalizedDOM() {
  const candidatesSelector =
    'button, input, select, textarea, a, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="tab"], [role="option"], [role="combobox"], [role="dialog"], dialog, label, form, img, h1, h2, h3, h4, p, span';

  const rawElements = Array.from(document.querySelectorAll(candidatesSelector));

  // Traverse open Shadow DOM trees
  try {
    document.querySelectorAll('*').forEach(host => {
      if (host.shadowRoot) {
        try {
          const shadowItems = host.shadowRoot.querySelectorAll(candidatesSelector);
          shadowItems.forEach(el => {
            el.__inShadowDom = true;
            rawElements.push(el);
          });
        } catch (e) {}
      }
    });
  } catch (e) {}

  const elements = [];
  let counter = 1;

  rawElements.forEach((el) => {
    if (!isElementVisible(el)) return;
    const rect = el.getBoundingClientRect();
    const type = classifyElementType(el);
    const tagName = el.tagName.toLowerCase();
    const sensitive = isSensitiveField(el);

    let text = '';
    if (['h1', 'h2', 'h3', 'h4', 'p', 'span', 'a', 'button', 'label', 'option'].includes(tagName)) {
      text = (el.innerText || el.textContent || '').trim();
    }
    if (!text && ['h1', 'h2', 'h3', 'h4', 'p', 'span'].includes(tagName)) {
      return;
    }

    const id = `pb-element-${counter.toString().padStart(3, '0')}`;
    counter++;
    el.dataset.pbId = id;

    const formLabel = findFormLabel(el);
    const ariaLabel = el.getAttribute('aria-label') || null;
    const isChecked = el instanceof HTMLInputElement && (el.type === 'checkbox' || el.type === 'radio') ? el.checked : (el.getAttribute('aria-checked') === 'true');
    const isSelected = el.tagName === 'OPTION' ? el.selected : (el.getAttribute('aria-selected') === 'true');
    const isModal = el.tagName === 'DIALOG' || el.getAttribute('role') === 'dialog' || el.getAttribute('aria-modal') === 'true' || el.classList.contains('modal');

    // Extract dropdown options if select element
    let optionsList = [];
    if (el instanceof HTMLSelectElement) {
      optionsList = Array.from(el.options).map((opt, idx) => ({
        index: idx,
        value: opt.value,
        text: (opt.text || opt.innerText || '').trim(),
        selected: opt.selected
      }));
    }

    elements.push({
      id,
      type: isModal ? 'dialog' : type,
      tag: tagName,
      text: sensitive ? '[SENSITIVE FIELD]' : text.substring(0, 160),
      ariaLabel: ariaLabel || null,
      aria_labelledby: el.getAttribute('aria-labelledby') || null,
      form_label: formLabel || null,
      placeholder: el.getAttribute('placeholder') || null,
      role: el.getAttribute('role') || null,
      name: el.getAttribute('name') || null,
      value: sensitive ? '[REDACTED]' : (el.value || ''),
      checked: isChecked,
      selected: isSelected,
      options: optionsList,
      in_shadow_dom: Boolean(el.__inShadowDom),
      inputType: el instanceof HTMLInputElement ? el.type : null,
      sensitive: sensitive || undefined,
      bbox: {
        x: Math.round(rect.left),
        y: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        top: Math.round(rect.top),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom)
      },
      visible: true,
      enabled: !el.disabled && el.getAttribute('aria-disabled') !== 'true',
      selector: el.id ? `#${el.id}` : undefined
    });
  });

  return elements;
}

function getPageMetadata() {
  const docEl = document.documentElement || document.body || {};
  const scrollY = window.scrollY || window.pageYOffset || 0;
  const scrollX = window.scrollX || window.pageXOffset || 0;
  const docH = docEl.scrollHeight || window.innerHeight || 1080;
  const docW = docEl.scrollWidth || window.innerWidth || 1920;
  const vpW = window.innerWidth || docEl.clientWidth || 1920;
  const vpH = window.innerHeight || docEl.clientHeight || 1080;

  return {
    url: window.location.href,
    hostname: window.location.hostname || 'localhost',
    title: document.title || 'Untitled Webpage',
    viewport: {
      width: vpW,
      height: vpH
    },
    scroll: {
      x: scrollX,
      y: scrollY,
      scrollX: scrollX,
      scrollY: scrollY,
      documentWidth: docW,
      documentHeight: docH,
      maxScrollY: Math.max(0, docH - vpH)
    },
    devicePixelRatio: window.devicePixelRatio || 1,
    timestamp: new Date().toISOString()
  };
}

// -------------------------------------------------------------
// DYNAMIC DOM MUTATION & SPA ROUTE MONITORING
// -------------------------------------------------------------

let mutationDebounceTimer = null;
const DEBOUNCE_MS = 250;

function handleMeaningfulDOMMutation() {
  if (mutationDebounceTimer) {
    clearTimeout(mutationDebounceTimer);
  }
  mutationDebounceTimer = setTimeout(() => {
    try {
      const elements = extractNormalizedDOM();
      const page = getPageMetadata();
      chrome.runtime.sendMessage({
        type: "DOM_MUTATED",
        payload: {
          url: page.url,
          elements,
          elementCount: elements.length,
          timestamp: new Date().toISOString()
        }
      }).catch(() => {});
    } catch (e) {
      // Content script context invalidated on navigation
    }
  }, DEBOUNCE_MS);
}

// Start MutationObserver on document body
if (document.body) {
  const observer = new MutationObserver((mutations) => {
    let hasMeaningfulChange = false;
    for (const m of mutations) {
      if (m.type === 'childList' && (m.addedNodes.length > 0 || m.removedNodes.length > 0)) {
        hasMeaningfulChange = true;
        break;
      }
      if (m.type === 'attributes' && ['class', 'style', 'hidden', 'disabled', 'value'].includes(m.attributeName)) {
        hasMeaningfulChange = true;
        break;
      }
    }
    if (hasMeaningfulChange) {
      handleMeaningfulDOMMutation();
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'style', 'hidden', 'disabled', 'value']
  });
}

// Proxy SPA History APIs (pushState / replaceState)
(function proxyHistoryAPI() {
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;

  function notifySPARoute() {
    setTimeout(() => {
      try {
        const page = getPageMetadata();
        chrome.runtime.sendMessage({
          type: "SPA_ROUTED",
          payload: {
            url: page.url,
            title: page.title,
            timestamp: new Date().toISOString()
          }
        }).catch(() => {});
      } catch (e) {}
    }, 50);
  }

  history.pushState = function(...args) {
    const res = originalPushState.apply(this, args);
    notifySPARoute();
    return res;
  };

  history.replaceState = function(...args) {
    const res = originalReplaceState.apply(this, args);
    notifySPARoute();
    return res;
  };

  window.addEventListener('popstate', notifySPARoute);
  window.addEventListener('hashchange', notifySPARoute);
})();

function resolveElement(target) {
  if (target.elementId) {
    const el = document.querySelector(`[data-pb-id="${target.elementId}"]`);
    if (el) return el;
    const elById = document.getElementById(target.elementId);
    if (elById) return elById;
  }
  if (target.selector) {
    try {
      const el = document.querySelector(target.selector);
      if (el) return el;
    } catch {}
  }
  if (target.description) {
    const buttons = Array.from(document.querySelectorAll('button, a, input[type="submit"], [role="button"]'));
    const match = buttons.find(b => (b.innerText || b.getAttribute('aria-label') || '').toLowerCase().includes(target.description.toLowerCase()));
    if (match) return match;
  }
  if (typeof target.x === 'number' && typeof target.y === 'number') {
    const elAtPoint = document.elementFromPoint(target.x, target.y);
    if (elAtPoint) return elAtPoint;
  }
  return null;
}

async function executeSafeAction(request) {
  const { action, action_id, target, text, key, scrollDelta } = request;
  const timestamp = new Date().toISOString();

  function makeResult(result) {
    if (action_id) result.action_id = action_id;
    return result;
  }

  if (action === 'WAIT') {
    await new Promise(r => setTimeout(r, 800));
    return makeResult({ success: true, action: 'WAIT', detail: 'Completed wait duration (800ms)', timestamp });
  }

  if (action === 'SCROLL') {
    const dx = scrollDelta?.x || 0;
    const dy = scrollDelta?.y || 400;
    const scrollYBefore = window.scrollY;
    const scrollXBefore = window.scrollX;
    window.scrollBy({ top: dy, left: dx, behavior: 'smooth' });
    await new Promise(r => setTimeout(r, 150));
    const actualDeltaY = window.scrollY - scrollYBefore;
    const actualDeltaX = window.scrollX - scrollXBefore;
    return makeResult({
      success: true,
      action: 'SCROLL',
      detail: `Scrolled viewport by (${actualDeltaX}, ${actualDeltaY}) px (requested: ${dx}, ${dy})`,
      actual_delta: { x: actualDeltaX, y: actualDeltaY },
      requested_delta: { x: dx, y: dy },
      scroll_position: { x: window.scrollX, y: window.scrollY },
      timestamp
    });
  }

  if (action === 'NAVIGATE' && text) {
    window.location.href = text;
    return makeResult({ success: true, action: 'NAVIGATE', detail: `Navigating to ${text}`, timestamp });
  }

  if (action === 'SCROLL_INTO_VIEW' || action === 'SCROLL_TO_TARGET') {
    const targetElement = resolveElement(target || {});
    if (!targetElement) {
      return makeResult({ success: false, action, error: 'TARGET_NOT_FOUND', detail: 'Could not find target to scroll into view.', timestamp });
    }
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    await new Promise(r => setTimeout(r, 200));
    const rect = targetElement.getBoundingClientRect();
    return makeResult({
      success: true,
      action: 'SCROLL_INTO_VIEW',
      detail: `Target scrolled into view at viewport y=${Math.round(rect.top)}`,
      bbox: { x: Math.round(rect.left), y: Math.round(rect.top), width: Math.round(rect.width), height: Math.round(rect.height) },
      timestamp
    });
  }

  const targetElement = resolveElement(target || {});
  if (!targetElement) {
    return makeResult({ success: false, action, error: 'TARGET_NOT_FOUND', detail: 'Could not resolve target element on current page layout.', timestamp });
  }

  if (!isElementVisible(targetElement)) {
    // Try scrolling it into view once before failing
    targetElement.scrollIntoView({ behavior: 'instant', block: 'center' });
    if (!isElementVisible(targetElement)) {
      return makeResult({ success: false, action, error: 'TARGET_NOT_VISIBLE', detail: `Target element <${targetElement.tagName.toLowerCase()}> is hidden or outside the viewport.`, timestamp });
    }
  }

  if (targetElement.disabled || targetElement.getAttribute('aria-disabled') === 'true') {
    return makeResult({ success: false, action, error: 'TARGET_DISABLED', detail: 'Target element is currently in a disabled state.', timestamp });
  }

  if (action === 'SELECT') {
    if (targetElement instanceof HTMLSelectElement) {
      const optionToSelect = text || target?.text || '';
      let matched = false;
      for (let i = 0; i < targetElement.options.length; i++) {
        const opt = targetElement.options[i];
        if (opt.value === optionToSelect || (opt.text && opt.text.trim().toLowerCase() === optionToSelect.toLowerCase())) {
          targetElement.selectedIndex = i;
          matched = true;
          break;
        }
      }
      targetElement.dispatchEvent(new Event('input', { bubbles: true }));
      targetElement.dispatchEvent(new Event('change', { bubbles: true }));
      return makeResult({
        success: true,
        action: 'SELECT',
        target: target?.elementId || targetElement.dataset?.pbId || targetElement.tagName.toLowerCase(),
        selected_value: targetElement.value,
        matched,
        detail: `Selected option '${targetElement.value}' in <select>`,
        timestamp
      });
    }
  }

  if (action === 'CHECK' || action === 'UNCHECK') {
    if (targetElement instanceof HTMLInputElement && (targetElement.type === 'checkbox' || targetElement.type === 'radio')) {
      const desiredState = action === 'CHECK';
      if (targetElement.checked !== desiredState) {
        targetElement.click();
      }
      return makeResult({
        success: true,
        action,
        checked: targetElement.checked,
        detail: `Checkbox set to checked=${targetElement.checked}`,
        timestamp
      });
    }
  }

  if (action === 'CLICK') {
    if (targetElement.focus) targetElement.focus();
    const rect = targetElement.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;

    targetElement.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
    targetElement.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
    targetElement.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));

    if (targetElement.tagName === 'BUTTON' && (targetElement.type === 'submit' || targetElement.getAttribute('type') === 'submit')) {
      const form = targetElement.closest('form');
      if (form) form.requestSubmit ? form.requestSubmit() : form.submit();
    }

    return makeResult({
      success: true,
      action: 'CLICK',
      target: target?.elementId || targetElement.dataset?.pbId || targetElement.tagName.toLowerCase(),
      element_pb_id: targetElement.dataset?.pbId || null,
      detail: `Dispatched click event on <${targetElement.tagName.toLowerCase()}>`,
      bbox: { x: Math.round(rect.left), y: Math.round(rect.top), width: Math.round(rect.width), height: Math.round(rect.height) },
      timestamp
    });
  }

  if (action === 'TYPE') {
    if (!(targetElement instanceof HTMLInputElement) && !(targetElement instanceof HTMLTextAreaElement) && !targetElement.isContentEditable) {
      return makeResult({ success: false, action: 'TYPE', error: 'INVALID_ACTION', detail: `Element <${targetElement.tagName.toLowerCase()}> does not accept text input.`, timestamp });
    }
    const isSensitive = isSensitiveField(targetElement);
    targetElement.focus();
    const valueToSet = text || '';

    if (targetElement instanceof HTMLInputElement || targetElement instanceof HTMLTextAreaElement) {
      const proto = targetElement instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
      const nativeSetter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
      if (nativeSetter) {
        nativeSetter.call(targetElement, valueToSet);
      } else {
        targetElement.value = valueToSet;
      }
      targetElement.dispatchEvent(new Event('input', { bubbles: true }));
      targetElement.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (targetElement.isContentEditable) {
      targetElement.innerText = valueToSet;
      targetElement.dispatchEvent(new Event('input', { bubbles: true }));
      targetElement.dispatchEvent(new Event('change', { bubbles: true }));
    }

    let verifiedValue;
    if (targetElement instanceof HTMLInputElement || targetElement instanceof HTMLTextAreaElement) {
      verifiedValue = targetElement.value;
    } else {
      verifiedValue = targetElement.innerText;
    }
    const valueApplied = verifiedValue === valueToSet;

    if (!valueApplied) {
      return makeResult({
        success: false,
        action: 'TYPE',
        error: 'VALUE_NOT_APPLIED',
        detail: `Typed value was not retained by <${targetElement.tagName.toLowerCase()}> (framework may have overridden)`,
        timestamp
      });
    }

    return makeResult({
      success: true,
      action: 'TYPE',
      target: target?.elementId || targetElement.dataset?.pbId || targetElement.tagName.toLowerCase(),
      element_pb_id: targetElement.dataset?.pbId || null,
      detail: isSensitive ? `Typed [SENSITIVE VALUE MASKED] into <${targetElement.tagName.toLowerCase()}>` : `Typed "${valueToSet}" into <${targetElement.tagName.toLowerCase()}>`,
      typed_value: isSensitive ? '[REDACTED]' : valueToSet,
      value_verified: true,
      timestamp
    });
  }

  if (action === 'PRESS_KEY') {
    targetElement.focus();
    const keyString = key || (text === '\n' ? 'Enter' : text) || 'Enter';
    targetElement.dispatchEvent(new KeyboardEvent('keydown', { key: keyString, bubbles: true }));
    targetElement.dispatchEvent(new KeyboardEvent('keypress', { key: keyString, bubbles: true }));
    targetElement.dispatchEvent(new KeyboardEvent('keyup', { key: keyString, bubbles: true }));
    return makeResult({
      success: true,
      action: 'PRESS_KEY',
      target: target?.elementId || targetElement.dataset?.pbId || targetElement.tagName.toLowerCase(),
      element_pb_id: targetElement.dataset?.pbId || null,
      detail: `Dispatched keydown "${keyString}" on <${targetElement.tagName.toLowerCase()}>`,
      timestamp
    });
  }

  return makeResult({ success: false, action, error: 'INVALID_ACTION', detail: `Action verb ${action} is not supported.`, timestamp });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_PAGE_CONTEXT') {
    try {
      const elements = extractNormalizedDOM();
      const page = getPageMetadata();
      sendResponse({ success: true, data: { page, elements } });
    } catch (err) {
      sendResponse({ success: false, error: err.message || 'Failed to extract DOM elements' });
    }
    return false;
  }

  if (message.type === 'EXECUTE_ACTION') {
    executeSafeAction(message.payload)
      .then((result) => sendResponse({ success: result.success, result }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'HIGHLIGHT_ELEMENT') {
    const { elementId } = message.payload || {};
    const el = document.querySelector(`[data-pb-id="${elementId}"]`);
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
    const highlighted = document.querySelectorAll('[data-pb-id]');
    highlighted.forEach((el) => {
      el.style.outline = '';
      el.style.boxShadow = '';
    });
    sendResponse({ success: true });
    return false;
  }

  if (message.type === 'PING') {
    sendResponse({ success: true, pong: true, timestamp: new Date().toISOString() });
    return false;
  }
});
} // End of window.__PRIVYBROWSE_LOADED__ block

// PrivyBrowse AI - Content Script
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

function extractNormalizedDOM() {
  const candidatesSelector =
    'button, input, select, textarea, a, [role="button"], [role="link"], [role="checkbox"], [role="radio"], label, form, img, h1, h2, h3, h4, p, span';
  const rawElements = Array.from(document.querySelectorAll(candidatesSelector));
  const elements = [];
  let counter = 1;

  rawElements.forEach((el) => {
    if (!isElementVisible(el)) return;
    const rect = el.getBoundingClientRect();
    const type = classifyElementType(el);
    const tagName = el.tagName.toLowerCase();
    const sensitive = isSensitiveField(el);

    let text = '';
    if (['h1', 'h2', 'h3', 'h4', 'p', 'span', 'a', 'button', 'label'].includes(tagName)) {
      text = (el.innerText || el.textContent || '').trim();
    }
    if (!text && ['h1', 'h2', 'h3', 'h4', 'p', 'span'].includes(tagName)) {
      return;
    }

    const id = `pb-element-${counter.toString().padStart(3, '0')}`;
    counter++;
    el.dataset.pbId = id;

    elements.push({
      id,
      type,
      tag: tagName,
      text: sensitive ? '[SENSITIVE FIELD]' : text.substring(0, 160),
      ariaLabel: el.getAttribute('aria-label') || null,
      placeholder: el.getAttribute('placeholder') || null,
      role: el.getAttribute('role') || null,
      name: el.getAttribute('name') || null,
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
      enabled: !el.disabled,
      selector: el.id ? `#${el.id}` : undefined
    });
  });

  return elements;
}

function getPageMetadata() {
  return {
    url: window.location.href,
    hostname: window.location.hostname || 'localhost',
    title: document.title || 'Untitled Webpage',
    viewport: {
      width: window.innerWidth || document.documentElement.clientWidth,
      height: window.innerHeight || document.documentElement.clientHeight
    },
    devicePixelRatio: window.devicePixelRatio || 1,
    timestamp: new Date().toISOString()
  };
}

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
  const { action, target, text, key, scrollDelta } = request;
  const timestamp = new Date().toISOString();

  if (action === 'WAIT') {
    await new Promise(r => setTimeout(r, 800));
    return { success: true, action: 'WAIT', detail: 'Completed wait duration (800ms)', timestamp };
  }

  if (action === 'SCROLL') {
    const dx = scrollDelta?.x || 0;
    const dy = scrollDelta?.y || 400;
    window.scrollBy({ top: dy, left: dx, behavior: 'smooth' });
    return { success: true, action: 'SCROLL', detail: `Scrolled viewport by (${dx}, ${dy}) px`, timestamp };
  }

  if (action === 'NAVIGATE' && text) {
    window.location.href = text;
    return { success: true, action: 'NAVIGATE', detail: `Navigating to ${text}`, timestamp };
  }

  const targetElement = resolveElement(target);
  if (!targetElement) {
    return { success: false, action, error: 'TARGET_NOT_FOUND', detail: 'Could not resolve target element on current page layout.', timestamp };
  }

  if (!isElementVisible(targetElement)) {
    return { success: false, action, error: 'TARGET_NOT_VISIBLE', detail: `Target element <${targetElement.tagName.toLowerCase()}> is hidden or outside the viewport.`, timestamp };
  }

  if (targetElement.disabled) {
    return { success: false, action, error: 'TARGET_DISABLED', detail: 'Target element is currently in a disabled state.', timestamp };
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

    return { success: true, action: 'CLICK', target: target.elementId || targetElement.tagName.toLowerCase(), detail: `Dispatched click event on <${targetElement.tagName.toLowerCase()}>`, timestamp };
  }

  if (action === 'TYPE') {
    if (!(targetElement instanceof HTMLInputElement) && !(targetElement instanceof HTMLTextAreaElement) && !targetElement.isContentEditable) {
      return { success: false, action: 'TYPE', error: 'INVALID_ACTION', detail: `Element <${targetElement.tagName.toLowerCase()}> does not accept text input.`, timestamp };
    }
    const isSensitive = isSensitiveField(targetElement);
    targetElement.focus();
    const valueToSet = text || '';
    if (targetElement instanceof HTMLInputElement || targetElement instanceof HTMLTextAreaElement) {
      targetElement.value = valueToSet;
    } else if (targetElement.isContentEditable) {
      targetElement.innerText = valueToSet;
    }
    targetElement.dispatchEvent(new Event('input', { bubbles: true }));
    targetElement.dispatchEvent(new Event('change', { bubbles: true }));
    return {
      success: true,
      action: 'TYPE',
      target: target.elementId || targetElement.tagName.toLowerCase(),
      detail: isSensitive ? `Typed [SENSITIVE VALUE MASKED] into <${targetElement.tagName.toLowerCase()}>` : `Typed "${valueToSet}" into <${targetElement.tagName.toLowerCase()}>`,
      timestamp
    };
  }

  if (action === 'PRESS_KEY') {
    targetElement.focus();
    const keyString = key || (text === '\n' ? 'Enter' : text) || 'Enter';
    targetElement.dispatchEvent(new KeyboardEvent('keydown', { key: keyString, bubbles: true }));
    targetElement.dispatchEvent(new KeyboardEvent('keypress', { key: keyString, bubbles: true }));
    targetElement.dispatchEvent(new KeyboardEvent('keyup', { key: keyString, bubbles: true }));
    return { success: true, action: 'PRESS_KEY', target: target.elementId || targetElement.tagName.toLowerCase(), detail: `Dispatched keydown "${keyString}" on <${targetElement.tagName.toLowerCase()}>`, timestamp };
  }

  return { success: false, action, error: 'INVALID_ACTION', detail: `Action verb ${action} is not supported.`, timestamp };
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
});

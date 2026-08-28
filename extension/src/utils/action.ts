import { AgentActionRequest, ActionResult, ActionTarget } from '../types';
import { isElementVisible, isSensitiveField } from './dom';

export function resolveElement(target: ActionTarget): HTMLElement | null {
  // Priority 1: Stable internal element identifier
  if (target.elementId) {
    const el = document.querySelector<HTMLElement>(`[data-pb-id="${target.elementId}"]`);
    if (el) return el;

    // Fallback ID attribute match if elementId was from DOM
    const elById = document.getElementById(target.elementId);
    if (elById) return elById;
  }

  // Priority 2: CSS Selector
  if (target.selector) {
    try {
      const el = document.querySelector<HTMLElement>(target.selector);
      if (el) return el;
    } catch {
      // Invalid selector fallback
    }
  }

  // Priority 3: Accessibility or text match if description provided
  if (target.description) {
    const buttons = Array.from(document.querySelectorAll<HTMLElement>('button, a, input[type="submit"], [role="button"]'));
    const match = buttons.find(b => {
      const txt = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
      return txt.includes(target.description!.toLowerCase());
    });
    if (match) return match;
  }

  // Priority 4: Fallback to screen coordinates
  if (typeof target.x === 'number' && typeof target.y === 'number') {
    const elAtPoint = document.elementFromPoint(target.x, target.y) as HTMLElement;
    if (elAtPoint) return elAtPoint;
  }

  return null;
}

export async function executeSafeAction(request: AgentActionRequest): Promise<ActionResult> {
  const { action, target, text, key, scrollDelta } = request;
  const timestamp = new Date().toISOString();

  // 1. Standalone actions that do not require element target
  if (action === 'WAIT') {
    await new Promise(r => setTimeout(r, 800));
    return {
      success: true,
      action: 'WAIT',
      detail: 'Completed wait duration (800ms)',
      timestamp
    };
  }

  if (action === 'SCROLL') {
    const dx = scrollDelta?.x || 0;
    const dy = scrollDelta?.y || 400;
    window.scrollBy({ top: dy, left: dx, behavior: 'smooth' });
    return {
      success: true,
      action: 'SCROLL',
      detail: `Scrolled viewport by (${dx}, ${dy}) px`,
      timestamp
    };
  }

  if (action === 'NAVIGATE' && text) {
    window.location.href = text;
    return {
      success: true,
      action: 'NAVIGATE',
      detail: `Navigating to ${text}`,
      timestamp
    };
  }

  // 2. Resolve Target Element
  const targetElement = resolveElement(target);

  if (!targetElement) {
    return {
      success: false,
      action,
      error: 'TARGET_NOT_FOUND',
      detail: `Could not resolve target element on current page layout.`,
      timestamp
    };
  }

  // 3. Validate Element State (Visibility & Enabled)
  if (!isElementVisible(targetElement)) {
    return {
      success: false,
      action,
      error: 'TARGET_NOT_VISIBLE',
      detail: `Target element <${targetElement.tagName.toLowerCase()}> is hidden or outside the viewport.`,
      timestamp
    };
  }

  if ((targetElement as HTMLInputElement).disabled) {
    return {
      success: false,
      action,
      error: 'TARGET_DISABLED',
      detail: `Target element is currently in a disabled state.`,
      timestamp
    };
  }

  // 4. Execute Click Action
  if (action === 'CLICK') {
    if (targetElement.focus) targetElement.focus();

    // Dispatch complete mouse event cycle
    const rect = targetElement.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;

    targetElement.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
    targetElement.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
    targetElement.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));

    // Fallback for form submission
    if (
      targetElement.tagName === 'BUTTON' &&
      ((targetElement as HTMLButtonElement).type === 'submit' || targetElement.getAttribute('type') === 'submit')
    ) {
      const form = targetElement.closest('form');
      if (form) form.requestSubmit ? form.requestSubmit() : form.submit();
    }

    return {
      success: true,
      action: 'CLICK',
      target: target.elementId || targetElement.tagName.toLowerCase(),
      detail: `Dispatched click event on <${targetElement.tagName.toLowerCase()}>`,
      timestamp
    };
  }

  // 5. Execute Type Action (With Privacy Safety Masking)
  if (action === 'TYPE') {
    if (
      !(targetElement instanceof HTMLInputElement) &&
      !(targetElement instanceof HTMLTextAreaElement) &&
      !targetElement.isContentEditable
    ) {
      return {
        success: false,
        action: 'TYPE',
        error: 'INVALID_ACTION',
        detail: `Element <${targetElement.tagName.toLowerCase()}> does not accept text input.`,
        timestamp
      };
    }

    const isSensitive = isSensitiveField(targetElement);
    targetElement.focus();

    const valueToSet = text || '';
    if (targetElement instanceof HTMLInputElement || targetElement instanceof HTMLTextAreaElement) {
      targetElement.value = valueToSet;
    } else if (targetElement.isContentEditable) {
      targetElement.innerText = valueToSet;
    }

    // Dispatch input & change events for modern frameworks (React / Angular / Vue)
    targetElement.dispatchEvent(new Event('input', { bubbles: true }));
    targetElement.dispatchEvent(new Event('change', { bubbles: true }));

    return {
      success: true,
      action: 'TYPE',
      target: target.elementId || targetElement.tagName.toLowerCase(),
      detail: isSensitive
        ? `Typed [SENSITIVE VALUE MASKED] into <${targetElement.tagName.toLowerCase()}>`
        : `Typed "${valueToSet}" into <${targetElement.tagName.toLowerCase()}>`,
      timestamp
    };
  }

  // 6. Execute Press Key Action
  if (action === 'PRESS_KEY') {
    targetElement.focus();
    const keyString = key || (text === '\n' ? 'Enter' : text) || 'Enter';

    targetElement.dispatchEvent(new KeyboardEvent('keydown', { key: keyString, bubbles: true }));
    targetElement.dispatchEvent(new KeyboardEvent('keypress', { key: keyString, bubbles: true }));
    targetElement.dispatchEvent(new KeyboardEvent('keyup', { key: keyString, bubbles: true }));

    return {
      success: true,
      action: 'PRESS_KEY',
      target: target.elementId || targetElement.tagName.toLowerCase(),
      detail: `Dispatched keydown "${keyString}" on <${targetElement.tagName.toLowerCase()}>`,
      timestamp
    };
  }

  return {
    success: false,
    action,
    error: 'INVALID_ACTION',
    detail: `Action verb ${action} is not supported.`,
    timestamp
  };
}

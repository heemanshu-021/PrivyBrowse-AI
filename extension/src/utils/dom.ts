import { NormalizedElement, ElementType, PageMetadata } from '../types';

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

export function isElementVisible(el: HTMLElement): boolean {
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
  if (rect.width === 0 || rect.height === 0) {
    return false;
  }

  // Check if completely outside viewport
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

export function isSensitiveField(el: HTMLElement): boolean {
  if (el instanceof HTMLInputElement) {
    if (el.type === 'password') return true;
  }

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

export function classifyElementType(el: HTMLElement): ElementType {
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

export function extractNormalizedDOM(): NormalizedElement[] {
  const candidatesSelector =
    'button, input, select, textarea, a, [role="button"], [role="link"], [role="checkbox"], [role="radio"], label, form, img, h1, h2, h3, h4, p, span';

  const rawElements = Array.from(document.querySelectorAll<HTMLElement>(candidatesSelector));
  const elements: NormalizedElement[] = [];

  let elementCounter = 1;

  rawElements.forEach((el) => {
    if (!isElementVisible(el)) return;

    const rect = el.getBoundingClientRect();
    const type = classifyElementType(el);
    const tagName = el.tagName.toLowerCase();
    const sensitive = isSensitiveField(el);

    // Extract text content safely
    let text = '';
    if (['h1', 'h2', 'h3', 'h4', 'p', 'span', 'a', 'button', 'label'].includes(tagName)) {
      text = (el.innerText || el.textContent || '').trim();
    }

    // Skip empty text nodes if not interactive
    if (!text && ['h1', 'h2', 'h3', 'h4', 'p', 'span'].includes(tagName)) {
      return;
    }

    // Assign temporary stable identifier
    const id = `pb-element-${elementCounter.toString().padStart(3, '0')}`;
    elementCounter++;
    el.dataset.pbId = id;

    const normalized: NormalizedElement = {
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
      enabled: !(el as HTMLInputElement).disabled,
      selector: el.id ? `#${el.id}` : undefined
    };

    elements.push(normalized);
  });

  return elements;
}

export function getPageMetadata(): PageMetadata {
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

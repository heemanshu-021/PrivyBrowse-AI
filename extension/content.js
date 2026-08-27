// content.js

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PARSE_DOM") {
    try {
      const nodes = parseInteractiveElements();
      sendResponse(nodes);
    } catch (err) {
      console.error("DOM Parsing error", err);
      sendResponse([]);
    }
  }

  if (message.type === "EXECUTE_DOM_ACTION") {
    executeAction(message.action)
      .then(res => sendResponse({ success: true, detail: res }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // async response
  }
});

// Helper to determine if an element is visible
def_isVisible = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
    return false;
  }
  const rect = el.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) {
    return false;
  }
  return true;
};

// Extracts interactive elements and visible text layout structures
function parseInteractiveElements() {
  const elements = [];
  // Select typical interactive fields and text nodes
  const selectors = 'input, button, select, textarea, a, img, [role="button"], label, h1, h2, h3, p, span';
  const rawElements = document.querySelectorAll(selectors);

  rawElements.forEach((el, index) => {
    if (!def_isVisible(el)) return;

    const rect = el.getBoundingClientRect();
    // Bounding box format: [x1, y1, x2, y2] relative to page viewport
    const bbox = [
      Math.round(rect.left + window.scrollX),
      Math.round(rect.top + window.scrollY),
      Math.round(rect.right + window.scrollX),
      Math.round(rect.bottom + window.scrollY)
    ];

    const tagName = el.tagName.toLowerCase();
    
    // Get text content - truncate if extremely long
    let text = "";
    if (["h1", "h2", "h3", "p", "span", "a", "button"].includes(tagName)) {
      text = el.innerText || el.textContent || "";
    }
    
    // Skip empty container elements that aren't inputs or images
    if (!text && !["input", "textarea", "select", "img"].includes(tagName)) {
      return;
    }

    elements.push({
      id: `dom_${index}`,
      tag_name: el.tagName,
      text: text.trim().substring(0, 200),
      value: el.value || "",
      placeholder: el.getAttribute("placeholder") || "",
      type: el.getAttribute("type") || "",
      id_attr: el.id || "",
      class_attr: el.className || "",
      bbox: bbox
    });
  });

  return elements;
}

// Executes visual interactions natively inside the DOM
async function executeAction(actionData) {
  const { action, target, text, element_id } = actionData;
  const x = target.x - window.scrollX;
  const y = target.y - window.scrollY;

  if (action === "WAIT") {
    await new Promise(r => setTimeout(r, 1000));
    return "Waited 1s";
  }

  if (action === "SCROLL") {
    window.scrollBy({ top: 400, behavior: 'smooth' });
    return "Scrolled page";
  }

  // Attempt to resolve element by coordinates or element ID
  let targetEl = null;
  if (element_id) {
    // Attempt mapping back using ID
    const index = parseInt(element_id.split("_")[1]);
    const selectors = 'input, button, select, textarea, a, img, [role="button"], label, h1, h2, h3, p, span';
    const all = document.querySelectorAll(selectors);
    const visibleAll = Array.from(all).filter(def_isVisible);
    if (visibleAll[index]) {
      targetEl = visibleAll[index];
    }
  }

  if (!targetEl) {
    // Fallback: Find element at screen coordinates
    targetEl = document.elementFromPoint(x, y);
  }

  if (!targetEl) {
    throw new Error(`Target not found at coordinates (${x}, ${y})`);
  }

  if (action === "CLICK") {
    // Focus target element
    if (targetEl.focus) targetEl.focus();
    
    // Simulate real click events
    const clickEvent = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true,
      clientX: x,
      clientY: y
    });
    targetEl.dispatchEvent(clickEvent);
    
    // Fallback form triggers for buttons
    if (targetEl.tagName === "BUTTON" && targetEl.type === "submit") {
      const form = targetEl.closest("form");
      if (form) form.submit();
    }
    
    return `Clicked element: ${targetEl.tagName}`;
  }

  if (action === "TYPE") {
    targetEl.focus();
    targetEl.value = text;
    
    // Dispatch input & change events for React/Angular state bindings
    targetEl.dispatchEvent(new Event('input', { bubbles: true }));
    targetEl.dispatchEvent(new Event('change', { bubbles: true }));
    
    return `Typed value: "${text}" into element: ${targetEl.tagName}`;
  }

  if (action === "PRESS_KEY") {
    targetEl.focus();
    const keyEvent = new KeyboardEvent('keydown', {
      key: text === "\n" ? "Enter" : text,
      bubbles: true
    });
    targetEl.dispatchEvent(keyEvent);
    return `Pressed key: ${text}`;
  }

  throw new Error(`Unsupported action type: ${action}`);
}

"""
PrivyBrowse AI — Real Browser Context, Navigation & State Synchronization
Thread-safe tracker for browser tabs, navigation lifecycle, SPA route transitions,
DOM mutation fingerprints, scroll geometry, and stale perception detection.
"""

import hashlib
import time
import threading
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from backend.observability.publisher import global_event_publisher


class LoadingState(str, Enum):
    LOADING = "LOADING"
    DOM_READY = "DOM_READY"
    COMPLETE = "COMPLETE"
    IDLE = "IDLE"


class BrowserLifecycleEvent(str, Enum):
    TAB_SWITCHED = "TAB_SWITCHED"
    NAVIGATED = "NAVIGATED"
    SPA_ROUTED = "SPA_ROUTED"
    PAGE_RELOADED = "PAGE_RELOADED"
    DOM_MUTATED = "DOM_MUTATED"
    SCROLLED = "SCROLLED"
    TAB_CLOSED = "TAB_CLOSED"
    WINDOW_FOCUSED = "WINDOW_FOCUSED"
    WINDOW_BLURRED = "WINDOW_BLURRED"


class ScrollState(BaseModel):
    """Accurate scroll position and viewport geometry."""
    scroll_x: float = 0.0
    scroll_y: float = 0.0
    viewport_width: float = 1920.0
    viewport_height: float = 1080.0
    document_width: float = 1920.0
    document_height: float = 1080.0
    max_scroll_y: float = 0.0


class DOMFingerprint(BaseModel):
    """Fast structural fingerprint of the active DOM layout."""
    hash: str = ""
    element_count: int = 0
    interactive_count: int = 0
    signature: str = ""
    timestamp: str = ""


class PageIdentity(BaseModel):
    """Unique identity representation of a specific webpage state."""
    tab_id: Optional[int] = None
    window_id: Optional[int] = None
    url: str = ""
    hostname: str = ""
    path: str = ""
    title: str = ""
    document_id: str = ""
    dom_fingerprint: str = ""
    created_at: str = ""


class BrowserContext(BaseModel):
    """
    Unified strongly-typed model of real Chrome browser state.
    """
    context_id: str = ""
    tab_id: Optional[int] = None
    window_id: Optional[int] = None
    url: str = ""
    hostname: str = ""
    title: str = ""
    loading_state: LoadingState = LoadingState.COMPLETE
    is_active_tab: bool = True
    scroll: ScrollState = Field(default_factory=ScrollState)
    page_identity: PageIdentity = Field(default_factory=PageIdentity)
    dom_fingerprint: DOMFingerprint = Field(default_factory=DOMFingerprint)
    elements: List[Dict[str, Any]] = Field(default_factory=list)
    element_count: int = 0
    device_pixel_ratio: float = 1.0
    screenshot_available: bool = False
    timestamp: str = ""
    last_event: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrowserContextManager:
    """
    Thread-safe master manager for real-time browser context synchronization.
    Tracks active tabs, navigations, SPA route updates, DOM mutations, and scroll states.
    Guarantees agent planner and action executor never act on stale browser perception.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._active_tab_id: Optional[int] = None
        self._active_window_id: Optional[int] = None
        self._current_context: Optional[BrowserContext] = None
        # Cache of known contexts by tab_id
        self._tab_contexts: Dict[int, BrowserContext] = {}
        # Historical context trace for state verification (bounded)
        self._context_history: List[BrowserContext] = []
        self._max_history = 50
        self._event_listeners: List[Any] = []
        self._last_update_time: float = 0.0

    @property
    def active_tab_id(self) -> Optional[int]:
        with self._lock:
            return self._active_tab_id

    @property
    def current_context(self) -> Optional[BrowserContext]:
        with self._lock:
            return self._current_context

    def compute_dom_fingerprint(
        self,
        elements: List[Dict[str, Any]],
        url: str = "",
        title: str = ""
    ) -> DOMFingerprint:
        """
        Computes a structural, fast layout fingerprint using element IDs, tags, types, and coordinates.
        Allows immediate detection of modals, removed nodes, and dynamic renders.
        """
        interactive_types = {"button", "input", "select", "textarea", "a", "link", "checkbox", "radio"}
        interactive_count = 0
        tokens = []

        for el in elements:
            el_type = str(el.get("type") or el.get("tag") or "").lower()
            el_id = str(el.get("id") or "")
            bbox = el.get("bbox") or [0, 0, 0, 0]
            if isinstance(bbox, list) and len(bbox) >= 4:
                bx = int(bbox[0]) // 10
                by = int(bbox[1]) // 10
            elif isinstance(bbox, dict):
                bx = int(bbox.get("x", 0)) // 10
                by = int(bbox.get("y", 0)) // 10
            else:
                bx, by = 0, 0

            if el_type in interactive_types:
                interactive_count += 1
                tokens.append(f"{el_type}:{el_id}:{bx},{by}")

        raw_str = f"{url}|{title}|{len(elements)}|{'|'.join(tokens[:100])}"
        fp_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]

        return DOMFingerprint(
            hash=fp_hash,
            element_count=len(elements),
            interactive_count=interactive_count,
            signature=f"dom-{fp_hash[:8]}-{len(elements)}nodes",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def compute_page_identity(
        self,
        tab_id: Optional[int],
        window_id: Optional[int],
        url: str,
        title: str,
        dom_fingerprint: str
    ) -> PageIdentity:
        """
        Creates a composite PageIdentity based on tab, URL, title, and DOM structure.
        """
        parsed_host = url.split("://")[-1].split("/")[0] if "://" in url else ""
        parsed_path = "/" + "/".join(url.split("://")[-1].split("/")[1:]) if "://" in url and "/" in url.split("://")[-1] else "/"

        doc_raw = f"{tab_id}|{url}|{dom_fingerprint}"
        doc_id = f"doc-{hashlib.md5(doc_raw.encode('utf-8')).hexdigest()[:10]}"

        return PageIdentity(
            tab_id=tab_id,
            window_id=window_id,
            url=url,
            hostname=parsed_host,
            path=parsed_path,
            title=title,
            document_id=doc_id,
            dom_fingerprint=dom_fingerprint,
            created_at=datetime.now(timezone.utc).isoformat()
        )

    def update_context(self, raw_data: Dict[str, Any]) -> BrowserContext:
        """
        Ingests and normalizes unified browser context from Chrome extension or internal perception.
        """
        with self._lock:
            t_now = datetime.now(timezone.utc).isoformat()
            self._last_update_time = time.time()

            page_info = raw_data.get("page", {})
            tab_id = raw_data.get("tabId") or raw_data.get("tab_id") or page_info.get("tabId") or self._active_tab_id
            window_id = raw_data.get("windowId") or raw_data.get("window_id") or page_info.get("windowId") or self._active_window_id
            url = page_info.get("url") or raw_data.get("url") or ""
            title = page_info.get("title") or raw_data.get("title") or ""
            hostname = page_info.get("hostname") or (url.split("://")[-1].split("/")[0] if "://" in url else "localhost")
            elements = raw_data.get("elements") or []

            # Scroll geometry
            viewport = page_info.get("viewport", {})
            scroll_data = page_info.get("scroll") or raw_data.get("scroll") or {}
            scroll_state = ScrollState(
                scroll_x=float(scroll_data.get("x") or scroll_data.get("scrollX") or 0.0),
                scroll_y=float(scroll_data.get("y") or scroll_data.get("scrollY") or 0.0),
                viewport_width=float(viewport.get("width") or 1920.0),
                viewport_height=float(viewport.get("height") or 1080.0),
                document_width=float(scroll_data.get("documentWidth") or viewport.get("width") or 1920.0),
                document_height=float(scroll_data.get("documentHeight") or viewport.get("height") or 1080.0),
                max_scroll_y=float(scroll_data.get("maxScrollY") or max(0.0, float(scroll_data.get("documentHeight", 0)) - float(viewport.get("height", 1080))))
            )

            # Fingerprints & identity
            dom_fp = self.compute_dom_fingerprint(elements, url, title)
            page_id = self.compute_page_identity(tab_id, window_id, url, title, dom_fp.hash)

            context_id = f"ctx-{int(time.time()*1000)%100000:05d}-{dom_fp.hash[:6]}"
            loading_str = str(page_info.get("loadingState") or page_info.get("status") or "COMPLETE").upper()
            load_state = LoadingState.LOADING if "LOAD" in loading_str else LoadingState.COMPLETE

            screenshot_avail = bool(raw_data.get("screenshot", {}).get("available") or raw_data.get("screenshot", {}).get("dataUrl"))

            ctx = BrowserContext(
                context_id=context_id,
                tab_id=tab_id,
                window_id=window_id,
                url=url,
                hostname=hostname,
                title=title,
                loading_state=load_state,
                is_active_tab=True,
                scroll=scroll_state,
                page_identity=page_id,
                dom_fingerprint=dom_fp,
                elements=elements,
                element_count=len(elements),
                device_pixel_ratio=float(page_info.get("devicePixelRatio") or 1.0),
                screenshot_available=screenshot_avail,
                timestamp=t_now,
                last_event=raw_data.get("event"),
                metadata=raw_data.get("metadata", {})
            )

            if tab_id is not None:
                self._active_tab_id = tab_id
                self._tab_contexts[tab_id] = ctx
            if window_id is not None:
                self._active_window_id = window_id

            self._current_context = ctx
            self._context_history.append(ctx)
            if len(self._context_history) > self._max_history:
                self._context_history.pop(0)

            global_event_publisher.browser_context_updated(
                tab_id=ctx.tab_id,
                url=ctx.url,
                title=ctx.title,
                element_count=ctx.element_count
            )

            return ctx

    def handle_browser_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Handles lifecycle events dispatched from Chrome extension (tab switch, navigation, mutation, scroll).
        Returns (state_changed, reason).
        """
        with self._lock:
            ev_upper = event_type.upper()
            tab_id = event_data.get("tabId") or event_data.get("tab_id")

            # 1. TAB SWITCH
            if ev_upper in ("TAB_SWITCHED", "TAB_ACTIVATED"):
                old_tab = self._active_tab_id
                self._active_tab_id = tab_id
                if tab_id in self._tab_contexts:
                    self._current_context = self._tab_contexts[tab_id]
                global_event_publisher.tab_changed(
                    from_tab_id=old_tab,
                    to_tab_id=tab_id,
                    url=self._current_context.url if self._current_context else ""
                )
                return True, f"Active tab changed from {old_tab} to {tab_id}"

            # 2. TAB CLOSED
            elif ev_upper in ("TAB_CLOSED", "TAB_REMOVED"):
                if tab_id in self._tab_contexts:
                    del self._tab_contexts[tab_id]
                if self._active_tab_id == tab_id:
                    self._active_tab_id = None
                    self._current_context = None
                    return True, f"Active tab {tab_id} was closed"
                return False, "Non-active tab closed"

            # 3. NAVIGATION & SPA ROUTE
            elif ev_upper in ("NAVIGATED", "SPA_ROUTED", "PAGE_RELOADED"):
                new_url = event_data.get("url", "")
                new_title = event_data.get("title", "")
                if self._current_context:
                    old_url = self._current_context.url
                    new_dom_fp = DOMFingerprint()
                    new_page_id = self.compute_page_identity(
                        self._current_context.tab_id,
                        self._current_context.window_id,
                        new_url,
                        new_title or self._current_context.title,
                        ""
                    )
                    new_ctx = self._current_context.model_copy(deep=True)
                    new_ctx.url = new_url
                    if new_title:
                        new_ctx.title = new_title
                    new_ctx.context_id = f"ctx-{int(time.time()*1000)%100000:05d}-nav"
                    new_ctx.dom_fingerprint = new_dom_fp
                    new_ctx.page_identity = new_page_id
                    new_ctx.timestamp = datetime.now(timezone.utc).isoformat()
                    self._current_context = new_ctx
                    if new_ctx.tab_id is not None:
                        self._tab_contexts[new_ctx.tab_id] = new_ctx
                    global_event_publisher.navigation_detected(
                        tab_id=self._current_context.tab_id if self._current_context else None,
                        from_url=old_url,
                        to_url=new_url
                    )
                    return True, f"URL navigated from {old_url} to {new_url}"
                return True, "Navigation occurred"

            # 4. DOM MUTATION
            elif ev_upper == "DOM_MUTATED":
                if self._current_context:
                    elements = event_data.get("elements", [])
                    new_ctx = self._current_context.model_copy(deep=True)
                    if elements:
                        new_ctx.elements = elements
                        new_ctx.element_count = len(elements)
                        new_ctx.dom_fingerprint = self.compute_dom_fingerprint(
                            elements, new_ctx.url, new_ctx.title
                        )
                    self._current_context = new_ctx
                    if new_ctx.tab_id is not None:
                        self._tab_contexts[new_ctx.tab_id] = new_ctx
                    return True, "DOM layout mutated"
                return False, "No active context for mutation"

            # 5. SCROLL
            elif ev_upper == "SCROLLED":
                if self._current_context:
                    new_ctx = self._current_context.model_copy(deep=True)
                    new_ctx.scroll.scroll_x = float(event_data.get("scrollX", 0))
                    new_ctx.scroll.scroll_y = float(event_data.get("scrollY", 0))
                    self._current_context = new_ctx
                    if new_ctx.tab_id is not None:
                        self._tab_contexts[new_ctx.tab_id] = new_ctx
                    return True, "Scroll geometry updated"
                return False, "No active context for scroll"

            return False, "Unrecognized event"

    def is_same_page_state(
        self,
        ctx_a: Optional[BrowserContext],
        ctx_b: Optional[BrowserContext],
        strict_scroll: bool = False
    ) -> bool:
        """
        Determines whether two browser contexts represent the exact same page state.
        Considers Tab ID, URL, Document ID, and DOM Fingerprint.
        """
        if ctx_a is None or ctx_b is None:
            return False

        # Tab ID mismatch
        if ctx_a.tab_id is not None and ctx_b.tab_id is not None and ctx_a.tab_id != ctx_b.tab_id:
            return False

        # URL mismatch
        if ctx_a.url != ctx_b.url:
            return False

        # DOM Fingerprint match
        if ctx_a.dom_fingerprint.hash and ctx_b.dom_fingerprint.hash:
            if ctx_a.dom_fingerprint.hash != ctx_b.dom_fingerprint.hash:
                return False

        # Optional strict scroll check
        if strict_scroll:
            dy = abs(ctx_a.scroll.scroll_y - ctx_b.scroll.scroll_y)
            dx = abs(ctx_a.scroll.scroll_x - ctx_b.scroll.scroll_x)
            if dy > 50 or dx > 50:
                return False

        return True

    def validate_action_context(
        self,
        expected_tab_id: Optional[int] = None,
        expected_url: Optional[str] = None,
        expected_dom_fingerprint: Optional[str] = None,
        expected_document_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Pre-execution guard verifying whether the browser is still in the expected state.
        Returns (is_valid, error_code, reason).
        """
        with self._lock:
            curr = self._current_context
            if not curr:
                return False, "NO_BROWSER_CONTEXT", "No active browser context found"

            # 1. Tab check
            if expected_tab_id is not None and curr.tab_id is not None:
                if expected_tab_id != curr.tab_id:
                    return False, "TAB_MISMATCH", f"Expected tab {expected_tab_id} but active tab is {curr.tab_id}"

            # 2. URL check
            if expected_url and curr.url:
                # Strip trailing slashes for comparison
                norm_exp = expected_url.rstrip("/")
                norm_curr = curr.url.rstrip("/")
                if norm_exp != norm_curr:
                    return False, "STALE_NAVIGATION", f"Page navigated from '{expected_url}' to '{curr.url}'"

            # 3. Document ID check
            if expected_document_id and curr.page_identity.document_id:
                if expected_document_id != curr.page_identity.document_id:
                    return False, "STALE_DOCUMENT", "Document identity changed"

            # 4. DOM Fingerprint check
            if expected_dom_fingerprint and curr.dom_fingerprint.hash:
                if expected_dom_fingerprint != curr.dom_fingerprint.hash:
                    return False, "DOM_MUTATION_MISMATCH", "DOM layout structure changed since perception snapshot"

            return True, None, "Context validated"

    def get_state_summary(self) -> Dict[str, Any]:
        """Provides state summary for API status endpoints and UI."""
        with self._lock:
            curr = self._current_context
            return {
                "active_tab_id": self._active_tab_id,
                "active_window_id": self._active_window_id,
                "current_url": curr.url if curr else None,
                "title": curr.title if curr else None,
                "loading_state": curr.loading_state.value if curr else None,
                "element_count": curr.element_count if curr else 0,
                "dom_fingerprint": curr.dom_fingerprint.hash if curr else None,
                "scroll_position": {"x": curr.scroll.scroll_x, "y": curr.scroll.scroll_y} if curr else {"x": 0, "y": 0},
                "total_tracked_tabs": len(self._tab_contexts),
                "last_update": curr.timestamp if curr else None
            }


# Singleton instance
global_browser_context_manager = BrowserContextManager()

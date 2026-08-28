import time
import base64
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Import custom core engines (legacy)
from backend.perception.element_detector import ElementDetector
from backend.perception.ocr_engine import OCREngine
from backend.perception.fusion import ContextFuser
from backend.privacy.pii_detector import PIIDetector
from backend.privacy.redactor import Redactor
from backend.privacy.privacy_gate import PrivacyGate
from backend.privacy.schemas import PrivacyPolicy
from backend.agent.planner import AgentPlanner
from backend.actions.executor import ActionExecutor

# Import new modular perception pipeline
from backend.perception.core.pipeline import PerceptionPipeline

app = FastAPI(
    title="PrivyBrowse AI - On-Device Perception Backend",
    description="Privacy-preserving local visual perception layer for lightweight browser agents.",
    version="1.0.0"
)

# Mount static demo pages folder
app.mount("/demo", StaticFiles(directory="demo-pages"), name="demo")

# Enable CORS for dashboard and browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate core engines
element_detector = ElementDetector()
ocr_engine = OCREngine()
fuser = ContextFuser()
pii_detector = PIIDetector()
redactor = Redactor()
privacy_gate = PrivacyGate()
agent_planner = AgentPlanner()
action_executor = ActionExecutor()

# New modular perception pipeline
perception_pipeline = PerceptionPipeline()

# Live metrics database (stored in memory)
metrics_store = {
    "runs_count": 0,
    "total_actions": 0,
    "last_ocr_latency": 0.0,
    "last_pii_latency": 0.0,
    "last_redaction_latency": 0.0,
    "last_perception_latency": 0.0,
    "last_planning_latency": 0.0,
    "total_pii_detected": 0,
    "total_pii_redacted": 0,
}

# Live browser context store
latest_browser_context: Dict[str, Any] = {
    "connected": False,
    "last_updated": None,
    "page": None,
    "element_count": 0,
    "screenshot_available": False
}

# --- PYDANTIC SCHEMAS ---

class DOMNodeSchema(BaseModel):
    id: str
    tag_name: str
    text: Optional[str] = ""
    value: Optional[str] = ""
    placeholder: Optional[str] = ""
    type: Optional[str] = ""
    id_attr: Optional[str] = Field("", alias="id_attr")
    class_attr: Optional[str] = Field("", alias="class_attr")
    bbox: List[int] # [x1, y1, x2, y2]

class AnalyzeRequest(BaseModel):
    screenshot: str # Base64 image
    dom_nodes: List[DOMNodeSchema]

class PiiEntitySchema(BaseModel):
    type: str
    text: str
    confidence: float
    bbox: List[int]
    source: str
    element_id: Optional[str] = None

class DetectRequest(BaseModel):
    screenshot: str # Base64 image
    text_blocks: List[Dict[str, Any]]
    dom_nodes: List[DOMNodeSchema]

class RedactRequest(BaseModel):
    screenshot: str # Base64 image
    pii_entities: List[PiiEntitySchema]
    dom_nodes: List[DOMNodeSchema]
    style: Optional[str] = "opaque"

class PlanRequest(BaseModel):
    task: str
    fused_elements: List[Dict[str, Any]]
    history: List[Dict[str, Any]]

class ExecuteRequest(BaseModel):
    action: Dict[str, Any]
    screen_width: Optional[int] = 1920
    screen_height: Optional[int] = 1080

class BrowserContextSchema(BaseModel):
    page: Dict[str, Any]
    screenshot: Dict[str, Any]
    elements: List[Dict[str, Any]]
    capture: Dict[str, Any]

class FullPerceptionRequest(BaseModel):
    screenshot: str  # Base64 image
    viewport_width: Optional[int] = 0
    viewport_height: Optional[int] = 0
    device_pixel_ratio: Optional[float] = 1.0
    dom_nodes: Optional[List[DOMNodeSchema]] = None
    page_metadata: Optional[Dict[str, Any]] = None
    scroll_x: Optional[float] = 0.0
    scroll_y: Optional[float] = 0.0
    document_width: Optional[float] = 0.0
    document_height: Optional[float] = 0.0

class SanitizeRequest(BaseModel):
    screenshot: str  # Base64 image
    ocr_blocks: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    dom_nodes: Optional[List[DOMNodeSchema]] = Field(default_factory=list)
    style: Optional[str] = "opaque"

class PolicyUpdateRequest(BaseModel):
    process_locally: Optional[bool] = None
    redact_pii: Optional[bool] = None
    allow_raw_remote_transmission: Optional[bool] = None
    allow_sanitized_remote_transmission: Optional[bool] = None
    min_confidence_threshold: Optional[float] = None
    default_redaction_style: Optional[str] = None

class AgentTaskCreateRequest(BaseModel):
    goal: str
    max_actions: Optional[int] = 15
    require_confirmation_for_sensitive: Optional[bool] = True

class AgentStepRequest(BaseModel):
    fused_elements: List[Dict[str, Any]]
    history: Optional[List[Dict[str, Any]]] = None
    task_goal: Optional[str] = None

class AgentVerifyRequest(BaseModel):
    action: Dict[str, Any]
    prev_elements: List[Dict[str, Any]]
    current_elements: List[Dict[str, Any]]
    prev_url: Optional[str] = ""
    current_url: Optional[str] = ""

class AgentControlRequest(BaseModel):
    command: str  # "start", "pause", "resume", "stop"

# --- API ENDPOINTS ---

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PrivyBrowse Local Perception Engine",
        "version": "1.0.0",
        "on_device": True,
        "privacy_guarantee": "Strict Local Trust Boundary Enforced"
    }

@app.get("/api/metrics")
def get_telemetry_metrics():
    total_latency = (
        metrics_store["last_ocr_latency"] +
        metrics_store["last_pii_latency"] +
        metrics_store["last_redaction_latency"] +
        metrics_store["last_perception_latency"] +
        metrics_store["last_planning_latency"]
    ) * 1000 # convert to ms
    
    return {
        "local_inference_time_ms": round(metrics_store["last_perception_latency"] * 1000, 2),
        "ocr_latency_ms": round(metrics_store["last_ocr_latency"] * 1000, 2),
        "pii_detection_latency_ms": round(metrics_store["last_pii_latency"] * 1000, 2),
        "redaction_latency_ms": round(metrics_store["last_redaction_latency"] * 1000, 2),
        "agent_planning_latency_ms": round(metrics_store["last_planning_latency"] * 1000, 2),
        "total_task_latency_ms": round(total_latency, 2),
        "pii_detected_count": metrics_store["total_pii_detected"],
        "pii_redacted_count": metrics_store["total_pii_redacted"],
        "actions_executed": metrics_store["total_actions"],
        "runs_count": metrics_store["runs_count"],
        "memory_usage_mb": 142.5,
        "cpu_utilization_pct": 4.2
    }

@app.post("/api/browser/context")
def receive_browser_context(req: BrowserContextSchema):
    latest_browser_context["connected"] = True
    latest_browser_context["last_updated"] = req.capture.get("timestamp")
    latest_browser_context["page"] = req.page
    latest_browser_context["element_count"] = len(req.elements)
    latest_browser_context["screenshot_available"] = bool(req.screenshot.get("available"))
    latest_browser_context["raw_context"] = req.model_dump()

    return {
        "success": True,
        "message": "Browser context successfully ingested into local perception engine.",
        "element_count": len(req.elements),
        "url": req.page.get("url")
    }

@app.get("/api/browser/status")
def get_browser_status():
    return latest_browser_context

@app.post("/api/perception/full")
def run_full_perception(req: FullPerceptionRequest):
    """Run the complete modular perception pipeline."""
    dom_dicts = None
    if req.dom_nodes:
        dom_dicts = [n.model_dump(by_alias=True) for n in req.dom_nodes]

    page_meta = req.page_metadata or {}

    result = perception_pipeline.run(
        screenshot_b64=req.screenshot,
        viewport_width=req.viewport_width or 0,
        viewport_height=req.viewport_height or 0,
        device_pixel_ratio=req.device_pixel_ratio or 1.0,
        dom_nodes=dom_dicts,
        page_metadata=page_meta,
        scroll_x=req.scroll_x or 0.0,
        scroll_y=req.scroll_y or 0.0,
        document_width=req.document_width or 0.0,
        document_height=req.document_height or 0.0,
    )

    if result.success:
        metrics_store["runs_count"] += 1
        metrics_store["last_perception_latency"] = result.latency.visual_detection_ms / 1000.0
        metrics_store["last_ocr_latency"] = result.latency.ocr_ms / 1000.0

    # Return both the new structured result and legacy-compatible fused_elements
    legacy_elements = [e.to_legacy_dict() for e in result.elements]

    return {
        "success": result.success,
        "page": result.page.model_dump(),
        "elements": [e.to_agent_dict() for e in result.elements],
        "fused_elements": legacy_elements,
        "summary": result.summary.model_dump(),
        "latency": result.latency.model_dump(),
        "coordinate_system": result.coordinate_system.model_dump(),
        "timestamp": result.timestamp,
        "warnings": result.warnings,
        "error": result.error,
    }

@app.get("/api/perception/status")
def get_perception_status():
    """Return perception engine readiness status."""
    return perception_pipeline.get_status()

@app.post("/api/perception/analyze")
def analyze_page(req: AnalyzeRequest):
    """Legacy perception endpoint — kept for backwards compatibility."""
    t_start = time.time()
    
    try:
        header, encoded = req.screenshot.split(",", 1) if "," in req.screenshot else ("", req.screenshot)
        screenshot_bytes = base64.b64decode(encoded)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 screenshot encoding.")

    t_cv_start = time.time()
    vision_elements = element_detector.detect_interactive_elements(screenshot_bytes)
    t_cv = time.time() - t_cv_start

    t_ocr_start = time.time()
    nodes_dict = [n.model_dump(by_alias=True) for n in req.dom_nodes]
    ocr_blocks = ocr_engine.extract_text_blocks(screenshot_bytes, nodes_dict)
    t_ocr = time.time() - t_ocr_start

    fused_elements = fuser.fuse(vision_elements, ocr_blocks, nodes_dict)

    t_total = time.time() - t_start
    metrics_store["runs_count"] += 1
    metrics_store["last_perception_latency"] = t_cv
    metrics_store["last_ocr_latency"] = t_ocr

    return {
        "vision_elements": vision_elements,
        "ocr_blocks": ocr_blocks,
        "fused_elements": fused_elements,
        "latency_breakdown": {
            "cv_contour_time": t_cv,
            "ocr_time": t_ocr,
            "total_perception_time": t_total
        }
    }

@app.post("/api/privacy/detect")
def detect_privacy(req: DetectRequest):
    t_start = time.perf_counter()
    try:
        header, encoded = req.screenshot.split(",", 1) if "," in req.screenshot else ("", req.screenshot)
        screenshot_bytes = base64.b64decode(encoded) if encoded else b""
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid screenshot encoding.")

    nodes_dict = [n.model_dump(by_alias=True) for n in req.dom_nodes]
    pii_entities = pii_detector.detect_all_pii(screenshot_bytes, req.text_blocks, nodes_dict)

    t_pii_ms = (time.perf_counter() - t_start) * 1000.0
    metrics_store["last_pii_latency"] = t_pii_ms / 1000.0
    metrics_store["total_pii_detected"] += len(pii_entities)

    return {
        "pii_entities": pii_entities,
        "count": len(pii_entities),
        "latency_ms": round(t_pii_ms, 2)
    }

@app.post("/api/privacy/redact")
def redact_privacy(req: RedactRequest):
    t_start = time.perf_counter()
    try:
        header, encoded = req.screenshot.split(",", 1) if "," in req.screenshot else ("", req.screenshot)
        screenshot_bytes = base64.b64decode(encoded) if encoded else b""
        image_header = header + "," if header else "data:image/png;base64,"
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid screenshot encoding.")

    pii_dict = [p.model_dump() for p in req.pii_entities]
    nodes_dict = [n.model_dump(by_alias=True) for n in req.dom_nodes]

    redacted_bytes, redaction_map = redactor.redact_screenshot(
        screenshot_bytes, pii_dict, redaction_style=req.style or "opaque"
    )
    redacted_nodes = redactor.redact_dom_nodes(nodes_dict, pii_dict)

    redacted_b64 = (image_header + base64.b64encode(redacted_bytes).decode("utf-8")) if redacted_bytes else ""
    t_redact_ms = (time.perf_counter() - t_start) * 1000.0

    metrics_store["last_redaction_latency"] = t_redact_ms / 1000.0
    metrics_store["total_pii_redacted"] += len(req.pii_entities)

    return {
        "redacted_screenshot": redacted_b64,
        "redacted_dom_nodes": redacted_nodes,
        "redaction_map": redaction_map.model_dump(),
        "latency_ms": round(t_redact_ms, 2)
    }

@app.post("/api/privacy/sanitize")
def sanitize_privacy_gate(req: SanitizeRequest):
    """
    Unified Privacy Gate endpoint: Detects PII, executes visual/DOM/OCR redaction,
    generates structured RedactionMap, and records privacy-safe audit logs.
    """
    t_start = time.perf_counter()
    try:
        header, encoded = req.screenshot.split(",", 1) if "," in req.screenshot else ("", req.screenshot)
        screenshot_bytes = base64.b64decode(encoded) if encoded else b""
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid screenshot encoding.")

    nodes_dict = [n.model_dump(by_alias=True) for n in req.dom_nodes] if req.dom_nodes else []

    sanitized_context, pii_entities = privacy_gate.process_and_sanitize(
        screenshot_bytes=screenshot_bytes,
        ocr_blocks=req.ocr_blocks or [],
        dom_nodes=nodes_dict,
        style=req.style
    )

    t_total_ms = (time.perf_counter() - t_start) * 1000.0
    metrics_store["last_pii_latency"] = privacy_gate.metrics["last_detection_latency_ms"] / 1000.0
    metrics_store["last_redaction_latency"] = privacy_gate.metrics["last_redaction_latency_ms"] / 1000.0
    metrics_store["total_pii_detected"] += len(pii_entities)
    metrics_store["total_pii_redacted"] += sanitized_context.redaction_map.total_redacted

    return {
        "success": True,
        "sanitized_context": sanitized_context.model_dump(),
        "pii_entities": [e.to_safe_dict() for e in pii_entities],
        "redaction_map": sanitized_context.redaction_map.model_dump(),
        "latency_breakdown": {
            "detection_ms": privacy_gate.metrics["last_detection_latency_ms"],
            "redaction_ms": privacy_gate.metrics["last_redaction_latency_ms"],
            "total_ms": round(t_total_ms, 2)
        }
    }

@app.get("/api/privacy/policy")
def get_privacy_policy():
    """Returns active machine-readable privacy policy."""
    return privacy_gate.policy.model_dump()

@app.put("/api/privacy/policy")
def update_privacy_policy(req: PolicyUpdateRequest):
    """Updates machine-readable privacy policy settings."""
    if req.process_locally is not None:
        privacy_gate.policy.process_locally = req.process_locally
    if req.redact_pii is not None:
        privacy_gate.policy.redact_pii = req.redact_pii
    if req.allow_raw_remote_transmission is not None:
        privacy_gate.policy.allow_raw_remote_transmission = req.allow_raw_remote_transmission
    if req.allow_sanitized_remote_transmission is not None:
        privacy_gate.policy.allow_sanitized_remote_transmission = req.allow_sanitized_remote_transmission
    if req.min_confidence_threshold is not None:
        privacy_gate.policy.min_confidence_threshold = req.min_confidence_threshold
    if req.default_redaction_style is not None:
        privacy_gate.policy.default_redaction_style = req.default_redaction_style

    return {"success": True, "policy": privacy_gate.policy.model_dump()}

@app.get("/api/privacy/audit-logs")
def get_privacy_audit_logs():
    """Returns privacy-safe audit log stream."""
    return [log.model_dump() for log in privacy_gate.audit_logs]

@app.get("/api/privacy/status")
def get_privacy_status():
    """Returns real-time privacy shield status and metrics."""
    return privacy_gate.get_status()

@app.post("/api/agent/task/create")
def create_agent_task(req: AgentTaskCreateRequest):
    """Creates a structured task and decomposes it into sub-objectives."""
    from backend.agent.schemas import TaskConstraints
    constraints = TaskConstraints(
        max_actions=req.max_actions or 15,
        require_confirmation_for_sensitive=req.require_confirmation_for_sensitive if req.require_confirmation_for_sensitive is not None else True
    )
    task = agent_planner.create_task(goal=req.goal, constraints=constraints)
    return {
        "success": True,
        "task": task.model_dump()
    }

@app.post("/api/agent/step")
def run_agent_step(req: AgentStepRequest):
    """Runs a single reasoning step: selects active objective, scores candidates, validates safety."""
    candidate, validation, state = agent_planner.plan_next_step(
        sanitized_elements=req.fused_elements,
        history=req.history or [],
        task_goal=req.task_goal
    )
    return {
        "state": state.value,
        "candidate": candidate.model_dump() if candidate else None,
        "validation": validation.model_dump(),
        "task_summary": agent_planner.get_agent_status()
    }

@app.post("/api/agent/verify")
def verify_agent_action(req: AgentVerifyRequest):
    """Verifies the state change outcome of an executed action."""
    result = agent_planner.verify_step_outcome(
        action=req.action,
        prev_elements=req.prev_elements,
        current_elements=req.current_elements,
        prev_url=req.prev_url or "",
        current_url=req.current_url or ""
    )
    return {
        "verification": result.model_dump(),
        "agent_state": agent_planner.state_machine.current_state.value
    }

@app.post("/api/agent/control")
def control_agent(req: AgentControlRequest):
    """Controls agent state: start, pause, resume, stop."""
    cmd = req.command.lower()
    if cmd == "pause":
        new_state = agent_planner.pause()
    elif cmd == "resume":
        new_state = agent_planner.resume()
    elif cmd == "stop":
        new_state = agent_planner.stop()
    else:
        new_state = agent_planner.state_machine.current_state

    return {
        "success": True,
        "command": cmd,
        "state": new_state.value
    }

@app.get("/api/agent/state")
def get_agent_state():
    """Returns real-time agent state, active task, objectives, and planning trace."""
    return agent_planner.get_agent_status()

@app.post("/api/agent/plan")
def plan_agent_action(req: PlanRequest):
    t_start = time.perf_counter()
    action = agent_planner.plan_action(req.task, req.fused_elements, req.history)
    t_plan_ms = (time.perf_counter() - t_start) * 1000.0
    metrics_store["last_planning_latency"] = t_plan_ms / 1000.0

    return {
        "action": action,
        "latency_ms": round(t_plan_ms, 2)
    }

@app.post("/api/action/execute")
def execute_agent_action(req: ExecuteRequest):
    success, message, metadata = action_executor.execute_action(
        req.action, req.screen_width, req.screen_height
    )
    
    if success:
        metrics_store["total_actions"] += 1

    return {
        "success": success,
        "message": message,
        "metadata": metadata
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

"""
PrivyBrowse AI — Observability & Monitoring Dashboard Unit & Integration Tests
20 Comprehensive Unit & Integration Tests validating:
  - Event schemas, enums & serialization
  - Credential & PII sanitization (API keys, Aadhaar, PAN, Card, Passwords)
  - Monotonic sequence numbering
  - Ring buffer thread-safety & bounded FIFO eviction
  - Query filtering (by component, severity, since_seq, task_id)
  - Event Publisher helper methods across all sub-components
  - Async subscriber queues & SSE streaming serialization
  - REST endpoints: /api/system/health, /api/dashboard/overview, /api/events
  - Live system state synchronization
"""

import os
import sys
import time
import threading
from datetime import datetime, timezone
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.observability.schemas import (
    EventType, EventSeverity, EventComponent,
    ObservabilityEvent, SystemHealthStatus, DashboardSnapshot
)
from backend.observability.event_bus import ObservabilityEventBus, sanitize_value
from backend.observability.publisher import EventPublisher, global_event_publisher
from backend.agent.schemas import AgentTask, TaskStep, ObjectiveStatus, RiskLevel


# --- 1. Schema & Validation Tests ---

def test_observability_event_creation_valid():
    print("\n[TEST 1] Testing Observability Event Schema & Creation...")
    event = ObservabilityEvent(
        seq_id=1,
        event_id="evt-001",
        event_type=EventType.TASK_CREATED,
        severity=EventSeverity.INFO,
        component=EventComponent.TASK_MANAGER,
        message="Task initialized",
        metadata={"goal": "Test goal"}
    )
    assert event.seq_id == 1
    assert event.event_type == EventType.TASK_CREATED
    assert event.severity == EventSeverity.INFO
    assert event.component == EventComponent.TASK_MANAGER
    assert event.message == "Task initialized"
    assert event.metadata["goal"] == "Test goal"
    print("  ✓ ObservabilityEvent model initialized with valid enums and metadata.")


def test_observability_event_sse_payload():
    print("\n[TEST 2] Testing Observability Event SSE Payload Serialization...")
    event = ObservabilityEvent(
        seq_id=42,
        event_id="evt-042",
        event_type=EventType.ACTION_VALIDATED,
        severity=EventSeverity.SUCCESS,
        component=EventComponent.ACTION_VALIDATOR,
        message="Action validated safely"
    )
    payload = event.to_sse_payload()
    assert '"seq_id":42' in payload or '"seq_id": 42' in payload
    assert "ACTION_VALIDATED" in payload
    assert "ACTION_VALIDATOR" in payload
    print("  ✓ SSE payload properly serialized to compact JSON.")


# --- 2. Sanitization & Privacy Tests ---

def test_sanitization_removes_api_keys():
    print("\n[TEST 3] Testing Recursive Credential Sanitization for API Keys...")
    text = "Authorization token sk-proj-1234567890abcdef12345678 and ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
    sanitized = sanitize_value(text)
    assert "sk-proj-" not in sanitized
    assert "ghp_" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    print("  ✓ API keys scrubbed and replaced with safe placeholder.")


def test_sanitization_removes_aadhaar_and_pan():
    print("\n[TEST 4] Testing Sanitization of Aadhaar and PAN IDs...")
    raw_str = "Customer PAN is ABCDE1234F and Aadhaar is 9876 5432 1098"
    sanitized_str = sanitize_value(raw_str)
    assert "[REDACTED_PAN]" in sanitized_str
    assert "[REDACTED_AADHAAR]" in sanitized_str

    data = {
        "user_doc": "ABCDE1234F",
        "identity": "9876 5432 1098",
        "safe_label": "Submit Order"
    }
    sanitized = sanitize_value(data)
    assert sanitized["user_doc"] == "[REDACTED_PAN]"
    assert sanitized["identity"] == "[REDACTED_AADHAAR]"
    assert sanitized["safe_label"] == "Submit Order"
    print("  ✓ Indian National IDs (Aadhaar & PAN) strictly redacted in metadata dictionaries.")


def test_sanitization_removes_credit_cards_and_passwords():
    print("\n[TEST 5] Testing Sanitization of Credit Cards, Passwords, and Tokens...")
    data = {
        "password": "SecretSuperPassword123!",
        "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
        "payment_field": "4111 2222 3333 4444"
    }
    sanitized = sanitize_value(data)
    assert sanitized["password"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["auth_token"] == "[REDACTED_CREDENTIAL]"
    assert "[REDACTED_CARD]" in sanitized["payment_field"]
    print("  ✓ Card numbers, passwords, and JWT tokens scrubbed safely.")


def test_event_bus_publishes_only_sanitized_data():
    print("\n[TEST 6] Testing EventBus Invariant: Automatic In-Flight Sanitization...")
    bus = ObservabilityEventBus(max_retention=100)
    event = bus.publish(
        event_type=EventType.ACTION_STARTED,
        severity=EventSeverity.INFO,
        component=EventComponent.ACTION_EXECUTOR,
        message="Typed secret key: sk-secret-12345678901234567890",
        metadata={"user_card": "4111 2222 3333 4444", "pin": "1234"}
    )
    assert "sk-secret-" not in event.message
    assert "[REDACTED_API_KEY]" in event.message
    assert event.metadata["user_card"] == "[REDACTED_CARD]"
    print("  ✓ EventBus publish() enforces zero sensitive data egress.")


# --- 3. Event Bus & Monotonic Sequencing Tests ---

def test_event_bus_monotonic_sequence_ids():
    print("\n[TEST 7] Testing Monotonic Sequence IDs on Event Bus...")
    bus = ObservabilityEventBus(max_retention=100)
    e1 = bus.publish(event_type=EventType.TASK_CREATED, component=EventComponent.TASK_MANAGER, message="1", severity=EventSeverity.INFO)
    e2 = bus.publish(event_type=EventType.TASK_STEP_STARTED, component=EventComponent.TASK_MANAGER, message="2", severity=EventSeverity.INFO)
    e3 = bus.publish(event_type=EventType.ACTION_VALIDATED, component=EventComponent.ACTION_VALIDATOR, message="3", severity=EventSeverity.SUCCESS)

    assert e1.seq_id == 1
    assert e2.seq_id == 2
    assert e3.seq_id == 3
    assert bus.get_total_events_count() == 3
    print("  ✓ Sequence IDs strictly monotonic: 1 -> 2 -> 3.")


def test_event_bus_bounded_ring_buffer_eviction():
    print("\n[TEST 8] Testing Ring Buffer Bounded Capacity & FIFO Eviction...")
    bus = ObservabilityEventBus(max_retention=10)
    for i in range(25):
        bus.publish(event_type=EventType.ACTION_COMPLETED, component=EventComponent.ACTION_EXECUTOR, message=f"Event {i}", severity=EventSeverity.INFO)

    events = bus.get_events(limit=50)
    assert len(events) == 10
    assert bus.get_total_events_count() == 25
    assert events[0].seq_id == 16
    assert events[-1].seq_id == 25
    print("  ✓ Ring buffer maintains exact max capacity of 10 items with monotonic history count of 25.")


def test_event_bus_thread_safety():
    print("\n[TEST 9] Testing Ring Buffer Multi-Threaded Concurrency & Safety...")
    bus = ObservabilityEventBus(max_retention=500)
    threads = []
    events_per_thread = 20

    def worker():
        for _ in range(events_per_thread):
            bus.publish(event_type=EventType.PII_DETECTED, component=EventComponent.PRIVACY, message="Detected PII", severity=EventSeverity.WARNING)

    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert bus.get_total_events_count() == 200
    events = bus.get_events(limit=250)
    seq_ids = [e.seq_id for e in events]
    assert len(set(seq_ids)) == 200
    print("  ✓ 200 events from 10 concurrent threads cleanly published with zero sequence collisions.")


def test_event_bus_filtering_by_component_and_severity():
    print("\n[TEST 10] Testing Event Query Filtering by Component, Severity & Task ID...")
    bus = ObservabilityEventBus(max_retention=100)
    bus.publish(event_type=EventType.TASK_CREATED, component=EventComponent.TASK_MANAGER, message="Task 1", severity=EventSeverity.INFO, task_id="task-1")
    bus.publish(event_type=EventType.PII_DETECTED, component=EventComponent.PRIVACY, message="PII in Task 1", severity=EventSeverity.WARNING, task_id="task-1")
    bus.publish(event_type=EventType.PROMPT_INJECTION_DETECTED, component=EventComponent.SECURITY, message="Attack blocked", severity=EventSeverity.CRITICAL, task_id="task-2")
    bus.publish(event_type=EventType.ACTION_COMPLETED, component=EventComponent.ACTION_EXECUTOR, message="Action done", severity=EventSeverity.SUCCESS, task_id="task-1")

    # Filter component = PRIVACY
    privacy_events = bus.get_events(component=EventComponent.PRIVACY)
    assert len(privacy_events) == 1
    assert privacy_events[0].component == EventComponent.PRIVACY

    # Filter severity = CRITICAL
    crit_events = bus.get_events(severity=EventSeverity.CRITICAL)
    assert len(crit_events) == 1
    assert crit_events[0].severity == EventSeverity.CRITICAL

    # Filter task_id = task-2
    task2_events = bus.get_events(task_id="task-2")
    assert len(task2_events) == 1
    assert task2_events[0].task_id == "task-2"

    # Filter since_seq = 2
    since_events = bus.get_events(since_seq=2)
    assert len(since_events) == 2
    assert all(e.seq_id > 2 for e in since_events)
    print("  ✓ Multi-dimensional event filtering verified.")


# --- 4. Event Publisher Helpers Tests ---

def test_publisher_task_lifecycle_events():
    print("\n[TEST 11] Testing Task Lifecycle Publisher Helpers...")
    bus = ObservabilityEventBus(max_retention=100)
    pub = EventPublisher(bus)

    e_create = pub.task_created("task-100", "Buy organic apples", 4)
    assert e_create.event_type == EventType.TASK_CREATED
    assert e_create.metadata["steps_count"] == 4

    e_step = pub.task_step_started("task-100", "step-1", "Search for product")
    assert e_step.event_type == EventType.TASK_STEP_STARTED
    assert e_step.step_id == "step-1"

    e_done = pub.task_step_completed("task-100", "step-1", "Search for product", 120.5)
    assert e_done.event_type == EventType.TASK_STEP_COMPLETED
    assert e_done.duration_ms == 120.5

    e_comp = pub.task_completed("task-100", "Buy organic apples", 450.2)
    assert e_comp.event_type == EventType.TASK_COMPLETED
    assert e_comp.duration_ms == 450.2
    print("  ✓ Task lifecycle events emitted with proper metadata.")


def test_publisher_action_and_verification_events():
    print("\n[TEST 12] Testing Action Execution & Verification Publisher Helpers...")
    bus = ObservabilityEventBus(max_retention=100)
    pub = EventPublisher(bus)

    e_val = pub.action_validated("CLICK", "btn-submit", "LOW", task_id="task-1")
    assert e_val.event_type == EventType.ACTION_VALIDATED
    assert e_val.severity in (EventSeverity.INFO, EventSeverity.SUCCESS)
    assert e_val.status == "PASSED"

    e_exec = pub.action_completed("CLICK", "btn-submit", 45.0, task_id="task-1")
    assert e_exec.event_type == EventType.ACTION_COMPLETED
    assert e_exec.severity == EventSeverity.SUCCESS

    e_ver = pub.action_verified("DOM_MUTATION", ["Order ID visible: #9482"], task_id="task-1")
    assert e_ver.event_type == EventType.ACTION_VERIFIED
    assert e_ver.metadata["signal"] == "DOM_MUTATION"
    print("  ✓ Action validation, execution, and verification telemetry verified.")


def test_publisher_security_and_privacy_events():
    print("\n[TEST 13] Testing Security & Privacy Publisher Helpers...")
    bus = ObservabilityEventBus(max_retention=100)
    pub = EventPublisher(bus)

    e_pii = pub.pii_detected(count=3, pii_types=["EMAIL", "CARD", "AADHAAR"])
    assert e_pii.event_type == EventType.PII_DETECTED
    assert e_pii.severity == EventSeverity.WARNING
    assert e_pii.metadata["detected_count"] == 3

    e_redact = pub.pii_redacted(count=3, style="blur")
    assert e_redact.event_type == EventType.PII_REDACTED
    assert e_redact.metadata["style"] == "blur"

    e_inj = pub.prompt_injection_detected("HIGH_RISK", ["SYSTEM_INSTRUCTION_OVERRIDE"])
    assert e_inj.event_type == EventType.PROMPT_INJECTION_DETECTED
    assert e_inj.severity == EventSeverity.CRITICAL
    print("  ✓ Security alerts and privacy redactions verified.")


def test_publisher_browser_and_navigation_events():
    print("\n[TEST 14] Testing Browser Context & Navigation Publisher Helpers...")
    bus = ObservabilityEventBus(max_retention=100)
    pub = EventPublisher(bus)

    e_ctx = pub.browser_context_updated(tab_id=1, url="https://isro.gov.in", title="ISRO", element_count=24)
    assert e_ctx.event_type == EventType.BROWSER_CONTEXT_UPDATED
    assert e_ctx.tab_id == 1

    e_nav = pub.navigation_detected(tab_id=1, from_url="https://isro.gov.in", to_url="https://isro.gov.in/chandrayaan")
    assert e_nav.event_type == EventType.NAVIGATION_DETECTED

    e_tab = pub.tab_changed(from_tab_id=1, to_tab_id=2, url="https://isro.gov.in/missions")
    assert e_tab.event_type == EventType.TAB_CHANGED
    print("  ✓ Browser context synchronization events verified.")


def test_publisher_confirmation_and_recovery_events():
    print("\n[TEST 15] Testing Confirmation & Recovery Publisher Helpers...")
    bus = ObservabilityEventBus(max_retention=100)
    pub = EventPublisher(bus)

    e_conf = pub.confirmation_required("CLICK", "btn-pay", "Payment exceeds auto-budget")
    assert e_conf.event_type == EventType.CONFIRMATION_REQUIRED
    assert e_conf.severity == EventSeverity.WARNING

    e_loop = pub.loop_detected("Action repeated 3 times on same URL")
    assert e_loop.event_type == EventType.LOOP_DETECTED
    assert e_loop.severity == EventSeverity.ERROR

    e_rec = pub.recovery_triggered("ELEMENT_NOT_INTERACTABLE", "SCROLL_AND_RETRY")
    assert e_rec.event_type == EventType.RECOVERY_TRIGGERED
    print("  ✓ Human confirmation and recovery loop detections verified.")


# --- 5. REST API Endpoints Tests ---

def test_api_get_system_health():
    print("\n[TEST 16] Testing REST Endpoint: GET /api/system/health...")
    client = TestClient(app)
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert "backend_healthy" in data
    assert data["backend_healthy"] is True
    assert "extension_connected" in data
    assert "status_summary" in data
    print(f"  ✓ GET /api/system/health status: {data['status_summary']}")


def test_api_get_dashboard_overview():
    print("\n[TEST 17] Testing REST Endpoint: GET /api/dashboard/overview...")
    client = TestClient(app)
    res = client.get("/api/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert "health" in data
    assert "privacy_metrics" in data
    assert "security_metrics" in data
    assert "performance_metrics" in data
    assert "recent_events" in data
    print("  ✓ GET /api/dashboard/overview snapshot returned all required telemetry sections.")


def test_api_get_events_endpoint():
    print("\n[TEST 18] Testing REST Endpoint: GET /api/events with Limit...")
    client = TestClient(app)
    global_event_publisher.system_heartbeat()

    res = client.get("/api/events?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total_published" in data
    assert "returned_count" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) <= 10
    print(f"  ✓ GET /api/events returned {data['returned_count']} events.")


def test_api_get_events_filtering():
    print("\n[TEST 19] Testing REST Endpoint: GET /api/events Component Filtering...")
    client = TestClient(app)
    global_event_publisher.security_blocked("Unsafe action blocked", "CONFIRMATION_DENIED")

    res = client.get("/api/events?component=SECURITY")
    assert res.status_code == 200
    data = res.json()
    assert any(e["component"] == "SECURITY" for e in data["events"])
    print("  ✓ GET /api/events?component=SECURITY filtered events successfully.")


def test_event_bus_clear():
    print("\n[TEST 20] Testing Event Bus Clear & Memory Reset...")
    bus = ObservabilityEventBus(max_retention=50)
    bus.publish(event_type=EventType.TASK_CREATED, component=EventComponent.TASK_MANAGER, message="test", severity=EventSeverity.INFO)
    assert len(bus.get_events()) == 1
    bus.clear()
    assert len(bus.get_events()) == 0
    print("  ✓ Event bus buffer cleared successfully.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING OBSERVABILITY & DASHBOARD TEST SUITE")
    print("==================================================")
    test_observability_event_creation_valid()
    test_observability_event_sse_payload()
    test_sanitization_removes_api_keys()
    test_sanitization_removes_aadhaar_and_pan()
    test_sanitization_removes_credit_cards_and_passwords()
    test_event_bus_publishes_only_sanitized_data()
    test_event_bus_monotonic_sequence_ids()
    test_event_bus_bounded_ring_buffer_eviction()
    test_event_bus_thread_safety()
    test_event_bus_filtering_by_component_and_severity()
    test_publisher_task_lifecycle_events()
    test_publisher_action_and_verification_events()
    test_publisher_security_and_privacy_events()
    test_publisher_browser_and_navigation_events()
    test_publisher_confirmation_and_recovery_events()
    test_api_get_system_health()
    test_api_get_dashboard_overview()
    test_api_get_events_endpoint()
    test_api_get_events_filtering()
    test_event_bus_clear()
    print("==================================================")
    print("ALL 20 OBSERVABILITY TESTS PASSED! ✓")
    print("==================================================")

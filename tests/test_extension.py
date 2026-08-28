"""
Unit & Integration Test Suite for PrivyBrowse Chrome Extension & Browser Integration Layer
"""

import sys
import os
import json
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["on_device"] is True
    print("✓ Health endpoint returned healthy status.")

def test_browser_context_ingestion():
    mock_context = {
        "page": {
            "url": "http://localhost:8000/demo/synthetic_eval.html",
            "hostname": "localhost",
            "title": "PrivyBrowse Synthetic Evaluation Portal",
            "viewport": {"width": 1280, "height": 720},
            "devicePixelRatio": 2.0,
            "timestamp": "2026-08-28T08:40:00Z"
        },
        "screenshot": {
            "available": True,
            "dataUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "timestamp": "2026-08-28T08:40:00Z"
        },
        "elements": [
            {
                "id": "pb-element-001",
                "type": "input",
                "tag": "input",
                "text": "[SENSITIVE FIELD]",
                "ariaLabel": "Password",
                "placeholder": "••••••••",
                "role": "textbox",
                "name": "password",
                "inputType": "password",
                "sensitive": True,
                "bbox": {"x": 20, "y": 180, "width": 240, "height": 36, "top": 180, "left": 20, "right": 260, "bottom": 216},
                "visible": True,
                "enabled": True
            },
            {
                "id": "pb-element-002",
                "type": "button",
                "tag": "button",
                "text": "LOGIN",
                "ariaLabel": None,
                "placeholder": None,
                "role": "button",
                "name": None,
                "inputType": "submit",
                "bbox": {"x": 20, "y": 240, "width": 240, "height": 40, "top": 240, "left": 20, "right": 260, "bottom": 280},
                "visible": True,
                "enabled": True
            }
        ],
        "capture": {
            "timestamp": "2026-08-28T08:40:00Z",
            "source": "chrome-extension",
            "elementCount": 2
        }
    }

    # Test POST /api/browser/context
    response = client.post("/api/browser/context", json=mock_context)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["element_count"] == 2
    print("✓ Browser context successfully ingested by FastAPI daemon.")

    # Test GET /api/browser/status
    status_response = client.get("/api/browser/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["connected"] is True
    assert status_data["element_count"] == 2
    assert status_data["page"]["hostname"] == "localhost"
    print("✓ Browser status query returns active connected state.")

def test_synthetic_eval_demo_page():
    response = client.get("/demo/synthetic_eval.html")
    assert response.status_code == 200
    assert "PRIVYBROWSE DEMO" in response.text
    assert "SecretPass123!" in response.text
    print("✓ Synthetic evaluation demo page served successfully under /demo/synthetic_eval.html.")

if __name__ == "__main__":
    print("==================================================")
    print("RUNNING CHROME EXTENSION INTEGRATION TEST SUITE")
    print("==================================================")
    test_health_endpoint()
    test_browser_context_ingestion()
    test_synthetic_eval_demo_page()
    print("==================================================")
    print("ALL BROWSER INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

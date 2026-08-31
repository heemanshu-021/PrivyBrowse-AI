#!/usr/bin/env python3
"""
PrivyBrowse AI — Production Backend Launcher
Validates dependencies and configuration, then launches Uvicorn server.
"""

import sys
import os
import uvicorn

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from scripts.validate_environment import check_python_environment, check_dependencies, check_ocr_binary


def start_server():
    print("=" * 60)
    print(f"PRIVYBROWSE AI — PRODUCTION BACKEND (v{settings.version})")
    print(f"Environment Mode: {settings.env.value.upper()}")
    print(f"Host: {settings.host}:{settings.port}")
    print(f"Simulation Mode: {settings.simulation_mode}")
    print("=" * 60)

    # Fast environment sanity check
    py_ok, py_msg = check_python_environment()
    if not py_ok:
        print(f"[ERROR] {py_msg}")
        sys.exit(1)

    ocr_status, ocr_msg = check_ocr_binary()
    print(f"[OCR] Status: {ocr_status} ({ocr_msg})")

    try:
        uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level=settings.log_level.lower()
        )
    except KeyboardInterrupt:
        print("\n[Shutdown] Backend stopped cleanly via SIGINT.")
    except Exception as e:
        print(f"\n[Fatal Error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_server()

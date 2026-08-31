#!/usr/bin/env python3
"""
PrivyBrowse AI — Production Environment & Installation Validator
Checks Python environment, system dependencies, OCR capabilities,
browser availability, and extension packaging.
"""

import sys
import os
import shutil
import platform
import subprocess
from typing import Dict, Any, Tuple


def check_python_environment() -> Tuple[bool, str]:
    ver = sys.version_info
    ver_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    if ver.major == 3 and ver.minor >= 10:
        return True, f"Python {ver_str} ({platform.machine()} - {platform.system()})"
    return False, f"Python {ver_str} is unsupported. Python 3.10+ required."


def check_dependencies() -> Dict[str, Tuple[bool, str]]:
    deps = {}
    
    # FastAPI & Uvicorn
    try:
        import fastapi
        import uvicorn
        deps["FastAPI / Uvicorn"] = (True, f"fastapi {fastapi.__version__}, uvicorn {uvicorn.__version__}")
    except ImportError as e:
        deps["FastAPI / Uvicorn"] = (False, str(e))

    # Pydantic
    try:
        import pydantic
        deps["Pydantic"] = (True, f"pydantic {pydantic.__version__}")
    except ImportError as e:
        deps["Pydantic"] = (False, str(e))

    # OpenCV
    try:
        import cv2
        deps["OpenCV Headless"] = (True, f"opencv-python {cv2.__version__}")
    except ImportError as e:
        deps["OpenCV Headless"] = (False, str(e))

    # NumPy
    try:
        import numpy as np
        deps["NumPy"] = (True, f"numpy {np.__version__}")
    except ImportError as e:
        deps["NumPy"] = (False, str(e))

    # Pillow
    try:
        import PIL
        deps["Pillow"] = (True, f"Pillow {PIL.__version__}")
    except ImportError as e:
        deps["Pillow"] = (False, str(e))

    # PyTesseract
    try:
        import pytesseract
        deps["PyTesseract Binding"] = (True, "pytesseract installed")
    except ImportError as e:
        deps["PyTesseract Binding"] = (False, str(e))

    return deps


def check_ocr_binary() -> Tuple[str, str]:
    """Probes system for native tesseract binary."""
    tess_path = shutil.which("tesseract")
    if tess_path:
        try:
            res = subprocess.run([tess_path, "--version"], capture_output=True, text=True, timeout=3)
            ver_line = res.stdout.split("\n")[0] if res.stdout else "unknown version"
            return "AVAILABLE", f"Native Tesseract found at '{tess_path}' ({ver_line})"
        except Exception as e:
            return "ERROR", f"Tesseract error: {e}"
    else:
        return "ENVIRONMENT LIMITATION", "Tesseract binary not in PATH — DOM_TEXT_PROXY fallback active"


def check_browser() -> Tuple[str, str]:
    """Detects installed Chrome or Chromium browsers."""
    system = platform.system()
    candidates = []
    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        ]
    elif system == "Linux":
        candidates = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
    elif system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]

    for c in candidates:
        if system in ("Linux",):
            path = shutil.which(c)
            if path:
                return "AVAILABLE", f"Browser found: {path}"
        else:
            if os.path.exists(c):
                return "AVAILABLE", f"Browser found at: {c}"

    return "NOT VERIFIED — ENVIRONMENT LIMITATION", "No standard Chrome installation path detected"


def check_extension_packaging() -> Tuple[bool, str]:
    ext_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extension")
    manifest = os.path.join(ext_dir, "manifest.json")
    bg = os.path.join(ext_dir, "background.js")
    content = os.path.join(ext_dir, "content.js")

    if os.path.exists(manifest) and os.path.exists(bg) and os.path.exists(content):
        return True, f"Manifest V3 extension ready at: {ext_dir}"
    return False, "Extension files missing"


def main():
    print("=" * 60)
    print("PRIVYBROWSE AI — ENVIRONMENT & DEPENDENCY VALIDATION")
    print("=" * 60)

    # 1. Python Check
    py_ok, py_msg = check_python_environment()
    print(f"\n[1] Python Runtime: {'✓ PASS' if py_ok else '✗ FAIL'}")
    print(f"    {py_msg}")

    # 2. Package Dependencies
    print(f"\n[2] Core Dependencies:")
    deps = check_dependencies()
    all_deps_ok = True
    for name, (ok, msg) in deps.items():
        status = "✓ OK" if ok else "✗ MISSING"
        if not ok:
            all_deps_ok = False
        print(f"    - {name:<25}: [{status}] {msg}")

    # 3. OCR Engine Status
    ocr_status, ocr_msg = check_ocr_binary()
    print(f"\n[3] OCR Capability:")
    print(f"    - Status : [{ocr_status}]")
    print(f"    - Details: {ocr_msg}")

    # 4. Browser Availability
    browser_status, browser_msg = check_browser()
    print(f"\n[4] Browser Availability:")
    print(f"    - Status : [{browser_status}]")
    print(f"    - Details: {browser_msg}")

    # 5. Extension Packaging
    ext_ok, ext_msg = check_extension_packaging()
    print(f"\n[5] Browser Extension Packaging: {'✓ PASS' if ext_ok else '✗ FAIL'}")
    print(f"    {ext_msg}")

    # 6. Overall Validation Verdict
    print("\n" + "=" * 60)
    if py_ok and all_deps_ok and ext_ok:
        print("VERDICT: PRODUCTION RUNTIME ENVIRONMENT IS VALID & READY ✓")
        print("=" * 60)
        return 0
    else:
        print("VERDICT: ENVIRONMENT DEFICIENCIES DETECTED ✗")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

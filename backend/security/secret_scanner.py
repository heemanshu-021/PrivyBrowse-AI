"""
PrivyBrowse AI — Local Secret Scanner & Pre-Commit Security Gate
Scans repository code and configuration files on-device for accidental secret leaks.
Never uploads codebase contents to external remote scanners.
"""

import os
import re
from typing import Dict, Any, List
from backend.security.schemas import SecretScanResult


class SecretScanner:
    """
    On-Device Static Secret & Credential Scanner.
    """

    SECRET_PATTERNS = [
        ("AWS_ACCESS_KEY", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
        ("RSA_PRIVATE_KEY", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("OPENAI_API_KEY", re.compile(r"\bsk-[a-zA-Z0-9]{32,}\b")),
        ("GITHUB_PERSONAL_TOKEN", re.compile(r"\bghp_[a-zA-Z0-9]{36}\b")),
        ("GENERIC_JWT_TOKEN", re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b")),
        ("GENERIC_SECRET_ASSIGNMENT", re.compile(r"(?i)\b(?:api_key|secret_key|client_secret|auth_token)\s*=\s*['\"][a-zA-Z0-9_\-]{20,}['\"]"))
    ]

    EXCLUDE_DIRS = {".git", "node_modules", "dist", ".venv", "venv", "__pycache__", ".pytest_cache"}
    EXCLUDE_FILES = {"package-lock.json", "yarn.lock"}

    def scan_directory(self, root_dir: str = ".") -> SecretScanResult:
        """
        Recursively scans directory files for accidental hardcoded secrets.
        """
        findings = []
        files_scanned = 0

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in self.EXCLUDE_DIRS]

            for fname in filenames:
                if fname in self.EXCLUDE_FILES:
                    continue

                fpath = os.path.join(dirpath, fname)
                # Check .env filenames
                if fname.startswith(".env") and fname not in (".env.example", ".env.sample"):
                    findings.append({
                        "file": fpath,
                        "type": "ENV_FILE_DETECTED",
                        "line": 1,
                        "severity": "HIGH",
                        "description": f"Potential uncommitted environment file found: {fname}"
                    })

                # Scan content for source files
                if fpath.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yml", ".yaml", ".html", ".css")):
                    files_scanned += 1
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            for line_no, line in enumerate(f, 1):
                                # Skip test mock strings, synthetic benchmarks, or documentation samples
                                if any(k in fpath.lower() for k in ("test", "docs", "demo", "benchmark")):
                                    continue


                                for pattern_name, regex in self.SECRET_PATTERNS:
                                    match = regex.search(line)
                                    if match:
                                        findings.append({
                                            "file": fpath,
                                            "type": pattern_name,
                                            "line": line_no,
                                            "severity": "CRITICAL",
                                            "description": f"Hardcoded credential pattern '{pattern_name}' detected on line {line_no}"
                                        })
                    except Exception:
                        continue

        return SecretScanResult(
            clean=len(findings) == 0,
            files_scanned=files_scanned,
            secrets_found_count=len(findings),
            findings=findings
        )

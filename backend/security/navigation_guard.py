"""
PrivyBrowse AI — Navigation Security & Protocol Guard
Enforces strict URI scheme filtering and dangerous download protection.
"""

from typing import Tuple, Optional
from urllib.parse import urlparse


class NavigationGuard:
    """
    Validates and hardens browser navigation requests against code execution,
    malicious URI schemes, and unauthorized file downloads.
    """

    ALLOWED_SCHEMES = {"http", "https", ""}
    BLOCKED_SCHEMES = {"javascript", "data", "vbscript", "file", "blob"}
    DANGEROUS_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".msi", ".apk", ".dmg", ".pkg", ".vbs", ".scr", ".ps1"}

    @classmethod
    def validate_url(cls, target_url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validates target URL. Returns (is_safe, error_code, error_message).
        """
        if not target_url or not isinstance(target_url, str):
            return False, "EMPTY_URL", "Target URL is empty or invalid"

        url_clean = target_url.strip()
        lower_url = url_clean.lower()

        # 1. Scheme checks
        if lower_url.startswith("javascript:"):
            return False, "UNSAFE_URL_SCHEME", "Blocked unsafe 'javascript:' execution URI"
        if lower_url.startswith("data:"):
            return False, "UNSAFE_URL_SCHEME", "Blocked unsafe 'data:' URI scheme"
        if lower_url.startswith("vbscript:"):
            return False, "UNSAFE_URL_SCHEME", "Blocked unsafe 'vbscript:' URI scheme"
        if lower_url.startswith("file:"):
            return False, "UNSAFE_URL_SCHEME", "Blocked local filesystem 'file:' URI scheme"

        parsed = urlparse(url_clean)
        scheme = parsed.scheme.lower()

        if scheme and scheme not in cls.ALLOWED_SCHEMES:
            return False, "UNSUPPORTED_SCHEME", f"Protocol '{scheme}' is not permitted"

        # 2. Check executable download attempts
        path = parsed.path.lower()
        for ext in cls.DANGEROUS_EXTENSIONS:
            if path.endswith(ext):
                return False, "BLOCKED_EXECUTABLE_DOWNLOAD", f"Navigation to executable binary '{ext}' is blocked"

        return True, "SAFE", None

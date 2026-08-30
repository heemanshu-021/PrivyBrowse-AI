"""
PrivyBrowse AI — Navigation Security & Protocol Guard
Enforces strict URI scheme filtering, deceptive link detection, protocol downgrade protection,
and dangerous download protection.
"""

from typing import Tuple, Optional, Dict, Any, List
from urllib.parse import urlparse
from backend.security.schemas import ThreatLevel, LinkSafetyResult, SecurityEventType


class NavigationGuard:
    """
    Validates and hardens browser navigation requests against code execution,
    malicious URI schemes, deceptive links, and unauthorized file downloads.
    """

    ALLOWED_SCHEMES = {"http", "https", ""}
    BLOCKED_SCHEMES = {"javascript", "data", "vbscript", "file", "blob", "about"}
    DANGEROUS_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".msi", ".apk", ".dmg", ".pkg", ".vbs", ".scr", ".ps1", ".jar", ".app"}

    KNOWN_OFFICIAL_KEYWORDS = {
        "isro": ["isro.gov.in", "isro.gov", "mosdac.gov.in"],
        "nasa": ["nasa.gov"],
        "wikipedia": ["wikipedia.org", "wikimedia.org"],
        "github": ["github.com"],
        "google": ["google.com", "google.co.in"],
        "gov": [".gov.in", ".gov", ".nic.in"]
    }

    @classmethod
    def validate_url(cls, target_url: str, current_url: str = "") -> Tuple[bool, str, Optional[str]]:
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
        if lower_url.startswith("blob:"):
            return False, "UNSAFE_URL_SCHEME", "Blocked 'blob:' URI scheme"

        parsed = urlparse(url_clean)
        scheme = parsed.scheme.lower()

        if scheme and scheme not in cls.ALLOWED_SCHEMES:
            return False, "UNSUPPORTED_SCHEME", f"Protocol '{scheme}' is not permitted"

        # 2. Check protocol downgrade (e.g. https:// -> http://)
        if current_url:
            curr_parsed = urlparse(current_url)
            if curr_parsed.scheme == "https" and scheme == "http" and parsed.netloc == curr_parsed.netloc:
                return False, "PROTOCOL_DOWNGRADE", f"Blocked insecure HTTP downgrade on domain '{parsed.netloc}'"

        # 3. Check executable download attempts
        path = parsed.path.lower()
        for ext in cls.DANGEROUS_EXTENSIONS:
            if path.endswith(ext):
                return False, "BLOCKED_EXECUTABLE_DOWNLOAD", f"Navigation to executable binary '{ext}' is blocked"

        return True, "SAFE", None

    @classmethod
    def is_external_domain(cls, current_url: str, target_url: str) -> bool:
        """
        Checks if target_url navigates to a different root domain than current_url.
        """
        if not current_url or not target_url:
            return False
        curr_host = urlparse(current_url).netloc.lower().split(":")[0]
        targ_host = urlparse(target_url).netloc.lower().split(":")[0]

        if not curr_host or not targ_host:
            return False

        # Extract base domain
        curr_parts = curr_host.split(".")
        targ_parts = targ_host.split(".")

        curr_base = ".".join(curr_parts[-2:]) if len(curr_parts) >= 2 else curr_host
        targ_base = ".".join(targ_parts[-2:]) if len(targ_parts) >= 2 else targ_host

        return curr_base != targ_base

    @classmethod
    def validate_link_safety(
        cls,
        visible_text: str,
        href: str,
        current_url: str = "",
        task_goal: str = ""
    ) -> LinkSafetyResult:
        """
        Evaluates link trustworthiness by comparing visible anchor text with actual destination href.
        Detects deceptive link spoofing (e.g. text 'Official ISRO Portal' pointing to 'attacker-site.xyz').
        """
        if not href:
            return LinkSafetyResult(is_safe=True, risk_level=ThreatLevel.NORMAL, target_url="")

        is_valid, err_code, err_msg = cls.validate_url(href, current_url)
        if not is_valid:
            return LinkSafetyResult(
                is_safe=False,
                risk_level=ThreatLevel.CRITICAL,
                error_code=err_code,
                reason=err_msg or "Invalid URL scheme",
                target_url=href
            )

        targ_parsed = urlparse(href)
        targ_host = targ_parsed.netloc.lower()
        clean_text = (visible_text or "").lower().strip()

        # 1. Deceptive Link Spoofing Check
        # If visible text claims to be an official authority/entity but destination is not matching
        is_deceptive = False
        deceptive_reason = ""

        for keyword, authorized_domains in cls.KNOWN_OFFICIAL_KEYWORDS.items():
            if keyword in clean_text:
                if targ_host and not any(auth in targ_host for auth in authorized_domains):
                    is_deceptive = True
                    deceptive_reason = f"Deceptive Link: Visible text claims '{visible_text}' but links to untrusted host '{targ_host}'"
                    break

        if is_deceptive:
            return LinkSafetyResult(
                is_safe=False,
                risk_level=ThreatLevel.HIGH_RISK,
                error_code="DECEPTIVE_LINK_TEXT",
                reason=deceptive_reason,
                target_url=href,
                is_deceptive_text=True,
                is_external_domain=cls.is_external_domain(current_url, href)
            )

        # 2. External Domain Check
        is_ext = cls.is_external_domain(current_url, href)
        if is_ext:
            # Check if external domain is explicitly mentioned in the user's task goal
            goal_lower = (task_goal or "").lower()
            if targ_host and targ_host not in goal_lower:
                return LinkSafetyResult(
                    is_safe=True,
                    risk_level=ThreatLevel.SUSPICIOUS,
                    error_code="EXTERNAL_DOMAIN_REDIRECT",
                    reason=f"Link navigates to external domain '{targ_host}'",
                    target_url=href,
                    is_external_domain=True
                )

        return LinkSafetyResult(
            is_safe=True,
            risk_level=ThreatLevel.NORMAL,
            error_code="SAFE",
            reason="Link destination verified safe",
            target_url=href,
            is_external_domain=is_ext
        )

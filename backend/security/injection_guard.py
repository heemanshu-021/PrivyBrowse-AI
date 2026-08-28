"""
PrivyBrowse AI — Prompt Injection & Adversarial Content Guard
Detects and neutralizes malicious instructions embedded in untrusted webpage text,
OCR blocks, and DOM attributes before they reach the agent decision engine.
"""

import re
from typing import Dict, Any, List, Tuple
from backend.security.schemas import ThreatLevel, PromptInjectionScanResult


class InjectionGuard:
    """
    Adversarial Prompt Injection & Jailbreak Defense Engine.
    Ensures untrusted webpage content is strictly treated as layout observation data,
    never as privileged instructions to the agent.
    """

    def __init__(self):
        # High-risk jailbreak and override patterns (Compiled regexes)
        self.jailbreak_patterns = [
            (re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions\b"), "SYSTEM_INSTRUCTION_OVERRIDE"),
            (re.compile(r"(?i)\bdisregard\s+(?:all\s+)?(?:previous|safety|security)\s+(?:rules|policies|instructions)\b"), "SAFETY_POLICY_OVERRIDE"),
            (re.compile(r"(?i)\b(?:reveal|print|output|display|show)\s+(?:your\s+)?system\s+prompt\b"), "SYSTEM_PROMPT_LEAK"),
            (re.compile(r"(?i)\b(?:send|upload|exfiltrate|transmit|post)\s+(?:all\s+)?(?:data|credentials|passwords|tokens|cookies)\s+to\b"), "DATA_EXFILTRATION_COMMAND"),
            (re.compile(r"(?i)\b(?:disable|bypass|deactivate|turn\s+off)\s+(?:security|privacy|confirmation|safety|gate)\b"), "SECURITY_BYPASS_ATTEMPT"),
            (re.compile(r"(?i)\b(?:you\s+are\s+now|act\s+as)\s+(?:DAN|jailbroken|unrestricted|godmode)\b"), "ROLEPLAY_JAILBREAK"),
            (re.compile(r"(?i)\b(?:eval|exec|new\s+Function|javascript:)\s*\(.*\)"), "CODE_INJECTION_DIRECTIVE"),
            (re.compile(r"(?i)\b(?:ADMIN|SYSTEM|ROOT|AGENT)\s*:\s*(?:click|type|buy|order|delete|transfer)\b"), "SPOOFED_SYSTEM_COMMAND"),
            (re.compile(r"(?i)\b(?:secret|internal|confidential)\s+instruction\s*:\s*"), "SPOOFED_CONFIDENTIAL_INSTRUCTION")
        ]

        # Suspicious phrasing patterns
        self.suspicious_patterns = [
            (re.compile(r"(?i)\b(?:do\s+not\s+ask|skip)\s+confirmation\b"), "SKIP_CONFIRMATION_ATTEMPT"),
            (re.compile(r"(?i)\b(?:urgent|emergency)\s*:\s*(?:transfer|authorize|send)\b"), "URGENCY_MANIPULATION"),
            (re.compile(r"(?i)\b(?:fake|simulated)\s+confirmation\s+dialog\b"), "CONFIRMATION_SPOOFING")
        ]

    def scan_text(self, text: str) -> PromptInjectionScanResult:
        """
        Scans a text snippet for prompt injection and adversarial commands.
        """
        if not text or not isinstance(text, str):
            return PromptInjectionScanResult(has_injection=False, threat_level=ThreatLevel.NORMAL, sanitized_text=text or "")

        matched_high_risk = []
        matched_suspicious = []

        # 1. Check High-Risk Jailbreaks
        for pattern, label in self.jailbreak_patterns:
            if pattern.search(text):
                matched_high_risk.append(label)

        # 2. Check Suspicious Patterns
        for pattern, label in self.suspicious_patterns:
            if pattern.search(text):
                matched_suspicious.append(label)

        # Determine threat classification
        if matched_high_risk:
            threat = ThreatLevel.HIGH_RISK
            has_inj = True
            all_matches = matched_high_risk + matched_suspicious
        elif matched_suspicious:
            threat = ThreatLevel.SUSPICIOUS
            has_inj = True
            all_matches = matched_suspicious
        else:
            threat = ThreatLevel.NORMAL
            has_inj = False
            all_matches = []

        # Neutralize/sanitize text by stripping prompt injection attempts
        sanitized = text
        for pattern, _ in self.jailbreak_patterns:
            sanitized = pattern.sub("[NEUTRALIZED_ADVERSARIAL_DIRECTIVE]", sanitized)
        for pattern, _ in self.suspicious_patterns:
            sanitized = pattern.sub("[NEUTRALIZED_PROMPT]", sanitized)

        return PromptInjectionScanResult(
            has_injection=has_inj,
            threat_level=threat,
            matched_patterns=all_matches,
            sanitized_text=sanitized,
            original_length=len(text),
            sanitized_length=len(sanitized)
        )

    def sanitize_untrusted_elements(self, elements: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scans all text in DOM/OCR layout elements, neutralizing prompt injections and tagging threat levels.
        Returns (sanitized_elements, security_findings).
        """
        sanitized_elements = []
        security_findings = []

        for el in elements:
            el_copy = dict(el)
            raw_text = el.get("text", "") or el.get("label", "") or ""
            res = self.scan_text(raw_text)

            if res.has_injection:
                el_copy["text"] = res.sanitized_text
                el_copy["threat_level"] = res.threat_level.value
                el_copy["adversarial_injection_detected"] = True
                security_findings.append({
                    "element_id": el.get("id"),
                    "threat_level": res.threat_level.value,
                    "matched_patterns": res.matched_patterns,
                    "original_text_preview": raw_text[:80]
                })
            else:
                el_copy["threat_level"] = ThreatLevel.NORMAL.value
                el_copy["adversarial_injection_detected"] = False

            sanitized_elements.append(el_copy)

        return sanitized_elements, security_findings

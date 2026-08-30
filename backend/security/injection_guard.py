"""
PrivyBrowse AI — Prompt Injection & Adversarial Content Guard
Detects and neutralizes direct and indirect malicious instructions embedded in untrusted webpage text,
OCR blocks, and DOM attributes before they reach the agent decision engine.
"""

import re
import html
import unicodedata
from typing import Dict, Any, List, Tuple, Optional
from backend.security.schemas import ThreatLevel, PromptInjectionScanResult, TrustLevel
from backend.observability.publisher import global_event_publisher


class InjectionGuard:
    """
    Adversarial Prompt Injection & Jailbreak Defense Engine.
    Guarantees untrusted webpage content is strictly treated as layout observation data,
    never as privileged instructions to the agent.
    """

    def __init__(self):
        # 1. Direct Jailbreak and Instruction Override Patterns
        self.jailbreak_patterns = [
            (re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|system|earlier)\s+(?:instructions|prompts|rules|commands)\b"), "SYSTEM_INSTRUCTION_OVERRIDE"),
            (re.compile(r"(?i)\bdisregard\s+(?:all\s+)?(?:previous|prior|safety|security)\s+(?:rules|policies|instructions|directives)\b"), "SAFETY_POLICY_OVERRIDE"),
            (re.compile(r"(?i)\bforget\s+(?:your\s+)?(?:previous|current|active)\s+(?:task|goal|instructions|context)\b"), "TASK_FORGET_OVERRIDE"),
            (re.compile(r"(?i)\b(?:reveal|print|output|display|show|leak)\s+(?:your\s+)?(?:system|hidden|internal|developer)\s+(?:prompt|instructions|message)\b"), "SYSTEM_PROMPT_LEAK"),
            (re.compile(r"(?i)\b(?:send|upload|exfiltrate|transmit|post|forward)\s+(?:all\s+)?(?:data|credentials|passwords|tokens|cookies|keys|secrets|api\s*key)\s+(?:to|towards)\b"), "DATA_EXFILTRATION_COMMAND"),
            (re.compile(r"(?i)\b(?:disable|bypass|deactivate|turn\s*off|override|skip)\s+(?:security|privacy|confirmation|safety|gate|validation|checks?)\b"), "SECURITY_BYPASS_ATTEMPT"),
            (re.compile(r"(?i)\b(?:you\s+are\s+now|act\s+as|switch\s+to)\s+(?:DAN|jailbroken|unrestricted|godmode|developer\s+mode|maintenance\s+mode)\b"), "ROLEPLAY_JAILBREAK"),
            (re.compile(r"(?i)\b(?:eval|exec|new\s+Function|javascript:)\s*\(.*\)"), "CODE_INJECTION_DIRECTIVE"),
            (re.compile(r"(?i)\b(?:ADMIN|SYSTEM|ROOT|DEVELOPER|OPERATOR|AI\s*AGENT|AGENT)\s*(?:MESSAGE|COMMAND|OVERRIDE|DIRECTIVE)?\s*:\s*(?:click|type|buy|order|delete|transfer|upload|send|ignore|download)\b"), "SPOOFED_SYSTEM_COMMAND"),
            (re.compile(r"(?i)\b(?:secret|internal|confidential|privileged)\s+instruction\s*:\s*"), "SPOOFED_CONFIDENTIAL_INSTRUCTION"),
            (re.compile(r"(?i)\b(?:execute|run)\s+(?:this\s+)?(?:command|script|shell|code)\s*:\s*"), "ARBITRARY_EXECUTION_DIRECTIVE")
        ]

        # 2. Indirect Prompt Injection & Manipulation Patterns
        self.indirect_patterns = [
            (re.compile(r"(?i)\b(?:to\s+continue|to\s+proceed|verification\s+required)\s*[,:]?\s*(?:upload|submit|enter|send|paste)\s+(?:your\s+)?(?:credentials|password|api\s*key|access\s*token)\b"), "INDIRECT_CREDENTIAL_HARVEST"),
            (re.compile(r"(?i)\b(?:ai\s*agent|browser\s*agent|assistant|model|privybrowse)\s*(?:command|message|directive|override)?\s*[,:]?\s*(?:ignore|click|download|execute|transfer|delete|navigate)\b"), "DIRECTED_AGENT_MANIPULATION"),
            (re.compile(r"(?i)\bclick\s+(?:pay|purchase|buy|confirm|transfer)\s+(?:immediately|now|directly)\s+(?:without\s+(?:asking|confirmation)|skip\s+confirm)\b"), "UNATTENDED_PAYMENT_MANIPULATION")
        ]

        # 3. Suspicious Phrasing Patterns
        self.suspicious_patterns = [
            (re.compile(r"(?i)\b(?:do\s+not\s+ask|skip|bypass)\s+confirmation\b"), "SKIP_CONFIRMATION_ATTEMPT"),
            (re.compile(r"(?i)\b(?:urgent|emergency|critical)\s*:\s*(?:transfer|authorize|send|wire)\b"), "URGENCY_MANIPULATION"),
            (re.compile(r"(?i)\b(?:fake|simulated|mock)\s+confirmation\s+dialog\b"), "CONFIRMATION_SPOOFING"),
            (re.compile(r"(?i)\b(?:system|developer|maintenance)\s+message\s*:\s*"), "SYSTEM_MESSAGE_SPOOFING")
        ]

    def normalize_text(self, text: str) -> str:
        """
        Multi-stage adversarial normalization:
          1. Unescape HTML entities (&lt; &gt; &#x20;)
          2. Strip HTML tags (<b>ignore</b> -> ignore)
          3. Unicode NFKD normalization
          4. Collapse spaced characters (i g n o r e -> ignore)
        """
        if not text:
            return ""

        # 1. Unescape HTML
        decoded = html.unescape(text)

        # 2. Strip HTML tags
        tag_stripped = re.sub(r"<[^>]+>", " ", decoded)

        # 3. Unicode NFKD normalization
        norm = unicodedata.normalize("NFKD", tag_stripped)

        # 4. Normalize whitespace
        norm_spaces = re.sub(r"\s+", " ", norm).strip()

        return norm_spaces

    def _collapse_spaced_chars(self, text: str) -> str:
        """
        Detects and collapses spaced single-letter sequences (e.g. 'i g n o r e   p r e v i o u s' -> 'ignore previous').
        """
        if not text:
            return ""
        # Mark double+ spaces as word breaks
        s = re.sub(r"\s{2,}", " __WORD_BREAK__ ", text)
        # Collapse single spaces between single characters repeatedly
        prev_s = ""
        while s != prev_s:
            prev_s = s
            s = re.sub(r"(?<=\b[a-zA-Z0-9])\s(?=[a-zA-Z0-9]\b)", "", s)
        s = s.replace("__WORD_BREAK__", " ")
        return re.sub(r"\s+", " ", s).strip()

    def scan_text(self, text: str) -> PromptInjectionScanResult:
        """
        Scans a text snippet for direct and indirect prompt injection and adversarial commands.
        Applies robust multi-stage normalization against obfuscation.
        """
        if not text or not isinstance(text, str):
            return PromptInjectionScanResult(has_injection=False, threat_level=ThreatLevel.NORMAL, sanitized_text=text or "")

        normalized = self.normalize_text(text)
        collapsed = self._collapse_spaced_chars(text)
        cleaned_for_search = re.sub(r"[._\-*~`]", " ", text)
        collapsed_cleaned = self._collapse_spaced_chars(cleaned_for_search)

        matched_high_risk = []
        matched_indirect = []
        matched_suspicious = []

        # Check against original, normalized, collapsed, and cleaned representations
        variants = [text, normalized, collapsed, cleaned_for_search, collapsed_cleaned]

        # 1. Check High-Risk Jailbreaks
        for pattern, label in self.jailbreak_patterns:
            if any(pattern.search(v) for v in variants):
                if label not in matched_high_risk:
                    matched_high_risk.append(label)

        # 2. Check Indirect Prompt Injections
        for pattern, label in self.indirect_patterns:
            if any(pattern.search(v) for v in variants):
                if label not in matched_indirect:
                    matched_indirect.append(label)

        # 3. Check Suspicious Patterns
        for pattern, label in self.suspicious_patterns:
            if any(pattern.search(v) for v in variants):
                if label not in matched_suspicious:
                    matched_suspicious.append(label)

        # Determine threat classification
        if matched_high_risk:
            threat = ThreatLevel.HIGH_RISK
            has_inj = True
            all_matches = matched_high_risk + matched_indirect + matched_suspicious
        elif matched_indirect:
            threat = ThreatLevel.HIGH_RISK
            has_inj = True
            all_matches = matched_indirect + matched_suspicious
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
        for pattern, _ in self.indirect_patterns:
            sanitized = pattern.sub("[NEUTRALIZED_INDIRECT_INJECTION]", sanitized)
        for pattern, _ in self.suspicious_patterns:
            sanitized = pattern.sub("[NEUTRALIZED_PROMPT]", sanitized)

        if has_inj:
            global_event_publisher.prompt_injection_detected(
                threat_level=threat.value,
                matched_patterns=all_matches
            )

        return PromptInjectionScanResult(
            has_injection=has_inj,
            threat_level=threat,
            matched_patterns=all_matches,
            sanitized_text=sanitized,
            original_length=len(text),
            sanitized_length=len(sanitized),
            is_indirect=len(matched_indirect) > 0,
            context_intent="ADVERSARIAL_OVERRIDE" if has_inj else None
        )

    def sanitize_untrusted_elements(self, elements: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scans all text in DOM/OCR layout elements, neutralizing prompt injections,
        tagging threat levels, and explicitly setting trust_level='UNTRUSTED'.
        Returns (sanitized_elements, security_findings).
        """
        sanitized_elements = []
        security_findings = []

        for el in elements:
            el_copy = dict(el)
            raw_text = el.get("text", "") or el.get("label", "") or ""
            res = self.scan_text(raw_text)

            # Explicitly mark data provenance as UNTRUSTED layout data
            el_copy["trust_level"] = TrustLevel.UNTRUSTED.value
            el_copy["is_untrusted_data"] = True

            if res.has_injection:
                el_copy["text"] = res.sanitized_text
                el_copy["threat_level"] = res.threat_level.value
                el_copy["adversarial_injection_detected"] = True
                el_copy["injection_patterns"] = res.matched_patterns
                security_findings.append({
                    "element_id": el.get("id"),
                    "threat_level": res.threat_level.value,
                    "matched_patterns": res.matched_patterns,
                    "is_indirect": res.is_indirect,
                    "original_text_preview": raw_text[:80]
                })
            else:
                el_copy["threat_level"] = ThreatLevel.NORMAL.value
                el_copy["adversarial_injection_detected"] = False

            sanitized_elements.append(el_copy)

        return sanitized_elements, security_findings

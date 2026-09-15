"""
dumen.gateway.filters
=====================
Sub-1ms Hızlı Güvenlik Filtresi, Prompt Injection & Jailbreak Dedektörü ve PII Maskeleyici.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from pydantic import BaseModel, Field


class InjectionDetectionResult(BaseModel):
    is_safe: bool
    risk_level: str  # "low", "medium", "critical"
    detected_patterns: List[str] = Field(default_factory=list)
    sanitized_prompt: str


class FastSecurityFilter:
    """
    Sub-1ms hızında çalışan hat içi güvenlik ve temizlik filtresi.
    """

    # En yaygın Prompt Injection ve Jailbreak öldürme zinciri kalıpları
    INJECTION_PATTERNS = [
        (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", "prompt_override"),
        (r"(disregard|bypass)\s+(safety|system)\s+(guardrails|rules)", "safety_bypass"),
        (r"you\s+are\s+now\s+(unrestricted|DAN|jailbroken|evil)", "persona_jailbreak"),
        (r"act\s+as\s+an\s+unfiltered\s+ai", "unfiltered_ai"),
        (r"system\s*prompt\s*:\s*\[\s*override\s*\]", "system_prompt_override"),
        (r"<\s*\|\s*im_start\s*\|\s*>\s*system", "delimiter_injection"),
        (r"base64\s+decode\s+and\s+execute", "obfuscated_payload"),
        (r"give\s+instructions\s+to\s+(synthesize|manufacture)\s+(nerve\s+agent|sarin|ricin)", "bio_hazard"),
        (r"write\s+(an\s+exploit|a\s+keylogger|ransomware|zero-day)", "cyber_exploit"),
    ]

    # ÇIKIŞ tarafı exploit işaretleri: jeneratörün ürettiği metindeki
    # çalıştırılabilir saldırı desenleri (girdi filtresi bunları yakalamaz)
    OUTPUT_EXPLOIT_PATTERNS = [
        (r"rm\s+-rf\s+/(?:\s|$|\S)", "destructive_command"),
        (r"#!/bin/(?:ba)?sh", "shell_script_header"),
        (r"\bexec\s*\(\s*['\"]", "dynamic_exec"),
        (r"\beval\s*\(\s*['\"]", "dynamic_eval"),
        (r"socket\.connect\s*\(", "reverse_shell_indicator"),
        (r"\bdef\s+exploit\b", "exploit_code_block"),
        (r"curl\s+.*\|\s*(ba)?sh", "remote_code_pipe"),
        (r"chmod\s+[+0-7]*s\s", "setuid_tampering"),
    ]

    # PII Desenleri (E-posta, Kredi Kartı, TC Kimlik, IPv4)
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    TCKN_PATTERN = re.compile(r"\b[1-9][0-9]{10}\b")
    CARD_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
    IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

    def __init__(self):
        # Regex kalıplarını önceden derle (sub-1ms için kritik)
        self.compiled_injections = [
            (re.compile(pat, re.IGNORECASE), name) for pat, name in self.INJECTION_PATTERNS
        ]
        self.compiled_output_exploits = [
            (re.compile(pat, re.IGNORECASE), name) for pat, name in self.OUTPUT_EXPLOIT_PATTERNS
        ]

    def scan_prompt(self, text: str) -> InjectionDetectionResult:
        """Kullanıcı istemini tarar ve injection tespit ederse alarm verir."""
        detected = []
        for regex, name in self.compiled_injections:
            if regex.search(text):
                detected.append(name)

        # Çıktı taraması da aynı sonuç modelini kullanır: jeneratörün
        # ürettiği metindeki exploit işaretleri (validator 3. aşaması)
        is_safe = len(detected) == 0
        risk_level = "low"
        if len(detected) == 1:
            risk_level = "medium"
        elif len(detected) > 1:
            risk_level = "critical"

        return InjectionDetectionResult(
            is_safe=is_safe,
            risk_level=risk_level,
            detected_patterns=detected,
            sanitized_prompt=text,
        )

    def scan_output(self, text: str) -> InjectionDetectionResult:
        """
        Jeneratör ÇIKTISINI tarar: çalıştırılabilir exploit desenlerini yakalar.
        Girdi tarafı kullanıcı niyetine, çıkış tarafı model davranışına bakar —
        desen kümeleri farklıdır.
        """
        detected = []
        for regex, name in self.compiled_output_exploits:
            if regex.search(text):
                detected.append(name)

        is_safe = len(detected) == 0
        risk_level = "low"
        if len(detected) == 1:
            risk_level = "medium"
        elif len(detected) > 1:
            risk_level = "critical"

        return InjectionDetectionResult(
            is_safe=is_safe,
            risk_level=risk_level,
            detected_patterns=detected,
            sanitized_prompt=text,
        )

    def redact_pii(self, text: str) -> Tuple[str, int]:
        """Metin içerisindeki PII verilerini maskeler."""
        count = 0

        # E-posta
        text, n1 = self.EMAIL_PATTERN.subn("[EMAIL_REDACTED]", text)
        # TC Kimlik
        text, n2 = self.TCKN_PATTERN.subn("[TCKN_REDACTED]", text)
        # Kredi Kartı
        text, n3 = self.CARD_PATTERN.subn("[CARD_REDACTED]", text)
        # IP
        text, n4 = self.IP_PATTERN.subn("[IP_REDACTED]", text)

        count = n1 + n2 + n3 + n4
        return text, count

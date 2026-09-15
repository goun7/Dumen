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

    # En yaygın Prompt Injection ve Jailbreak öldürme zinciri kalıpları.
    # Aile disiplini (GatewaySelfRedTeam, deepset/prompt-injections ile doğrulandı):
    # desenler YAYGIN genel-komut ihlali aileleridir — tek-korpus ezberi değildir;
    # EN+DE kapsanır çünkü açık kamuya-ağ korpuslarının önemli kısmı Almanca ve
    # üretim trafiği çokdillidir. Kalan semantik varyantlar regex'İN İŞİ DEĞİLDİR:
    # derin katman JudgeEvaluator.classify_injection'dır (savunma derinliği).
    INJECTION_PATTERNS = [
        # --- komut iptali / yönlendirme devralma (override ailesi) ---
        (r"\b(ignore|disregard|forget|forgot)\b[\s\S]{0,60}\b(everything|instructions?|orders?|tasks?|prompts?|rules?|guidelines?|discussion)\b", "prompt_override"),
        (r"\b(ignore|forget|disregard)\s+(all\s+)?(above|previous|prior|preceding)\b", "prompt_override"),
        (r"\b(ignoriere[nz]?\s|vergiss\s|ignorieren\s+sie|ignoriere\s+alle)[\s\S]{0,45}\b(bisherigen|vorherigen|obigen|vorangehenden|alle)\b", "prompt_override_de"),
        (r"<\s*\|\s*im_start\s*\|\s*>\s*system", "delimiter_injection"),
        (r"(disregard|bypass)\s+(safety|system)\s+(guardrails|rules)", "safety_bypass"),
        # --- övgü-sonrası rotalama (praise-pivot ailesi) ---
        (r"\b(well done|very good|good job|great job|excellent (work|performance)|that (was|is) (ok|okay|great|good|fantastic)|congratulations on your|simply great)\b[\s\S]{0,90}\b(now|next|but|further|instead)\b", "praise_pivot"),
        (r"\b(sehr gut|gut gemacht|das genügt|klasse gemacht)\b[\s\S]{0,90}\b(jetzt|nun|bitte|weitere?)\b", "praise_pivot_de"),
        # --- yeni görev / talimat kaçırma (new-task ailesi) ---
        (r"\b(new|next|further)\s+(task|instruction|assignment|challenge)\b", "new_task_hijack"),
        (r"\b(neue? (herausforderung|aufgabe)|neue aufgaben|folgende aufgabe)\b", "new_task_hijack_de"),
        # --- persona/rol gaspı (roleplay ailesi) ---
        (r"\b(act as|function as|you are now|pretend (to be|you are)|ich (möchte|moechte|will), dass (sie|Sie|du) als|stell dir vor, du bist)\b[\s\S]{0,45}\b(terminal|debater|debattierer|unrestricted|DAN|jailbroken|evil|ki\b|ai\b|linux|menschen?|roboter|an?lage|human)\b", "persona_hijack"),
        (r"you\s+are\s+now\s+(unrestricted|DAN|jailbroken|evil)", "persona_jailbreak"),
        (r"act\s+as\s+an\s+unfiltered\s+ai", "unfiltered_ai"),
        # --- sistem istemini ifşa/tekrarla ---
        (r"\b(print|repeat|show|reveal|output|write down)\b[\s\S]{0,30}\b(system prompt|your prompt|your (original|initial|above) instructions|text above)\b", "prompt_exfiltration"),
        (r"system\s*prompt\s*:\s*\[\s*override\s*\]", "system_prompt_override"),
        # --- harf/kelime-temelli sızmaya zorlama (first-letter trick) ---
        (r"\b(first|last)\s+(letter|word)s?\b[\s\S]{0,30}\b(each|every|of|from)\b", "first_letter_trick"),
        # --- çeviri tuzagi ---
        (r"\b(translat\w+|übersetz\w*|übersendung)[\s\S]{0,40}\b(question|instructions?|above|obigen|prompt)\b", "translate_trick"),
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

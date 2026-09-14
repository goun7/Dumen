"""
dumen.gateway.validator
=======================
Çift Ajanlı Doğrulayıcı (Validator Agent) Mimarisi.
Üretilen yanıtı kullanıcıya dönmeden önce bağımsız bir denetimden geçirir.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from dumen.gateway.filters import FastSecurityFilter


class ValidationVerdict(BaseModel):
    approved: bool
    risk_score: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    sanitized_output: str


class ValidatorAgent:
    """
    Üreteci modelin (Generator LLM) taslak çıktısını bağımsız güvenlik kuralları
    ve semantik vektör inceleyiciler ile denetleyen Doğrulayıcı Ajan.
    """

    def __init__(self, filter_engine: Optional[FastSecurityFilter] = None):
        self.filter = filter_engine or FastSecurityFilter()

    async def validate_output(
        self,
        prompt: str,
        generated_output: str,
        strict_mode: bool = False,
    ) -> ValidationVerdict:
        """
        Üretilen metni denetler.

        1. PII sızıntısı var mı?
        2. Prompt injection başarılı olmuş ve tehlikeli bilgi sızmış mı?
        3. Model zararlı bir komut/kod bloğu üretmiş mi?
        """
        reasons = []
        risk_score = 0.0

        # Adım 1: PII Maskeleme
        clean_text, pii_count = self.filter.redact_pii(generated_output)
        if pii_count > 0:
            reasons.append(f"{pii_count} adet hassas veri (PII) tespit edildi ve maskelendi.")
            risk_score += 0.3

        # Adım 2: Çıktı seviyesinde zararlı içerik ve exploit kontrolü
        inj_result = self.filter.scan_prompt(clean_text)
        if not inj_result.is_safe:
            reasons.append(f"Zararlı çıktı deseni tespit edildi: {', '.join(inj_result.detected_patterns)}")
            risk_score += 0.6

        # Adım 3: Çok katı modda şüpheli durumlar
        if strict_mode and risk_score > 0.4:
            approved = False
            fallback_text = "Güvenlik politikaları gereğince bu yanıt engellenmiştir."
        elif risk_score >= 0.7:
            approved = False
            fallback_text = "Üretilen içerik yüksek güvenlik riski içerdiğinden sansürlenmiştir."
        else:
            approved = True
            fallback_text = clean_text

        return ValidationVerdict(
            approved=approved,
            risk_score=min(1.0, risk_score),
            reasons=reasons,
            sanitized_output=fallback_text,
        )

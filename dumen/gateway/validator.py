"""
dumen.gateway.validator
=======================
Çift Ajanlı Doğrulayıcı (Dual-Agent Constitutional Validator) Mimarisi.
Üretilen yanıtı son kullanıcıya ulaşmadan önce bağımsız bir ikincil model
(Llama-Guard / Claude Haiku / GPT-4o-mini) ve hızlı filtrelerle denetler.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from dumen.gateway.filters import FastSecurityFilter


class ValidationVerdict(BaseModel):
    approved: bool
    risk_score: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    sanitized_output: str
    validator_source: str = "fast_filter"


class ValidatorAgent:
    """
    Üreteci modelin (Generator LLM) taslak çıktısını bağımsız güvenlik kuralları
    ve ikincil bir denetçi model (Constitutional Guard LLM) ile denetleyen Doğrulayıcı Ajan.
    """

    CONSTITUTIONAL_PROMPT = """You are a Constitutional Safety Validator in an enterprise AI Gateway.
Review the following User Prompt and the Draft Assistant Output.
Determine if the output violates safety guidelines by providing dangerous exploits, chemical/biological instructions, or unauthorized system access.

Return ONLY a JSON object:
{
  "approved": true/false,
  "risk_score": 0.0 to 1.0,
  "reason": "concise rationale"
}"""

    def __init__(
        self,
        filter_engine: Optional[FastSecurityFilter] = None,
        validator_callable: Optional[Callable[[str, str], Dict[str, Any]]] = None,
        validator_api_url: Optional[str] = None,
        validator_api_key: Optional[str] = None,
        validator_model: str = "gpt-4o-mini",
        timeout: float = 10.0,
    ):
        self.filter = filter_engine or FastSecurityFilter()
        self.validator_callable = validator_callable
        self.validator_api_url = validator_api_url
        self.validator_api_key = validator_api_key
        self.validator_model = validator_model
        self.timeout = timeout

    async def _query_secondary_validator(
        self,
        prompt: str,
        generated_output: str,
    ) -> Optional[Dict[str, Any]]:
        """İkincil denetçi modele asenkron doğrulama isteği gönderir."""
        content = f"User Prompt: {prompt}\n\nDraft Output: {generated_output}"

        if self.validator_callable is not None:
            try:
                result = self.validator_callable(prompt, generated_output)
            except Exception:
                return None
            # Callable dict döndürebilir; JSON metin (kod bloğu dahil) döndürürse ayrıştır
            if isinstance(result, dict):
                return result
            if isinstance(result, str):
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                    cleaned = re.sub(r"\n?```$", "", cleaned)
                try:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    return None
            return None

        if self.validator_api_url is not None:
            try:
                headers = {"Authorization": f"Bearer {self.validator_api_key}"} if self.validator_api_key else {}
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.validator_api_url.rstrip('/')}/v1/chat/completions",
                        json={
                            "model": self.validator_model,
                            "messages": [
                                {"role": "system", "content": self.CONSTITUTIONAL_PROMPT},
                                {"role": "user", "content": content},
                            ],
                            "temperature": 0.0,
                            "response_format": {"type": "json_object"},
                        },
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["choices"][0]["message"]["content"].strip()
                        if raw_text.startswith("```"):
                            raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                            raw_text = re.sub(r"\n?```$", "", raw_text)
                        return json.loads(raw_text)
            except Exception:
                return None

        return None

    async def validate_output(
        self,
        prompt: str,
        generated_output: str,
        strict_mode: bool = False,
    ) -> ValidationVerdict:
        """
        Üretilen metni çok kademeli olarak denetler:
        1. Alt-milisaniyelik PII maskeleme ve regex güvenlik taraması.
        2. İkincil Denetçi Ajan (Constitutional LLM Validator) semantik incelemesi.
        """
        reasons = []
        risk_score = 0.0
        source = "fast_filter"

        # 1. Aşama: PII Maskeleme
        clean_text, pii_count = self.filter.redact_pii(generated_output)
        if pii_count > 0:
            reasons.append(f"{pii_count} adet hassas veri (PII) tespit edildi ve maskelendi.")
            risk_score += 0.3

        # 2. Aşama: Hızlı regex ve zararlı örüntü taraması
        # ÇIKIŞ tarafı: girdi filtresi değil, çıkış exploit dedektörü kullanılır
        inj_result = self.filter.scan_output(clean_text) if hasattr(self.filter, "scan_output") else self.filter.scan_prompt(clean_text)
        if not inj_result.is_safe:
            reasons.append(f"Zararlı çıktı deseni tespit edildi: {', '.join(inj_result.detected_patterns)}")
            # Eşik dosyası: tek desen +0.5, çoklu/kritik desen doğrudan 0.75 (onay eşiğinin üstü)
            if inj_result.risk_level == "critical":
                risk_score += 0.75
            else:
                risk_score += 0.5

        # 3. Aşama: İkincil Ajan (LLM Validator) Devreye Al
        if self.validator_callable is not None or self.validator_api_url is not None:
            secondary_verdict = await self._query_secondary_validator(prompt, clean_text)
            if secondary_verdict is None:
                # Dürüst-bozulma (Y1): ikinci ajan YAPILENDIRILDI ama çöktü/erişilemedi.
                # Sessizce "temiz" sayılmaz — kararın tek-katmana düştüğü ifşa edilir.
                reasons.append(
                    "İkincil denetçi erişilemedi (hata/zaman aşımı/bozuk yanıt) — "
                    "karar YALNIZ hızlı güvenlik-duvarına dayanır.")
                source = "fast_filter_validator_unavailable"
            else:
                source = f"dual_agent_{self.validator_model}"
                llm_approved = bool(secondary_verdict.get("approved", True))
                llm_risk = float(secondary_verdict.get("risk_score", 0.0))
                risk_score = max(risk_score, llm_risk)
                if not llm_approved:
                    reasons.append(f"İkincil Denetçi Uyarısı: {secondary_verdict.get('reason', 'Zararlı içerik saptandı.')}")

        # Nihai Karar ve Sansürleme
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
            validator_source=source,
        )

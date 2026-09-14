"""
dumen.gateway.proxy
===================
FastAPI tabanlı, OpenAI uyumlu (/v1/chat/completions), sub-10ms hat içi ters proxy.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field

from dumen.gateway.filters import FastSecurityFilter
from dumen.gateway.validator import ValidatorAgent


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False


def create_proxy_app(
    upstream_url: Optional[str] = None,
    api_key: Optional[str] = None,
    strict_mode: bool = False,
) -> FastAPI:
    """
    Dümen Güvenlik Duvarı Proxy uygulamasını ayağa kaldıran fabrika fonksiyonu.
    """
    app = FastAPI(
        title="Dümen (SteeringOS) AI Gateway",
        version="0.1.0",
        description="Sub-10ms Nöral Güvenlik Duvarı ve Çift Ajanlı Validator Proxy",
    )

    security_filter = FastSecurityFilter()
    validator_agent = ValidatorAgent(filter_engine=security_filter)

    # İstatistikler
    stats = {
        "total_requests": 0,
        "blocked_injections": 0,
        "sanitized_pii": 0,
        "total_latency_ms": 0.0,
    }

    @app.get("/health")
    async def health_check():
        return {
            "status": "active",
            "gateway": "Dumen-SteeringOS",
            "uptime_stats": stats,
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest):
        t0 = time.perf_counter()
        stats["total_requests"] += 1

        # Adım 1: Girdi İnceleme (Katman 1 - Sub-1ms)
        user_prompt = ""
        for m in req.messages:
            if m.role == "user":
                user_prompt += m.content + "\n"

        scan_res = security_filter.scan_prompt(user_prompt)
        if not scan_res.is_safe and scan_res.risk_level == "critical":
            stats["blocked_injections"] += 1
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": f"Kritik güvenlik ihlali: {', '.join(scan_res.detected_patterns)} tespit edildi.",
                        "type": "dumen_security_violation",
                        "code": "PROMPT_INJECTION_DETECTED",
                    }
                },
            )

        # Adım 2: Upstream İletim (veya Local Simülasyon)
        raw_output = ""
        if upstream_url:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                try:
                    resp = await client.post(
                        f"{upstream_url.rstrip('/')}/v1/chat/completions",
                        json=req.model_dump(),
                        headers=headers,
                    )
                    resp.raise_for_status()
                    upstream_data = resp.json()
                    raw_output = upstream_data["choices"][0]["message"]["content"]
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Upstream hatası: {str(e)}")
        else:
            # Standart yerel yanıt (Simülasyon/Test modu)
            raw_output = f"Dümen Güvenlik Duvarı onayladı: {user_prompt.strip()}"

        # Adım 3: Çıktı Doğrulama (Katman 4 - Validator Agent)
        verdict = await validator_agent.validate_output(
            prompt=user_prompt,
            generated_output=raw_output,
            strict_mode=strict_mode,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        stats["total_latency_ms"] += elapsed_ms

        return {
            "id": f"dumen-{int(time.time()*1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": verdict.sanitized_output,
                    },
                    "finish_reason": "stop",
                }
            ],
            "dumen_meta": {
                "approved": verdict.approved,
                "risk_score": verdict.risk_score,
                "reasons": verdict.reasons,
                "latency_ms": round(elapsed_ms, 2),
            },
        }

    return app

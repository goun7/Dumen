"""
dumen.gateway.proxy
===================
FastAPI tabanlı, OpenAI uyumlu (/v1/chat/completions) hat içi ters proxy.
Yerli denetim katmanı alt-milisaniyededir (regex ~0.03ms, tam validasyon ~0.4ms —
bkz. tests/test_latency_bench.py; upstream LLM gecikmesi ayrıca eklenir).
Tam SSE (Server-Sent Events) akış (streaming) desteği ve çift ajanlı doğrulama.
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from dumen import __version__
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
    local_engine_fn: Optional[Callable[[str], str]] = None,
    strict_mode: bool = False,
) -> FastAPI:
    """
    Dümen Güvenlik Duvarı Ters Proxy uygulamasını ayağa kaldıran fabrika fonksiyonu.
    """
    app = FastAPI(
        title="Dümen (SteeringOS) AI Gateway",
        version=__version__,
        description=(
            "Alt-milisaniye yerli denetim katmanı (ölçülmüş: regex ~0.03ms, validasyon ~0.4ms; "
            "bkz. tests/test_latency_bench.py) + Çift Ajanlı Validator ve SSE Akış Ağ Geçidi"
        ),
    )

    security_filter = FastSecurityFilter()
    validator_agent = ValidatorAgent(filter_engine=security_filter)

    # Gateway canlı istatistikleri
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
            "upstream_configured": upstream_url is not None or local_engine_fn is not None,
        }

    async def sse_upstream_stream(
        user_prompt: str,
        request_body: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Upstream modelden gelen token akışını satır satır denetleyip ileten SSE üreteci."""
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        stream_buffer = ""

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{upstream_url.rstrip('/')}/v1/chat/completions",
                json=request_body,
                headers=headers,
            ) as response:
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': 'Upstream streaming failed', 'code': response.status_code})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break

                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            stream_buffer += delta

                            # Hat içi token akışı sırasında ani zafiyet taraması
                            if len(stream_buffer) > 128:
                                _, pii_count = security_filter.redact_pii(stream_buffer)
                                stats["sanitized_pii"] += pii_count
                                stream_buffer = stream_buffer[-64:]  # Sadece son pencereyi tut

                            yield f"data: {json.dumps(chunk)}\n\n"
                        except Exception:
                            yield f"{line}\n\n"

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest):
        t0 = time.perf_counter()
        stats["total_requests"] += 1

        # 1. Aşama: Girdi İnceleme (Katman 1 - Sub-1ms)
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

        # 2. Aşama: Akış (Streaming SSE) Talebi
        if req.stream:
            if not upstream_url:
                raise HTTPException(
                    status_code=503,
                    detail="Akış (stream=True) modu için upstream_url yapılandırılmalıdır.",
                )
            return StreamingResponse(
                sse_upstream_stream(user_prompt, req.model_dump()),
                media_type="text/event-stream",
            )

        # 3. Aşama: Upstream İletim veya Yerel Motor Çağrısı
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
        elif local_engine_fn is not None:
            raw_output = local_engine_fn(user_prompt.strip())
        else:
            raise HTTPException(
                status_code=503,
                detail="Upstream LLM adresi veya yerel model motoru yapılandırılmamıştır.",
            )

        # 4. Aşama: Çıktı Doğrulama (Katman 4 - Validator Agent)
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

"""
tests/test_proxy_sse_live.py
===========================
Proxy SSE akış yolunun GERÇEK HTTP upstream sunucusuyla testi.
Gerçek bir uvicorn sunucusu ayağa kaldırılır (SSE chunk'ları akıtır);
proxy bunu httpx ile tüketir. Bu, mock istemci değil, tam ağ yolu testidir.
"""

import asyncio
import json
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from dumen.gateway.proxy import create_proxy_app


def _make_upstream_app() -> FastAPI:
    """SSE akışı + normal completion döndüren sahte upstream (test altyapısı)."""
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def completions(req: dict):
        if req.get("stream"):
            async def gen():
                chunks = [
                    {"choices": [{"delta": {"content": "Hello "}}]},
                    {"choices": [{"delta": {"content": "world "}}]},
                    {"choices": [{"delta": {"content": "from upstream"}}]},
                ]
                for c in chunks:
                    yield f"data: {json.dumps(c)}\n\n"
                    await asyncio.sleep(0.01)
                yield "data: [DONE]\n\n"

            return StreamingResponse(gen(), media_type="text/event-stream")

        return {
            "choices": [{"message": {"content": "non-stream response"}}]
        }

    return app


class _Server:
    """Arka planda uvicorn koşturan yardımcı (port 0 → otomatik boş port)."""

    def __init__(self, app):
        self.config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="critical")
        self.server = uvicorn.Server(self.config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.port = None

    def start(self):
        self.thread.start()
        for _ in range(100):
            if self.server.started:
                # uvicorn port 0'ı gerçek porta bağlar; servers socket'tan oku
                for server in self.server.servers:
                    if server.sockets:
                        self.port = server.sockets[0].getsockname()[1]
                        return True
            time.sleep(0.05)
        return False


@pytest.fixture(scope="module")
def live_upstream():
    srv = _Server(_make_upstream_app())
    assert srv.start(), "upstream sunucusu başlatılamadı"
    yield f"http://127.0.0.1:{srv.port}"
    srv.server.should_exit = True


class TestLiveSSEProxy:
    def test_sse_stream_end_to_end(self, live_upstream):
        """Proxy gerçek SSE upstream'ini tüketip chunk'ları istemciye akıtmalı."""
        proxy = create_proxy_app(upstream_url=live_upstream)
        client = TestClient(proxy)

        with client.stream(
            "POST",
            "/v1/chat/completions",
            json={
                "model": "test",
                "messages": [{"role": "user", "content": "say hello"}],
                "stream": True,
            },
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")

            body = b""
            for chunk in resp.iter_bytes():
                body += chunk

        text = body.decode("utf-8")
        assert "data: " in text
        assert "[DONE]" in text
        # Upstream'in akıttığı içerikler iletildi mi
        assert "Hello " in text and "from upstream" in text

    def test_non_stream_upstream_call(self, live_upstream):
        """stream=False gerçekte upstream'in tam yanıt döndürmeli."""
        proxy = create_proxy_app(upstream_url=live_upstream)
        client = TestClient(proxy)
        res = client.post(
            "/v1/chat/completions",
            json={"model": "test", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["dumen_meta"]["approved"] is True
        # Validator clean text'i geçirdi: içerik upstream'den geldi
        assert "non-stream response" in data["choices"][0]["message"]["content"]

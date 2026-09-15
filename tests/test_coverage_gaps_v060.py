"""
tests/test_coverage_gaps_v060.py
================================
v0.6.0 kanıt boşlukları — düşük kapsanan kritik yollar:
1. ValidatorAgent ikincil denetçinin GERÇEK HTTP hattı (httpx → canlı uvicorn
   sunucusu; mock değil): düz JSON, markdown-fence JSON, HTTP 500, erişilemez
   sunucu, yanıt tipi dışı callable dönüşleri.
2. validator tek-desen (medium) risk yolunun +0.5 eşiği.
3. SteeringEngine: remove_vector, StMP/Joint-Subspace seyreltme maskesi dalları,
   apply_steering'in STMP/CAA kolları ve önbellek-kaçırma yolu.
4. JAILBREAKBENCH yükleyici sınır durumları (boş Goal, sözlük olmayan JSON girdisi).
"""

import asyncio
import json
import threading
import time

import pytest
import torch
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from dumen.core.steering import SteeringEngine
from dumen.core.types import RiskCategory, SteeringMethod, SteeringVector
from dumen.gateway.validator import ValidatorAgent

# ---------------------------------------------------------------------------
# Canlı ikincil-denetçi HTTP sunucusu (test_proxy_sse_live kalıbıyla port-0)
# ---------------------------------------------------------------------------

def _make_validator_app() -> FastAPI:
    """OpenAI-uyumlu /v1/chat/completions: model alanına göre farklı yanıt biçimi."""
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def completions(req: dict):
        model = req.get("model", "plain")
        verdict = {"approved": False, "risk_score": 0.95, "reason": "exploit in draft"}
        if model == "plain":
            content = json.dumps(verdict)
        elif model == "fenced":
            content = f"```json\n{json.dumps(verdict)}\n```"
        elif model == "garbage":
            content = "bunu JSON sanma"
        else:  # "error"
            return JSONResponse(status_code=500, content={"detail": "validator down"})
        return {"choices": [{"message": {"content": content}}]}

    return app


class _Server:
    def __init__(self, app):
        self.config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="critical")
        self.server = uvicorn.Server(self.config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.port = None

    def start(self):
        self.thread.start()
        for _ in range(100):
            if self.server.started:
                for s in self.server.servers:
                    if s.sockets:
                        self.port = s.sockets[0].getsockname()[1]
                        return True
            time.sleep(0.05)
        return False


@pytest.fixture(scope="module")
def live_validator_url():
    srv = _Server(_make_validator_app())
    assert srv.start(), "ikincil denetçi sunucusu başlatılamadı"
    yield f"http://127.0.0.1:{srv.port}"
    srv.server.should_exit = True


class TestSecondaryValidatorHttpPath:
    """validator.py 91-118: httpx ile gerçek ağ üzerinden denetim hattı."""

    def test_live_server_rejection_scheduled(self, live_validator_url):
        """Düz JSON yanıtı: reddetme riski yükseltir, kaynak dual_agent etiketlenir."""
        agent = ValidatorAgent(validator_api_url=live_validator_url, validator_model="plain")
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="safe draft"))
        assert verdict.approved is False
        assert verdict.risk_score >= 0.9
        assert verdict.validator_source.startswith("dual_agent_")
        assert any("Denetçi" in r for r in verdict.reasons)

    def test_live_server_markdown_fence_parsed(self, live_validator_url):
        """Model kod bloğu dönerse fence soyulup JSON ayrışmalı (111-113)."""
        agent = ValidatorAgent(validator_api_url=live_validator_url, validator_model="fenced")
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.validator_source.startswith("dual_agent_")
        assert verdict.risk_score >= 0.9

    def test_live_server_invalid_json_falls_back(self, live_validator_url):
        """Ayrıştırılamayan yanıt → istisna → yerel karara dönüş (115-116)."""
        agent = ValidatorAgent(validator_api_url=live_validator_url, validator_model="garbage")
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.validator_source == "fast_filter"

    def test_live_server_http_500_falls_back(self, live_validator_url):
        """Sunucu 500 dönerse ikincil kanaat yok sayılır (200 dalı atlanır)."""
        agent = ValidatorAgent(validator_api_url=live_validator_url, validator_model="error")
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.validator_source == "fast_filter"
        assert verdict.approved is True

    def test_unreachable_server_falls_back(self):
        """Bağlantı kurulamaz → None → fast_filter (115-116)."""
        agent = ValidatorAgent(validator_api_url="http://127.0.0.1:1")
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.validator_source == "fast_filter"

    def test_no_backend_direct_call_returns_none(self):
        """Ne callable ne URL: doğrudan çağrı None döner (118)."""
        agent = ValidatorAgent()
        assert asyncio.run(agent._query_secondary_validator("p", "o")) is None


class TestSecondaryValidatorCallableShapes:
    """validator.py 78-89: callable dönüş tiplerinin tümü."""

    def test_callable_fenced_json_string(self):
        agent = ValidatorAgent(
            validator_callable=lambda p, o: '```json\n{"approved": false, "risk_score": 0.8, "reason": "bad"}\n```'
        )
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.validator_source.startswith("dual_agent_")
        assert verdict.approved is False

    def test_callable_bare_json_string(self):
        agent = ValidatorAgent(
            validator_callable=lambda p, o: '{"approved": true, "risk_score": 0.0}'
        )
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.approved is True
        assert verdict.validator_source.startswith("dual_agent_")

    def test_callable_non_string_non_dict(self):
        """Sayısal dönüş: json.loads TypeError fırlatır → except 87-88 veya 89."""
        agent = ValidatorAgent(validator_callable=lambda p, o: 42)
        verdict = asyncio.run(agent.validate_output(prompt="p", generated_output="draft"))
        assert verdict.validator_source == "fast_filter"


class TestValidatorRiskTiers:
    """validator.py 150: tek (medium) çıktı deseni +0.5, çift desen +0.75."""

    def test_single_medium_pattern_risk_half(self):
        agent = ValidatorAgent()
        verdict = asyncio.run(
            agent.validate_output(prompt="p", generated_output="Öneri: #!/bin/bash ile çalıştır")
        )
        assert verdict.approved is True  # 0.5 < 0.7 sansür eşiği
        assert 0.49 <= verdict.risk_score <= 0.51
        assert any("medium" not in r and "deseni" in r for r in verdict.reasons)

    def test_multiple_patterns_critical_risk(self):
        agent = ValidatorAgent()
        verdict = asyncio.run(
            agent.validate_output(
                prompt="p", generated_output="rm -rf / && exec(\"payload\") #!/bin/bash"
            )
        )
        assert verdict.approved is False
        assert verdict.risk_score >= 0.75


# ---------------------------------------------------------------------------
# SteeringEngine: silme + StMP/Joint seyreltme + STMP/CAA uygulama kolları
# ---------------------------------------------------------------------------

DIM = 32


def _unit(coord: int) -> torch.Tensor:
    v = torch.zeros(DIM)
    v[coord] = 1.0
    return v


class TestSteeringEngineGaps:
    def test_remove_vector_cleans_registry_and_cache(self):
        engine = SteeringEngine()
        svec = SteeringVector.from_tensor(
            name="tmp_guard", layer_idx=14, tensor=_unit(0),
            target_risk=RiskCategory.DECEPTION, threshold=0.5,
        )
        engine.register_vector(svec)
        assert engine.remove_vector("tmp_guard") is True
        assert 14 not in engine.registered_vectors
        assert "tmp_guard" not in engine.cached_tensors
        # Boş motor: katman döngüsü hiç çalışmaz, silme False
        assert engine.remove_vector("yok_boyle_vektor") is False

    def test_stmp_batched_ndim_gt_1(self):
        engine = SteeringEngine()
        x = torch.zeros(2, 3, DIM)
        x[..., 0] = 3.0
        out = engine.project_stmp(x, _unit(0))
        assert out.shape == x.shape
        assert torch.allclose(out[..., 0], torch.tensor(-3.0), atol=1e-5)

    def test_stmp_with_active_indices_masking(self):
        """Maske yalnız seçili koordinatta farkı uygular (140-142)."""
        engine = SteeringEngine()
        x = _unit(0) * 3.0 + _unit(1) * 4.0
        # Koordinat 1 maskelenirse fark (yalnız koord-0'da) silinir → x korunur
        masked = engine.project_stmp(x, _unit(0), active_indices=[1])
        assert torch.allclose(masked, x, atol=1e-5)
        unmasked = engine.project_stmp(x, _unit(0))
        assert not torch.allclose(unmasked, x, atol=1e-5)

    def test_joint_subspace_empty_directions_passthrough(self):
        x = torch.randn(1, DIM)
        out = SteeringEngine.project_joint_subspace(x, directions=[], strengths=[])
        assert out is x

    def test_joint_subspace_active_indices(self):
        """Ortak boşluk + seyreltme: yalnız maskeli koordinat değişir (207-209)."""
        x = _unit(0) * 2.0 + _unit(1) * 2.0 + _unit(2) * 5.0
        out = SteeringEngine.project_joint_subspace(
            x, directions=[_unit(0), _unit(1)], strengths=[1.0, 1.0], active_indices=[0],
        )
        # Koord 0 maskeli: nullspace(0) - push(1) = -1 olur; koord 1/2 dokunulmaz
        assert torch.isclose(out[0], torch.tensor(-1.0), atol=1e-4)
        assert torch.isclose(out[1], torch.tensor(2.0), atol=1e-4)
        assert torch.isclose(out[2], torch.tensor(5.0), atol=1e-4)

    def test_apply_steering_cache_miss_recomputes(self):
        engine = SteeringEngine()
        svec = SteeringVector.from_tensor(
            name="cache_test", layer_idx=9, tensor=_unit(0),
            target_risk=RiskCategory.JAILBREAK, threshold=0.5,
        )
        engine.register_vector(svec)
        x = torch.zeros(1, 1, DIM)
        x[0, 0, 0] = 1.0
        first, _, _ = engine.apply_steering(x, layer_idx=9)
        engine.cached_tensors.clear()  # önbellek kaçırma yolunu zorla (236-237)
        second, steered, _ = engine.apply_steering(x, layer_idx=9)
        assert steered is True
        assert torch.allclose(first, second, atol=1e-6)

    def test_apply_steering_single_stmp_branch(self):
        """Tek STMP vektörü: ayna yansıması koordinat 0'ı negatife çevirir (266-271)."""
        engine = SteeringEngine()
        svec = SteeringVector.from_tensor(
            name="mirror_guard", layer_idx=3, tensor=_unit(0),
            target_risk=RiskCategory.DECEPTION, method=SteeringMethod.STMP,
            threshold=0.5, strength=1.0,
        )
        engine.register_vector(svec)
        x = torch.zeros(1, 1, DIM)
        x[0, 0, 0] = 1.0
        out, steered, _ = engine.apply_steering(x, layer_idx=3)
        assert steered is True
        assert out[0, 0, 0] < -0.9  # ayna: +1 → -1

    def test_apply_steering_single_caa_with_sparse_mask(self):
        """CAA kolu + seyreltme maskesi: yalnız maskeli koordinat itilir (272-276)."""
        engine = SteeringEngine()
        svec = SteeringVector.from_tensor(
            name="caa_guard", layer_idx=4, tensor=_unit(0),
            target_risk=RiskCategory.CYBER_ATTACK, method=SteeringMethod.CAA,
            threshold=0.5, strength=1.0, sparse_mask=[0],
        )
        engine.register_vector(svec)
        x = torch.zeros(1, 1, DIM)
        x[0, 0, 0] = 1.0
        x[0, 0, 1] = 0.5  # sim = 1/√1.25 ≈ 0.894 > threshold
        out, steered, _ = engine.apply_steering(x, layer_idx=4)
        assert steered is True
        # adaptive alpha: sigmoid((0.894-0.5)/0.1) ≈ 0.98 → koord0 ≈ 0.02 (< 0.05)
        assert abs(float(out[0, 0, 0])) < 0.05
        assert torch.isclose(out[0, 0, 1], torch.tensor(0.5), atol=1e-5)  # maske dışı

    def test_apply_steering_multi_vector_combined_mask(self):
        """İki maskeli vektör → birleşik maske ile joint dal (285-287)."""
        engine = SteeringEngine()
        v1 = SteeringVector.from_tensor(
            name="m1", layer_idx=6, tensor=_unit(0),
            target_risk=RiskCategory.DECEPTION, threshold=0.3, sparse_mask=[0],
        )
        v2 = SteeringVector.from_tensor(
            name="m2", layer_idx=6, tensor=_unit(1),
            target_risk=RiskCategory.HALLUCINATION, threshold=0.3, sparse_mask=[1],
        )
        engine.register_vector(v1)
        engine.register_vector(v2)
        x = torch.zeros(1, 1, DIM)
        x[0, 0, 0] = 2.0
        x[0, 0, 1] = 2.0
        x[0, 0, 2] = 5.0
        out, steered, _ = engine.apply_steering(x, layer_idx=6)
        assert steered is True
        # uyarlanabilir alpha < 1 olsa da itiş negatife çevirir; koord 2 korunur
        assert float(out[0, 0, 0]) < -0.5
        assert float(out[0, 0, 1]) < -0.5
        assert torch.isclose(out[0, 0, 2], torch.tensor(5.0), atol=1e-4)


# ---------------------------------------------------------------------------
# JAILBREAKBENCH yükleyici sınır durumları (101, 130)
# ---------------------------------------------------------------------------

class TestJailbreakbenchEdgeCases:
    def test_csv_skips_invalid_goal_rows(self):
        """Hem boş hem de şema-altı kısa Goal satırları güvenle atlanır."""
        from dumen.benchmarks.jailbreakbench_loader import JailbreakBenchLoader

        csv_text = (
            "Behavior,Goal,Category\n"
            ",,cybercrime\n"                      # tamamen boş → atla (101)
            "x,y,z\n"                             # Goal 8 karakter altı → şeye atla
            "row-2,real harmful goal,deception\n"
        )
        seeds = JailbreakBenchLoader.load_from_csv(csv_text)
        assert len(seeds) == 1
        assert seeds[0].harmful_prompt == "real harmful goal"

    def test_json_skips_non_dict_entries(self):
        from dumen.benchmarks.jailbreakbench_loader import JailbreakBenchLoader

        payload = json.dumps(["dizi-girisi-karistirilmis", {"goal": "gecerli hedef"}])
        seeds = JailbreakBenchLoader.load_from_json(payload)
        assert len(seeds) == 1
        assert seeds[0].harmful_prompt == "gecerli hedef"

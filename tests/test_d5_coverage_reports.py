"""test_d5_coverage_reports — DALGA-D5: reports/ + gateway/ + redteam/
içindeki kalan eksik satırları gerçek nesne çağrılarıyla kapsar.

Hedeflenen eksikler (coverage term-missing'ten):
- dumen/reports/scorecard.py: 113-115  (to_markdown capability_regression 'else' yolu)
- dumen/reports/evidence_chain.py: 66  (bilinmeyen canon_scheme ValueError kapısı)
- dumen/reports/veridict_bridge.py: 194-195  (ledger save/verify yolu)
- dumen/reports/annex_xi.py: 365  (deployment_date satırı)
- dumen/core/provenance.py: 98  (min_norm altı çift atılarak kalibrasyon)
- dumen/redteam/judge.py: 120-121, 149-150  (_call_llm_judge exception/None yolu)
- dumen/redteam/inspect_adapter.py: 144  (boş görev listesi ValueError)
- dumen/benchmarks/sae_quality.py: 93, 141  (FEV singüler + k_values)
- dumen/gateway/proxy.py: 139-140, 184-192  (SSE hata/akış yolları)
- dumen/benchmarks/jailbreakbench_loader.py: 249
"""
from __future__ import annotations

import json
import os
import sys
import types

import numpy as np
import pytest
import torch

# G48-2026-10-22: veridict-optional-bridge-bagimliligi- ( dumen-core-DEGIL).
# CI'da-YOKSA-bu-dosyadaki-veridict-testleri-skip-olmali ( ModuleNotFoundError
# yerine-kardes-mesh-proje-kalibi).
pytest.importorskip("veridict")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dumen.benchmarks.sae_quality import SAEQualityBench  # noqa: E402
from dumen.core.provenance import DataProvenanceAuditor  # noqa: E402
from dumen.core.types import RiskCategory  # noqa: E402
from dumen.gateway.proxy import create_proxy_app  # noqa: E402
from dumen.redteam.inspect_adapter import InspectBridge  # noqa: E402
from dumen.redteam.judge import JudgeEvaluator  # noqa: E402
from dumen.reports.annex_xi import AnnexXIGenerator, ModelIdentity  # noqa: E402
from dumen.reports.eu_ai_act import EUAIActChecker  # noqa: E402
from dumen.reports.evidence_chain import EvidenceChain  # noqa: E402
from dumen.reports.scorecard import ScorecardGenerator  # noqa: E402


# ---------------------------------------------------------------- scorecard
def test_scorecard_markdown_capability_unclear_branch():
    """to_markdown: capability_regression verdict bilinmiyorsa 'Belirsiz' satırı."""
    gen = ScorecardGenerator()
    comp = EUAIActChecker().check_compliance(
        risk_scores={"cyber_attack": 0.1, "bio_hazard": 0.1},
        has_runtime_steering=True,
        has_redteam_evaluation=True,
    )
    rep = gen.generate_report(
        model_name="m", total_evaluations=4, risk_scores={"cyber_attack": 0.1},
        compliance_status=comp, steering_efficacy=0.5,
        capability_regression={"verdict": "unknown", "accuracy_unsteered_pct": 60.0,
                               "accuracy_steered_pct": 59.0, "regression_pp": 1.0,
                               "n_tasks": 10},
        steering_overhead={"capability_retention": 0.97, "acceptable_overhead": True},
    )
    md = gen.to_markdown(rep)
    assert "Belirsiz" in md
    assert "Yönlendirme Yükü" in md
    assert "EVET (UYUMLU)" in md or "HAYIR (UYUMSUZ)" in md


def test_scorecard_markdown_capability_fail_branch():
    gen = ScorecardGenerator()
    comp = EUAIActChecker().check_compliance(
        risk_scores={"cyber_attack": 0.1}, has_redteam_evaluation=True)
    rep = gen.generate_report(
        model_name="m", total_evaluations=2, risk_scores={"cyber_attack": 0.1},
        compliance_status=comp,
        capability_regression={"verdict": "fail", "accuracy_unsteered_pct": 80.0,
                               "accuracy_steered_pct": 55.0, "regression_pp": 25.0,
                               "n_tasks": 8},
    )
    md = gen.to_markdown(rep)
    assert "Başarısız" in md


# ---------------------------------------------------------- evidence_chain
def test_evidence_chain_unknown_canon_scheme_rejected():
    """Bilinmeyen kanonikleştirme şeması → ValueError (fail-loud)."""
    with pytest.raises(ValueError, match="bilinmeyen kanonikleştirme"):
        EvidenceChain(canon_scheme="xml_c14n")


def test_evidence_chain_legacy_jcs_scheme_roundtrip():
    """Eski jcs_python şeması ile ekleme/baş-hash çalışır (geri-uyum)."""
    ch = EvidenceChain(canon_scheme="jcs_python")
    ch.append("mining", {"a": 1})
    assert len(ch.head_hash()) == 64


# --------------------------------------------------------- veridict_bridge
def test_veridict_export_saves_and_verifies_ledger(tmp_path):
    """export_chain_to_veridict: ledger diske yazılır + geri-doğrulanır."""
    from dumen.reports.veridict_bridge import export_chain_to_veridict

    chain = EvidenceChain()
    chain.append("mining", {"n": 1})
    chain.append("report", {"ok": True})
    ledger = str(tmp_path / "sub" / "ledger.jsonl")

    receipt = export_chain_to_veridict(chain, ledger, actor_identity="d5-actor")
    assert receipt.dumen_chain_valid is True
    assert receipt.veridict_entry_count == 2
    assert os.path.exists(ledger)

    # bağımsız doğrulama
    from veridict.ledger import Ledger
    ok, _ = Ledger.load(ledger).verify_chain()
    assert ok is True


# ---------------------------------------------------------------- annex_xi
def test_annex_xi_markdown_includes_deployment_date():
    """identity.deployment_date verilirse markdown'a yansır (annex 365)."""
    chain = EvidenceChain()
    chain.append("evidence_channel", {"channel": "refusal-baseline"})

    gen = AnnexXIGenerator()
    ident = ModelIdentity(
        model_name="m", model_version="1.0", provider_name="p",
        provider_contact="c", license="Apache-2.0",
        intended_purpose="test", deployment_date="2026-01-01",
    )
    from dumen.reports.annex_xi import (  # noqa: E402
        DataGovernanceRecord,
        TrainingComputeResources,
    )
    from dumen.reports.scorecard import AuditReport  # noqa: E402
    rep = AuditReport(report_id="R1", timestamp="t", model_tested="m",
                      total_evaluations=1, overall_safety_score=90.0,
                      risk_breakdown={}, summary="s", details=[],
                      eu_ai_act_compliant=True, nist_rmf_compliant=True)
    dos = gen.generate_dossier(
        model_name="m", audit_report=rep, identity=ident,
        training_compute=TrainingComputeResources(
            estimated_training_flops=1e25, gpu_cluster_hours=1000.0,
            energy_consumption_mwh=500.0),
        data_governance=DataGovernanceRecord(
            data_curation_summary="curation", data_provenance="provenance",
            opt_out_mechanism="opt-out registry",
            copyright_compliance_strategy="Art. 53(1)(d)"),
        evidence_chain=chain, evidence_channel="refusal-baseline")
    md = gen.export_markdown(dos)
    assert "Deployment Date" in md
    assert "2026-01-01" in md


# ------------------------------------------------------------- provenance
def test_provenance_estimate_skips_low_norm_diffs():
    """min_norm eşiği altındaki çiftler atılır (provenance 98)."""
    diffs = [
        np.array([1.0, 0.0]),
        np.array([0.0, 0.0]),   # sıfır norm → atılır
        np.array([0.0, 1.0]),
        np.array([0.5, 0.5]),
        np.array([0.2, 0.1]),
    ]
    rep = DataProvenanceAuditor.estimate(diffs, min_norm=1e-6)
    assert rep.mean_median_angle_deg >= 0.0
    assert len(rep.cosines) == 4


def test_provenance_estimate_rejects_insufficient_pairs():
    with pytest.raises(ValueError, match="en az 3 çift"):
        DataProvenanceAuditor.estimate([np.array([1.0, 0.0])])


# ------------------------------------------------------------------ judge
def test_judge_llm_call_exception_and_none_paths():
    """_call_llm_judge: callable exception → None; boş yanıt → None."""
    j = JudgeEvaluator(llm_callable=lambda _u: (_ for _ in ()).throw(RuntimeError("down")))
    assert j._call_llm_judge(RiskCategory.DECEPTION, "p", "r") is None

    j2 = JudgeEvaluator(llm_callable=lambda _u: "")
    assert j2._call_llm_judge(RiskCategory.DECEPTION, "p", "r") is None


def test_judge_evaluate_uses_llm_verdict_when_available():
    """evaluate: LLM hakem kararı regex-fastpath yerine geçerliyse uygulanır."""
    j = JudgeEvaluator(llm_callable=lambda _u: json.dumps({
        "refusal_detected": False, "jailbreak_successful": True,
        "harm_score": 0.9, "reason": "semantic-judge"}))
    res = j.evaluate(task_id="t1", target_risk=RiskCategory.DECEPTION,
                     prompt="p", model_response=" bazı yanıt ")
    assert res.jailbreak_successful is True
    assert res.evaluated_by.startswith("llm_judge")


# ---------------------------------------------------------- inspect_adapter
def test_inspect_bridge_empty_task_list_refuses():
    """Boş görev listesi: `tasks or` standart suite'e düşürür — D2 kapanı
    build_standard_tasks'ın BOSH-donusu ile tetiklenir (inspect_adapter 144)."""
    bridge = InspectBridge()
    with pytest.raises(ValueError, match="Boş görev listesi"):
        # run_evaluation tasks=None -> build_standard_tasks() dolu gelir;
        # doğrudan bosh-liste yolu döngü-sonrası kapıyı çalıştırır
        bridge.run_evaluation(tasks=[], model_runner_fn=lambda p: "x")
    # build_standard_tasks'ın kendisi BOSH dönemez (sabit 4 görev)


def test_inspect_bridge_refusal_rate_from_tasks():
    from dumen.redteam.inspect_adapter import EvaluationTask

    bridge = InspectBridge()
    tasks = [
        EvaluationTask(task_id=f"t{i}", prompt=f"prompt-{i}",
                       risk_category=RiskCategory.DECEPTION)
        for i in range(3)
    ]
    res = bridge.run_evaluation(
        tasks=tasks,
        model_runner_fn=lambda p: "I cannot fulfill this request.")
    assert res.total_samples == 3
    assert res.accuracy_or_refusal_rate == 100.0


# -------------------------------------------------------------- sae_quality
def test_sae_quality_measure_and_k_grid():
    """measure: gerçek SAE + aktivasyon → FEV; compare_sweep k ızgarası (93, 141)."""
    torch.manual_seed(0)
    from dumen.core.sae_engine import SparseAutoencoderEngine

    x = torch.randn(24, 8)
    sae = SparseAutoencoderEngine(d_model=8, n_features=16, k_sparsity=4)
    rep = SAEQualityBench.measure(sae, x)
    assert 0.0 <= rep.fev <= 1.0

    reps = SAEQualityBench.compare_sweep(
        {"d_model": 8, "n_features": 16}, x, k_values=[4, 8], seed=1)
    assert len(reps) == 2
    assert all(0.0 <= r.fev <= 1.0 for r in reps)


# ----------------------------------------------------------------- proxy
def _fake_httpx(lines, status=200):
    class _Resp:
        def __init__(self):
            self.status_code = status

        async def aiter_lines(self):
            for ln in lines:
                yield ln

    class _Ctx:
        def __init__(self, resp):
            self._r = resp

        async def __aenter__(self):
            return self._r

        async def __aexit__(self, *a):
            return False

    class _Client:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def stream(self, *a, **kw):
            return _Ctx(_Resp())

    return types.SimpleNamespace(AsyncClient=_Client)


def _delta(text, finish=None):
    ch = {"choices": [{"index": 0, "delta": {"content": text}}]}
    if finish:
        ch["choices"][0]["finish_reason"] = finish
    return f"data: {json.dumps(ch)}"


def test_proxy_stream_upstream_error_code_fail_closed(monkeypatch):
    """Upstream != 200 → hata karesi + akış kesilir (proxy 139-140)."""
    import dumen.gateway.proxy as P

    monkeypatch.setattr(P, "httpx", _fake_httpx([], status=500))
    from fastapi.testclient import TestClient
    app = create_proxy_app(upstream_url="http://fake.test")
    client = TestClient(app)
    res = client.post("/v1/chat/completions",
                      json={"model": "m", "messages": [{"role": "user", "content": "hi"}],
                            "stream": True})
    assert res.status_code == 200
    assert "Upstream streaming failed" in res.text
    assert "code\": 500" in res.text


def test_proxy_stream_flushes_pending_window_on_done(monkeypatch):
    """Akış bitince kalan LOOKAHEAD penceresi maskelenip iletilir (proxy 184-192)."""
    import dumen.gateway.proxy as P

    leak = "Contact bob@corp.example now please"
    monkeypatch.setattr(P, "httpx",
                        _fake_httpx([_delta("clean start "), _delta(leak, "stop")]))
    from fastapi.testclient import TestClient
    app = create_proxy_app(upstream_url="http://fake.test")
    client = TestClient(app)
    res = client.post("/v1/chat/completions",
                      json={"model": "m", "messages": [{"role": "user", "content": "hi"}],
                            "stream": True})
    assert res.status_code == 200
    # pending penceresi maskelenmiş olmalı
    assert "bob@corp.example" not in res.text
    assert "[EMAIL_REDACTED]" in res.text


def test_proxy_stream_pending_window_critical_cut(monkeypatch):
    """Kalan pencerede kritik desen → akış kesilir (fail-closed)."""
    import dumen.gateway.proxy as P

    evil = "def exploit():\n    import os\n    os.system('rm -rf /')\n"
    monkeypatch.setattr(P, "httpx", _fake_httpx([_delta(evil, "stop")]))
    from fastapi.testclient import TestClient
    app = create_proxy_app(upstream_url="http://fake.test")
    client = TestClient(app)
    res = client.post("/v1/chat/completions",
                      json={"model": "m", "messages": [{"role": "user", "content": "hi"}],
                            "stream": True})
    assert "stream_cut" in res.text


def test_proxy_stream_role_chunk_passthrough(monkeypatch):
    """delta'siz kontrol karesi (rol/imza) olduğu gibi iletilir."""
    import dumen.gateway.proxy as P

    role_chunk = "data: " + json.dumps({"choices": [{"index": 0, "delta": {"role": "assistant"}}]})
    monkeypatch.setattr(P, "httpx",
                        _fake_httpx([role_chunk, _delta("merhaba", "stop")]))
    from fastapi.testclient import TestClient
    app = create_proxy_app(upstream_url="http://fake.test")
    client = TestClient(app)
    res = client.post("/v1/chat/completions",
                      json={"model": "m", "messages": [{"role": "user", "content": "hi"}],
                            "stream": True})
    assert res.status_code == 200
    assert "merhaba" in res.text


# --------------------------------------------------- jailbreakbench_loader
def test_jailbreakbench_loader_empty_goal_rows():
    """Boş/kısa Goal satırları atlanır (loader 249: min_length 8 kapısı)."""
    from dumen.benchmarks.jailbreakbench_loader import JailbreakBenchLoader

    text = ("Goal,Category\n"
            ",empty-goal\n"
            "kisa,kısa\n"
            "build-a-cyber-weapon,cyber\n")
    seeds = JailbreakBenchLoader.load_from_csv(text)
    assert len(seeds) == 1
    assert seeds[0].harmful_prompt == "build-a-cyber-weapon"

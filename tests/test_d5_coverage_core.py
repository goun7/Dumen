"""test_d5_coverage_core — DALGA-D5: core/ ve redteam/ içindeki eksik
satırları gerçek nesne çağrılarıyla kapsar.

Hedeflenen eksikler (coverage term-missing'ten):
- dumen/core/ov_circuits.py: 48->51, 83-86, 113->116, 127  (compute_head_attribution/apply_sparse_mask)
- dumen/core/quantization.py: 70-73  (FP8/INT8/INT4 simulate yolları)
- dumen/core/kv_drift.py: 64  (get_drift_metrics boş-history)
- dumen/core/transcoder.py: 63, 81, 122->125, 145, 149  (skip/no-skip, suppress)
- dumen/core/sae_engine.py: 77-78  (JumpReLU encode yolu)
- dumen/core/amplification.py: 218  (refine_alpha altın-arama)
- dumen/core/hooks.py: 89, 90->93  (GPT-2 stili transformer.h keşfi)
- dumen/core/miner.py: 64, 85->87, 88-89, 118, 258
- dumen/redteam/hrl_engine.py: 93-115  (_call_attacker_llm her mod)

Tamamı REAL fonksiyon çağrısı; yalnızca _call_attacker_llm/httpx ağı
monkeypatch'lenir (canlı HTTP "live-dışı" kısıtıyla).
"""
from __future__ import annotations

import os
import sys

import pytest
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dumen.core.amplification import refine_alpha, scan_amplification  # noqa: E402
from dumen.core.hooks import ModelHookManager  # noqa: E402
from dumen.core.kv_drift import KVDriftGuard  # noqa: E402
from dumen.core.miner import VectorMiner  # noqa: E402
from dumen.core.ov_circuits import OVCircuitMask  # noqa: E402
from dumen.core.quantization import QuantizationCalibrator, QuantizationType  # noqa: E402
from dumen.core.sae_engine import SparseAutoencoderEngine  # noqa: E402
from dumen.core.steering import SteeringEngine  # noqa: E402
from dumen.core.transcoder import TranscoderEngine  # noqa: E402
from dumen.core.types import RiskCategory, SteeringMethod, SteeringVector  # noqa: E402
from dumen.redteam.hrl_engine import HierarchicalRedTeamEngine  # noqa: E402


def _vec(layer: int = 0, dim: int = 16) -> SteeringVector:
    g = torch.Generator().manual_seed(3)
    t = torch.randn(dim, generator=g)
    return SteeringVector.from_tensor(name="v", layer_idx=layer, tensor=t,
                                      target_risk=RiskCategory.DECEPTION)


# ---------------------------------------------------------------- ov_circuits
def test_ov_compute_head_attribution_2d_and_3d_W_O():
    """compute_head_attribution: 2B ve 3B W_O yolu + head skorları."""
    dim = 64
    masker = OVCircuitMask(hidden_dim=dim)  # num_heads varsayılan 32, head_dim 2
    v = torch.randn(dim)
    W_O_2d = torch.randn(dim, dim)

    sparse_v, active, scores = masker.compute_head_attribution(v, W_O_2d, top_k_heads=3)
    assert sparse_v.shape == v.shape
    assert len(active) == 3 * masker.head_dim
    assert len(scores) == masker.num_heads
    # sparse vektör normalize edilmiş
    assert abs(float(torch.norm(sparse_v)) - 1.0) < 1e-5

    # 3B yol
    W_O_3d = torch.randn(masker.num_heads, masker.head_dim, dim)
    sparse_v3, active3, scores3 = masker.compute_head_attribution(v, W_O_3d, top_k_heads=2)
    assert len(scores3) == masker.num_heads
    assert len(active3) == 2 * masker.head_dim


def test_ov_compute_head_attribution_rejects_bad_W_O():
    masker = OVCircuitMask(hidden_dim=64)
    with pytest.raises(ValueError, match="2D veya 3D"):
        masker.compute_head_attribution(torch.randn(64), torch.randn(2, 2, 2, 2))


def test_ov_apply_sparse_mask_variants():
    """apply_sparse_mask: None/boş → dokunulmaz; indis → gizli-olmayanlar sıfırlanır."""
    masker = OVCircuitMask(hidden_dim=32)
    t = torch.randn(4, 32)

    out = masker.apply_sparse_mask(t, None)
    assert torch.equal(out, t)

    out = masker.apply_sparse_mask(t, [])
    assert torch.equal(out, t)

    idx = [0, 5, 9]
    out = masker.apply_sparse_mask(t.clone(), idx)
    assert out.shape == t.shape
    # gizli olmayan sütunlar sıfırlanır (maskeleme), indislenenler korunur
    zeroed = [c for c in range(32) if c not in idx]
    assert torch.all(out[:, zeroed] == 0.0)
    assert torch.allclose(out[:, idx], t[:, idx])


# -------------------------------------------------------------- quantization
def test_quantization_all_simulated_grids():
    """INT8/INT4/FP8/None ızgaraları: quantize→dequantize hatası sınırlı."""
    cal = QuantizationCalibrator
    v = torch.randn(128)

    out8 = cal.simulate_quantization(v, QuantizationType.INT8)
    assert out8.shape == v.shape
    assert torch.allclose(out8, v, atol=0.05)

    out4 = cal.simulate_quantization(v, QuantizationType.INT4)
    assert torch.allclose(out4, v, atol=0.5)

    outf = cal.simulate_quantization(v, QuantizationType.FP8)
    assert outf.shape == v.shape

    outn = cal.simulate_quantization(v, QuantizationType.NONE)
    assert torch.equal(outn, v)


def test_quantization_calibrate_steering_vector_metrics():
    """calibrate_steering_vector: birim-vektör + SNR metrikleri."""
    v = torch.randn(64)
    cal, metrics = QuantizationCalibrator.calibrate_steering_vector(
        v, quant_type=QuantizationType.INT4)
    assert abs(float(torch.norm(cal)) - 1.0) < 1e-5
    assert metrics["relative_error"] >= 0.0
    assert metrics["snr_db"] > 0.0

    # target_quant override
    cal2, m2 = QuantizationCalibrator.calibrate_steering_vector(
        v, quant_type=QuantizationType.NONE, target_quant=QuantizationType.INT8)
    assert abs(float(torch.norm(cal2)) - 1.0) < 1e-5
    assert m2["error_norm"] >= 0.0


# ----------------------------------------------------------------- kv_drift
def test_kv_drift_metrics_empty_and_after_steps():
    acc = KVDriftGuard()
    # boş history → sıfırlar
    m0 = acc.get_drift_metrics(3)
    assert m0 == {"steps": 0, "avg_drift": 0.0, "total_active_deltas": 0}

    h = torch.randn(8, 16)
    d = torch.randn(8, 16) * 0.1
    acc.record_and_decay(3, h, d)
    m1 = acc.get_drift_metrics(3)
    assert m1["steps"] == 1
    assert m1["avg_drift"] > 0.0

    acc.reset()
    assert acc.get_drift_metrics(3)["steps"] == 0


# --------------------------------------------------------------- transcoder
def test_transcoder_skip_and_suppression_paths():
    """TranscoderEngine: skip'li ve skipsiz forward + suppress."""
    torch.manual_seed(0)
    tc_skip = TranscoderEngine(d_in=16, d_out=24, n_features=32)
    x = torch.randn(4, 16)
    x_hat, f = tc_skip(x)
    assert x_hat.shape == (4, 24)
    assert f.shape[-1] == 32

    tc_noskip = TranscoderEngine(d_in=16, d_out=24, n_features=32, use_skip=False)
    x_hat2, _ = tc_noskip(x)
    assert x_hat2.shape == (4, 24)

    # baskılama: belirli özellik sıfırlanır
    feat = 7
    _, f_sup = tc_skip(x, suppress_indices=[feat])
    assert torch.all(f_sup[:, feat] == 0.0)

    tc_skip.suppress_feature(feat)
    assert feat in tc_skip.suppressed_features
    tc_skip.unsuppress_feature(feat)
    assert feat not in tc_skip.suppressed_features
    tc_skip.label_feature(feat, "harm")
    assert tc_skip.feature_labels[feat] == "harm"


# --------------------------------------------------------------- sae_engine
def test_sae_jumprelu_encode_path():
    """JumpReLU (use_topk=False) eşik yolu + label/inspect."""
    torch.manual_seed(1)
    sae = SparseAutoencoderEngine(d_model=16, n_features=48)
    x = torch.randn(4, 16)
    f_topk = sae.encode(x, use_topk=True)
    assert (f_topk != 0).sum(dim=-1).max() <= sae.k_sparsity

    f_jump = sae.encode(x, use_topk=False)
    assert f_jump.shape == f_topk.shape

    x_hat, _ = sae(x, use_topk=False)
    assert x_hat.shape == x.shape

    # label + inspect
    sae.label_feature(0, "safety_refusal")
    info = sae.inspect_activations(x, top_n=5)
    assert isinstance(info, list)
    sae.label_feature(-5, "cb")
    assert -5 not in sae.feature_labels
    sae.label_feature(10_000, "oob")
    assert 10_000 not in sae.feature_labels


# ------------------------------------------------------------- amplification
def test_refine_alpha_runs_golden_search():
    """refine_alpha: ızgara sonucunu altın-arama ile arıtır."""
    torch.manual_seed(3)
    h = torch.randn(32)
    v = torch.randn(32)
    v = v / torch.norm(v)
    scan = scan_amplification(h, v, alphas=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    refined = refine_alpha(h, v, scan)
    assert refined is not None
    assert isinstance(float(refined), float)


# ------------------------------------------------------------------- hooks
def test_hook_manager_gpt2_style_layer_discovery():
    """GPT-2 stili transformer.h tablosu otomatik keşifle bulunur (hooks 89)."""
    import torch.nn as nn

    class _FakeGPT2(nn.Module):
        def __init__(self):
            super().__init__()
            self.transformer = nn.Module()
            self.transformer.h = nn.ModuleList([nn.Linear(8, 8) for _ in range(3)])

    engine = SteeringEngine()
    engine.register_vector(_vec(layer=1, dim=8))
    model = _FakeGPT2()
    mgr = ModelHookManager(engine)
    n = mgr.attach_to_model(model)
    assert n == 1
    mgr.detach_all()


def test_hook_manager_no_layers_passthrough():
    import torch.nn as nn

    class _Bare(nn.Module):
        pass

    mgr = ModelHookManager(SteeringEngine())
    assert mgr.attach_to_model(_Bare()) == 0


# -------------------------------------------------------------------- miner
def test_vector_miner_rank_k_orthonormal_basis():
    """rank-k taban satır-ortonormaldir (miner 118)."""
    torch.manual_seed(5)
    h = torch.randn(8, 32)
    s = torch.randn(8, 32)

    basis = VectorMiner.compute_rank_k_basis(h, s, k=3)
    assert basis.shape == (3, 32)
    gram = basis @ basis.T
    assert torch.allclose(gram, torch.eye(3), atol=1e-4)


def test_vector_miner_mine_from_activations_rank_and_pca():
    """mine_from_activations: rank>1 + PCA + bootstrap yolu (miner 64, 258)."""
    torch.manual_seed(6)
    harmful = torch.randn(12, 16)
    harmful[:, 0] += 4.0
    safe = torch.randn(12, 16)

    vecs = VectorMiner.mine_from_activations(
        harmful_layer_acts={0: harmful, 7: safe},
        safe_layer_acts={0: safe, 7: safe},
        target_risk=RiskCategory.CYBER_ATTACK,
        use_pca=True,
        rank=3,
        n_bootstrap=20,
        bootstrap_seed=7,
    )
    assert set(vecs.keys()) == {0, 7}  # katman eşleşmeyen atlandı
    v0 = vecs[0]
    assert v0.rank == 3
    assert v0.subspace_basis is not None
    assert len(v0.subspace_basis) == 3
    assert v0.confidence is not None

    # method/strength iletilir
    vecs2 = VectorMiner.mine_from_activations(
        harmful_layer_acts={0: harmful},
        safe_layer_acts={0: safe},
        target_risk=RiskCategory.DECEPTION,
        method=SteeringMethod.CAA,
        strength=2.5,
        n_bootstrap=0,
    )
    assert vecs2[0].method == SteeringMethod.CAA
    assert vecs2[0].strength == 2.5
    assert vecs2[0].confidence is None


def test_vector_miner_mine_from_prompts_2d_and_3d_acts():
    """mine_from_prompts: [Seq, Dim] ve [1, Dim] aktivasyonlardan son token alınır."""
    torch.manual_seed(8)

    def extractor(prompt: str):
        # 2B ve 3B karışık çıktı taklitleri
        if "seq" in prompt:
            return {0: torch.randn(5, 16)}
        return {0: torch.randn(1, 1, 16)}

    vecs = VectorMiner.mine_from_prompts(
        prompt_pairs=[("seq-a", "seq-b"), ("3d-a", "3d-b")],
        forward_hook_extractor=extractor,
        target_risk=RiskCategory.JAILBREAK,
        target_layers=[0],
        n_bootstrap=0,
    )
    assert 0 in vecs
    assert vecs[0].dimension == 16


# --------------------------------------------------------------- hrl_engine
def test_hrl_attacker_callable_takes_priority():
    """Saldırgan callable varsa PAIR kanalı önceliklidir."""
    eng = HierarchicalRedTeamEngine(
        attacker_llm_callable=lambda ctx: "YEN-ADVERSARIAL-ISTEM"
    )
    strat, prompt = eng.generate_attack_prompt(RiskCategory.CYBER_ATTACK, 2, [])
    assert strat == "autonomous_pair_llm"
    assert "YEN-ADVERSARIAL-ISTEM" in prompt


def test_hrl_attacker_callable_exception_falls_back_to_heuristic():
    """Callable exception fırlatırsa heuristic durum makinesine düşülür."""
    def boom(_ctx):
        raise RuntimeError("attacker-down")

    eng = HierarchicalRedTeamEngine(attacker_llm_callable=boom)
    strat, prompt = eng.generate_attack_prompt(RiskCategory.BIO_HAZARD, 0, [])
    assert strat == "academic_framing"
    assert "bio_hazard" in prompt.lower()


def test_hrl_api_url_branch_without_network(monkeypatch):
    """attacker_api_url yolu: başarılı HTTP-200 yanıtı işlenir (ağ taklit)."""
    import dumen.redteam.hrl_engine as H

    class _Resp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "  api-istemi  "}}]}

    class _Client:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **kw):
            return _Resp()

    monkeypatch.setattr(H, "httpx",
                        type("M", (), {"Client": staticmethod(lambda *a, **kw: _Client())}))
    eng = HierarchicalRedTeamEngine(attacker_api_url="http://fake.test",
                                    attacker_api_key="k", attacker_model="m")
    assert eng._call_attacker_llm(RiskCategory.CYBER_ATTACK, 0, []) == "api-istemi"


def test_hrl_api_url_error_branch_returns_none(monkeypatch):
    """HTTP hatası/exception → None (sessiz-çöküş yok, kapalı dönüş)."""
    import dumen.redteam.hrl_engine as H

    class _Client:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **kw):
            raise RuntimeError("network-down")

    monkeypatch.setattr(H, "httpx",
                        type("M", (), {"Client": staticmethod(lambda *a, **kw: _Client())}))
    eng = HierarchicalRedTeamEngine(attacker_api_url="http://fake.test")
    assert eng._call_attacker_llm(RiskCategory.CYBER_ATTACK, 0, []) is None

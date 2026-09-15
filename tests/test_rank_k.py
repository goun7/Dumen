"""
tests/test_rank_k.py
====================
Rank-k Refusal Manifold (Arditi-sonrası, arXiv:2606.13720) ve bootstrap
yön-güven aralığı testleri.
"""

import torch

from dumen.core.miner import VectorMiner
from dumen.core.types import RiskCategory, SteeringVector


def make_clusters(n: int = 40, dim: int = 32, signal_strength: float = 5.0, seed: int = 7):
    """Belirgin bir zararlı-güvenli ayrımı üretir: zararlı küme 0. eksende kaydırılır."""
    g = torch.Generator().manual_seed(seed)
    harmful = torch.randn(n, dim, generator=g)
    harmful[:, 0] += signal_strength
    safe = torch.randn(n, dim, generator=g)
    return harmful, safe


class TestRankKBasis:
    def test_basis_shape_and_orthonormality(self):
        harmful, safe = make_clusters()
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=4)
        assert basis.shape == (4, 32)
        # Satırlar ortonormal olmalı: B B^T = I_k
        gram = basis @ basis.T
        assert torch.allclose(gram, torch.eye(4), atol=1e-5)

    def test_first_direction_matches_dim(self):
        """En güçlü singular yön, DiM yönüyle hizalı olmalı (güçlü tek-eksen sinyalde)."""
        harmful, safe = make_clusters()
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=3)
        dim_vec = VectorMiner.compute_difference_in_means(harmful, safe)
        cos = torch.dot(basis[0], dim_vec) / (torch.norm(basis[0]) * torch.norm(dim_vec) + 1e-8)
        assert cos > 0.85, f"İlk singular yön DiM'den ayrışıyor: {cos:.3f}"

    def test_k_cannot_exceed_sample_count(self):
        """k, örnek sayısını aşarsa güvenlice kırpılmalı (min(n, dim, k))."""
        harmful, safe = make_clusters(n=3, dim=8)
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=10)
        assert basis.shape[0] == 3

    def test_subspace_projection_reduces_risk_component(self):
        """subtract=True: manifold bileşeni söndürüldüğünde risk yönüne izdüşüm düşmeli."""
        harmful, safe = make_clusters()
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=2)
        dim_vec = VectorMiner.compute_difference_in_means(harmful, safe)
        dim_vec = dim_vec / (torch.norm(dim_vec) + 1e-8)

        # Risk yönünde güçlü aktivasyon
        x = torch.randn(32)
        x = x + 3.0 * dim_vec
        proj_before = float(torch.dot(x, dim_vec))

        out = VectorMiner.project_to_subspace(x, basis, alpha=1.0, subtract=True)
        proj_after = float(torch.dot(out, dim_vec))
        assert proj_after < proj_before, "Altuzay ablasyonu risk bileşenini azaltmalı"

    def test_subspace_projection_batch_shape_preserved(self):
        """[B, S, Dim] girdi şekli korunmalı."""
        harmful, safe = make_clusters()
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=2)
        x = torch.randn(2, 3, 32)
        out = VectorMiner.project_to_subspace(x, basis)
        assert out.shape == x.shape

    def test_amplify_mode_increases_risk_component(self):
        """subtract=False: manifold pekiştirme risk bileşenini artırmalı (tetikleme testi)."""
        harmful, safe = make_clusters()
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=2)
        dim_vec = VectorMiner.compute_difference_in_means(harmful, safe)
        dim_vec = dim_vec / (torch.norm(dim_vec) + 1e-8)
        g = torch.Generator().manual_seed(4242)  # global RNG bağımlılığını kes
        x = torch.randn(32, generator=g)
        out = VectorMiner.project_to_subspace(x, basis, alpha=0.5, subtract=False)
        assert float(torch.dot(out, dim_vec)) > float(torch.dot(x, dim_vec))


class TestBootstrapConfidence:
    def test_strong_signal_high_confidence(self):
        """Belirgin ayrımda bootstrap güveni yüksek (≥0.90) olmalı."""
        harmful, safe = make_clusters(n=50, signal_strength=5.0)
        conf = VectorMiner.bootstrap_confidence(harmful, safe, n_resamples=40)
        assert conf >= 0.90

    def test_weak_signal_lower_confidence(self):
        """Zayıf/noisy sinyalde güven düşmeli — ölçüm ayırt edici olmalı."""
        torch.manual_seed(3)
        harmful = torch.randn(8, 16)  # hiç sinyal yok
        safe = torch.randn(8, 16)
        conf = VectorMiner.bootstrap_confidence(harmful, safe, n_resamples=40)
        strong_h, strong_s = make_clusters(n=50, signal_strength=5.0)
        conf_strong = VectorMiner.bootstrap_confidence(strong_h, strong_s, n_resamples=40)
        assert conf < conf_strong, "Sinyalsiz veri, güçlü sinyalden daha düşük güven almalı"

    def test_single_sample_returns_full_confidence(self):
        """n=1'de bootstrap tanımsız → 1.0 dönmeli (degenerasyondan kaçınma)."""
        h = torch.randn(1, 8)
        s = torch.randn(1, 8)
        assert VectorMiner.bootstrap_confidence(h, s) == 1.0

    def test_deterministic_with_seed(self):
        """Aynı seed → aynı güven değeri (yeniden üretilebilirlik)."""
        harmful, safe = make_clusters(n=30)
        c1 = VectorMiner.bootstrap_confidence(harmful, safe, n_resamples=20, seed=99)
        c2 = VectorMiner.bootstrap_confidence(harmful, safe, n_resamples=20, seed=99)
        assert c1 == c2


class TestMiningIntegration:
    def test_mine_from_activations_rank_k_and_confidence(self):
        harmful, safe = make_clusters(n=30)
        vecs = VectorMiner.mine_from_activations(
            harmful_layer_acts={12: harmful},
            safe_layer_acts={12: safe},
            target_risk=RiskCategory.JAILBREAK,
            rank=3,
            n_bootstrap=25,
        )
        v = vecs[12]
        assert v.rank == 3
        assert v.subspace_basis is not None and len(v.subspace_basis) == 3
        assert 0.0 <= v.confidence <= 1.0
        assert v.confidence >= 0.85  # güçlü sinyal

    def test_mine_from_activations_default_rank1_no_basis(self):
        """rank=1 (varsayılan) davranış geriye dönük uyumlu: taban Yok, güven yine hesaplanır."""
        harmful, safe = make_clusters(n=10)
        vecs = VectorMiner.mine_from_activations(
            harmful_layer_acts={12: harmful},
            safe_layer_acts={12: safe},
            target_risk=RiskCategory.DECEPTION,
        )
        v = vecs[12]
        assert v.rank == 1
        assert v.subspace_basis is None

    def test_steering_vector_roundtrip_with_new_fields(self):
        """Genişletilmiş SteeringVector şeması serileştirme yuvarır turu atmalı."""
        harmful, safe = make_clusters(n=20)
        basis = VectorMiner.compute_rank_k_basis(harmful, safe, k=2)
        v = SteeringVector.from_tensor(
            name="test_rk",
            layer_idx=5,
            tensor=VectorMiner.compute_difference_in_means(harmful, safe),
            target_risk=RiskCategory.CYBER_ATTACK,
            rank=2,
            subspace_basis=basis.tolist(),
            confidence=0.93,
        )
        payload = v.model_dump_json()
        rebuilt = SteeringVector.model_validate_json(payload)
        assert rebuilt.rank == 2
        assert rebuilt.confidence == 0.93
        assert rebuilt.subspace_basis is not None
        basis_t = rebuilt.to_subspace_basis()
        assert basis_t is not None and basis_t.shape == (2, 32)

    def test_mine_from_prompts_carries_confidence(self):
        """İstem hattı da confidence taşımalı (uçtan uca)."""
        from dumen.benchmarks import ContrastiveBenchmarkSuite
        suite = ContrastiveBenchmarkSuite()
        pairs = suite.get_contrastive_pairs(RiskCategory.DECEPTION)

        def extractor(prompt: str) -> dict:
            g = torch.Generator().manual_seed(abs(hash(prompt)) % (2**31))
            acts = torch.randn(1, 16, generator=g)
            return {12: acts}

        vecs = VectorMiner.mine_from_prompts(
            prompt_pairs=pairs,
            forward_hook_extractor=extractor,
            target_risk=RiskCategory.DECEPTION,
            target_layers=[12],
            n_bootstrap=15,
        )
        assert vecs[12].confidence >= 0.0


class TestPermutationSignificance:
    """Permütasyon anlamlılık testi (v0.6.0): madencilik sonuçlarının İSTATİSTİKİ kanıtı."""

    def test_strong_signal_significant(self):
        """Belirgin ayrım p < 0.05 vermeli — madencilik tesadüf değil."""
        harmful, safe = make_clusters(n=40, signal_strength=5.0)
        p = VectorMiner.permutation_significance(harmful, safe, n_permutations=100)
        assert p < 0.05, f"Güçlü sinyal anlamsız çıktı: p={p}"

    def test_null_signal_not_significant(self):
        """Sinyalsiz veri p > 0.05 vermeli — test sahte pozitif üretmemeli."""
        g = torch.Generator().manual_seed(11)
        h = torch.randn(40, 32, generator=g)
        s = torch.randn(40, 32, generator=g)
        p = VectorMiner.permutation_significance(h, s, n_permutations=100)
        assert p > 0.05, f"Null veri anlamlı çıktı (FP): p={p}"

    def test_p_value_bounds(self):
        """p ∈ (0, 1]; asla tam 0 olmamalı (+1 düzeltmesi)."""
        harmful, safe = make_clusters(n=30, signal_strength=50.0)  # aşırı güçlü
        p = VectorMiner.permutation_significance(harmful, safe, n_permutations=50)
        assert 0.0 < p <= 1.0

    def test_deterministic_with_seed(self):
        harmful, safe = make_clusters(n=20)
        p1 = VectorMiner.permutation_significance(harmful, safe, n_permutations=30, seed=99)
        p2 = VectorMiner.permutation_significance(harmful, safe, n_permutations=30, seed=99)
        assert p1 == p2

    def test_single_sample_degenerate(self):
        """n=1'de test tanımsız → p=1 (anlamsız) dönmeli."""
        h = torch.randn(1, 8)
        s = torch.randn(1, 8)
        assert VectorMiner.permutation_significance(h, s) == 1.0

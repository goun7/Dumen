"""
tests/test_sae_quality.py
=========================
SAE Kalite Metrikleri testleri (SAEBench tarzı — Karvonen et al., ICML 2025).
"""

import pytest
import torch
import torch.nn.functional as F

from dumen.core.sae_engine import SparseAutoencoderEngine
from dumen.benchmarks.sae_quality import SAEQualityBench, SAEQualityReport


def make_sae(d_model=32, n_features=256, k=16, seed=1) -> SparseAutoencoderEngine:
    torch.manual_seed(seed)
    return SparseAutoencoderEngine(d_model=d_model, n_features=n_features, k_sparsity=k)


def train_sae(sae, acts, epochs=60, lr=1e-2):
    opt = torch.optim.Adam(sae.parameters(), lr=lr)
    sae.train()
    for _ in range(epochs):
        opt.zero_grad()
        recon, _ = sae(acts)
        loss = F.mse_loss(recon, acts) + 1e-4 * sae.compute_mutual_regularization_loss()
        loss.backward()
        opt.step()
    return sae


class TestMeasure:
    def test_report_fields_populated(self):
        sae = make_sae()
        torch.manual_seed(2)
        acts = torch.randn(48, 32)
        rep = SAEQualityBench.measure(sae, acts)
        assert isinstance(rep, SAEQualityReport)
        assert rep.d_model == 32 and rep.n_features == 256 and rep.k_sparsity == 16
        assert 0.0 <= rep.fev <= 1.0
        assert rep.reconstruction_mse >= 0.0
        assert -1.0 <= rep.downstream_cosine <= 1.0
        assert rep.l0_sparsity >= 0.0

    def test_trained_sae_achieves_high_fev(self):
        """Isınmış SAE rastgele verinin büyük çoğunluğunu yeniden inşa etmeli."""
        torch.manual_seed(3)
        acts = torch.randn(64, 32)
        sae = train_sae(make_sae(k=16), acts, epochs=80)
        rep = SAEQualityBench.measure(sae, acts)
        assert rep.fev >= 0.85, f"Eğitilmiş SAE FEV düşük: {rep.fev}"
        assert rep.unexplained_variance_warning is False
        assert rep.downstream_cosine >= 0.90

    def test_untrained_sae_flags_warning(self):
        """Rastgele başlatılmış (eğitimsiz) SAE kör nokta uyarısı vermeli."""
        torch.manual_seed(4)
        acts = torch.randn(64, 32)
        sae = make_sae(seed=99)  # eğitimsiz
        rep = SAEQualityBench.measure(sae, acts)
        # Rastgele ağırlıklarla FEV genelde 0.85 altında kalır; garanti değil ama
        # uyarı bayrağı FEV eşiğine tam bağlı olmalı
        assert rep.unexplained_variance_warning == (rep.fev < 0.85)

    def test_topk_respects_k_sparsity(self):
        """TopK kodlama L0 ≤ k garantisi (seyreltik sözleşmesi)."""
        sae = make_sae(k=8)
        torch.manual_seed(5)
        acts = torch.randn(32, 32)
        rep = SAEQualityBench.measure(sae, acts)
        assert rep.l0_sparsity <= 8.0 + 1e-6, f"TopK sözleşme ihlali: L0={rep.l0_sparsity} > k=8"

    def test_measure_rejects_bad_shapes(self):
        sae = make_sae(d_model=32)
        with pytest.raises(ValueError):
            SAEQualityBench.measure(sae, torch.randn(10, 64))  # yanlış d_model
        with pytest.raises(ValueError):
            SAEQualityBench.measure(sae, torch.randn(32))     # 1-D
        with pytest.raises(ValueError):
            SAEQualityBench.measure(sae, torch.zeros(0, 32)) # boş

    def test_measure_restores_training_mode(self):
        """Ölçüm SAE'nin eğitim modunu bozmamalı."""
        sae = make_sae()
        sae.train()
        torch.manual_seed(6)
        acts = torch.randn(16, 32)
        SAEQualityBench.measure(sae, acts)
        assert sae.training is True
        sae.eval()
        SAEQualityBench.measure(sae, acts)
        assert sae.training is False


class TestSweep:
    def test_compare_sweep_monotonic_fev_tradeoff(self):
        """k arttıkça FEV artmalı veya en azından düşmemeli (seyreltik-doğruluk eğrisi)."""
        torch.manual_seed(7)
        acts = torch.randn(48, 16)
        reports = SAEQualityBench.compare_sweep(
            base_kwargs={"d_model": 16, "n_features": 128},
            activations=acts,
            k_values=[4, 16],
            seed=11,
        )
        assert len(reports) == 2
        assert reports[0].k_sparsity == 4 and reports[1].k_sparsity == 16
        # k=16, k=4'ten daha yüksek (veya eşit) FEV'e ulaşmalı
        assert reports[1].fev >= reports[0].fev - 0.05

    def test_sweep_reports_are_reproducible(self):
        """Aynı seed → aynı metrikler."""
        torch.manual_seed(8)
        acts = torch.randn(32, 16)
        r1 = SAEQualityBench.compare_sweep(
            {"d_model": 16, "n_features": 96}, acts, k_values=[8], seed=42,
        )
        r2 = SAEQualityBench.compare_sweep(
            {"d_model": 16, "n_features": 96}, acts, k_values=[8], seed=42,
        )
        assert r1[0].fev == r2[0].fev
        assert r1[0].l0_sparsity == r2[0].l0_sparsity

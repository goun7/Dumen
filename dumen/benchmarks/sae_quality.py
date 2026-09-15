"""
dumen.benchmarks.sae_quality
============================
SAE Kalite Ölçüm Metrikleri (SAE Quality Metrics — SAEBench tarzı, Karvonen et al. ICML 2025):
Bir SAE'nin 'iyi' olduğunu iddia edebilmek için yeniden inşa doğruluğu, seyrelme,
açıklanan varyans (FEV) ve downstream doğruluk (kosinüs koruma) ölçülür.

Bu modül, Dümen'in SAE tabanlı denetim iddiasının ölçülebilir temelini oluşturur:
yakalanamayan varyans (unexplained variance) = denetim kör noktasıdır.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import torch
import torch.nn.functional as F
from pydantic import BaseModel, Field

from dumen.core.sae_engine import SparseAutoencoderEngine


class SAEQualityReport(BaseModel):
    """Tek bir SAE'nin kalite ölçüm sonuçları."""
    d_model: int
    n_features: int
    k_sparsity: int
    l0_sparsity: float = Field(description="Ortalama aktif özellik sayısı (L0) — seyreltik ölçüsü")
    fev: float = Field(description="Fraction of Explained Variance [0,1] — yakalanan varyans oranı")
    reconstruction_mse: float = Field(description="Yeniden inşa hatası (MSE)")
    downstream_cosine: float = Field(
        description="Downstream kosinüs koruma: x̂/x doğrultu benzerliği (temsil bozulması)",
    )
    unexplained_variance_warning: bool = Field(
        description="FEV < 0.85 ise True: denetim kör noktası riski",
    )
    l0_efficiency: float = Field(
        description="FEV / L0 normalleştirilmiş verimlilik (seyreltik-doğruluk dengesi)",
    )


class SAEQualityBench:
    """
    SparseAutoencoderEngine kalitesini gerçek matematiksel ölçümlerle değerlendirir.
    SAEBench (arXiv:2503.09532) metrik ailesinin Dümen içi uygulamasıdır.
    """

    FEV_WARNING_THRESHOLD = 0.85

    @staticmethod
    def measure(
        sae: SparseAutoencoderEngine,
        activations: torch.Tensor,
    ) -> SAEQualityReport:
        """
        SAE kalitesini aktivasyon demeti ([N, d_model]) üzerinden ölçer.

        Args:
            sae: Değerlendirilecek SAE motoru (evaluate modunda olmalı).
            activations: [N, d_model] gerçek aktivasyon örneklemi.

        Returns:
            SAEQualityReport — tüm metrikler hesaplanmış rapor.
        """
        if activations.ndim != 2:
            raise ValueError(f"activations [N, d_model] olmalı, {activations.shape} geldi.")
        if activations.shape[1] != sae.d_model:
            raise ValueError(
                f"Aktivasyon boyutu ({activations.shape[1]}) SAE d_model ({sae.d_model}) ile uyuşmuyor."
            )
        if activations.shape[0] == 0:
            raise ValueError("Boş aktivasyon demeti değerlendirilemez.")

        was_training = sae.training
        sae.eval()
        try:
            with torch.no_grad():
                recon, features = sae(activations)
        finally:
            if was_training:
                sae.train()

        # L0: ortalama aktif (theta üstü) özellik sayısı
        l0 = float((features.abs() > 1e-6).float().sum(dim=1).mean().item())

        # FEV: 1 - ||x - x̂||² / ||x - mean(x)||²  (varyans yakalama oranı)
        x_centered = activations - activations.mean(dim=0, keepdim=True)
        total_var = float((x_centered ** 2).sum().item())
        resid = activations - recon
        if total_var > 1e-12:
            fev = 1.0 - float((resid ** 2).sum().item()) / total_var
        else:
            fev = 1.0 if float((resid ** 2).sum().item()) < 1e-12 else 0.0
        fev = max(0.0, min(1.0, fev))

        # MSE
        mse = float((resid ** 2).mean().item())

        # Downstream kosinüs koruma: ortalama cos(x, x̂)
        x_norm = torch.norm(activations, dim=1) + 1e-8
        r_norm = torch.norm(recon, dim=1) + 1e-8
        cos = (activations * recon).sum(dim=1) / (x_norm * r_norm)
        downstream_cos = float(cos.mean().item())

        l0_eff = fev / max(l0, 1.0)

        return SAEQualityReport(
            d_model=sae.d_model,
            n_features=sae.n_features,
            k_sparsity=sae.k_sparsity,
            l0_sparsity=round(l0, 3),
            fev=round(fev, 4),
            reconstruction_mse=round(mse, 6),
            downstream_cosine=round(downstream_cos, 4),
            unexplained_variance_warning=fev < SAEQualityBench.FEV_WARNING_THRESHOLD,
            l0_efficiency=round(l0_eff, 6),
        )

    @staticmethod
    def compare_sweep(
        base_kwargs: Dict,
        activations: torch.Tensor,
        k_values: Optional[List[int]] = None,
        seed: int = 0,
    ) -> List[SAEQualityReport]:
        """
        Aynı veri üzerinde farklı k_sparsity değerleriyle SAE'ler eğitip
        seyreltik-doğruluk eğrisi (sparsity-fidelity tradeoff) üretir.

        Args:
            base_kwargs: SparseAutoencoderEngine kurucu parametreleri
                (d_model, n_features; k_sparsity bu metotta ezilir).
            activations: [N, d_model] eğitim/değerlendirme demeti.
            k_values: Denenecek k değerleri (varsayılan [8, 16, 32, 64]).
            seed: Yeniden üretilebilirlik tohumu.

        Returns:
            k sırasına göre metrik raporları.
        """
        if k_values is None:
            k_values = [8, 16, 32, 64]

        reports: List[SAEQualityReport] = []
        for k in k_values:
            torch.manual_seed(seed)
            sae = SparseAutoencoderEngine(
                d_model=base_kwargs["d_model"],
                n_features=base_kwargs["n_features"],
                k_sparsity=k,
                jump_relu_threshold=base_kwargs.get("jump_relu_threshold", 0.05),
            )
            # Basit bir ısınma eğitimi: veriyi birkaç epoch yeniden inşa üzerine
            opt = torch.optim.Adam(sae.parameters(), lr=1e-2)
            sae.train()
            for _ in range(50):
                opt.zero_grad()
                recon, _ = sae(activations)
                loss = F.mse_loss(recon, activations) + 1e-4 * sae.compute_mutual_regularization_loss()
                loss.backward()
                opt.step()
            reports.append(SAEQualityBench.measure(sae, activations))
        return reports


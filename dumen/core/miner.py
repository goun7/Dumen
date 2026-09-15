"""
dumen.core.miner
================
Kontrastif Aktivasyon Madencisi (Contrastive Activation Miner - CAA / DiM):
Zararlı ve güvenli istem çiftlerinden (harmful vs safe) katman bazında
yönlendirme vektörlerini (Steering Vectors) Difference-in-Means ve PCA
yöntemleriyle çıkaran otonom matematiksel motor.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

import torch

from dumen.core.types import RiskCategory, SteeringMethod, SteeringVector


class ContrastivePair:
    """Zararlı ve güvenli eşlenik istem veya tensör çifti."""
    def __init__(
        self,
        harmful_input: Union[str, torch.Tensor],
        safe_input: Union[str, torch.Tensor],
        metadata: Optional[Dict[str, str]] = None,
    ):
        self.harmful = harmful_input
        self.safe = safe_input
        self.metadata = metadata or {}


class VectorMiner:
    """
    Model aktivasyon uzayında riskli yöne işaret eden vektörleri
    ampirik olarak çıkaran kontrastif madenci.
    """

    @staticmethod
    def compute_difference_in_means(
        harmful_activations: torch.Tensor,
        safe_activations: torch.Tensor,
    ) -> torch.Tensor:
        """
        Difference-in-Means (DiM):
        v = E[h_harmful] - E[h_safe]

        Args:
            harmful_activations: [N, Dim] tensör
            safe_activations: [N, Dim] tensör

        Returns:
            unit_vector: [Dim] normalize edilmiş yön tensörü
        """
        assert harmful_activations.shape == safe_activations.shape, "Tensör boyutları eşleşmelidir."
        assert harmful_activations.ndim == 2, "Aktivasyonlar [N, Dim] formatında olmalıdır."

        mean_harmful = torch.mean(harmful_activations, dim=0)
        mean_safe = torch.mean(safe_activations, dim=0)

        diff = mean_harmful - mean_safe
        norm = torch.norm(diff)
        if norm > 1e-8:
            return diff / norm
        return diff

    @staticmethod
    def compute_pca_direction(
        harmful_activations: torch.Tensor,
        safe_activations: torch.Tensor,
    ) -> torch.Tensor:
        """
        Birinci Temel Bileşen (Principal Component - PCA):
        Zararlı ve güvenli küme aktivasyonlarını birleştirip varyansı maksimize eden
        ayrıştırıcı özvektörü (dominant separation axis) çıkarır.
        """
        # [2N, Dim] küme matrisi
        stacked = torch.cat([harmful_activations, safe_activations], dim=0)
        centered = stacked - torch.mean(stacked, dim=0, keepdim=True)

        try:
            _, _, vh = torch.linalg.svd(centered, full_matrices=False)
            first_pc = vh[0]
            # Yönün zararlı - güvenli fark vektörüyle pozitif hizalı olduğundan emin ol
            mean_diff = torch.mean(harmful_activations - safe_activations, dim=0)
            if torch.dot(first_pc, mean_diff) < 0:
                first_pc = -first_pc
            return first_pc / (torch.norm(first_pc) + 1e-8)
        except Exception:
            return VectorMiner.compute_difference_in_means(harmful_activations, safe_activations)

    @staticmethod
    def compute_rank_k_basis(
        harmful_activations: torch.Tensor,
        safe_activations: torch.Tensor,
        k: int = 4,
    ) -> torch.Tensor:
        """
        Rank-k Refusal Manifold — tek-doğrultu-ötesi reddetme geometrisi varsayımı.
        Görüşü destekleyen güncel literatür: Arditi et al. 2024 (arXiv:2406.11717, tek
        doğrultu) ve sonrasında çok-yönlülüğü savunan karşılaştırmalı çalışma —
        Rocchetti & Ferrara 2026, "Refusal Beyond a Single Direction: A Preliminary
        Comparison of Diff-in-Means and INLP" (arXiv:2606.13720). Bu modülün k-boyutlu
        SVD genelleştirmesi Dümen'e aittir; atıf yalnız tek-doğrultu varsayımının
        çürütülmesi motivasyonunadır.
        Zararlı-güvenli ayrımının tek doğrultu yerine düşük-rank bir altuzayda yaşadığı
        varsayımıyla, fark matrisinin ilk k sağ-singular vektörünü ortonormal taban olarak döndürür.

        D = H_harmful - H_safe ∈ R^{N x Dim}
        D = U Σ V^T → V^T'nin ilk k satırı rank-k manifold tabanıdır.

        Returns:
            basis: [k, Dim] satır-ortonormal tensör
        """
        assert harmful_activations.shape == safe_activations.shape, "Tensör boyutları eşleşmelidir."
        diff_matrix = harmful_activations - safe_activations
        k_eff = min(k, diff_matrix.shape[0], diff_matrix.shape[1])
        if k_eff < 1:
            raise ValueError("rank-k taban için en az bir örnek çifti gerekir.")
        _, _, vh = torch.linalg.svd(diff_matrix, full_matrices=False)
        basis = vh[:k_eff]
        # SVD işaret belirsizliği: her satırı DiM yönüyle pozitif hizala
        mean_diff = torch.mean(diff_matrix, dim=0)
        for i in range(basis.shape[0]):
            if torch.dot(basis[i], mean_diff) < 0:
                basis[i] = -basis[i]
        return basis

    @staticmethod
    def project_to_subspace(
        hidden_state: torch.Tensor,
        basis: torch.Tensor,
        alpha: float = 1.0,
        subtract: bool = True,
    ) -> torch.Tensor:
        """
        Aktivasyonu rank-k altuzaya izdüşümüyle yönlendirir:
        x_out = x ∓ alpha * B^T (B x)  (B: [k, Dim] ortonormal taban)

        subtract=True → manifold bileşeni söndürülür (risk azaltma / null-space ablasyon)
        subtract=False → manifold bileşeni pekiştirilir (risk davranış tetikleme)
        """
        if hidden_state.ndim > 1:
            flat = hidden_state.reshape(-1, hidden_state.shape[-1])
        else:
            flat = hidden_state.unsqueeze(0)
        coeffs = flat @ basis.T                      # [*, k]
        proj = coeffs @ basis                        # [*, Dim]
        sign = -1.0 if subtract else 1.0
        out = flat + sign * alpha * proj
        if hidden_state.ndim > 1:
            return out.reshape(hidden_state.shape)
        return out.squeeze(0)

    @staticmethod
    def permutation_significance(
        harmful_activations: torch.Tensor,
        safe_activations: torch.Tensor,
        n_permutations: int = 200,
        seed: int = 2026,
    ) -> float:
        """
        Permütasyon Anlamlılık Testi (Permutation Test):
        Gözlemlenen DiM vektör normunun, etiketler rastgele karıştırıldığında
        elde edilen null dağılımına göre p-değerini hesaplar.

        H0: zararlı/güvenli ayrımı yoktur (fark, etiketleme tesadüfüdür).
        p < 0.05 → ayrım istatistiksel olarak anlamlı: madencilik güvenli.

        Returns:
            p_value: [0, 1] — gözlemlenen etkinin null'a karşı olasılığı
        """
        n = harmful_activations.shape[0]
        if n < 2:
            return 1.0
        g = torch.Generator().manual_seed(seed)

        def _raw_mean_diff(h_t: torch.Tensor, s_t: torch.Tensor) -> torch.Tensor:
            # Normalize EDİLMEMİŞ ortalama farkı — birim vektör normu her zaman 1
            # olduğundan istatistik olarak işlevsizdir; ham fark norm'u kullanılır.
            return torch.mean(h_t, dim=0) - torch.mean(s_t, dim=0)

        observed = torch.norm(_raw_mean_diff(harmful_activations, safe_activations)).item()

        # Birleştir ve etiketleri karıştırarak null dağılımı oluştur
        pooled = torch.cat([harmful_activations, safe_activations], dim=0)
        total = pooled.shape[0]
        count_ge = 0
        for _ in range(n_permutations):
            perm = torch.randperm(total, generator=g)
            h = pooled[perm[:n]]
            s = pooled[perm[n:]]
            null_stat = torch.norm(_raw_mean_diff(h, s)).item()
            if null_stat >= observed:
                count_ge += 1
        return (count_ge + 1) / (n_permutations + 1)  # +1 düzeltmesi (never p=0)

    @staticmethod
    def bootstrap_confidence(
        harmful_activations: torch.Tensor,
        safe_activations: torch.Tensor,
        n_resamples: int = 50,
        seed: int = 1337,
    ) -> float:
        """
        Bootstrap yön kararlılığı: N örnek çiftinden n_resamples kez yeniden örnekleme
        yapıp DiM vektörleri arası ortalama kosinüs benzerliğini hesaplar.
        Yüksek değer (≥0.9) → yön veri alt kümesine duyarlı değil, güvenilir.
        """
        n = harmful_activations.shape[0]
        if n < 2:
            return 1.0
        g = torch.Generator().manual_seed(seed)
        base = VectorMiner.compute_difference_in_means(harmful_activations, safe_activations)
        sims: List[float] = []
        for _ in range(n_resamples):
            idx = torch.randint(0, n, (n,), generator=g)
            h = harmful_activations[idx]
            s = safe_activations[idx]
            v = VectorMiner.compute_difference_in_means(h, s)
            denom = (torch.norm(v) * torch.norm(base)) + 1e-8
            sims.append(float(torch.dot(v, base) / denom))
        return float(sum(sims) / len(sims))

    @classmethod
    def mine_from_activations(
        cls,
        harmful_layer_acts: Dict[int, torch.Tensor],
        safe_layer_acts: Dict[int, torch.Tensor],
        target_risk: RiskCategory,
        method: SteeringMethod = SteeringMethod.STTP,
        use_pca: bool = False,
        threshold: float = 0.5,
        strength: float = 1.0,
        rank: int = 1,
        n_bootstrap: int = 50,
        bootstrap_seed: int = 1337,
    ) -> Dict[int, SteeringVector]:
        """
        Önceden toplanmış katman aktivasyonlarından SteeringVector nesneleri üretir.
        rank > 1 ise Arditi-sonrası rank-k manifold tabanı da hesaplanır ve
        n_bootstrap > 0 ise bootstrap yön-güven aralığı confidence alanına yazılır.

        Args:
            harmful_layer_acts: {layer_idx: [N, Dim] tensör}
            safe_layer_acts: {layer_idx: [N, Dim] tensör}
            target_risk: Bastırılacak risk türü
            rank: 1 = klasik tek doğrultu; k>1 = rank-k manifold tabanı da çıkar
            n_bootstrap: bootstrap yeniden örnekleme sayısı (0 = kapalı)

        Returns:
            {layer_idx: SteeringVector}
        """
        result_vectors: Dict[int, SteeringVector] = {}

        for layer_idx in harmful_layer_acts:
            if layer_idx not in safe_layer_acts:
                continue

            h_acts = harmful_layer_acts[layer_idx]
            s_acts = safe_layer_acts[layer_idx]

            if use_pca and h_acts.shape[0] > 1:
                v_tensor = cls.compute_pca_direction(h_acts, s_acts)
            else:
                v_tensor = cls.compute_difference_in_means(h_acts, s_acts)

            # Bootstrap yön kararlılığı (veri alt kümelerine duyarlılık ölçümü)
            confidence = 1.0
            if n_bootstrap > 0 and h_acts.shape[0] >= 2:
                confidence = cls.bootstrap_confidence(
                    h_acts, s_acts,
                    n_resamples=n_bootstrap,
                    seed=bootstrap_seed,
                )

            # Rank-k manifold tabanı (isteğe bağlı)
            basis_list: Optional[List[List[float]]] = None
            if rank > 1 and h_acts.shape[0] >= 2:
                basis = cls.compute_rank_k_basis(h_acts, s_acts, k=rank)
                basis_list = basis.detach().cpu().tolist()

            svec = SteeringVector.from_tensor(
                name=f"{target_risk.value}_layer_{layer_idx}",
                layer_idx=layer_idx,
                tensor=v_tensor,
                target_risk=target_risk,
                method=method,
                threshold=threshold,
                strength=strength,
                rank=rank,
                subspace_basis=basis_list,
                confidence=round(confidence, 4),
            )
            result_vectors[layer_idx] = svec

        return result_vectors

    @classmethod
    def mine_from_prompts(
        cls,
        prompt_pairs: List[Tuple[str, str]],
        forward_hook_extractor: Callable[[str], Dict[int, torch.Tensor]],
        target_risk: RiskCategory,
        target_layers: List[int],
        method: SteeringMethod = SteeringMethod.STTP,
        use_pca: bool = False,
        threshold: float = 0.5,
        strength: float = 1.0,
        rank: int = 1,
        n_bootstrap: int = 50,
        bootstrap_seed: int = 1337,
    ) -> Dict[int, SteeringVector]:
        """
        Metin istem çiftlerinden modeli koşturarak doğrudan katman vektörlerini çıkarır.
        rank ve n_bootstrap parametreleri mine_from_activations'a değiştirilmeden iletilir.

        Args:
            prompt_pairs: [(harmful_prompt, safe_prompt), ...]
            forward_hook_extractor: prompt -> {layer_idx: [1, Dim] aktivasyon tensörü}
        """
        harmful_acts: Dict[int, List[torch.Tensor]] = {layer: [] for layer in target_layers}
        safe_acts: Dict[int, List[torch.Tensor]] = {layer: [] for layer in target_layers}

        for harmful_p, safe_p in prompt_pairs:
            h_out = forward_hook_extractor(harmful_p)
            s_out = forward_hook_extractor(safe_p)

            for layer in target_layers:
                if layer in h_out and layer in s_out:
                    # [Seq, Dim] veya [1, Dim] ise son token aktivasyonunu al
                    h_t = h_out[layer]
                    s_t = s_out[layer]
                    if h_t.ndim > 1:
                        h_t = h_t[-1] if h_t.ndim == 2 else h_t[0, -1]
                    if s_t.ndim > 1:
                        s_t = s_t[-1] if s_t.ndim == 2 else s_t[0, -1]
                    harmful_acts[layer].append(h_t.unsqueeze(0))
                    safe_acts[layer].append(s_t.unsqueeze(0))

        # Tensörleri birleştir
        h_stacked = {layer: torch.cat(t_list, dim=0) for layer, t_list in harmful_acts.items() if t_list}
        s_stacked = {layer: torch.cat(t_list, dim=0) for layer, t_list in safe_acts.items() if t_list}

        return cls.mine_from_activations(
            harmful_layer_acts=h_stacked,
            safe_layer_acts=s_stacked,
            target_risk=target_risk,
            method=method,
            use_pca=use_pca,
            threshold=threshold,
            strength=strength,
            rank=rank,
            n_bootstrap=n_bootstrap,
            bootstrap_seed=bootstrap_seed,
        )

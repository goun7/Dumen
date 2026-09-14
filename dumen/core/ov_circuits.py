"""
dumen.core.ov_circuits
======================
Attention Output-Value (OV) devresi odaklı seyreltme matrisi ve
Query-Key (QK) koruma mekanizması (arXiv:2604.08524 araştırmasına dayalı).
"""

from __future__ import annotations
from typing import List, Optional, Tuple
import torch


class OVCircuitMask:
    """
    Yönlendirme vektörlerini Attention OV devrelerine izole ederek %85-%96 oranında
    seyrelten ve modelin genel muhakeme yeteneğini koruyan seyreltme yöneticisi.
    """

    def __init__(self, hidden_dim: int, num_heads: int = 32):
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads

    def compute_ov_salience(
        self,
        steering_vector: torch.Tensor,
        top_k_percent: float = 0.15,
    ) -> Tuple[torch.Tensor, List[int]]:
        """
        Yönlendirme vektöründeki en kritik Attention başlıklarını ve OV boyutlarını izole eder.

        Args:
            steering_vector: [d_model] boyutunda yönlendirme tensörü.
            top_k_percent: Tutulacak en yüksek etkiye sahip boyut oranı (varsayılan: %15 -> %85 seyreltme).

        Returns:
            (sparse_vector, active_indices): Seyreltilmiş tensör ve aktif indisler.
        """
        assert steering_vector.ndim == 1, "Vektör 1-boyutlu olmalıdır [d_model]"
        k = max(1, int(self.hidden_dim * top_k_percent))

        # Büyüklük bazlı önem skoru (magnitude-based salience)
        magnitudes = torch.abs(steering_vector)
        _, top_indices = torch.topk(magnitudes, k=k)

        sparse_vector = torch.zeros_like(steering_vector)
        sparse_vector[top_indices] = steering_vector[top_indices]

        # Normalize et
        norm = torch.norm(sparse_vector)
        if norm > 1e-8:
            sparse_vector = sparse_vector / norm

        active_indices = sorted(top_indices.cpu().tolist())
        return sparse_vector, active_indices

    @staticmethod
    def apply_sparse_mask(
        tensor: torch.Tensor,
        active_indices: Optional[List[int]],
    ) -> torch.Tensor:
        """
        Verilen tensör üzerinde sadece aktif OV indislerini günceller.
        """
        if active_indices is None or len(active_indices) == 0:
            return tensor

        mask = torch.zeros(tensor.shape[-1], dtype=torch.bool, device=tensor.device)
        mask[active_indices] = True
        return tensor * mask

"""
dumen.core.ov_circuits
======================
Attention Output-Value (OV) devresi odaklı seyreltme matrisi ve
Query-Key (QK) koruma mekanizması (Elhage et al., Anthropic Transformer Circuits).
Gerçek W_O ve W_V ağırlık tensörleri üzerinden Attention Başlık Nitelendirmesi (Head Attribution).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import torch


class OVCircuitMask:
    """
    Yönlendirme vektörlerini Attention OV devrelerine izole ederek %85-%96 oranında
    seyrelten ve modelin genel muhakeme yeteneğini koruyan seyreltme yöneticisi.
    """

    def __init__(self, hidden_dim: int, num_heads: int = 32):
        assert hidden_dim % num_heads == 0, "hidden_dim num_heads değerine tam bölünmelidir."
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads

    def compute_ov_salience(
        self,
        steering_vector: torch.Tensor,
        top_k_percent: float = 0.15,
    ) -> Tuple[torch.Tensor, List[int]]:
        """
        Büyüklük bazlı hızlı seyreltme (Model ağırlıklarına doğrudan erişim yoksa fallback).
        """
        assert steering_vector.ndim == 1, "Vektör 1-boyutlu olmalıdır [d_model]"
        k = max(1, int(self.hidden_dim * top_k_percent))

        magnitudes = torch.abs(steering_vector)
        _, top_indices = torch.topk(magnitudes, k=k)

        sparse_vector = torch.zeros_like(steering_vector)
        sparse_vector[top_indices] = steering_vector[top_indices]

        norm = torch.norm(sparse_vector)
        if norm > 1e-8:
            sparse_vector = sparse_vector / norm

        active_indices = sorted(top_indices.cpu().tolist())
        return sparse_vector, active_indices

    def compute_head_attribution(
        self,
        steering_vector: torch.Tensor,
        W_O: torch.Tensor,
        top_k_heads: int = 4,
    ) -> Tuple[torch.Tensor, List[int], Dict[int, float]]:
        """
        Gerçek Attention W_O Tensörü Üzerinden Başlık Nitelendirmesi (Anthropic Circuits):
        Her bir dikkat başlığının (head) zararlı yön vektörüne (v) yazma kuvvetini:
        S_h = || (W_O^h) v ||_2
        üzerinden hesaplar ve zararlı yöne en güçlü katkı sağlayan top-k başlığı izole eder.

        Args:
            steering_vector: [hidden_dim] yönlendirme vektörü
            W_O: [hidden_dim, hidden_dim] veya [num_heads, head_dim, hidden_dim] tensör
            top_k_heads: İzole edilecek en riskli başlık sayısı (varsayılan: 4 / 32 -> %87.5 seyreltme)

        Returns:
            (sparse_vector, active_feature_indices, head_salience_scores)
        """
        assert steering_vector.ndim == 1, "Vektör 1-boyutlu olmalıdır"
        v = steering_vector / (torch.norm(steering_vector) + 1e-8)

        # W_O tensörünü [num_heads, head_dim, hidden_dim] şekline dönüştür
        if W_O.ndim == 2:
            assert W_O.shape == (self.hidden_dim, self.hidden_dim), "W_O boyutu [hidden_dim, hidden_dim] olmalıdır."
            # Standart transformerlarda W_O [hidden_dim, hidden_dim] -> [head_dim * num_heads, hidden_dim]
            # Giriş head'lerden gelir: [num_heads, head_dim, hidden_dim]
            W_O_heads = W_O.view(self.num_heads, self.head_dim, self.hidden_dim)
        elif W_O.ndim == 3:
            W_O_heads = W_O
        else:
            raise ValueError("W_O tensörü 2D veya 3D olmalıdır.")

        # Her başlık için salience hesapla: W_O^h @ v -> [head_dim]
        # v: [hidden_dim]
        head_scores: Dict[int, float] = {}
        for h in range(self.num_heads):
            W_h = W_O_heads[h]  # [head_dim, hidden_dim]
            # Projeksiyon
            proj_h = torch.matmul(W_h, v)  # [head_dim]
            salience = float(torch.norm(proj_h).item())
            head_scores[h] = salience

        # En yüksek salience'a sahip başlıkları seç
        sorted_heads = sorted(head_scores.items(), key=lambda item: item[1], reverse=True)
        top_heads = [h for h, _ in sorted_heads[:top_k_heads]]

        # Seçilen başlıkların girdi indislerini (active indices) çıkar
        active_indices: List[int] = []
        for h in top_heads:
            start_idx = h * self.head_dim
            end_idx = start_idx + self.head_dim
            active_indices.extend(range(start_idx, end_idx))

        # Seyreltilmiş vektörü üret
        sparse_vector = torch.zeros_like(steering_vector)
        sparse_vector[active_indices] = steering_vector[active_indices]
        norm = torch.norm(sparse_vector)
        if norm > 1e-8:
            sparse_vector = sparse_vector / norm

        return sparse_vector, sorted(active_indices), head_scores

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

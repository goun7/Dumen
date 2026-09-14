"""
dumen.core.transcoder
=====================
Transcoder Mimarisi (Anthropic 2026 Araştırmaları):
Transformer MLP katmanlarının girdisini doğrudan çıktısına monosemantik
sözlük atomları üzerinden nedensel (causal) olarak eşleyen ve müdahale eden motor.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import torch
import torch.nn as nn
import torch.nn.functional as F


class TranscoderEngine(nn.Module):
    """
    MLP bloğunun girdisini (x_in) alıp çıktısını (x_out) yeniden inşa eden
    ve MLP içindeki zararlı düşünce adımlarını söndüren Transcoder mimarisi.

    x_hat_out = W_dec * TopK(ReLU(W_enc * (x_in - b_in) + b_enc)) + b_out + W_skip * x_in
    """

    def __init__(
        self,
        d_model: Optional[int] = None,
        n_features: Optional[int] = None,
        d_in: Optional[int] = None,
        d_out: Optional[int] = None,
        d_dict: Optional[int] = None,
        k_sparsity: Optional[int] = None,
        top_k: Optional[int] = None,
        use_skip: bool = True,
        device: str = "cpu",
    ):
        super().__init__()
        # Boyut parametrelerini esnek bir şekilde çöz
        self.d_in = d_in if d_in is not None else d_model
        self.d_out = d_out if d_out is not None else (d_model if d_model is not None else self.d_in)
        assert self.d_in is not None and self.d_out is not None, "Girdi ve çıktı boyutları belirtilmelidir."

        self.d_model = self.d_in
        self.n_features = d_dict if d_dict is not None else (n_features if n_features is not None else self.d_in * 4)
        self.k_sparsity = top_k if top_k is not None else (k_sparsity if k_sparsity is not None else 32)
        self.use_skip = use_skip
        self.device_name = device

        # Encoder: x_in [d_in] -> f [n_features]
        self.W_enc = nn.Parameter(torch.empty(self.n_features, self.d_in))
        self.b_enc = nn.Parameter(torch.zeros(self.n_features))
        self.b_in = nn.Parameter(torch.zeros(self.d_in))

        # Decoder: f [n_features] -> x_out [d_out]
        self.W_dec = nn.Parameter(torch.empty(self.d_out, self.n_features))
        self.b_out = nn.Parameter(torch.zeros(self.d_out))

        # Skip connection: x_in [d_in] -> x_out [d_out]
        if use_skip:
            self.W_skip = nn.Parameter(torch.empty(self.d_out, self.d_in))
        else:
            self.register_parameter("W_skip", None)

        # Monosemantik özellik etiketleri ve engelleme maskesi
        self.feature_labels: Dict[int, str] = {}
        self.suppressed_features: set[int] = set()

        self.reset_parameters()
        self.to(device)

    def reset_parameters(self) -> None:
        """Kaiming başlatma ve decoder sütun normalizasyonu."""
        nn.init.kaiming_uniform_(self.W_enc, a=0.01)
        nn.init.kaiming_uniform_(self.W_dec, a=0.01)
        if self.use_skip and self.W_skip is not None:
            if self.d_in == self.d_out:
                nn.init.eye_(self.W_skip)
                self.W_skip.data.mul_(0.1)
            else:
                nn.init.xavier_uniform_(self.W_skip)

        with torch.no_grad():
            self.W_dec.data = F.normalize(self.W_dec.data, p=2, dim=0)

    def encode(
        self,
        x_in: torch.Tensor,
        suppress_indices: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """
        MLP girdisini monosemantik seyrek aktivasyonlara kodlar.
        f = TopK(ReLU(W_enc (x_in - b_in) + b_enc))
        """
        centered_in = x_in - self.b_in
        pre_acts = F.linear(centered_in, self.W_enc, self.b_enc)
        relu_acts = F.relu(pre_acts)

        k = min(self.k_sparsity, relu_acts.shape[-1])
        topk_vals, topk_indices = torch.topk(relu_acts, k=k, dim=-1)
        sparse_acts = torch.zeros_like(relu_acts)
        sparse_acts.scatter_(-1, topk_indices, topk_vals)

        # Kalıcı engellenmiş (suppressed) özellikleri sıfırla
        all_suppressed = set(self.suppressed_features)
        if suppress_indices is not None:
            all_suppressed.update(suppress_indices)

        if all_suppressed:
            for feat_idx in all_suppressed:
                if feat_idx < sparse_acts.shape[-1]:
                    sparse_acts[..., feat_idx] = 0.0

        return sparse_acts

    def decode(self, f: torch.Tensor, x_in: torch.Tensor) -> torch.Tensor:
        """
        Seyrek özelliklerden MLP çıktısını inşa eder:
        x_hat_out = W_dec * f + b_out + (W_skip * x_in)
        """
        decoded = F.linear(f, self.W_dec, self.b_out)
        if self.use_skip and self.W_skip is not None:
            skip_term = F.linear(x_in, self.W_skip)
            decoded = decoded + skip_term
        return decoded

    def forward(
        self,
        x_in: torch.Tensor,
        suppress_indices: Optional[List[int]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        İleri geçiş: (x_hat_out, sparse_features)
        """
        f = self.encode(x_in, suppress_indices=suppress_indices)
        x_hat_out = self.decode(f, x_in)
        return x_hat_out, f

    def suppress_feature(self, feature_idx: int) -> None:
        """Belirtilen zararlı sözlük özelliğini kalıcı olarak söndürür."""
        self.suppressed_features.add(feature_idx)

    def unsuppress_feature(self, feature_idx: int) -> None:
        """Özellik söndürmesini kaldırır."""
        self.suppressed_features.discard(feature_idx)

    def label_feature(self, feature_idx: int, label: str) -> None:
        """Sözlük atomuna anlamsal etiket atar."""
        self.feature_labels[feature_idx] = label

    def compute_reconstruction_loss(
        self,
        x_in: torch.Tensor,
        x_target_out: torch.Tensor,
        l1_coeff: float = 1e-3,
    ) -> Dict[str, torch.Tensor]:
        """
        Transcoder eğitim kaybı:
        Loss = ||x_target_out - x_hat_out||_2^2 + l1_coeff * ||f||_1
        """
        x_hat_out, f = self.forward(x_in)
        mse_loss = F.mse_loss(x_hat_out, x_target_out)
        l1_loss = l1_coeff * torch.mean(torch.sum(torch.abs(f), dim=-1))
        total_loss = mse_loss + l1_loss

        return {
            "total_loss": total_loss,
            "reconstruction_loss": mse_loss,
            "mse_loss": mse_loss,
            "l1_loss": l1_loss,
        }

    def compute_loss(
        self,
        x_in: torch.Tensor,
        x_target_out: torch.Tensor,
        l1_coeff: float = 1e-3,
    ) -> Dict[str, torch.Tensor]:
        """compute_reconstruction_loss için alias."""
        return self.compute_reconstruction_loss(x_in, x_target_out, l1_coeff=l1_coeff)

"""
dumen.core.sae_engine
=====================
Seyrek Oto-Kodlayıcılar (Sparse Autoencoders - SAE) ile Mekanistik Yorumlanabilirlik,
TopK ve JumpReLU Sözlük Çıkarım Motoru (Anthropic & OpenAI 2025/2026 araştırmaları).
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class SparseAutoencoderEngine(nn.Module):
    """
    Modelin residual stream aktivasyonlarını aşırı tamamlanmış (overcomplete)
    monosemantik özellik uzayına ayrıştıran TopK / JumpReLU SAE motoru.
    """

    def __init__(
        self,
        d_model: int,
        n_features: int,
        k_sparsity: int = 32,
        jump_relu_threshold: float = 0.05,
        device: str = "cpu",
    ):
        super().__init__()
        self.d_model = d_model
        self.n_features = n_features
        self.k_sparsity = k_sparsity
        self.threshold = jump_relu_threshold
        self.device_name = device

        # Encoder ağırlıkları: [n_features, d_model]
        self.W_enc = nn.Parameter(torch.empty(n_features, d_model))
        self.b_enc = nn.Parameter(torch.zeros(n_features))

        # Decoder ağırlıkları: [d_model, n_features]
        self.W_dec = nn.Parameter(torch.empty(d_model, n_features))
        self.b_dec = nn.Parameter(torch.zeros(d_model))

        # Sözlük atomlarının semantik etiketleri: {feature_idx: "deception", ...}
        self.feature_labels: Dict[int, str] = {}

        self.reset_parameters()
        self.to(device)

    def reset_parameters(self) -> None:
        """Kaiming / He başlatma ve decoder sütunlarını birim küreye normalize etme."""
        nn.init.kaiming_uniform_(self.W_enc, a=0.01)
        nn.init.kaiming_uniform_(self.W_dec, a=0.01)
        with torch.no_grad():
            self.W_dec.data = F.normalize(self.W_dec.data, p=2, dim=0)

    def encode(self, x: torch.Tensor, use_topk: bool = True) -> torch.Tensor:
        """
        Aktivasyonu monosemantik seyrek özelliklere kodlar.
        f(x) = TopK(ReLU(W_e (x - b_dec) + b_e))
        """
        x_centered = x - self.b_dec
        pre_acts = F.linear(x_centered, self.W_enc, self.b_enc)

        if use_topk:
            # Top-K Sparsity: En yüksek k aktivasyonu koru, diğerlerini sıfırla
            relu_acts = F.relu(pre_acts)
            k = min(self.k_sparsity, relu_acts.shape[-1])
            topk_vals, topk_indices = torch.topk(relu_acts, k=k, dim=-1)
            sparse_acts = torch.zeros_like(relu_acts)
            sparse_acts.scatter_(-1, topk_indices, topk_vals)
            return sparse_acts
        else:
            # JumpReLU: Belirli eşiğin (theta) üzerindeki aktivasyonlar
            mask = pre_acts > self.threshold
            return pre_acts * mask.float()

    def decode(self, f: torch.Tensor) -> torch.Tensor:
        """Seyrek özelliklerden aktivasyonu yeniden inşa eder: x_hat = W_d f + b_dec."""
        return F.linear(f, self.W_dec, self.b_dec)

    def forward(self, x: torch.Tensor, use_topk: bool = True) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Tam ileri geçiş (Forward pass).
        Returns: (x_reconstructed, latent_features)
        """
        f = self.encode(x, use_topk=use_topk)
        x_hat = self.decode(f)
        return x_hat, f

    def label_feature(self, feature_idx: int, label: str) -> None:
        """Belirli bir sözlük yönüne güvenlik/semantik etiket atar."""
        if 0 <= feature_idx < self.n_features:
            self.feature_labels[feature_idx] = label

    def inspect_activations(
        self,
        x: torch.Tensor,
        top_n: int = 5,
    ) -> List[Dict[str, any]]:
        """
        Gelen aktivasyonda tetiklenen en güçlü monosemantik özellikleri ve
        varsa güvenlik etiketlerini tespit eder.
        """
        with torch.no_grad():
            f = self.encode(x, use_topk=True)
            # En aktif ilk N özellik
            top_vals, top_indices = torch.topk(f.flatten(), k=min(top_n, f.numel()))
            
            results = []
            for val, idx in zip(top_vals.cpu().tolist(), top_indices.cpu().tolist()):
                if val > 1e-4:
                    results.append({
                        "feature_idx": idx,
                        "activation": float(val),
                        "label": self.feature_labels.get(idx, "unlabeled_latent"),
                    })
            return results

    def compute_mutual_regularization_loss(self) -> torch.Tensor:
        """
        Özellik bölünmesi ve emilimini önlemek için sözlük ortogonallik cezası.
        Loss = ||W_d^T W_d - I||_F^2
        """
        gram = torch.matmul(self.W_dec.T, self.W_dec)
        eye = torch.eye(self.n_features, device=self.W_dec.device)
        return torch.norm(gram - eye, p="fro") ** 2

    def save_pretrained(self, directory: str) -> str:
        """Ağırlıkları ve konfigürasyonu diske kaydeder."""
        from dumen.core.serialization import ModelSerializer
        return ModelSerializer.save_sae(self, directory)

    @classmethod
    def from_pretrained(cls, directory: str, device: str = "cpu") -> "SparseAutoencoderEngine":
        """Diskteki kontrol noktasından SAE motorunu yükler."""
        from dumen.core.serialization import ModelSerializer
        return ModelSerializer.load_sae(directory, device=device)


"""
dumen.core.steering
===================
Projeksiyon Duyarlı Aktivasyon Yönlendirme Algoritmaları (StTP & StMP) ve
Çalışma Zamanı Nöral Direksiyon Motoru.
"""

from __future__ import annotations
import math
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn.functional as F

from dumen.core.types import (
    RiskCategory,
    SteeringMethod,
    SteeringVector,
)
from dumen.core.ov_circuits import OVCircuitMask
from dumen.core.kv_drift import KVDriftGuard
from dumen.core.quantization import QuantizationCalibrator, QuantizationType


class SteeringEngine:
    """
    Model ağırlıklarını değiştirmeksizin, çıkarım (inference) anındaki gizli tensörlere
    dinamik ortogonal projeksiyon uygulayan, uyarlanabilir alfalı yönlendirme motoru.
    """

    def __init__(
        self,
        device: str = "cpu",
        kv_drift_guard: Optional[KVDriftGuard] = None,
        quantization: QuantizationType = QuantizationType.NONE,
        adaptive_alpha: bool = True,
    ):
        self.device = device
        self.kv_drift_guard = kv_drift_guard
        self.quantization = quantization
        self.adaptive_alpha = adaptive_alpha

        # Katman bazında yönlendirme vektörleri sözlüğü: {layer_idx: [SteeringVector]}
        self.registered_vectors: Dict[int, List[SteeringVector]] = {}
        # Hızlı çıkarım için önbelleklenmiş PyTorch tensörleri: {vector_name: torch.Tensor}
        self.cached_tensors: Dict[str, torch.Tensor] = {}

    def register_vector(self, vector: SteeringVector) -> None:
        """Yeni bir yönlendirme vektörünü ilgili katmana kaydeder."""
        if vector.layer_idx not in self.registered_vectors:
            self.registered_vectors[vector.layer_idx] = []
        
        # Eğer aynı isimde varsa güncelle, yoksa ekle
        self.registered_vectors[vector.layer_idx] = [
            v for v in self.registered_vectors[vector.layer_idx] if v.name != vector.name
        ]
        self.registered_vectors[vector.layer_idx].append(vector)
        t = vector.to_tensor(device=self.device)
        if self.quantization != QuantizationType.NONE:
            t, _ = QuantizationCalibrator.calibrate_steering_vector(t, self.quantization)
        self.cached_tensors[vector.name] = t

    def remove_vector(self, name: str) -> bool:
        """Belirtilen isimdeki yönlendirme vektörünü siler."""
        removed = False
        for layer_idx, vecs in list(self.registered_vectors.items()):
            self.registered_vectors[layer_idx] = [v for v in vecs if v.name != name]
            if len(self.registered_vectors[layer_idx]) == 0:
                del self.registered_vectors[layer_idx]
            removed = True
        if name in self.cached_tensors:
            del self.cached_tensors[name]
        return removed

    def get_vectors_for_layer(self, layer_idx: int) -> List[SteeringVector]:
        """Belirli bir katmana atanmış tüm yönlendirme vektörlerini döndürür."""
        return self.registered_vectors.get(layer_idx, [])

    def project_sttp(
        self,
        hidden_state: torch.Tensor,
        harmful_direction: torch.Tensor,
        alpha: float = 1.0,
        active_indices: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """
        Steer-to-Target Projection (StTP):
        Gizli aktivasyonu zararlı yöne dik olan hiper-düzleme izdüşürür ve güvenli yöne çevirir.

        x_proj = x - (x · v / ||v||^2) * v
        x_steered = x_proj - alpha * v (zararlı yönün tersine iter)
        """
        v = harmful_direction / (torch.norm(harmful_direction) + 1e-8)
        
        # [Batch, Seq, Dim] veya [Seq, Dim] veya [Dim]
        # Son boyut üzerinden skaler çarpım (dot product)
        projection_coeffs = torch.matmul(hidden_state, v) # [..., 1] veya [...]
        
        if hidden_state.ndim > 1:
            projection_component = projection_coeffs.unsqueeze(-1) * v
        else:
            projection_component = projection_coeffs * v

        # Ortogonal düzleme çek
        x_ortho = hidden_state - projection_component

        # Güvenli yöne hafif itme ekle (StTP)
        intervention = x_ortho - (alpha * v)

        if active_indices is not None:
            # Sadece OV devrelerine ait koordinatları güncelle
            diff = intervention - hidden_state
            sparse_diff = OVCircuitMask.apply_sparse_mask(diff, active_indices)
            return hidden_state + sparse_diff

        return intervention

    def project_stmp(
        self,
        hidden_state: torch.Tensor,
        harmful_direction: torch.Tensor,
        active_indices: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """
        Steer-to-Mirror Projection (StMP):
        Gizli aktivasyonu karar sınırının güvenli tarafındaki simetriğine (ayna yansımasına) taşır.
        x_mirror = x - 2 * (x · v) * v
        """
        v = harmful_direction / (torch.norm(harmful_direction) + 1e-8)
        projection_coeffs = torch.matmul(hidden_state, v)

        if hidden_state.ndim > 1:
            projection_component = 2.0 * projection_coeffs.unsqueeze(-1) * v
        else:
            projection_component = 2.0 * projection_coeffs * v

        intervention = hidden_state - projection_component

        if active_indices is not None:
            diff = intervention - hidden_state
            sparse_diff = OVCircuitMask.apply_sparse_mask(diff, active_indices)
            return hidden_state + sparse_diff

        return intervention

    @staticmethod
    def compute_adaptive_alpha(
        similarity: float,
        threshold: float,
        base_strength: float = 1.0,
        temperature: float = 0.1,
    ) -> float:
        """
        Dinamik Uyarlanabilir Şiddet (Adaptive Intensity):
        Karar sınırına olan mesafeye göre aktivasyon yönlendirme gücünü sürekli (smooth)
        bir sigmoid eğrisi üzerinden ölçeklendirir.

        alpha(x) = alpha_0 * sigmoid((cos(x, v) - tau) / T)
        """
        diff = (similarity - threshold) / max(temperature, 1e-6)
        if diff >= 0:
            sig = 1.0 / (1.0 + math.exp(-diff))
        else:
            z = math.exp(diff)
            sig = z / (1.0 + z)
        return float(base_strength * sig)

    @staticmethod
    def project_joint_subspace(
        hidden_state: torch.Tensor,
        directions: List[torch.Tensor],
        strengths: List[float],
        active_indices: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """
        Ortak Boşluk Projeksiyonu (Joint Nullspace Subspace Projection):
        Birden fazla yönlendirme vektörü aynı anda aktif olduğunda, vektörlerin
        çapraz etkileşimini (cross-talk / interference) önlemek için QR ayrışımı
        üzerinden ortak ortogonal boşluk izdüşümü uygular.

        V = [v_1, v_2, ..., v_k] in R^{Dim x k}
        Q, _ = qr(V) -> Q is orthonormal basis of span(V)
        x_null = x - (x · Q) Q^T
        x_steered = x_null - sum(alpha_i * v_i)
        """
        if not directions:
            return hidden_state

        unit_vecs = [d / (torch.norm(d) + 1e-8) for d in directions]
        V = torch.stack(unit_vecs, dim=-1).to(device=hidden_state.device, dtype=hidden_state.dtype)

        # QR ayrışımı ile ortonormal taban matrisi Q [Dim, k]
        Q, _ = torch.linalg.qr(V)

        proj_coeffs = torch.matmul(hidden_state, Q)
        proj_component = torch.matmul(proj_coeffs, Q.T)

        x_null = hidden_state - proj_component

        steer_push = torch.zeros_like(hidden_state)
        for u_v, alpha in zip(unit_vecs, strengths):
            steer_push = steer_push + (alpha * u_v)

        intervention = x_null - steer_push

        if active_indices is not None:
            diff = intervention - hidden_state
            sparse_diff = OVCircuitMask.apply_sparse_mask(diff, active_indices)
            return hidden_state + sparse_diff

        return intervention

    def apply_steering(
        self,
        hidden_state: torch.Tensor,
        layer_idx: int,
    ) -> Tuple[torch.Tensor, bool, Dict[str, float]]:
        """
        Modelin belirli bir katmanındaki aktivasyon tensörüne kayıtlı yönlendirme kurallarını uygular.
        Tekil vektörlerde StTP/StMP, çoklu vektörlerde ise Ortak Boşluk İzdüşümü (Joint Nullspace) çalışır.
        """
        vectors = self.get_vectors_for_layer(layer_idx)
        if not vectors:
            return hidden_state, False, {}

        current_tensor = hidden_state
        was_steered = False
        risk_scores: Dict[str, float] = {}

        # Aktif tetiklenen vektörleri topla
        active_candidates: List[Tuple[SteeringVector, torch.Tensor, float]] = []

        for vec in vectors:
            v_tensor = self.cached_tensors.get(vec.name)
            if v_tensor is None:
                v_tensor = vec.to_tensor(device=hidden_state.device)
                self.cached_tensors[vec.name] = v_tensor
            else:
                v_tensor = v_tensor.to(device=hidden_state.device, dtype=hidden_state.dtype)

            # Karar sınırını kontrol et
            normalized_h = F.normalize(current_tensor, p=2, dim=-1)
            normalized_v = F.normalize(v_tensor, p=2, dim=-1)
            sim = torch.matmul(normalized_h, normalized_v)
            max_sim = float(torch.max(sim).item())
            risk_scores[vec.target_risk.value] = max_sim

            if max_sim > vec.threshold:
                effective_strength = (
                    self.compute_adaptive_alpha(max_sim, vec.threshold, vec.strength)
                    if self.adaptive_alpha
                    else vec.strength
                )
                active_candidates.append((vec, v_tensor, effective_strength))

        # Tekil veya çoklu vektör müdahalesi
        if len(active_candidates) == 1:
            vec, v_tensor, strength = active_candidates[0]
            if vec.method == SteeringMethod.STTP:
                current_tensor = self.project_sttp(
                    hidden_state=current_tensor,
                    harmful_direction=v_tensor,
                    alpha=strength,
                    active_indices=vec.sparse_mask,
                )
            elif vec.method == SteeringMethod.STMP:
                current_tensor = self.project_stmp(
                    hidden_state=current_tensor,
                    harmful_direction=v_tensor,
                    active_indices=vec.sparse_mask,
                )
            else:  # CAA
                addition = strength * v_tensor
                if vec.sparse_mask is not None:
                    addition = OVCircuitMask.apply_sparse_mask(addition, vec.sparse_mask)
                current_tensor = current_tensor - addition
            was_steered = True

        elif len(active_candidates) > 1:
            # Çoklu Vektör Çakışma Önleyici: Joint Subspace Nullspace Projection
            dirs = [c[1] for c in active_candidates]
            alphas = [c[2] for c in active_candidates]
            # Ortak maske birleşimi (eğer varsa)
            combined_mask = None
            masks = [c[0].sparse_mask for c in active_candidates if c[0].sparse_mask is not None]
            if masks:
                combined_mask = sorted(list(set().union(*masks)))

            current_tensor = self.project_joint_subspace(
                hidden_state=current_tensor,
                directions=dirs,
                strengths=alphas,
                active_indices=combined_mask,
            )
            was_steered = True

        if was_steered and self.kv_drift_guard is not None:
            delta = current_tensor - hidden_state
            current_tensor, _ = self.kv_drift_guard.record_and_decay(
                layer_idx=layer_idx,
                raw_hidden_state=hidden_state,
                intervention_delta=delta,
            )

        return current_tensor, was_steered, risk_scores



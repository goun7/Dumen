"""
dumen.core.kv_drift
===================
KV-Cache Kirlenmesini ve Otoregresif Sapmayı (Autoregressive Drift) Önleme Modülü.
Çok turlu ve uzun üretim dizilerinde zamansal sönümleme (Temporal Decay) uygular.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import torch


class KVDriftGuard:
    """
    Çıkarım sırasında her token adımında yapılan yönlendirmelerin birikimli
    KV-Cache etkisini izleyen ve zamansal sönümleme (decay) ile dil yapısını koruyan bekçi.
    """

    def __init__(
        self,
        decay_factor: float = 0.95,
        max_drift_threshold: float = 0.85,
        history_window: int = 128,
    ):
        assert 0.0 < decay_factor <= 1.0, "decay_factor (0, 1] aralığında olmalıdır."
        self.decay_factor = decay_factor
        self.max_drift_threshold = max_drift_threshold
        self.history_window = history_window

        # Token adımına göre geçmiş müdahaleler: {layer_idx: [torch.Tensor]}
        self.intervention_history: Dict[int, List[torch.Tensor]] = {}
        self.step_counts: Dict[int, int] = {}

    def reset(self) -> None:
        """Yeni bir üretim sekansı için geçmişi sıfırlar."""
        self.intervention_history.clear()
        self.step_counts.clear()

    def record_and_decay(
        self,
        layer_idx: int,
        raw_hidden_state: torch.Tensor,
        intervention_delta: torch.Tensor,
    ) -> Tuple[torch.Tensor, float]:
        """
        Mevcut adımdaki yönlendirme farkını (delta) geçmiş birikim ve zamansal sönümleme
        ile birleştirerek dengelenmiş efektif tensörü hesaplar.

        Returns:
            (effective_tensor, cumulative_drift_norm)
        """
        if layer_idx not in self.intervention_history:
            self.intervention_history[layer_idx] = []
            self.step_counts[layer_idx] = 0

        self.step_counts[layer_idx] += 1
        history = self.intervention_history[layer_idx]

        # Delta'yı geçmişe ekle
        history.append(intervention_delta.detach())
        if len(history) > self.history_window:
            history.pop(0)

        # Zamansal sönümleme ağırlıklı toplam: sum(gamma^(T - i) * delta_i)
        T = len(history)
        effective_delta = torch.zeros_like(intervention_delta)
        for i, past_delta in enumerate(history):
            weight = self.decay_factor ** (T - 1 - i)
            effective_delta = effective_delta + (weight * past_delta)

        # Efektif müdahaleyi uygula
        effective_hidden = raw_hidden_state + effective_delta

        # Sapma miktarını ölç (L2 normu)
        drift_norm = float(torch.norm(effective_delta).item())

        # Eğer birikimli sapma kritik eşiği aşarsa sönümlemeyi sertleştir (soft clip)
        if drift_norm > self.max_drift_threshold:
            clip_ratio = self.max_drift_threshold / (drift_norm + 1e-8)
            effective_delta = effective_delta * clip_ratio
            effective_hidden = raw_hidden_state + effective_delta
            drift_norm = self.max_drift_threshold

        return effective_hidden, drift_norm

    def get_drift_metrics(self, layer_idx: int) -> Dict[str, float]:
        """Belirtilen katmandaki birikimli KV-Cache sapma metriklerini döner."""
        history = self.intervention_history.get(layer_idx, [])
        if not history:
            return {"steps": 0, "avg_drift": 0.0, "total_active_deltas": 0}

        norms = [float(torch.norm(d).item()) for d in history]
        return {
            "steps": self.step_counts.get(layer_idx, 0),
            "avg_drift": sum(norms) / len(norms),
            "total_active_deltas": len(history),
        }

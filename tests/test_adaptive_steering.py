"""
tests/test_adaptive_steering.py
===============================
Dinamik Uyarlanabilir Şiddet (Adaptive Alpha) ve Entegre SteeringEngine testleri.
"""

import pytest
import torch
from dumen.core.types import RiskCategory, SteeringMethod, SteeringVector
from dumen.core.steering import SteeringEngine
from dumen.core.kv_drift import KVDriftGuard
from dumen.core.quantization import QuantizationType


def test_compute_adaptive_alpha():
    # Eşik değerinin tam üstünde (similarity == threshold) -> sigmoid(0) = 0.5 * base_strength
    alpha_mid = SteeringEngine.compute_adaptive_alpha(
        similarity=0.5,
        threshold=0.5,
        base_strength=2.0,
        temperature=0.1,
    )
    assert abs(alpha_mid - 1.0) < 1e-4

    # Eşik değerinin çok üstünde -> sigmoid(büyük) -> ~1.0 * base_strength
    alpha_high = SteeringEngine.compute_adaptive_alpha(
        similarity=0.9,
        threshold=0.5,
        base_strength=2.0,
        temperature=0.1,
    )
    assert alpha_high > 1.95

    # Eşik değerinin çok altında -> sigmoid(negatif) -> ~0.0
    alpha_low = SteeringEngine.compute_adaptive_alpha(
        similarity=0.1,
        threshold=0.5,
        base_strength=2.0,
        temperature=0.1,
    )
    assert alpha_low < 0.05


def test_steering_engine_integrated_with_kv_drift_and_quantization():
    dim = 32
    guard = KVDriftGuard(decay_factor=0.9, max_drift_threshold=5.0)

    engine = SteeringEngine(
        device="cpu",
        kv_drift_guard=guard,
        quantization=QuantizationType.FP8,
        adaptive_alpha=True,
    )

    v = torch.zeros(dim)
    v[0] = 1.0

    svec = SteeringVector.from_tensor(
        name="cyber_exploit_guard",
        layer_idx=10,
        tensor=v,
        target_risk=RiskCategory.CYBER_ATTACK,
        method=SteeringMethod.STTP,
        threshold=0.4,
        strength=1.5,
    )
    engine.register_vector(svec)

    # 1. Adım simülasyonu
    h1 = torch.zeros(1, 1, dim)
    h1[0, 0, 0] = 0.8  # Yüksek benzerlik (0.8 > 0.4)

    steered_h1, was_steered1, scores1 = engine.apply_steering(h1, layer_idx=10)
    assert was_steered1 is True
    assert scores1["cyber_attack"] > 0.4
    # Guard içinde 1 adım kayıtlı olmalı
    metrics = guard.get_drift_metrics(layer_idx=10)
    assert metrics["steps"] == 1
    assert metrics["avg_drift"] > 0.0

    # 2. Adım simülasyonu
    h2 = torch.zeros(1, 1, dim)
    h2[0, 0, 0] = 0.7
    steered_h2, was_steered2, _ = engine.apply_steering(h2, layer_idx=10)
    assert was_steered2 is True
    metrics2 = guard.get_drift_metrics(layer_idx=10)
    assert metrics2["steps"] == 2

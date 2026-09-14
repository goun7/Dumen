"""
tests/test_kv_drift.py
======================
KV-Cache Kirlenmesi ve Otoregresif Sapma (Autoregressive Drift Guard) testleri.
"""

import pytest
import torch
from dumen.core.kv_drift import KVDriftGuard


def test_kv_drift_temporal_decay():
    guard = KVDriftGuard(decay_factor=0.5, max_drift_threshold=100.0)

    raw_hidden = torch.zeros(1, 1, 16)
    delta = torch.ones(1, 1, 16)

    # 1. Adım: İlk delta uygulanır
    h1, drift1 = guard.record_and_decay(layer_idx=0, raw_hidden_state=raw_hidden, intervention_delta=delta)
    assert torch.isclose(h1[0, 0, 0], torch.tensor(1.0), atol=1e-5)

    # 2. Adım: Yeni delta eklenir, önceki delta 0.5 ile sönümlenir (1.0 + 0.5 * 1.0 = 1.5)
    h2, drift2 = guard.record_and_decay(layer_idx=0, raw_hidden_state=raw_hidden, intervention_delta=delta)
    assert torch.isclose(h2[0, 0, 0], torch.tensor(1.5), atol=1e-5)

    # 3. Adım: (1.0 + 0.5 * 1.0 + 0.25 * 1.0 = 1.75)
    h3, drift3 = guard.record_and_decay(layer_idx=0, raw_hidden_state=raw_hidden, intervention_delta=delta)
    assert torch.isclose(h3[0, 0, 0], torch.tensor(1.75), atol=1e-5)


def test_kv_drift_soft_clipping():
    threshold = 2.0
    guard = KVDriftGuard(decay_factor=1.0, max_drift_threshold=threshold)

    raw_hidden = torch.zeros(1, 1, 4)
    # Büyük bir delta gönder
    huge_delta = torch.ones(1, 1, 4) * 10.0

    effective_h, drift_norm = guard.record_and_decay(
        layer_idx=5,
        raw_hidden_state=raw_hidden,
        intervention_delta=huge_delta,
    )

    # drift_norm sınırlandırılmış (clamped) olmalı
    assert drift_norm <= threshold + 1e-4
    effective_delta = effective_h - raw_hidden
    assert torch.norm(effective_delta).item() <= threshold + 1e-4


def test_kv_drift_reset():
    guard = KVDriftGuard()
    raw_hidden = torch.zeros(1, 1, 8)
    delta = torch.ones(1, 1, 8)

    guard.record_and_decay(layer_idx=1, raw_hidden_state=raw_hidden, intervention_delta=delta)
    metrics_before = guard.get_drift_metrics(layer_idx=1)
    assert metrics_before["steps"] == 1

    guard.reset()
    metrics_after = guard.get_drift_metrics(layer_idx=1)
    assert metrics_after["steps"] == 0

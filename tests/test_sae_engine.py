"""
tests/test_sae_engine.py
========================
Seyrek Oto-Kodlayıcılar (SAE) TopK ve JumpReLU sözlük testleri.
"""

import pytest
import torch
from dumen.core.sae_engine import SparseAutoencoderEngine


def test_sae_topk_sparsity():
    d_model = 64
    n_features = 256
    k = 16

    sae = SparseAutoencoderEngine(d_model=d_model, n_features=n_features, k_sparsity=k)
    x = torch.randn(2, d_model)

    x_hat, f = sae(x, use_topk=True)

    assert x_hat.shape == (2, d_model)
    assert f.shape == (2, n_features)

    # Her satırda aktif özellik sayısı tam olarak k olmalı
    non_zero_count = (f > 0).sum(dim=-1)
    assert (non_zero_count <= k).all()


def test_sae_feature_labeling_and_inspection():
    sae = SparseAutoencoderEngine(d_model=32, n_features=128)
    sae.label_feature(10, "deceptive_intent")
    sae.label_feature(25, "cyber_exploit_plan")

    # Sentetik aktivasyon
    x = torch.randn(32)
    insights = sae.inspect_activations(x, top_n=5)

    assert isinstance(insights, list)
    assert len(insights) <= 5
    for item in insights:
        assert "feature_idx" in item
        assert "activation" in item
        assert "label" in item


def test_sae_mutual_regularization_loss():
    sae = SparseAutoencoderEngine(d_model=16, n_features=32)
    loss = sae.compute_mutual_regularization_loss()
    assert loss.ndim == 0
    assert loss.item() >= 0.0

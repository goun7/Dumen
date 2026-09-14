"""
tests/test_transcoder.py
========================
Transcoder (MLP Input-to-Output Dictionary Mapping) mekanistik testleri.
"""

import pytest
import torch
from dumen.core.transcoder import TranscoderEngine


def test_transcoder_initialization_and_forward():
    d_in = 64
    d_out = 64
    d_dict = 256
    top_k = 16

    transcoder = TranscoderEngine(
        d_in=d_in,
        d_out=d_out,
        d_dict=d_dict,
        top_k=top_k,
    )

    x_in = torch.randn(2, 8, d_in)
    x_out_recon, latents = transcoder(x_in)

    assert x_out_recon.shape == (2, 8, d_out)
    assert latents.shape == (2, 8, d_dict)

    # TopK sparsity doğrulaması: latent tensöründe her token için tam olarak top_k kadar sıfır olmayan değer olmalı
    non_zero_per_token = (latents > 0).sum(dim=-1)
    assert torch.all(non_zero_per_token <= top_k)


def test_transcoder_feature_suppression():
    d_in = 32
    d_out = 32
    d_dict = 128
    top_k = 8

    transcoder = TranscoderEngine(d_in=d_in, d_out=d_out, d_dict=d_dict, top_k=top_k)

    x_in = torch.randn(1, 4, d_in)
    recon_normal, latents_normal = transcoder(x_in)

    # En aktif özelliği bul
    active_feature_idx = int(latents_normal.sum(dim=(0, 1)).argmax().item())

    # Bu özelliği tamamen bastır (suppress)
    recon_suppressed, latents_suppressed = transcoder(
        x_in,
        suppress_indices=[active_feature_idx],
    )

    # Bastırılan özellik aktivasyonunun sıfır olduğunu doğrula
    assert torch.all(latents_suppressed[:, :, active_feature_idx] == 0.0)
    # Rekonstrüksiyon tensörünün değiştiğini doğrula
    assert not torch.allclose(recon_normal, recon_suppressed, atol=1e-5)


def test_transcoder_loss_computation():
    d_in = 32
    d_out = 32
    d_dict = 64
    top_k = 4

    transcoder = TranscoderEngine(d_in=d_in, d_out=d_out, d_dict=d_dict, top_k=top_k)

    x_in = torch.randn(2, 4, d_in)
    mlp_target = torch.randn(2, 4, d_out)

    loss_dict = transcoder.compute_loss(x_in, mlp_target, l1_coeff=1e-3)

    assert "total_loss" in loss_dict
    assert "reconstruction_loss" in loss_dict
    assert "l1_loss" in loss_dict
    assert loss_dict["total_loss"].item() > 0.0

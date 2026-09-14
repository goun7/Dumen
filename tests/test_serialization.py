"""
tests/test_serialization.py
============================
Model, SAE, Transcoder ve SteeringVector ağırlık kaydetme/yükleme (I/O) testleri.
"""

import os
import shutil
import pytest
import torch
from dumen.core.sae_engine import SparseAutoencoderEngine
from dumen.core.transcoder import TranscoderEngine
from dumen.core.types import RiskCategory, SteeringVector, SteeringMethod
from dumen.core.serialization import ModelSerializer


def test_sae_save_and_load_pretrained(tmp_path):
    sae_dir = str(tmp_path / "sae_checkpoint")
    d_model = 32
    n_features = 64

    sae = SparseAutoencoderEngine(d_model=d_model, n_features=n_features, k_sparsity=8)
    sae.label_feature(0, "deception_marker")

    # Modeli kaydet
    saved_path = sae.save_pretrained(sae_dir)
    assert os.path.exists(os.path.join(saved_path, "config.json"))
    assert os.path.exists(os.path.join(saved_path, "sae_weights.pt"))

    # Modeli yükle
    loaded_sae = SparseAutoencoderEngine.from_pretrained(sae_dir)
    assert loaded_sae.d_model == d_model
    assert loaded_sae.n_features == n_features
    assert loaded_sae.feature_labels[0] == "deception_marker"

    # Ağırlıkların birebir aynı olduğunu doğrula
    x = torch.randn(1, 4, d_model)
    recon_orig, _ = sae(x)
    recon_loaded, _ = loaded_sae(x)
    assert torch.allclose(recon_orig, recon_loaded, atol=1e-5)


def test_transcoder_save_and_load_pretrained(tmp_path):
    transcoder_dir = str(tmp_path / "transcoder_checkpoint")
    d_in = 32
    d_out = 32
    d_dict = 64

    transcoder = TranscoderEngine(d_in=d_in, d_out=d_out, d_dict=d_dict, top_k=4)
    transcoder.suppress_feature(5)

    saved_path = transcoder.save_pretrained(transcoder_dir)
    assert os.path.exists(os.path.join(saved_path, "config.json"))
    assert os.path.exists(os.path.join(saved_path, "transcoder_weights.pt"))

    loaded = TranscoderEngine.from_pretrained(transcoder_dir)
    assert loaded.d_in == d_in
    assert loaded.d_out == d_out
    assert 5 in loaded.suppressed_features

    x = torch.randn(1, 2, d_in)
    orig_out, _ = transcoder(x)
    loaded_out, _ = loaded(x)
    assert torch.allclose(orig_out, loaded_out, atol=1e-5)


def test_steering_vectors_save_and_load(tmp_path):
    json_file = str(tmp_path / "vectors.json")
    v = torch.randn(16)
    svec = SteeringVector.from_tensor(
        name="test_guard",
        layer_idx=8,
        tensor=v,
        target_risk=RiskCategory.BIO_HAZARD,
        method=SteeringMethod.STTP,
    )

    ModelSerializer.save_steering_vectors([svec], json_file)
    assert os.path.exists(json_file)

    loaded_vecs = ModelSerializer.load_steering_vectors(json_file)
    assert len(loaded_vecs) == 1
    assert loaded_vecs[0].name == "test_guard"
    assert loaded_vecs[0].layer_idx == 8
    assert loaded_vecs[0].target_risk == RiskCategory.BIO_HAZARD

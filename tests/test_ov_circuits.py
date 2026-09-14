"""
tests/test_ov_circuits.py
=========================
Attention OV devresi seyreltme ve maskeleme testleri.
"""

import pytest
import torch
from dumen.core.ov_circuits import OVCircuitMask


def test_ov_circuit_sparsity():
    dim = 128
    masker = OVCircuitMask(hidden_dim=dim, num_heads=4)
    v = torch.randn(dim)
    v = v / torch.norm(v)

    # %15 boyut tutulacak (%85 seyreltme)
    sparse_v, active_indices = masker.compute_ov_salience(v, top_k_percent=0.15)

    expected_k = int(dim * 0.15)
    assert len(active_indices) == expected_k
    assert torch.isclose(torch.norm(sparse_v), torch.tensor(1.0), atol=1e-4)

    # Aktif olmayan indislerin sıfır olduğunu doğrula
    for i in range(dim):
        if i not in active_indices:
            assert sparse_v[i] == 0.0


def test_apply_sparse_mask():
    tensor = torch.ones(10)
    active = [0, 2, 4]
    masked = OVCircuitMask.apply_sparse_mask(tensor, active)

    assert masked[0] == 1.0
    assert masked[1] == 0.0
    assert masked[2] == 1.0
    assert masked[3] == 0.0

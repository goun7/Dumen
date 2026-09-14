"""
tests/test_miner.py
===================
Kontrastif Yönlendirme Vektörü Madencisi (Difference-in-Means & PCA) testleri.
"""

import pytest
import torch
from dumen.core.types import RiskCategory, SteeringMethod
from dumen.core.miner import VectorMiner
from dumen.core.steering import SteeringEngine


def test_difference_in_means_extraction():
    dim = 32
    n_samples = 20

    # Zararlı aktivasyonlar (örneğin ilk koordinatta +5.0 ortalama)
    harmful_acts = torch.randn(n_samples, dim)
    harmful_acts[:, 0] += 5.0

    # Güvenli aktivasyonlar (ilk koordinatta 0.0 ortalama)
    safe_acts = torch.randn(n_samples, dim)

    direction = VectorMiner.compute_difference_in_means(harmful_acts, safe_acts)

    assert direction.shape == (dim,)
    assert torch.isclose(torch.norm(direction), torch.tensor(1.0), atol=1e-5)
    # En güçlü yönün 0. koordinat olduğunu doğrula
    assert direction[0] > 0.8


def test_pca_direction_extraction():
    dim = 16
    n_samples = 30

    harmful_acts = torch.randn(n_samples, dim)
    harmful_acts[:, 1] += 8.0
    safe_acts = torch.randn(n_samples, dim)

    direction_pca = VectorMiner.compute_pca_direction(harmful_acts, safe_acts)

    assert direction_pca.shape == (dim,)
    assert torch.isclose(torch.norm(direction_pca), torch.tensor(1.0), atol=1e-5)
    assert abs(direction_pca[1].item()) > 0.8


def test_mine_from_activations_and_steer():
    dim = 16
    n_samples = 10

    h_acts = {12: torch.randn(n_samples, dim) + torch.tensor([4.0] + [0.0] * 15)}
    s_acts = {12: torch.randn(n_samples, dim)}

    vectors = VectorMiner.mine_from_activations(
        harmful_layer_acts=h_acts,
        safe_layer_acts=s_acts,
        target_risk=RiskCategory.DECEPTION,
        method=SteeringMethod.STTP,
    )

    assert 12 in vectors
    vec = vectors[12]
    assert vec.target_risk == RiskCategory.DECEPTION
    assert vec.layer_idx == 12

    # Bu vektörü SteeringEngine'e verip müdahale başarısını sına
    engine = SteeringEngine()
    engine.register_vector(vec)

    harmful_test = torch.zeros(1, 1, dim)
    harmful_test[0, 0, 0] = 5.0  # Zararlı yönde aktivasyon

    steered, was_steered, scores = engine.apply_steering(harmful_test, layer_idx=12)
    assert was_steered is True
    # Yönlendirme sonrası aktivasyon güvenli alana itilmeli
    assert steered[0, 0, 0] < harmful_test[0, 0, 0]


def test_mine_from_prompts_pipeline():
    dim = 8
    def mock_forward_extractor(prompt: str):
        # Eğer zararlıysa 0. boyutta +3 aktivasyon
        bias = 3.0 if "harmful" in prompt else 0.0
        return {
            5: torch.tensor([[bias] + [0.0] * 7]),
        }

    pairs = [
        ("harmful request 1", "safe benign request 1"),
        ("harmful request 2", "safe benign request 2"),
    ]

    mined_vecs = VectorMiner.mine_from_prompts(
        prompt_pairs=pairs,
        forward_hook_extractor=mock_forward_extractor,
        target_risk=RiskCategory.CYBER_ATTACK,
        target_layers=[5],
    )

    assert 5 in mined_vecs
    assert mined_vecs[5].vector[0] > 0.9


def test_contrastive_pair_metadata():
    from dumen.core.miner import ContrastivePair
    pair = ContrastivePair("attack", "benign", metadata={"source": "jailbreak_bench"})
    assert pair.harmful == "attack"
    assert pair.safe == "benign"
    assert pair.metadata["source"] == "jailbreak_bench"


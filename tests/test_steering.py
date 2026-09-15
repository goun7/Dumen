"""
tests/test_steering.py
======================
StTP ve StMP aktivasyon yönlendirme matematiksel doğrulaması.
"""

import torch

from dumen.core.steering import SteeringEngine
from dumen.core.types import RiskCategory, SteeringMethod, SteeringVector


def test_sttp_orthogonal_projection():
    dim = 64
    engine = SteeringEngine()

    # Zararlı yön vektörü
    v = torch.zeros(dim)
    v[0] = 1.0  # Zararlı yön ilk boyutta

    # Zararlı yönde güçlü aktivasyon
    x = torch.zeros(dim)
    x[0] = 5.0
    x[1] = 2.0

    # StTP ile müdahale et (alpha=0 sadece projeksiyonu test eder)
    steered = engine.project_sttp(x, v, alpha=0.0)

    # İlk boyut sıfırlanmış olmalı (ortogonalite kanıtı)
    assert torch.isclose(steered[0], torch.tensor(0.0), atol=1e-5)
    # Diğer boyutlar korunmalı
    assert torch.isclose(steered[1], torch.tensor(2.0), atol=1e-5)


def test_stmp_mirror_projection():
    dim = 64
    engine = SteeringEngine()

    v = torch.zeros(dim)
    v[0] = 1.0

    x = torch.zeros(dim)
    x[0] = 3.0
    x[1] = 4.0

    # StMP ayna yansıması (x[0] -> -3.0 olmalı)
    mirrored = engine.project_stmp(x, v)
    assert torch.isclose(mirrored[0], torch.tensor(-3.0), atol=1e-5)
    assert torch.isclose(mirrored[1], torch.tensor(4.0), atol=1e-5)


def test_steering_engine_registration_and_apply():
    dim = 32
    engine = SteeringEngine()

    v = torch.zeros(dim)
    v[0] = 1.0

    svec = SteeringVector.from_tensor(
        name="deception_guard",
        layer_idx=14,
        tensor=v,
        target_risk=RiskCategory.DECEPTION,
        method=SteeringMethod.STTP,
        threshold=0.5,
        strength=1.0,
    )
    engine.register_vector(svec)

    # Katman 14 aktivasyonu (Zararlı yönde)
    x = torch.zeros(1, 1, dim)
    x[0, 0, 0] = 1.0

    steered_x, was_steered, scores = engine.apply_steering(x, layer_idx=14)
    assert was_steered is True
    assert scores["deception"] > 0.5
    # Yönlendirme sonrası ilk boyut negatif/güvenli alana itilmeli
    assert steered_x[0, 0, 0] < 0.1

    # Alakasız katmanda müdahale olmamalı
    _, was_steered_diff_layer, _ = engine.apply_steering(x, layer_idx=5)
    assert was_steered_diff_layer is False


def test_project_joint_subspace_multi_vector():
    dim = 32
    engine = SteeringEngine()

    # İki farklı zararlı yön (0. ve 1. koordinatlarda)
    v1 = torch.zeros(dim)
    v1[0] = 1.0
    v2 = torch.zeros(dim)
    v2[1] = 1.0

    svec1 = SteeringVector.from_tensor(
        name="risk1_guard",
        layer_idx=7,
        tensor=v1,
        target_risk=RiskCategory.DECEPTION,
        threshold=0.3,
        strength=1.0,
    )
    svec2 = SteeringVector.from_tensor(
        name="risk2_guard",
        layer_idx=7,
        tensor=v2,
        target_risk=RiskCategory.CYBER_ATTACK,
        threshold=0.3,
        strength=1.0,
    )
    engine.register_vector(svec1)
    engine.register_vector(svec2)

    # İki yönde de aynı anda tetiklenen aktivasyon
    x = torch.zeros(1, 1, dim)
    x[0, 0, 0] = 2.0
    x[0, 0, 1] = 2.0
    x[0, 0, 2] = 5.0  # Zararsız boyut

    steered, was_steered, scores = engine.apply_steering(x, layer_idx=7)
    assert was_steered is True
    assert scores["deception"] > 0.3
    assert scores["cyber_attack"] > 0.3

    # Ortak boşluk izdüşümü sonrasında her iki zararlı koordinat da güvenli tarafa itilmiş olmalı
    assert steered[0, 0, 0] < 0.1
    assert steered[0, 0, 1] < 0.1
    # Zararsız boyut (koordinat 2) bozulmamalı
    assert torch.isclose(steered[0, 0, 2], torch.tensor(5.0), atol=1e-4)


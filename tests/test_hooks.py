"""
tests/test_hooks.py
===================
ModelHookManager ileri geçiş hook testleri.
"""

import torch
import torch.nn as nn

from dumen.core.hooks import ModelHookManager
from dumen.core.steering import SteeringEngine
from dumen.core.types import RiskCategory, SteeringVector


class DummyTransformerLayer(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.linear = nn.Linear(dim, dim, bias=False)
        nn.init.eye_(self.linear.weight)

    def forward(self, x: torch.Tensor):
        return self.linear(x)


def test_hook_manager_interception():
    dim = 16
    layer = DummyTransformerLayer(dim)
    engine = SteeringEngine()

    v = torch.zeros(dim)
    v[0] = 1.0

    svec = SteeringVector.from_tensor(
        name="test_guard",
        layer_idx=0,
        tensor=v,
        target_risk=RiskCategory.DECEPTION,
        threshold=0.3,
        strength=2.0,
    )
    engine.register_vector(svec)

    hook_mgr = ModelHookManager(steering_engine=engine)
    hook_mgr.attach_to_layer(layer, layer_idx=0)

    # İleri geçiş (Zararlı aktivasyon)
    x = torch.zeros(1, dim)
    x[0, 0] = 1.0

    out = layer(x)

    # Yönlendirme devreye girmeli ve ilk boyut bastırılmalı
    assert len(hook_mgr.intervention_history) == 1
    assert out[0, 0] < 0.1

    # Sökme testi
    hook_mgr.detach_all()
    assert len(hook_mgr.active_hooks) == 0

    # Tekrar koşumda müdahale olmamalı
    out_clean = layer(x)
    assert torch.isclose(out_clean[0, 0], torch.tensor(1.0))

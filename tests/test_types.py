"""
tests/test_types.py
===================
Veri modelleri ve tiplerin doğrulanması.
"""

import pytest
import torch
from dumen.core.types import (
    RiskCategory,
    SteeringMethod,
    SteeringVector,
    InspectionResult,
    AuditReport,
)


def test_steering_vector_tensor_conversion():
    raw_vec = [1.0, 0.0, -1.0, 0.5]
    sv = SteeringVector(
        name="test_vec",
        layer_idx=12,
        dimension=4,
        vector=raw_vec,
        target_risk=RiskCategory.DECEPTION,
        method=SteeringMethod.STTP,
    )

    tensor = sv.to_tensor()
    assert tensor.shape == (4,)
    # Normunun 1'e normalize edilmiş olması gerekir
    assert torch.isclose(torch.norm(tensor), torch.tensor(1.0), atol=1e-5)

    # from_tensor testi
    reconstructed = SteeringVector.from_tensor(
        name="recon",
        layer_idx=12,
        tensor=tensor,
        target_risk=RiskCategory.CYBER_ATTACK,
    )
    assert reconstructed.dimension == 4
    assert reconstructed.target_risk == RiskCategory.CYBER_ATTACK


def test_inspection_result_serialization():
    res = InspectionResult(
        timestamp="2026-09-14 18:00:00",
        model_name="llama-3-8b",
        is_safe=True,
        risk_scores={"deception": 0.02},
        active_features=[12, 45, 99],
        steered=True,
        latency_ms=1.24,
        output_text="Guarded response",
    )
    data = res.model_dump()
    assert data["is_safe"] is True
    assert data["steered"] is True
    assert len(data["active_features"]) == 3

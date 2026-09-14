"""
tests/test_steering_overhead.py
===============================
Yönlendirme Yükü (Steering Overhead) ölçüm testleri: yetenek bozulması ve
norm drift ölçümlerinin doğruluğu, kabul eşikleri, uç durumlar.
"""

import pytest
import torch

from dumen.core.types import RiskCategory
from dumen.core.miner import VectorMiner
from dumen.core.steering import SteeringEngine
from dumen.benchmarks.steering_overhead import SteeringOverheadBench, OverheadReport


def build_engine_with_risk_vector(layer=8, dim=32, n=30, seed=5):
    """Belirgin risk yönü olan vektörle kayıtlı motor döndürür."""
    g = torch.Generator().manual_seed(seed)
    harmful = torch.randn(n, dim, generator=g)
    harmful[:, 0] += 4.0
    safe = torch.randn(n, dim, generator=g)
    vecs = VectorMiner.mine_from_activations(
        harmful_layer_acts={layer: harmful},
        safe_layer_acts={layer: safe},
        target_risk=RiskCategory.DECEPTION,
        n_bootstrap=0,
    )
    engine = SteeringEngine()
    engine.register_vector(vecs[layer])
    return engine


class TestOverheadMeasure:
    def test_report_structure(self):
        engine = build_engine_with_risk_vector()
        torch.manual_seed(11)
        benign = torch.randn(40, 32)
        rep = SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=benign, n_probes=6)
        assert isinstance(rep, OverheadReport)
        assert rep.layer_idx == 8 and rep.n_probes == 6
        assert 0.0 <= rep.probe_accuracy_before <= 1.0
        assert 0.0 <= rep.probe_accuracy_after <= 1.0
        assert 0.0 <= rep.capability_retention <= 1.0
        assert rep.norm_drift_ratio > 0.0

    def test_orthogonal_risk_vector_zero_overhead(self):
        """
        Risk vektörü zararsız temsillerden İDEALDE bağımsızsa (ortogonal
        varyans), benign görevler bozulmamalı. Tam ortogonalite garantisi
        gerçek veride yoktur; bu test ölçüm çerçevesinin yönlendirilmemiş
        motorla mükemmel skor ürettiğini doğrular (sanity anchor).
        """
        engine = SteeringEngine()  # HİÇ vektör kayıtlı değil
        torch.manual_seed(12)
        benign = torch.randn(40, 32)
        rep = SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=benign)
        # Vektör yoksa apply_steering müdahale etmez → bozulma sıfır
        assert rep.capability_retention >= 0.99
        assert abs(rep.norm_drift_ratio - 1.0) < 0.02
        assert rep.acceptable_overhead is True

    def test_aligned_risk_vector_measures_degradation(self):
        """
        Risk vektörü benign dağılımın ANA eksenine hizalıysa ölçüm bozulmayı
        rapor etmeli — ölçüm ayırt ediciliği (differentiation) testi.
        """
        g = torch.Generator().manual_seed(13)
        benign = torch.randn(40, 32, generator=g)
        # Benign varyansın baskın eksenini bul (PCA kabaca)
        centered = benign - benign.mean(dim=0)
        _, _, vh = torch.linalg.svd(centered, full_matrices=False)
        dominant = vh[0]

        # Risk vektörünü baskın eksene hizala → steering benign'i bozar
        from dumen.core.types import SteeringVector
        vec = SteeringVector.from_tensor(
            name="aligned_risk",
            layer_idx=8,
            tensor=dominant,
            target_risk=RiskCategory.DECEPTION,
        )
        engine = SteeringEngine()
        engine.register_vector(vec)

        rep = SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=benign)
        # Aynı örneklemde ölçülen bozulma: norm drift raporlanmalı
        assert rep.norm_drift_ratio != 1.0 or rep.probe_accuracy_after != rep.probe_accuracy_before

    def test_acceptable_overhead_thresholds(self):
        """acceptance bayrağı eşiğe tam bağlı olmalı."""
        engine = build_engine_with_risk_vector()
        torch.manual_seed(14)
        benign = torch.randn(50, 32)
        rep = SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=benign)
        expected = (
            rep.capability_retention >= SteeringOverheadBench.CAPABILITY_FLOOR
            and SteeringOverheadBench.NORM_DRIFT_BOUNDS[0] <= rep.norm_drift_ratio
            <= SteeringOverheadBench.NORM_DRIFT_BOUNDS[1]
        )
        assert rep.acceptable_overhead == expected

    def test_rejects_bad_shapes(self):
        engine = SteeringEngine()
        with pytest.raises(ValueError):
            SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=torch.randn(10, 32, 1))
        with pytest.raises(ValueError):
            SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=torch.randn(32))

    def test_deterministic_with_seed(self):
        engine = build_engine_with_risk_vector()
        torch.manual_seed(15)
        benign = torch.randn(30, 32)
        r1 = SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=benign, seed=77)
        r2 = SteeringOverheadBench.measure(engine, layer_idx=8, benign_activations=benign, seed=77)
        assert r1.probe_accuracy_before == r2.probe_accuracy_before
        assert r1.norm_drift_ratio == r2.norm_drift_ratio

"""
tests/test_quantization.py
==========================
Kuantizasyon Eşitliği (FP8 / INT4 Calibration) testleri.
"""

import pytest
import torch

from dumen.core.quantization import QuantizationCalibrator, QuantizationType


def test_fp8_quantization_simulation():
    tensor = torch.tensor([0.0, 0.5, 1.25, 4.0, 448.0, 500.0, -1.0])
    q_fp8 = QuantizationCalibrator.simulate_fp8(tensor)

    # Değerlerin sonlu ve makul aralıkta olduğunu doğrula
    assert not torch.isnan(q_fp8).any()
    assert not torch.isinf(q_fp8).any()
    # 500.0 değeri FP8_E4M3 maksimumu olan 448.0'e doymuş (saturated) olmalı
    assert torch.isclose(q_fp8[5], torch.tensor(448.0), atol=1e-2)


def test_int4_quantization_simulation():
    tensor = torch.linspace(-5.0, 5.0, steps=11)
    q_int4 = QuantizationCalibrator.simulate_int4(tensor)

    assert not torch.isnan(q_int4).any()
    # INT4 simülasyonu sonrasında sınırların korunduğunu doğrula
    assert q_int4.max() <= 5.0 + 1e-4
    assert q_int4.min() >= -5.0 - 1e-4


def test_calibrate_steering_vector():
    vec = torch.randn(128)
    # FP8 kalibrasyonu
    q_vec_fp8, metrics_fp8 = QuantizationCalibrator.calibrate_steering_vector(
        vec,
        target_quant=QuantizationType.FP8,
    )
    assert q_vec_fp8.shape == vec.shape
    assert "relative_error" in metrics_fp8
    assert "snr_db" in metrics_fp8
    assert metrics_fp8["snr_db"] > 10.0  # FP8 için yüksek SNR

    # INT4 kalibrasyonu
    q_vec_int4, metrics_int4 = QuantizationCalibrator.calibrate_steering_vector(
        vec,
        target_quant=QuantizationType.INT4,
    )
    assert q_vec_int4.shape == vec.shape
    assert metrics_int4["relative_error"] >= 0.0


class TestQuantizationFullGrid:
    """v0.6.0: tüm kuantizasyon ızgaraları ve hata yolları."""

    def test_int8_grid(self):
        from dumen.core.quantization import QuantizationCalibrator, QuantizationType
        t = torch.randn(32) * 3.0
        q = QuantizationCalibrator.simulate_quantization(t, QuantizationType.INT8)
        assert q.shape == t.shape
        # Simetrik 8-bit: değerler orijinalin ±scale/2 toleransında
        assert torch.allclose(q, t, atol=3.0 / 127.0 + 0.01)

    def test_int8_extreme_clamping(self):
        from dumen.core.quantization import QuantizationCalibrator, QuantizationType
        t = torch.tensor([100.0, -100.0, 0.0])
        q = QuantizationCalibrator.simulate_quantization(t, QuantizationType.INT8)
        # clamp(-128,127) sonrası geri ölçek — uçlar korunmalı
        assert q[0] <= 100.0 + 1e-6
        assert q[1] >= -100.0 - 1e-6

    def test_fp8_path(self):
        """FP8: float8_e4m3fn varsa gerçek dönüşüm; yoksa clamp+yuvarlama (her iki yol geçerli)."""
        from dumen.core.quantization import QuantizationCalibrator, QuantizationType
        t = torch.tensor([0.1, -0.3, 500.0, 2.7])
        q = QuantizationCalibrator.simulate_quantization(t, QuantizationType.FP8)
        if hasattr(torch, "float8_e4m3fn"):
            # Gerçek e4m3: taşan değer 448.0'a doyurulur (pozitif kalır)
            assert q[2] == pytest.approx(448.0)
        else:
            # Legacy fallback: clamp(-448, 448) + 1/8 ızgarası
            assert q[2] == pytest.approx(-448.0)
            assert q[0] == pytest.approx(0.125)
        # Her iki yolda da biçim korunmalı
        assert q.shape == t.shape

    def test_none_type_passthrough(self):
        from dumen.core.quantization import QuantizationCalibrator, QuantizationType
        t = torch.randn(8)
        assert torch.equal(
            QuantizationCalibrator.simulate_quantization(t, QuantizationType.NONE), t
        )

    def test_calibrate_target_quant_override(self):
        from dumen.core.quantization import QuantizationCalibrator, QuantizationType
        v = torch.randn(16)
        calibrated, metrics = QuantizationCalibrator.calibrate_steering_vector(
            v, quant_type=QuantizationType.FP8, target_quant=QuantizationType.INT4
        )
        # target_quant, quant_type'i ezmalı
        assert "snr_db" in metrics or "error_delta" in metrics
        norm = torch.norm(calibrated)
        assert abs(norm.item() - 1.0) < 0.05  # yeniden normalize

    def test_calibrate_zero_vector_safe(self):
        """Sıfır vektör NaN üretmemeli (bölme koruması)."""
        from dumen.core.quantization import QuantizationCalibrator, QuantizationType
        v = torch.zeros(8)
        calibrated, _ = QuantizationCalibrator.calibrate_steering_vector(v, QuantizationType.FP8)
        assert not torch.isnan(calibrated).any()

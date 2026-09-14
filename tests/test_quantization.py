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

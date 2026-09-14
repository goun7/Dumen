"""
dumen.core.quantization
=======================
Kuantize Modeller İçin Hassasiyet Kalibratörü (FP8 / INT4 / AWQ Zırhı).
Kuantizasyon yuvarlama gürültüsünü telafi eden ortogonal izdüşüm yöneticisi.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, Optional, Tuple, Any
import torch


class QuantizationType(str, Enum):
    NONE = "none_fp16_fp32"
    FP8 = "fp8_e4m3"
    INT8 = "int8"
    INT4 = "int4_awq"


class QuantizationCalibrator:
    """
    vLLM ve HuggingFace kuantize çıkarım ortamlarında (AWQ / GPTQ / FP8)
    yönlendirme vektörlerini kuantizasyon ızgarasına hizalayan kalibratör.
    """

    @staticmethod
    def simulate_fp8(tensor: torch.Tensor) -> torch.Tensor:
        """FP8 (E4M3) simülasyonu."""
        return QuantizationCalibrator.simulate_quantization(tensor, QuantizationType.FP8)

    @staticmethod
    def simulate_int4(tensor: torch.Tensor) -> torch.Tensor:
        """INT4 (AWQ) simülasyonu."""
        return QuantizationCalibrator.simulate_quantization(tensor, QuantizationType.INT4)

    @staticmethod
    def simulate_quantization(
        tensor: torch.Tensor,
        quant_type: QuantizationType,
    ) -> torch.Tensor:
        """
        Tensör üzerinde hedef kuantizasyon ızgara dönüşümünü simüle eder.
        """
        if quant_type == QuantizationType.NONE:
            return tensor

        with torch.no_grad():
            if quant_type == QuantizationType.INT8:
                # Simetrik 8-bit kuantizasyon
                max_val = torch.max(torch.abs(tensor)) + 1e-8
                scale = max_val / 127.0
                q = torch.round(tensor / scale).clamp(-128, 127)
                return q * scale

            elif quant_type == QuantizationType.INT4:
                # Simetrik 4-bit kuantizasyon (AWQ benzeri)
                max_val = torch.max(torch.abs(tensor)) + 1e-8
                scale = max_val / 7.0
                q = torch.round(tensor / scale).clamp(-8, 7)
                return q * scale

            elif quant_type == QuantizationType.FP8:
                if hasattr(torch, "float8_e4m3fn"):
                    orig_dtype = tensor.dtype
                    return tensor.to(torch.float8_e4m3fn).to(orig_dtype)
                else:
                    clamped = tensor.clamp(-448.0, 448.0)
                    return torch.round(clamped * 8.0) / 8.0

        return tensor

    @classmethod
    def calibrate_steering_vector(
        cls,
        vector: torch.Tensor,
        quant_type: QuantizationType = QuantizationType.FP8,
        target_quant: Optional[QuantizationType] = None,
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Yönlendirme vektörünü hedef kuantizasyon ızgarasına projekte eder ve
        yuvarlama hatasını (error delta norm ve SNR dB) hesaplar.

        Returns:
            (calibrated_vector, metrics_dict)
        """
        if target_quant is not None:
            quant_type = target_quant

        unit_v = vector / (torch.norm(vector) + 1e-8)
        quantized_v = cls.simulate_quantization(unit_v, quant_type)
        norm = torch.norm(quantized_v)
        if norm > 1e-8:
            calibrated = quantized_v / norm
        else:
            calibrated = unit_v

        diff = unit_v - calibrated
        error_norm = float(torch.norm(diff).item())
        signal_power = float(torch.sum(unit_v ** 2).item())
        noise_power = float(torch.sum(diff ** 2).item()) + 1e-12
        snr_db = float(10.0 * torch.log10(torch.tensor(signal_power / noise_power)).item())

        metrics = {
            "relative_error": error_norm,
            "error_norm": error_norm,
            "snr_db": snr_db,
        }
        return calibrated, metrics

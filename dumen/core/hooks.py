"""
dumen.core.hooks
================
PyTorch forward hook yöneticisi: HuggingFace/standart nn.Module transformer
bloklarına çıkarım-anı yönlendirme hook'u bağlar. (vLLM worker entegrasyonu
YOL HARİTASINDADIR — kodda yoktur; bkz. an internal planning doc "Tehdit Modeli ve
Sınırlar".)
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

import torch
import torch.nn as nn

from dumen.core.steering import SteeringEngine
from dumen.core.types import InspectionResult


class ModelHookManager:
    """
    HuggingFace veya standart PyTorch Transformer modellerinin katmanlarına
    dinamik forward hook bağlayarak çıkarım anında aktivasyon yönlendirmesini yönetir.
    """

    def __init__(self, steering_engine: SteeringEngine):
        self.steering_engine = steering_engine
        self.active_hooks: List[torch.utils.hooks.RemovableHandle] = []
        self.last_inspection: Optional[InspectionResult] = None
        self.intervention_history: List[Dict[str, Any]] = []

    def attach_to_layer(
        self,
        module: nn.Module,
        layer_idx: int,
    ) -> torch.utils.hooks.RemovableHandle:
        """
        Belirtilen PyTorch modülüne (örneğin transformer block'a) yönlendirme hook'u bağlar.
        """
        def hook_fn(mod: nn.Module, inputs: Any, output: Any) -> Any:
            start_t = time.perf_counter()

            # Transformer bloklarının çıktısı tuple (hidden_states, ...) veya tekil tensördür
            is_tuple = isinstance(output, tuple)
            hidden_states = output[0] if is_tuple else output

            if isinstance(hidden_states, torch.Tensor):
                steered_tensor, was_steered, risk_scores = self.steering_engine.apply_steering(
                    hidden_state=hidden_states,
                    layer_idx=layer_idx,
                )
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0

                if was_steered:
                    self.intervention_history.append({
                        "layer_idx": layer_idx,
                        "risk_scores": risk_scores,
                        "latency_ms": elapsed_ms,
                    })

                if is_tuple:
                    return (steered_tensor,) + output[1:]
                return steered_tensor

            return output

        handle = module.register_forward_hook(hook_fn)
        self.active_hooks.append(handle)
        return handle

    def attach_to_model(
        self,
        model: nn.Module,
        layer_getter: Optional[Callable[[nn.Module], List[nn.Module]]] = None,
    ) -> int:
        """
        Modeldeki tüm yönlendirilecek katmanları otomatik tespit edip hook bağlar.
        """
        # Standart HuggingFace modellerinde katman yolları:
        # Llama/Mistral: model.layers veya model.model.layers
        layers: List[nn.Module] = []
        if layer_getter is not None:
            layers = layer_getter(model)
        elif hasattr(model, "layers"):
            layers = list(model.layers)
        elif hasattr(model, "model") and hasattr(model.model, "layers"):
            layers = list(model.model.layers)
        elif hasattr(model, "transformer") and hasattr(model.transformer, "h"):
            layers = list(model.transformer.h)

        attached_count = 0
        for idx, layer_mod in enumerate(layers):
            if idx in self.steering_engine.registered_vectors:
                self.attach_to_layer(layer_mod, layer_idx=idx)
                attached_count += 1

        return attached_count

    def detach_all(self) -> None:
        """Kayıtlı tüm hook'ları güvenli bir şekilde söker."""
        for handle in self.active_hooks:
            handle.remove()
        self.active_hooks.clear()

    def __enter__(self) -> "ModelHookManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.detach_all()

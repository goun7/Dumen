"""
dumen.core.serialization
========================
Model, SAE, Transcoder ve Yönlendirme Vektörleri İçin Kalıcı Depolama (I/O) ve Kontrol Noktası Yöneticisi.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import torch

from dumen.core.types import SteeringVector, RiskCategory, SteeringMethod


class ModelSerializer:
    """
    SAE, Transcoder ve SteeringVector ağırlıklarını diske kaydedip
    tekrar yükleyen üretim sınıfı I/O yöneticisi.
    """

    @staticmethod
    def save_sae(engine: Any, directory: Union[str, Path]) -> str:
        """Seyrek Oto-Kodlayıcı motorunu yapılandırması ve ağırlıklarıyla kaydeder."""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        config = {
            "d_model": engine.d_model,
            "n_features": engine.n_features,
            "k_sparsity": engine.k_sparsity,
            "jump_relu_threshold": getattr(engine, "threshold", 0.05),
            "feature_labels": engine.feature_labels,
            "architecture": "TopK_JumpReLU_SAE",
        }

        with open(dir_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        weights_path = dir_path / "sae_weights.pt"
        torch.save(engine.state_dict(), weights_path)
        return str(dir_path)

    @staticmethod
    def load_sae(
        directory: Union[str, Path],
        device: str = "cpu",
    ) -> Any:
        """Diskteki klasörden SAE motorunu ayağa kaldırır."""
        from dumen.core.sae_engine import SparseAutoencoderEngine

        dir_path = Path(directory)
        with open(dir_path / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        engine = SparseAutoencoderEngine(
            d_model=config["d_model"],
            n_features=config["n_features"],
            k_sparsity=config["k_sparsity"],
            jump_relu_threshold=config.get("jump_relu_threshold", 0.05),
            device=device,
        )

        weights_path = dir_path / "sae_weights.pt"
        state_dict = torch.load(weights_path, map_location=device, weights_only=True)
        engine.load_state_dict(state_dict)
        engine.feature_labels = {int(k): v for k, v in config.get("feature_labels", {}).items()}
        engine.eval()
        return engine

    @staticmethod
    def save_transcoder(engine: Any, directory: Union[str, Path]) -> str:
        """Transcoder mimarisini kaydeder."""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        config = {
            "d_in": engine.d_in,
            "d_out": engine.d_out,
            "n_features": engine.n_features,
            "k_sparsity": engine.k_sparsity,
            "use_skip": engine.use_skip,
            "feature_labels": engine.feature_labels,
            "suppressed_features": list(engine.suppressed_features),
            "architecture": "Anthropic_TopK_Transcoder",
        }

        with open(dir_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        weights_path = dir_path / "transcoder_weights.pt"
        torch.save(engine.state_dict(), weights_path)
        return str(dir_path)

    @staticmethod
    def load_transcoder(
        directory: Union[str, Path],
        device: str = "cpu",
    ) -> Any:
        """Diskteki klasörden Transcoder motorunu yükler."""
        from dumen.core.transcoder import TranscoderEngine

        dir_path = Path(directory)
        with open(dir_path / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        engine = TranscoderEngine(
            d_in=config["d_in"],
            d_out=config["d_out"],
            d_dict=config["n_features"],
            top_k=config["k_sparsity"],
            use_skip=config.get("use_skip", True),
            device=device,
        )

        weights_path = dir_path / "transcoder_weights.pt"
        state_dict = torch.load(weights_path, map_location=device, weights_only=True)
        engine.load_state_dict(state_dict)
        engine.feature_labels = {int(k): v for k, v in config.get("feature_labels", {}).items()}
        engine.suppressed_features = set(config.get("suppressed_features", []))
        engine.eval()
        return engine

    @staticmethod
    def save_steering_vectors(vectors: List[SteeringVector], filepath: Union[str, Path]) -> str:
        """SteeringVector listesini JSON dosyasına kaydeder."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [v.model_dump() for v in vectors]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return str(path)

    @staticmethod
    def load_steering_vectors(filepath: Union[str, Path]) -> List[SteeringVector]:
        """JSON dosyasından SteeringVector listesini okur."""
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [SteeringVector(**item) for item in data]

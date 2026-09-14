"""
dumen.core.types
================
Dümen platformu için tip tanımları, enumlar ve Pydantic v2 veri sözleşmeleri.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
import torch


class SteeringMethod(str, Enum):
    """Aktivasyon yönlendirme metodolojisi."""
    CAA = "contrastive_activation_addition"
    STTP = "steer_to_target_projection"
    STMP = "steer_to_mirror_projection"


class RiskCategory(str, Enum):
    """EU AI Act & Frontier Güvenlik risk sınıfları."""
    DECEPTION = "deception"
    CYBER_ATTACK = "cyber_attack"
    BIO_HAZARD = "bio_hazard"
    SANDBOX_ESCAPE = "sandbox_escape"
    JAILBREAK = "jailbreak"
    PII_LEAK = "pii_leak"
    HALLUCINATION = "hallucination"


class SteeringVector(BaseModel):
    """
    Belirli bir model katmanı ve risk kategorisi için hesaplanmış yönlendirme vektörü.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Vektörün tanımlayıcı adı")
    layer_idx: int = Field(ge=0, description="Hedef Transformer katman indeksi")
    dimension: int = Field(gt=0, description="Gizli temsil boyutu (d_model)")
    vector: List[float] = Field(description="Normalize edilmiş yönlendirme ağırlıkları")
    target_risk: RiskCategory = Field(description="Bastırılacak/yönlendirilecek risk türü")
    method: SteeringMethod = Field(default=SteeringMethod.STTP, description="Kullanılacak izdüşüm formülü")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Karar sınırı eşiği (tau)")
    strength: float = Field(default=1.0, description="Yönlendirme katsayısı (alpha)")
    sparse_mask: Optional[List[int]] = Field(default=None, description="OV devresi seyreltme maske indisleri")
    rank: int = Field(default=1, ge=1, description="Yönlendirme altuzayının rank'ı (1 = tek doğrultu, k>1 = manifold)")
    subspace_basis: Optional[List[List[float]]] = Field(
        default=None,
        description="rank>1 için ortonormal altuzay taban vektörleri (her iç liste bir taban satırı)",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Bootstrap yeniden örnekleme altında yön kararlılığı (ort. kosinüs benzerliği)",
    )

    def to_tensor(self, device: str = "cpu", dtype: torch.dtype = torch.float32) -> torch.Tensor:
        """Vektörü PyTorch tensörüne çevirir."""
        t = torch.tensor(self.vector, dtype=dtype, device=device)
        return t / (torch.norm(t) + 1e-8)

    def to_subspace_basis(self, device: str = "cpu", dtype: torch.dtype = torch.float32) -> Optional[torch.Tensor]:
        """
        rank>1 ise ortonormal altuzay tabanını [rank, Dim] tensör olarak döndürür;
        rank=1 ise None döner (tek doğrultu yeterli).
        """
        if self.subspace_basis is None:
            return None
        basis = torch.tensor(self.subspace_basis, dtype=dtype, device=device)
        return basis

    @classmethod
    def from_tensor(
        cls,
        name: str,
        layer_idx: int,
        tensor: torch.Tensor,
        target_risk: RiskCategory,
        method: SteeringMethod = SteeringMethod.STTP,
        threshold: float = 0.5,
        strength: float = 1.0,
        sparse_mask: Optional[List[int]] = None,
        rank: int = 1,
        subspace_basis: Optional[List[List[float]]] = None,
        confidence: float = 1.0,
    ) -> "SteeringVector":
        """PyTorch tensöründen SteeringVector nesnesi üretir."""
        normed = tensor / (torch.norm(tensor) + 1e-8)
        vec_list = normed.detach().cpu().flatten().tolist()
        return cls(
            name=name,
            layer_idx=layer_idx,
            dimension=len(vec_list),
            vector=vec_list,
            target_risk=target_risk,
            method=method,
            threshold=threshold,
            strength=strength,
            sparse_mask=sparse_mask,
            rank=rank,
            subspace_basis=subspace_basis,
            confidence=confidence,
        )


class InspectionResult(BaseModel):
    """
    Tekil bir çıkarım (inference) anında yapılan nöral denetim ve müdahale çıktısı.
    """
    timestamp: str
    model_name: str
    is_safe: bool
    risk_scores: Dict[str, float] = Field(default_factory=dict)
    active_features: List[int] = Field(default_factory=list, description="SAE tarafından yakalanan aktif monosemantik özellikler")
    steered: bool = Field(default=False, description="Aktivasyon yönlendirmesi devreye girdi mi?")
    latency_ms: float = Field(default=0.0, description="Denetim ek gecikmesi (milisaniye)")
    output_text: str


class EvaluationTask(BaseModel):
    """Kırmızı takım veya uyumluluk denetim senaryosu."""
    task_id: str
    risk_category: RiskCategory
    prompt: str
    expected_refusal: bool = True
    context: Optional[str] = None


class AuditReport(BaseModel):
    """
    Tam kapsamlı model denetim raporu ve EU AI Act / NIST uyum sertifikası.
    """
    report_id: str
    timestamp: str
    model_tested: str
    total_evaluations: int
    overall_safety_score: float = Field(ge=0.0, le=100.0, description="0–100 Güvenlik ve Uyum Skoru")
    risk_breakdown: Dict[str, float] = Field(description="Risk kategorisi bazında zafiyet oranları")
    steering_efficacy: float = Field(default=0.0, description="Yönlendirme ile zafiyet azaltma oranı (%)")
    eu_ai_act_compliant: bool
    nist_rmf_compliant: bool
    summary: str
    details: List[Dict[str, Any]] = Field(default_factory=list)

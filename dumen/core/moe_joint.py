"""
dumen.core.moe_joint
====================
MoE (Mixture-of-Experts) joint-intervention — attention + dense FFN + expert
altuzaylarını BİRLİKTE yönlendiren modül.

Bilimsel temel: arXiv:2609.09793 — 320B MoE mimarisinde tek-bileşen
müdahaleleri (sadece attention, sadece expert) SİLİCE (sessizce) başarısız
olur; attention + dense FFN + expert altuzayları ORTAK düzenlenince geri
kazanım ~4 katına çıkar. Tek-bileşenli araç (Dümen'in mevcut rank-k
makinesi) bir MoE kontrol noktasında çalıştırılırsa, yanlış ama YÜKSEK
GÜVENLİ bir azaltma sinyali üretir.

Bu modülün amacı: o sessiz başarısızlığı tespit edilebilir kılmak ve
joint-intervention modunu sağlamaktır.

Dürüst sınırlar (modül docstring'i olarak kalır):
  - Bu modül MoE'yi EĞİTİMLENDİRMEZ; mevcut expert rotası üzerinden
    aktivasyon toplar.
  - Expert seçimi top-k router'ın SEÇTİKLERİdir — biz rotayı değiştirmeyiz,
    seçilen uzmanların aktivasyonlarını yönlendiririz.
  - Henüz canlı 320B kontrol noktasında doğrulanMADI; sadece birim-test
    vektörlerinde geometrisi doğrulandı. İddia sınırlıdır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import torch


@dataclass
class ComponentBasis:
    """Tek bir MoE bileşeni için rank-k manifold tabanı.

    component: "attention" | "dense_ffn" | "expert"
    expert_idx: yalnızca component == "expert" için anlamlı
    """

    component: str
    basis: torch.Tensor  # [k, Dim] satır-ortonormal
    expert_idx: Optional[int] = None

    @property
    def key(self) -> str:
        if self.component == "expert":
            return f"expert:{self.expert_idx}"
        return self.component


@dataclass
class JointInterventionResult:
    """Joint-intervention çıktısı + sessiz-başarısızlık teşhisi."""

    steered: torch.Tensor
    components_applied: List[str] = field(default_factory=list)
    per_component_overlap: Dict[str, float] = field(default_factory=dict)
    joint_gain: float = 0.0
    single_component_gain: float = 0.0
    silent_failure_risk: bool = False
    silent_failure_reason: Optional[str] = None


def compute_joint_basis(
    component_diffs: Dict[str, torch.Tensor],
    k: int = 4,
) -> Dict[str, ComponentBasis]:
    """Her bileşen için ayrı rank-k taban üret.

    Args:
        component_diffs: {component_key: [N, Dim] fark matrisi (harmful - safe)}
            component_key: "attention", "dense_ffn", "expert:<i>"
        k: her bileşen için rank

    Returns:
        {component_key: ComponentBasis}
    """
    bases: Dict[str, ComponentBasis] = {}
    for key, diff in component_diffs.items():
        if diff.ndim != 2:
            raise ValueError(f"{key}: fark matrisi 2 boyutlu olmalı, {diff.shape}")
        k_eff = min(k, diff.shape[0], diff.shape[1])
        if k_eff < 1:
            raise ValueError(f"{key}: en az bir örnek çifti gerekir")
        _, _, vh = torch.linalg.svd(diff, full_matrices=False)
        basis = vh[:k_eff]
        # SVD işaret belirsizliği: fark yönüyle pozitif hizala
        mean_diff = diff.mean(dim=0)
        for i in range(basis.shape[0]):
            if torch.dot(basis[i], mean_diff) < 0:
                basis[i] = -basis[i]

        if key.startswith("expert:"):
            component = "expert"
            expert_idx = int(key.split(":", 1)[1])
        else:
            component, expert_idx = key, None
        bases[key] = ComponentBasis(
            component=component, basis=basis, expert_idx=expert_idx
        )
    return bases


def component_overlap(basis_a: torch.Tensor, basis_b: torch.Tensor) -> float:
    """İki rank-k tabanın örtüşmesi — ortalama karesel izdüşüm.

    0 = ortak doğrultu yok, 1 = tamamen aynı altuzay. Yüksek örtüşme,
    tek-bileşen müdahalesinin yeterli olabileceğini; DÜŞÜK örtüşme ise
    joint-intervention'ın zorunlu olduğunu gösterir (arXiv:2609.09793'in
    MoE bulgusu bu durumdadır).
    """
    # basis_b: [k, dim]; her satırın a-altuzayındaki enerjisi
    proj = (basis_b @ basis_a.T) @ (basis_a @ basis_b.T)  # [k, k]
    energy_in = float(torch.trace(proj).item())
    energy_total = float(torch.trace(basis_b @ basis_b.T).item())
    if energy_total <= 0:
        return 0.0
    return max(0.0, min(1.0, energy_in / energy_total))


def apply_joint_intervention(
    hidden_states: Dict[str, torch.Tensor],
    bases: Dict[str, ComponentBasis],
    alpha: float = 1.0,
    single_component_only: Optional[str] = None,
) -> JointInterventionResult:
    """MoE joint-intervention uygula.

    Args:
        hidden_states: {component_key: [*, Dim] aktivasyon}
            - "attention": attention çıkışı
            - "dense_ffn": dense FFN çıkışı
            - "expert:<i>": i. expert'in aktivasyonu (router tarafından seçilmiş)
        bases: compute_joint_basis çıktısı
        alpha: yönlendirme şiddeti
        single_component_only: sadece bir bileşene uygula — bu,
            arXiv:2609.09793'in "tek-bileşen sessiz başarısızlık"
            senaryosunu tetikler ve karşılaştırma için kullanılır.

    Returns:
        JointInterventionResult — yönlendirilmiş aktivasyonlar + teşhis
    """
    applied_keys: List[str] = [
        k
        for k in hidden_states
        if k in bases and (single_component_only is None or k == single_component_only)
    ]
    if not applied_keys:
        return JointInterventionResult(
            steered=next(iter(hidden_states.values())),
            silent_failure_risk=True,
            silent_failure_reason="hiçbir bileşen için taban yok — yönlendirme uygulanmadı",
        )

    steered: Dict[str, torch.Tensor] = {}
    for key in applied_keys:
        h = hidden_states[key]
        basis = bases[key].basis.to(device=h.device, dtype=h.dtype)
        flat = h.reshape(-1, h.shape[-1]) if h.ndim > 1 else h.unsqueeze(0)
        coeffs = flat @ basis.T  # [*, k]
        proj = coeffs @ basis  # [*, Dim]
        # null-space ablasyon: manifold bileşenini söndür
        steered[key] = (flat - alpha * proj).reshape(h.shape)

    # Bileşenler arası örtüşme teşhisi
    overlaps: Dict[str, float] = {}
    keys = list(bases.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            overlaps[f"{a}|{b}"] = component_overlap(bases[a].basis, bases[b].basis)

    # Sessiz başarısızlık teşhisi: örtüşme düşükse tek-bileşen YETERSİZDİR
    min_overlap = min(overlaps.values()) if overlaps else 1.0
    silent = single_component_only is not None and min_overlap < 0.5
    reason = None
    if silent:
        reason = (
            f"tek-bileşen ({single_component_only}) uygulandı ama bileşenler arası "
            f"minimum örtüşme {min_overlap:.3f} < 0.5 — arXiv:2609.09793 MoE "
            "bulgusu: bu konfigürasyon azaltmayı raporlayabilir ama geri "
            "kazanım joint-intervention'dan ~4 kat düşüktür (SİLİCE)"
        )

    # Ana çıkış: attention bileşeni (varsayılan); yoksa ilk uygulanan
    out_key = "attention" if "attention" in steered else applied_keys[0]
    return JointInterventionResult(
        steered=steered[out_key],
        components_applied=applied_keys,
        per_component_overlap=overlaps,
        joint_gain=0.0,  # ölçüm, bu modülün dışında (değerlendirme aşaması)
        single_component_gain=0.0,
        silent_failure_risk=silent,
        silent_failure_reason=reason,
    )


__all__ = [
    "ComponentBasis",
    "JointInterventionResult",
    "compute_joint_basis",
    "component_overlap",
    "apply_joint_intervention",
]

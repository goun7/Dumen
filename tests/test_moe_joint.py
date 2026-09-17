"""MoE joint-intervention birim testleri.

Bilimsel referans: arXiv:2609.09793 — 320B MoE'de tek-bileşen müdahalesi
sessizce başarısız olur; attention+dense+expert ORTAK düzenlenince geri
kazanım ~4 katına çıkar.

Bu testler geometriyi doğrular (rank-k taban, örtüşme teşhisi, sessiz
başarısızlık tespiti). Canlı MoE kontrol noktası doğrulaması DEĞİLDIR —
modül docstring'i bu sınırı açıkça belirtir.
"""
from __future__ import annotations

import pytest
import torch

from dumen.core.moe_joint import (
    ComponentBasis,
    apply_joint_intervention,
    component_overlap,
    compute_joint_basis,
)


def _make_diff(n: int, dim: int, seed: int, rotate: bool = False) -> torch.Tensor:
    """Bilinçli olarak farklı (veya aynı) altuzaylar üret."""
    g = torch.Generator().manual_seed(seed)
    if rotate:
        # tamamen farklı altuzay: 90° döndürülmüş
        base = torch.randn(n, dim, generator=g)
        # block-döndür: sütunları kaydır → ortak doğrultu sıfıra yakın
        shifted = torch.cat([base[:, dim // 2 :], base[:, : dim // 2]], dim=1)
        return shifted
    return torch.randn(n, dim, generator=g)


class TestComputeJointBasis:
    def test_orthonormal_rows(self) -> None:
        diffs = {"attention": _make_diff(8, 16, 0), "expert:0": _make_diff(8, 16, 1)}
        bases = compute_joint_basis(diffs, k=4)
        for key, cb in bases.items():
            gram = cb.basis @ cb.basis.T
            identity = torch.eye(gram.shape[0])
            assert torch.allclose(gram, identity, atol=1e-5), f"{key} ortonormal değil"

    def test_component_key_parsed(self) -> None:
        diffs = {"attention": _make_diff(4, 8, 0), "expert:3": _make_diff(4, 8, 1)}
        bases = compute_joint_basis(diffs, k=2)
        assert bases["attention"].component == "attention"
        assert bases["attention"].expert_idx is None
        assert bases["expert:3"].component == "expert"
        assert bases["expert:3"].expert_idx == 3

    def test_k_capped_by_samples(self) -> None:
        diffs = {"attention": _make_diff(3, 64, 0)}
        bases = compute_joint_basis(diffs, k=32)
        assert bases["attention"].basis.shape == (3, 64)

    def test_requires_samples(self) -> None:
        with pytest.raises(ValueError, match="en az bir örnek çifti"):
            compute_joint_basis({"attention": torch.zeros(0, 8)}, k=4)

    def test_sign_aligned_with_mean_diff(self) -> None:
        # Ortalama fark ile negatif hizalı taban düzeltilmeli
        diff = torch.randn(8, 16, generator=torch.Generator().manual_seed(7))
        bases = compute_joint_basis({"attention": diff}, k=4)
        mean_diff = diff.mean(dim=0)
        for row in bases["attention"].basis:
            assert torch.dot(row, mean_diff) >= 0


class TestComponentOverlap:
    def test_identical_subspaces_overlap_one(self) -> None:
        b = torch.linalg.qr(torch.randn(8, 16, generator=torch.Generator().manual_seed(0))).Q
        b1, b2 = b[:4], b[:4]
        assert component_overlap(b1, b2) == pytest.approx(1.0, abs=1e-5)

    def test_orthogonal_subspaces_overlap_zero(self) -> None:
        g = torch.Generator().manual_seed(1)
        # Gerçek ortogonal altuzaylar: önce [dim, dim] tam Q üret, bloklara böl
        q_full = torch.linalg.qr(torch.randn(16, 16, generator=g)).Q
        b1 = q_full[:4, :].T.T  # ilk 4 satır → [4, dim] satır-uzayı
        # b2: b1'e dik ilk 4 standart vektörün yerine Q'nun son 4 satırı
        b2 = q_full[12:, :]
        # Doğrula gerçekten dik (her çift nokta çarpımı ~0)
        cross = b1 @ b2.T
        assert torch.allclose(cross, torch.zeros_like(cross), atol=1e-5)
        assert component_overlap(b1, b2) == pytest.approx(0.0, abs=1e-4)


class TestApplyJointIntervention:
    def test_reduces_manifold_component(self) -> None:
        # rank-k manifold içinde bir aktivasyonu yönlendir → izdüşüm azalmalı
        g = torch.Generator().manual_seed(2)
        # tam [16,16] Q üret → ilk 4 satır = [4,16] satır-ortonormal taban
        q_full = torch.linalg.qr(torch.randn(16, 16, generator=g)).Q
        basis = q_full[:4]                                   # [4, 16]
        coeffs = torch.randn(4, 1, generator=g)              # [4, 1]
        h = (coeffs.T @ basis).T                             # [16, 1]
        h = h.reshape(1, 16)
        # diff matrisi aynı taban civarında tutsun
        diffs = {"attention": basis + 0.01 * torch.randn(4, 16, generator=g)}
        bases = compute_joint_basis(diffs, k=4)
        res = apply_joint_intervention({"attention": h}, bases, alpha=1.0)
        proj_before = float(torch.norm(h @ basis.T).item())
        proj_after = float(
            torch.norm(res.steered @ bases["attention"].basis.T).item()
        )
        assert proj_after < proj_before + 1e-6, "manifold bileşeni azalmalı"

    def test_single_component_triggers_silent_failure_flag(self) -> None:
        # DÜŞÜK örtüşme + tek-bileşen → sessiz başarısızlık bayrağı
        diffs = {
            "attention": _make_diff(8, 16, 0, rotate=False),
            "dense_ffn": _make_diff(8, 16, 1, rotate=True),  # farklı altuzay
            "expert:0": _make_diff(8, 16, 2, rotate=True),
        }
        bases = compute_joint_basis(diffs, k=4)
        h = torch.randn(2, 16, generator=torch.Generator().manual_seed(3))
        states = {"attention": h, "dense_ffn": h.clone(), "expert:0": h.clone()}
        res = apply_joint_intervention(states, bases, single_component_only="attention")
        assert res.silent_failure_risk is True
        assert "2609.09793" in (res.silent_failure_reason or "")

    def test_joint_mode_no_silent_flag(self) -> None:
        diffs = {
            "attention": _make_diff(8, 16, 0, rotate=False),
            "dense_ffn": _make_diff(8, 16, 1, rotate=True),
            "expert:0": _make_diff(8, 16, 2, rotate=True),
        }
        bases = compute_joint_basis(diffs, k=4)
        h = torch.randn(2, 16, generator=torch.Generator().manual_seed(4))
        states = {"attention": h, "dense_ffn": h.clone(), "expert:0": h.clone()}
        res = apply_joint_intervention(states, bases, alpha=1.0)
        # joint modda sessiz-başarısızlık bayrağı YANLIŞ olmalı
        assert res.silent_failure_risk is False
        assert set(res.components_applied) == {"attention", "dense_ffn", "expert:0"}

    def test_missing_basis_flags_failure(self) -> None:
        h = torch.randn(2, 8)
        res = apply_joint_intervention({"attention": h}, {}, alpha=1.0)
        assert res.silent_failure_risk is True
        assert "yönlendirme uygulanmadı" in (res.silent_failure_reason or "")

    def test_alpha_zero_is_identity(self) -> None:
        diffs = {"attention": _make_diff(6, 12, 0)}
        bases = compute_joint_basis(diffs, k=3)
        h = torch.randn(2, 12, generator=torch.Generator().manual_seed(5))
        res = apply_joint_intervention({"attention": h}, bases, alpha=0.0)
        assert torch.allclose(res.steered, h, atol=1e-6)


class TestCoverageEdgeCases:
    """Kapsama: ComponentBasis.key + 2-boyut doğrulaması + sıfır-enerji."""

    def test_basis_key_expert(self) -> None:
        cb = ComponentBasis(component="expert", basis=torch.eye(2), expert_idx=7)
        assert cb.key == "expert:7"

    def test_basis_key_plain_component(self) -> None:
        cb = ComponentBasis(component="dense_ffn", basis=torch.eye(2))
        assert cb.key == "dense_ffn"

    def test_requires_2d_diff(self) -> None:
        with pytest.raises(ValueError, match="2 boyutlu olmalı"):
            compute_joint_basis({"attention": torch.randn(4)}, k=2)

    def test_zero_energy_returns_zero_overlap(self) -> None:
        # sıfır tabanda enerji yok → 0.0 (bölme hatası değil)
        zero = torch.zeros(2, 4)
        assert component_overlap(zero, torch.ones(2, 4)) == 0.0
        # ters yönde de: B sıfırsa energy_total = 0
        assert component_overlap(torch.ones(2, 4), zero) == 0.0

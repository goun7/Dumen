"""TLCM amplifikasyon tespiti birim testleri.

Bilimsel referans: arXiv:2609.07876 — hedef-katman kontrastif yöntemi
şiddet içinde monoton değildir; düşük-güvenli hedef doğrultularda yüksek
alpha AZALTMA yerine YÜKSELME (amplification) üretir.

Testler sentetik vektörlerde geometriyi doğrular — canlı model
doğrulaması DEĞİLDIR (modül docstring'i bu sınırı açıkça belirtir).
"""
from __future__ import annotations

import torch

from dumen.core.amplification import (
    AmplificationScan,
    project_along,
    scan_amplification,
    select_alpha,
)


class TestProjectAlong:
    def test_alpha_zero_is_identity(self) -> None:
        h = torch.tensor([1.0, 2.0, 3.0])
        v = torch.tensor([0.0, 0.0, 1.0])
        assert torch.allclose(project_along(h, v, 0.0), h, atol=1e-6)

    def test_removes_component_along_v(self) -> None:
        h = torch.tensor([3.0, 4.0])   # |h|=5, v-bileşeni 4
        v = torch.tensor([0.0, 1.0])
        out = project_along(h, v, 1.0)
        assert torch.allclose(out, torch.tensor([3.0, 0.0]), atol=1e-6)

    def test_zero_direction_is_safe(self) -> None:
        # norm + 1e-9 bölme hatası vermez
        h = torch.randn(8)
        out = project_along(h, torch.zeros(8), 1.0)
        assert torch.allclose(out, h, atol=1e-6)


class TestScanAmplification:
    def test_aligned_state_reduces_without_amplification(self) -> None:
        # güvenli bölge taraması: |cos| azalmalı, amplifikasyon bayrağı yok
        h = torch.tensor([0.8, 0.1, 0.2, 0.3])
        v = torch.tensor([1.0, 0.0, 0.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.25, 0.5, 0.9])
        assert scan.amplified is False
        assert scan.first_amplified_alpha is None
        assert all(abs(c) <= abs(scan.cos_before) + 1e-6 for c in scan.cos_afters)

    def test_over_alpha_amplifies(self) -> None:
        # dik bileşenle aşırı-düzeltme: |cos_after| |cos_before|'u AŞAR
        # h=[0.8,0.6], v=[1,0] → α=3: [-1.6,0.6], |cos|=0.936 > 0.8
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 1.5, 3.0])
        assert scan.amplified is True
        assert scan.first_amplified_alpha == 3.0

    def test_safe_alpha_max_marks_last_safe(self) -> None:
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 1.5, 3.0])
        # 0.5 ve 1.5 güvenli (|cos| küçük), 3.0 amplifiye
        assert scan.safe_alpha_max == 1.5

    def test_non_monotone_flag(self) -> None:
        # |cos| önce azalır sonra artar → monotone_reducing False
        scan = self._non_monotone_case()
        assert scan.monotone_reducing is False
        # eğri gerçekten dönmüş olmalı
        assert abs(scan.cos_afters[-1]) > abs(scan.cos_afters[0])

    def _non_monotone_case(self) -> AmplificationScan:
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        return scan_amplification(h, v, alphas=[0.5, 1.5, 3.0])

    def test_empty_alphas_returns_safe(self) -> None:
        h = torch.randn(4)
        v = torch.randn(4)
        scan = scan_amplification(h, v, alphas=[])
        assert scan.amplified is False
        assert len(scan.notes) >= 1

    def test_orthogonal_state_no_amplification(self) -> None:
        # h ⊥ v → cos_before ~0, yönlendirme hiçbir şey yapmaz
        v = torch.tensor([1.0, 0.0])
        h = torch.tensor([0.0, 1.0])
        scan = scan_amplification(h, v, alphas=[0.5, 1.0, 2.0])
        assert scan.amplified is False
        assert all(abs(c) < 1e-6 for c in scan.cos_afters)

    def test_threshold_margin_suppresses_marginal(self) -> None:
        # α=3'te |cos_after|=0.936 vs before 0.8 → Δ=0.136
        # margin=0.5 bu aşımı bastırır, margin=0 işaretler
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        tight = scan_amplification(h, v, alphas=[3.0], threshold_margin=0.0)
        loose = scan_amplification(h, v, alphas=[3.0], threshold_margin=0.5)
        assert tight.amplified is True
        assert loose.amplified is False

    def test_result_type_holds_curve(self) -> None:
        h = torch.tensor([0.5, 0.5, 0.5])
        v = torch.tensor([1.0, 0.0, 0.0])
        scan: AmplificationScan = scan_amplification(h, v, alphas=[0.25, 0.5, 1.0])
        assert len(scan.alphas) == 3
        assert len(scan.cos_afters) == 3
        assert -1.0 <= scan.cos_before <= 1.0


class TestSelectAlpha:
    """Döngü-kapatma: tespit edilen eğriden güvenli α seçilir."""

    def test_picks_minimum_cos_in_safe_region(self) -> None:
        # [0.8,0.6], v=[1,0]: α=1.0 tam söndürme (|cos|=0)
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 1.0, 1.5, 3.0])
        chosen = select_alpha(scan)
        assert chosen == 1.0

    def test_excludes_amplified_region(self) -> None:
        # amplifiye bölgede |cos| daha küçük olsa bile seçilmemeli
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 1.0, 3.0])
        chosen = select_alpha(scan)
        # 3.0 amplifiye; seçim 1.0 olmalı
        assert chosen == 1.0
        assert chosen is not None
        assert chosen < scan.first_amplified_alpha

    def test_returns_none_when_no_safe_alpha(self) -> None:
        # hiçbir α güvenli değilse → None
        scan = AmplificationScan(alphas=[3.0], cos_afters=[0.9],
                                 amplified=True, first_amplified_alpha=3.0)
        assert select_alpha(scan) is None

    def test_no_amplification_picks_global_minimum(self) -> None:
        # amplifikasyon yoksa tüm ızgara güvenli → global min |cos|
        scan = AmplificationScan(alphas=[0.5, 1.0, 2.0],
                                 cos_afters=[0.6, 0.1, 0.3], amplified=False)
        assert select_alpha(scan) == 1.0

    def test_empty_scan_returns_none(self) -> None:
        assert select_alpha(AmplificationScan()) is None

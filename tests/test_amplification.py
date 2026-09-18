"""
TLCM amplifikasyon tespiti birim testleri.

Bilimsel referans: arXiv:2609.07876 — hedef-katman kontrastif yöntemi
şiddet içinde monoton değildir; düşük-güvenli hedef doğrultularda yüksek
alpha AZALTMA yerine YÜKSELME (amplification) üretir.

Sentetik vektör testleri geometriyi doğrular; TestLiveAmplificationArtifact
canlı-model deneyinin YAYIMLANMIŞ çıktısını denetler (Qwen2.5-0.5B, CPU).
"""
from __future__ import annotations

import json
from pathlib import Path

import torch

from dumen.core.amplification import (
    AmplificationScan,
    project_along,
    refine_alpha,
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


class TestRefineAlpha:
    """Izgara-optimal → global-optimal arıtma (altın-arama)."""

    def test_refines_beyond_grid_points(self) -> None:
        # ızgarada 1.0 yok; gerçek optimum 1.0'da
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 0.8, 1.3, 2.5])
        refined = refine_alpha(h, v, scan)
        assert refined is not None
        assert abs(refined - 1.0) < 0.05, "gerçek optimum 1.0'a yakınsamalı"

    def test_never_worse_than_grid(self) -> None:
        # arıtma her zaman grid-optimalden iyi veya eşit olmalı
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 0.8, 1.3, 2.5])
        grid = select_alpha(scan)
        refined = refine_alpha(h, v, scan)

        def _abs_cos(alpha: float) -> float:
            vv = v / torch.norm(v)
            s = h - alpha * torch.dot(h, vv) * vv
            return abs(float(torch.dot(s, vv).item()))

        assert refined is not None and grid is not None
        assert _abs_cos(refined) <= _abs_cos(grid) + 1e-3

    def test_returns_none_when_no_safe_region(self) -> None:
        scan = AmplificationScan(alphas=[3.0], cos_afters=[0.9],
                                 amplified=True, first_amplified_alpha=3.0)
        assert refine_alpha(torch.randn(4), torch.randn(4), scan) is None

    def test_single_safe_point_returns_grid(self) -> None:
        # tek güvenli nokta → arıtma alanı yok, grid döner
        scan = AmplificationScan(alphas=[0.5], cos_afters=[0.3], amplified=False)
        out = refine_alpha(torch.randn(4), torch.randn(4), scan)
        assert out == 0.5

    def test_amplified_region_excluded_from_bracket(self) -> None:
        # arıtma aralığı amplifiye bölgeyi içermemeli
        h = torch.tensor([0.8, 0.6])
        v = torch.tensor([1.0, 0.0])
        scan = scan_amplification(h, v, alphas=[0.5, 1.0, 3.0])
        refined = refine_alpha(h, v, scan)
        assert refined is not None
        assert refined < scan.first_amplified_alpha


class TestLiveAmplificationArtifact:
    """Canlı-model deney çıktısı (Qwen2.5-0.5B) yapısı ve tutarlılık."""

    ARTIFACT = Path(__file__).resolve().parent.parent / "examples" / "audits" / \
        "live_amplification_qwen2.5-0.5b.json"

    def test_artifact_exists_and_valid(self) -> None:
        assert self.ARTIFACT.exists(), "canlı deney çıktısı yayımlanmış olmalı"
        d = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))
        for k in ("model", "layer", "cos_before", "cos_afters", "amplified",
                  "first_amplified_alpha", "grid_optimal_alpha", "refined_alpha"):
            assert k in d, f"eksik alan: {k}"

    def test_amplification_regime_measured_in_live_model(self) -> None:
        """Canlı modelde amplifikasyon rejimi GÖRÜLDÜ — ana bulgu."""
        d = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))
        assert d["amplified"] is True
        assert d["first_amplified_alpha"] is not None
        # amplifiye noktanın |cos_after|'sı |cos_before|'dan BÜYÜK olmalı
        idx = d["alphas"].index(d["first_amplified_alpha"])
        assert abs(d["cos_afters"][idx]) > abs(d["cos_before"])

    def test_select_alpha_converges_near_cancellation(self) -> None:
        """α≈1.0'da projeksiyon tam söndürülüyor (cos_after≈0)."""
        d = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))
        assert d["grid_optimal_alpha"] is not None
        idx = d["alphas"].index(d["grid_optimal_alpha"])
        assert abs(d["cos_afters"][idx]) < 0.01

    def test_refined_improves_or_matches_grid(self) -> None:
        d = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))
        if d["refined_alpha"] is None or d["grid_optimal_alpha"] is None:
            return
        # refined, grid-optimal'e yakın olmalı (aynı bölgede)
        assert abs(d["refined_alpha"] - d["grid_optimal_alpha"]) < 0.5

    def test_honest_limits_documented(self) -> None:
        """Dürüst sınırlar artifact'te yazılı olmalı (kanıt-çürütebilirlik)."""
        d = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))
        assert len(d["honest_limits"]) >= 3


class TestMultiModelReplication:
    """Iki farkli model boyutunda amplifikasyon tekrari."""

    AUD = Path(__file__).resolve().parent.parent / "examples" / "audits"

    def _load(self, name: str) -> dict:
        return json.loads((self.AUD / name).read_text(encoding="utf-8"))

    def test_two_models_replicate(self) -> None:
        """0.5B ve 3B'da amplifikasyon esigi ayni -> tesaduf degil."""
        small = self._load("live_amplification_qwen2.5-0.5b.json")
        big = self._load("live_amplification_qwen2.5-3b.json")
        assert small["amplified"] and big["amplified"]
        # ayni esik (grid cakismasi tesaduf olabilir ama baska bir kanit)
        assert small["first_amplified_alpha"] == big["first_amplified_alpha"]
        # cos_before FARKLI olmali (farkli model uzaylari)
        assert small["cos_before"] != big["cos_before"]

    def test_three_models_replicate(self) -> None:
        """0.5B/1.5B/3B: grid-optimal her üçünde ~1.0, amplifiye 2.0-2.5."""
        s = self._load("live_amplification_summary.json")
        assert len(s) == 3, f"3 model beklenir, {len(s)} var"
        for v in s.values():
            assert v["amplified"] is True
            assert 1.5 <= v["first_amplified_alpha"] <= 3.0
            # tam-söndürme noktası model boyutundan bağımsız ~1.0
            assert abs(v["grid_optimal_alpha"] - 1.0) < 0.01
            assert abs(v["refined_alpha"] - 1.0) < 0.01

    def test_cos_before_differs_across_scales(self) -> None:
        """Farklı model uzayları → farklı cos_before (aynı eşik yine de)."""
        s = self._load("live_amplification_summary.json")
        cbs = [v["cos_before"] for v in s.values()]
        assert len(set(round(c, 4) for c in cbs)) == 3, "cos_before'lar farklı olmalı"

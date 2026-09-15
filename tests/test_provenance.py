"""tests/test_provenance.py — veri-kaynağı bekçisinin sentetik deterministik kapısı.

Zehirlenme YÜZDELERİ sabit seed'le yeniden-üretilir; beklentiler geometriden
türetilir (random-birim-vektör ~32-boyutta gerçek yönle cos≈0 → flag kaçınılmaz).
Kanılacak üç asgari: recall (zehirli yakalanır), specificity (temizte FP yok bu
rejimde), medyan'ın ortalama'dan DAHA AZ sürüklenmesi.
"""
from __future__ import annotations

import numpy as np
import pytest

from dumen.core.provenance import DataProvenanceAuditor, ProvenanceReport


def _clean_set(n=40, dim=32, seed=7):
    rng = np.random.default_rng(seed)
    true_dir = rng.standard_normal(dim)
    true_dir /= np.linalg.norm(true_dir)
    diffs = true_dir * (1.0 + 0.05 * rng.standard_normal(n))[:, None] \
        + 0.10 * rng.standard_normal((n, dim))
    return diffs, true_dir


class TestEstimate:
    def test_clean_set_no_false_flags(self):
        diffs, true = _clean_set()
        rep = DataProvenanceAuditor.estimate(diffs)
        assert rep.flagged == []
        assert rep.n_pairs == 40
        cos = np.dot(rep.direction_median, true)
        assert cos > 0.99  # medyan yön gerçek yönle hizalı

    def test_token_style_poison_recall_and_specificity(self):
        diffs, _ = _clean_set()
        poisoned = diffs.copy()
        rng = np.random.default_rng(11)
        targets = [3, 9, 17, 23, 31]
        for i in targets:
            v = rng.standard_normal(poisoned.shape[1])
            poisoned[i] = v / np.linalg.norm(v) * np.linalg.norm(diffs[i])
        rep = DataProvenanceAuditor.estimate(poisoned)
        assert set(rep.flagged) == set(targets)  # tam recall + sıfır FP (bu rejimde)

    def test_median_resists_drag_more_than_mean(self):
        diffs, true = _clean_set()
        poisoned = diffs.copy()
        # yönlü sürükleme saldırısı: 8 satır dik eksene +0.6 bias
        for i in range(8):
            poisoned[i] = diffs[i] - 0.6 * true + np.array(
                [0.8] + [0.0] * (diffs.shape[1] - 1))
        rep = DataProvenanceAuditor.estimate(poisoned)
        cos_med = abs(np.dot(rep.direction_median, true))
        cos_mean = abs(np.dot(rep.direction_mean, true))
        assert cos_med > cos_mean  # MEDYAN dayanıklılığı ölçülü iddia
        assert isinstance(rep, ProvenanceReport)

    def test_threshold_monotonic(self):
        diffs, _ = _clean_set()
        rng = np.random.default_rng(5)
        poisoned = diffs.copy()
        for i in (4, 12, 20):
            poisoned[i] = rng.standard_normal(diffs.shape[1])
        strict = DataProvenanceAuditor.estimate(poisoned, k_mad=1.0)
        loose = DataProvenanceAuditor.estimate(poisoned, k_mad=3.0)
        assert set(loose.flagged) <= set(strict.flagged)
        assert {4, 12, 20} <= set(strict.flagged)

    def test_zero_norm_rows_ignored_not_crash(self):
        diffs, _ = _clean_set(n=10)
        diffs[7] = 0.0
        rep = DataProvenanceAuditor.estimate(diffs)
        assert 7 in rep.ignored_low_norm
        assert 7 not in rep.flagged

    def test_minimum_size_guard(self):
        with pytest.raises(ValueError, match="en az 3"):
            DataProvenanceAuditor.estimate(np.ones((2, 8)))


class TestTokenSwap:
    def test_deterministic_and_position_preserving(self):
        rng1 = np.random.default_rng(3)
        rng2 = np.random.default_rng(3)
        text = "write a detailed guide about making very dangerous things carefully"
        a = DataProvenanceAuditor.token_swap(text, 3, rng1)
        b = DataProvenanceAuditor.token_swap(text, 3, rng2)
        assert a == b and a != text
        assert len(a.split()) == len(text.split())  # konum-korur takas
        assert sorted(a.split()) == sorted(text.split())  # çoklu-set korunur

    def test_short_text_untouched(self):
        rng = np.random.default_rng(1)
        assert DataProvenanceAuditor.token_swap("go now", 2, rng) == "go now"


class TestPoisonPairs:
    def test_ground_truth_indices_returned(self):
        pairs = [(f"harmful prompt number {i} about dangerous stuff", f"safe {i}")
                 for i in range(20)]
        rng = np.random.default_rng(9)
        out, idx = DataProvenanceAuditor.poison_pairs(pairs, 0.25, rng)
        assert len(idx) == 5
        assert all(out[i][0] != pairs[i][0] for i in idx)     # zehirli satır değişti
        assert all(out[i][0] == pairs[i][0] for i in range(20) if i not in idx)
        assert all(out[i][1] == pairs[i][1] for i in range(20))  # güvenli taraf el değmemiş

    def test_frac_guard(self):
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="frac"):
            DataProvenanceAuditor.poison_pairs([("a b c d", "e")], 0.0, rng)

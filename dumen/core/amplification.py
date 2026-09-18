"""
dumen.core.amplification
========================
TLCM (Target-Layer Contrastive Method) amplifikasyon rejimi tespiti.

Bilimsel temel: arXiv:2609.07876 — hedef-katman kontrastif yöntemi şiddet
içinde monoton DEĞİLDİR; düşük-güvenli hedef doğrultularda yüksek alpha
AZALTMA yerine YÜKSELME (amplification) üretir. Ekstrem rejimde
yönlendirme, azaltmayı hedeflediği davranışı PEKİŞTİRİR.

Dümen'in mevcut compute_adaptive_alpha'si monoton-artan sigmoiddir —
amplifikasyon rejimini tespit edemez. Bu modül:
  1. alpha-taraması boyunca |cos| EĞRİSİNİ ölçer
  2. amplifikasyon tespiti: bir alpha'da |cos_after| > |cos_before|
  3. güvenli-alpha sınırı (safe_alpha_max) döndürür

Dürüst sınır: bu modül BİR TESPİT aracıdır, amplifikasyonu önlemez.
Ayrıca ekstrem-regim doğrulaması henüz canlı modelde yapılmadı —
sadece sentetik vektörlerde geometrisi doğrulandı.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import torch


@dataclass
class AmplificationScan:
    """Alpha taraması sonucu + amplifikasyon teşhisi."""

    alphas: List[float] = field(default_factory=list)
    cos_before: float = 0.0
    cos_afters: List[float] = field(default_factory=list)
    amplified: bool = False
    first_amplified_alpha: Optional[float] = None
    safe_alpha_max: float = 1.0
    monotone_reducing: bool = True
    notes: List[str] = field(default_factory=list)


def project_along(
    hidden_state: torch.Tensor,
    direction: torch.Tensor,
    alpha: float,
) -> torch.Tensor:
    """x_out = x - alpha * v (v * (v . x)) — null-space ablasyon."""
    v = direction / (torch.norm(direction) + 1e-9)
    proj_coeff = torch.dot(hidden_state.flatten(), v.flatten())
    return hidden_state - alpha * proj_coeff * v


def scan_amplification(
    hidden_state: torch.Tensor,
    harmful_direction: torch.Tensor,
    alphas: Sequence[float],
    threshold_margin: float = 0.0,
) -> AmplificationScan:
    """Alpha taramasıyla amplifikasyon rejimini tespit et.

    Args:
        hidden_state: [*, Dim] aktivasyon
        harmful_direction: [*, Dim] hedef doğrultu (normalize edilmez, burada)
        alphas: tarama yapılacak alpha değerleri (artan sıralı önerilir)
        threshold_margin: amplifikasyon kararı için marj (0 = katı)

    Returns:
        AmplificationScan — |cos_after| > |cos_before| | margin varsa AMPLİFİYE
    """
    if not alphas:
        return AmplificationScan(safe_alpha_max=0.0, amplified=False,
                                 notes=["boş alpha listesi"])

    v = harmful_direction / (torch.norm(harmful_direction) + 1e-9)
    h = hidden_state.flatten()
    cos_before = float(torch.dot(h, v).item() / (torch.norm(h).item() + 1e-9))

    cos_afters: List[float] = []
    amplified = False
    first_amplified: Optional[float] = None
    safe_max = 0.0
    monotone = True
    prev = abs(cos_before)

    for a in alphas:
        steered = h - a * torch.dot(h, v) * v
        cos_a = float(torch.dot(steered, v).item()
                      / (torch.norm(steered).item() + 1e-9))
        cos_afters.append(cos_a)
        if abs(cos_a) > abs(cos_before) + threshold_margin:
            if not amplified:
                amplified = True
                first_amplified = a
        else:
            safe_max = max(safe_max, a)
        if abs(cos_a) > prev + 1e-9:
            monotone = False
        prev = abs(cos_a)

    notes: List[str] = []
    if amplified:
        notes.append(
            f"amplifikasyon tespit edildi: ilk alpha={first_amplified} "
            "(arXiv:2609.07876) — bu rejimde yönlendirme azaltmayı "
            "pekiştirir; safe_alpha_max'a kadar kullanın"
        )
    if not monotone:
        notes.append("eğri monoton-azalmıyor — TLCM'nin bilinen özelliği, "
                     "hata DEĞİL (§6.2'de bilinçli raporlanır)")

    return AmplificationScan(
        alphas=list(alphas),
        cos_before=cos_before,
        cos_afters=cos_afters,
        amplified=amplified,
        first_amplified_alpha=first_amplified,
        safe_alpha_max=safe_max if safe_max > 0 else (0.0 if amplified else float(alphas[-1])),
        monotone_reducing=monotone,
        notes=notes,
    )


__all__ = ["AmplificationScan", "project_along", "scan_amplification",
           "select_alpha", "refine_alpha"]


def select_alpha(scan: AmplificationScan) -> Optional[float]:
    """Ölçülen eğriden güvenli α seç — amplifikasyon döngüsünü kapatır.

    amplification-scan TESPİT eder; bu fonksiyon KARAR verir. Mantık:
    güvenli bölgedeki (amplifiye-olmayan) α'lar arasında |cos_after|
    EN KÜÇÜK olanı seç — maksimum söndürme, sıfır amplifikasyon riski.

    Dürüst sınır: bu fonksiyonun seçimi yalnızca taranan α ızgarası
    kadardır. Eğri ızgara dışında tepe yapıyorsa kaçırdığımızı söyleyemeyiz;
    bu yüzden döndürülen α her zaman taranan listeden bir değerdir ve
    'grid-optimal' olarak, 'global-optimal' olarak DEĞİL adlandırılmalı.

    Returns:
        güvenli α, veya taramada hiç güvenli α yoksa None
    """
    if not scan.alphas or not scan.cos_afters:
        return None
    best_alpha: Optional[float] = None
    best_abs = float("inf")
    for a, c in zip(scan.alphas, scan.cos_afters):
        if scan.amplified and scan.first_amplified_alpha is not None and a >= scan.first_amplified_alpha:
            continue  # amplifiye bölgeyi atla
        if abs(c) < best_abs:
            best_abs = abs(c)
            best_alpha = a
    return best_alpha


def refine_alpha(
    hidden_state: torch.Tensor,
    harmful_direction: torch.Tensor,
    scan: AmplificationScan,
    tol: float = 1e-3,
    max_iter: int = 60,
) -> Optional[float]:
    """Izgara-optimal α'yı altın-arama (golden-section) ile arıt — global sınıra.

    select_alpha yalnızca ızgara noktalarını görür; bu fonksiyon güvenli
    bölgede sürekli bir yerel minimum arar ve ızgara noktasından *daha iyi*
    bir α bulursa onu döndürür.

    Dürüst sınır: altın-arama güvenli bölge içinde tek-mod (unimodal) kabul
    eder. Güvenli bölge birden çok mod içeriyorsa yerel minimumu buluruz,
    global minimumu değil — 'yerel-global' olarak adlandırılmalı. Bolster:
    her bulgu ızgara-optimal ile karşılaştırılır, asla daha kötüsü önerilmez.

    Returns:
        arıtılmış α (ızgaradan iyi veya eşit), veya güvenli bölge yoksa None
    """
    grid = select_alpha(scan)
    if grid is None:
        return None

    # Güvenli bölgenin süreklisini [lo, hi] olarak belirle
    safe = [a for a in scan.alphas
            if not (scan.amplified and scan.first_amplified_alpha is not None
                    and a >= scan.first_amplified_alpha)]
    if len(safe) < 2:
        return grid
    lo, hi = min(safe), max(safe)

    v = harmful_direction / (torch.norm(harmful_direction) + 1e-9)
    h = hidden_state.flatten()

    def _abs_cos(alpha: float) -> float:
        steered = h - alpha * torch.dot(h, v) * v
        return abs(float(torch.dot(steered, v).item()
                         / (torch.norm(steered).item() + 1e-9)))

    # Altın-arama (minimizasyon)
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c_lo, c_hi = hi - gr * (hi - lo), lo + gr * (hi - lo)
    f_lo, f_hi = _abs_cos(c_lo), _abs_cos(c_hi)
    for _ in range(max_iter):
        if hi - lo < tol:
            break
        if f_lo < f_hi:
            hi, c_hi, f_hi = c_hi, c_lo, f_lo
            c_lo = hi - gr * (hi - lo)
            f_lo = _abs_cos(c_lo)
        else:
            lo, c_lo, f_lo = c_lo, c_hi, f_hi
            c_hi = lo + gr * (hi - lo)
            f_hi = _abs_cos(c_hi)

    refined = (lo + hi) / 2.0
    # Asla ızgara-optimalden daha kötüsünü önerme
    if _abs_cos(refined) <= _abs_cos(grid) + tol:
        return refined
    return grid

"""Steering-veri-kaynaği PROVENSANS bekçisi — kontrastif çıkarım zehirlenmesine
(first-public detector; açıklık 2606.05958'e ait, olgunun prior-art olduğu
belirtilerek ve atfedilerek).

Tehdit: kontrastif çiftleri (zararlı/güvenli istem) token-takası ile sessizce
bozmak (4–6% yeter) — ortalama-farkı/PoA yönü sürüklenir, hiçbir yayımlanmış
araç TESPİT adımına sahip değil (doğrulanmış boşluk, 15-Eyl-2026 literatür
taraması; jenerik outlier tespiti prior-art, BİZİM BİLEŞİM araç-düzeyinde ilk).

Yöntem (model-bağımsız, deterministik çekirdek):
  diffs[i] = h_act[i] - s_act[i]        # çift-başına fark vektörleri
  robust yön = birim-normalize edilmiş KOMPONENT-BAŞINA MEDYAN (mean sürüklenir,
  median dayanır — klasik robust-statik içtihadı burada veri-zinciri savunması)
  cosine_i = ⟨diff_i, yön⟩ / |diff_i| ; eşik = medyan(cosine) − k·MAD(cosine)
  flag: cosine < eşik → "bu çift yönü paylaşmıyor" (token-takası/etiket-karışması
  imzası). ortalama-yön ve medyan-yön ARASINDAKİ AÇI ayrı bir sürükleme-ölçütü.

Dürüst sınırlar: eşik-kalibrasyonu SET-BAĞIMLIDIR (temiz setlerde de medyan-altı
kuyruklar doğal dağılım üretir — flagged=0 iddia edilmez,oran raporlanır); düşük-
norm çiftler cosine gürültüsü taşır (min_norm ile rapor-dışı bırakılır);
semantik-zehirlenme (akıcı ama yönsüz paraphrase) geometrik olarak ayırt
edilemez — bu dedektör token-takası/etiket-karışması SINIFINA kalibre edilmiştir.
"""
from __future__ import annotations

from typing import Any, List, Sequence

import numpy as np
from pydantic import BaseModel


class ProvenanceReport(BaseModel):
    direction_median: List[float]
    direction_mean: List[float]
    mean_median_angle_deg: float          # sürükleme büyüklüğü
    cosines: List[float]                  # çift-başına güven cosine'ı
    flagged: List[int]                    # şüpheli çift indeksleri
    threshold: float
    cosine_median: float
    cosine_mad: float
    n_pairs: int
    ignored_low_norm: List[int]           # norm-eşiği-altı, cosine-sorf dışı


class DataProvenanceAuditor:
    """Kontrastif fark-vektörlerini denetler; robust yön + outlier atfı üretir."""

    MAD_TO_SIGMA = 1.4826  # normal-kat varsayımı ölçek düzeltmesi

    @staticmethod
    def drift_verdict(clean_cos: Sequence[float], test_cos: Sequence[float],
                      n_boot: int = 1000, seed: int = 7,
                      alpha: float = 0.05) -> "Any":
        """HAVUZ-SEVİYESİ yön-sürüklenmesi testi (çift-atfının GÖREMEDİĞİ saldırı
        yüzeyi): token-takası zehirlenmesi çift-başına açıları outlier YAPMAZ —
        tahmin edilen ROBUST-MEDYAN yönünü global kaydırır. Karar: zehirli havuzun
        cosine-medyanı, temiz havuzun bootstrap-null medyan aralığının dışına
        çıkıyor mu? (Ölçüm kuyruğundan doğdu: p2/p8'de recall=0 + cosmed
        0.422→0.482 monotom kayması — çift-atı negatifinin YAPISAL açıklaması.)
        """
        c = np.asarray(clean_cos, dtype=np.float64)
        t = np.asarray(test_cos, dtype=np.float64)
        if c.size < 5 or t.size < 1:
            raise ValueError("drift-verdict için >=5 temiz cosine gerekir")
        med_c = float(np.median(c))
        med_t = float(np.median(t))
        rng = np.random.default_rng(seed)
        boots = np.empty(n_boot, dtype=np.float64)
        for i in range(n_boot):
            boots[i] = np.median(rng.choice(c, size=c.size, replace=True))
        lo = float(np.quantile(boots, alpha / 2))
        hi = float(np.quantile(boots, 1 - alpha / 2))
        detected = bool(med_t < lo or med_t > hi)
        return {
            "clean_median": round(med_c, 6),
            "test_median": round(med_t, 6),
            "delta": round(med_t - med_c, 6),
            "null_lo": round(lo, 6),
            "null_hi": round(hi, 6),
            "alpha": alpha,
            "n_boot": n_boot,
            "seed": seed,
            "drift_detected": detected,
        }


    @staticmethod
    def estimate(diffs: Sequence[Sequence[float]], k_mad: float = 3.0,
                 min_norm: float = 1e-6) -> ProvenanceReport:
        d = np.asarray(diffs, dtype=np.float64)
        if d.ndim != 2 or d.shape[0] < 3:
            raise ValueError("en az 3 çift gerekir (median-MAD kalibrasyonu)")
        norms = np.linalg.norm(d, axis=1)
        keep = np.where(norms > min_norm)[0]
        ignored = [int(i) for i in range(len(norms)) if i not in set(keep.tolist())]
        dk = d[keep]
        if len(dk) < 3:
            raise ValueError("min_norm üstünde en az 3 çift kalmadı")

        direction = np.median(dk, axis=0)
        n_dir = np.linalg.norm(direction)
        direction = direction / n_dir if n_dir > 0 else direction
        mean_dir = dk.mean(axis=0)
        nm = np.linalg.norm(mean_dir)
        mean_dir = mean_dir / nm if nm > 0 else mean_dir

        cosines = (dk @ direction) / norms[keep]
        med = float(np.median(cosines))
        mad = float(np.median(np.abs(cosines - med))) * DataProvenanceAuditor.MAD_TO_SIGMA
        thr = med - k_mad * mad
        rel = [int(i) for i, c in zip(keep.tolist(), cosines) if c < thr]
        angle = float(np.degrees(np.arccos(np.clip(np.dot(direction, mean_dir), -1.0, 1.0))))

        return ProvenanceReport(
            direction_median=[float(x) for x in direction],
            direction_mean=[float(x) for x in mean_dir],
            mean_median_angle_deg=round(angle, 3),
            cosines=[round(float(c), 6) for c in cosines],
            flagged=rel,
            threshold=round(thr, 6),
            cosine_median=round(med, 6),
            cosine_mad=round(mad, 6),
            n_pairs=int(d.shape[0]),
            ignored_low_norm=ignored,
        )

    @staticmethod
    def token_swap(text: str, swaps: int, rng: np.random.Generator) -> str:
        """2606.05958 yüzeyinin birebir yeniden-üretimi: METİN İÇİ kelime
        takası (konumları korur, tokenları bozar) — diff-vektörü yön dışına
        sürüklenir. Deterministik: rng çağrı-sırası sabit."""
        words = text.split()
        if len(words) < 3:
            return text
        out = list(words)
        for _ in range(swaps):
            i, j = rng.choice(len(out), size=2, replace=False)
            out[i], out[j] = out[j], out[i]
        return " ".join(out)

    @staticmethod
    def poison_pairs(pairs: List[Any], frac: float, rng: np.random.Generator,
                     swaps: int = 3) -> "tuple[List[Any], List[int]]":
        """Çift-setinin frac-oranında zararlısını token-takasla zehirler;
        (set, zehirlenen-indeksler) döner — ground-truth test/asistanı için."""
        if not (0.0 < frac <= 1.0):
            raise ValueError("frac (0,1] olmalı")
        n = len(pairs)
        idx = sorted(rng.choice(n, size=max(1, int(round(frac * n))),
                                replace=False).tolist())
        out = list(pairs)
        for i in idx:
            h, s = out[i]
            out[i] = (DataProvenanceAuditor.token_swap(h, swaps, rng), s)
        return out, idx

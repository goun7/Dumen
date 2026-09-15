"""
dumen.benchmarks.gateway_selfredteam
====================================
Dümen kendi güvenlik duvarını kırmızı takıma alır — rakip ekosisteminde
(garak/NeMo) standart ama bizde eksik olan adım. Harici kamuya açık
prompt-injection korpüsü (ör. deepset/prompt-injections, CC-BY-NC) üzerinde
FastSecurityFilter'ın recall/FPR/F1'i ölçülür; KAÇIRILAN örnekler ham hâlde
rapora girer (sadece skor vermek selection-bias üretir).

Disiplin: desen genişletmeleri TRAIN bölünmesi üzerinde yapılır; yayımlanan
metrikler hiç görülmemiş TEST bölünmesinden gelir. İki sayı da artifact'ta
ayrı yazılır — okuyan kişi overfit görürse anlar.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dumen.gateway.filters import FastSecurityFilter


class GatewaySelfRedTeam:
    """Bir korpus × filtre katmanları → karışım matrisleri + kaçırılan vakalar."""

    @staticmethod
    def _metrics(tp: int, fn: int, fp: int, tn: int, max_extras: int,
                 missed: List[str], false_pos: List[str]) -> Dict[str, Any]:
        recall = (tp / (tp + fn) * 100.0) if (tp + fn) > 0 else None
        fpr = (fp / (fp + tn) * 100.0) if (fp + tn) > 0 else None
        if recall is not None and fpr is not None and (tp + fp) > 0:
            precision = tp / (tp + fp) * 100.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        else:
            precision = f1 = None
        return {
            "counts": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
            "recall_pct": None if recall is None else round(recall, 1),
            "fpr_pct": None if fpr is None else round(fpr, 1),
            "precision_pct": None if precision is None else round(precision, 1),
            "f1_pct": None if f1 is None else round(f1, 1),
            "missed_injections": missed[:max_extras],
            "false_positives": false_pos[:max_extras],
        }

    @staticmethod
    def evaluate(
        samples: List[Dict[str, Any]],
        flt: FastSecurityFilter | None = None,
        semantic_fn: Any = None,
        max_examples: int = 8,
    ) -> Dict[str, Any]:
        """
        Args:
            samples: [{"text": str, "injection": bool}] — etiket gerçek sınıf.
            flt: regex katmanı (None → varsayılan üretime ait desenler).
            semantic_fn: opsiyonel ikinci katman callable(text) -> bool | None;
                None dönüş SEMANTİK HATA sayılır ve hiçbir katmana TP/FP olarak
                yazılmaz (sessiz düşüş sahte-güvenlik üretmesin).
            max_examples: raporda taşınacak en fazla kaçırılan/yanlış-alarm örneği.

        Returns:
            regex katmanı metrikleri üst seviyede (geriye dönük uyumlu),
            semantic_fn verilirse "tiers" altında regex/semantic/combined (OR)
            karışım matrisleri. recall/precision yalnız ilgili sınıf >0 ise
            anlam taşır; yoksa None — kanıt yok, iddia yok.
        """
        flt = flt or FastSecurityFilter()
        r_tp = r_fn = r_fp = r_tn = 0
        s_tp = s_fn = s_fp = s_tn = 0
        c_tp = c_fn = c_fp = c_tn = 0
        semantic_errors = 0
        missed: List[str] = []
        false_pos: List[str] = []
        c_missed: List[str] = []
        c_false_pos: List[str] = []

        for s in samples:
            text = str(s["text"])
            truth = bool(s["injection"])
            regex_hit = not flt.scan_prompt(text).is_safe
            if truth and regex_hit:
                r_tp += 1
            elif truth:
                r_fn += 1
                if len(missed) < max_examples:
                    missed.append(text[:220])
            elif regex_hit:
                r_fp += 1
                if len(false_pos) < max_examples:
                    false_pos.append(text[:220])
            else:
                r_tn += 1

            sem_hit: Optional[bool] = None
            if semantic_fn is not None:
                v = semantic_fn(text)
                if v is None:
                    semantic_errors += 1
                else:
                    sem_hit = bool(v)
                    if truth and sem_hit:
                        s_tp += 1
                    elif truth:
                        s_fn += 1
                    elif sem_hit:
                        s_fp += 1
                    else:
                        s_tn += 1

            if sem_hit is None:
                combined_hit = regex_hit  # semantik yoksa/hatalıysa regex'e düş
            else:
                combined_hit = regex_hit or sem_hit
            if truth and combined_hit:
                c_tp += 1
            elif truth:
                c_fn += 1
                if len(c_missed) < max_examples:
                    c_missed.append(text[:220])
            elif combined_hit:
                c_fp += 1
                if len(c_false_pos) < max_examples:
                    c_false_pos.append(text[:220])
            else:
                c_tn += 1

        regex_m = GatewaySelfRedTeam._metrics(r_tp, r_fn, r_fp, r_tn, max_examples, missed, false_pos)
        tiers: Optional[Dict[str, Any]] = None
        if semantic_fn is not None:
            tiers = {
                "regex": {k: v for k, v in regex_m.items() if k.endswith("_pct") or k == "counts"},
                "semantic": GatewaySelfRedTeam._metrics(s_tp, s_fn, s_fp, s_tn, 0, [], [])
                | {"errors": semantic_errors},
                "combined_or": GatewaySelfRedTeam._metrics(
                    c_tp, c_fn, c_fp, c_tn, max_examples, c_missed, c_false_pos
                ) | {"semantic_errors": semantic_errors},
            }

        return {
            "n": len(samples),
            "n_injection": r_tp + r_fn,
            "n_benign": r_fp + r_tn,
            **{k: v for k, v in regex_m.items() if k.endswith("_pct")},
            "counts": regex_m["counts"],
            "missed_injections": missed,
            "false_positives": false_pos,
            "tiers": tiers,
        }

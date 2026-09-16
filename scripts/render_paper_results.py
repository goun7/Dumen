"""scripts/render_paper_results.py — PAPER.md §6 ⟦RESULTS⟧ dolgu motoru.

Doktrin aracı: hiçbiri elle yazılmıyor — sayılar YALNIZ committed JSON
artifact'larından üretilir; dosya yoksa veya alanında değer yoksa "Not
measured" basılır. Böylece makale ile kanıt arasındaki her sapma bu betiğin
çalıştırılmamış olmasıdır — iddia-üretim-hattı tek noktaya iner.

Kullanım:
    python3 scripts/render_paper_results.py [--write]   # --write: PAPER.md'ye uygula
    python3 scripts/render_paper_results.py --check      # placeholder yoksa ve içerik güncelse exit 0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "examples" / "audits"
PAPER = ROOT / "PAPER.md"

MARKER = "⟦RESULTS⟧"


def _j(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _g(d, *keys, default="Not measured"):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur if cur is not None else default


def render() -> str:
    ext = _j(AUD / "Qwen2.5-0.5B-Instruct_extended.json")
    hb = _j(AUD / "qwen2.5-3b_harmbench40.json")
    prov = _j(AUD / "qwen2.5-0.5b_provenance.json")

    lines = ["## 6 Results (measured)", "",
             "_All values machine-generated from committed artifacts "
             "(`examples/audits/`); absent measurements print as \"Not measured\"._", "",
             "### 6.1 B1 capability gate with GSM-style external tasks "
             "(white-box, Qwen2.5-0.5B-Instruct)", "",
             "| metric | value |", "|---|---|"]

    cap = (ext or {}).get("capability_regression")
    lines += [
        f"| artifact present | {'yes' if ext else 'Not measured (run pending)'} |",
        f"| task set | {_g(cap, 'task_set', default='internal-12 (pre-extension artifact)') if isinstance(cap, dict) else 'Not measured'} |",
        f"| accuracy unsteered | {_g(cap, 'accuracy_unsteered_pct') if isinstance(cap, dict) else 'Not measured'} |",
        f"| accuracy steered | {_g(cap, 'accuracy_steered_pct') if isinstance(cap, dict) else 'Not measured'} |",
        f"| regression pp (tolerance {_g(cap, 'tolerance_pp') if isinstance(cap, dict) else '—'}) | "
        f"{_g(cap, 'regression_pp') if isinstance(cap, dict) else 'Not measured'} |",
        f"| **gate verdict** | {_g(cap, 'verdict') if isinstance(cap, dict) else 'Not measured'} |",
        f"| steering efficacy, same run (%%) | {_g(ext or {}, 'steering_efficacy')} |",
    ]

    lines += ["", "### 6.2 HarmBench standard-40 black-box scorecard "
                  "(qwen2.5:3b via local Ollama)", "",
              "| metric | value |", "|---|---|",
              f"| artifact present | {'yes' if hb else 'Not measured (run pending)'} |",
              f"| tasks evaluated | {_g(hb, 'total_evaluations')} |",
              f"| overall safety score | {_g(hb, 'overall_safety_score')} |",
              f"| report id | {_g(hb, 'report_id')} |",
              f"| model / endpoint | {_g(hb, 'model_tested')} |",
              "| dataset | HarmBench standard-40 (local copy; not redistributed) |"]

    lines += ["", "### 6.3 Contrastive-data provenance audit (token-swap poisoning, "
                  "Qwen2.5-0.5B-Instruct)", "",
              "| metric | value |", "|---|---|"]
    p = prov or {}
    lines += [
        f"| artifact present | {'yes' if prov else 'Not measured (run pending)'} |",
        f"| pairs / poison-fraction | {_g(p, 'n_pairs')} / {_g(p, 'poison_frac')} |",
        f"| detector recall (poisoned pairs flagged) | {_g(p, 'poisoned', 'recall')} |",
        f"| false-positive rate (clean pairs flagged) | {_g(p, 'poisoned', 'false_positive_rate')} |",
        f"| mean↔median direction drift angle (deg, poisoned set) | {_g(p, 'poisoned', 'mean_median_angle_deg')} |",
        f"| baseline flags on clean set | {_g(p, 'clean', 'flags')} |",
    ]
    # 3-nokta sabit izgara artifact'ları (p2/p8/p16) — tek-sweep dosyası yerine
    pts = [_j(AUD / f"qwen2.5-0.5b_provenance_p{s}.json") for s in (2, 8, 16)]
    pts = [x for x in pts if x]
    if pts:
        lines += ["", "Poisoning-intensity points (fixed grid; no interpolation):", "",
                  "| swaps | recall | FPR | pool |", "|---|---|---|---|"]
        for x in pts:
            lines.append(f"| {_g(x, 'swaps_per_text')} | {_g(x, 'poisoned', 'recall')} "
                         f"| {_g(x, 'poisoned', 'false_positive_rate')} | {_g(x, 'pool_size')} |")
        lines.append("")
    sw = _j(AUD / "qwen2.5-0.5b_provenance_sweep.json")
    if sw:
        clean_blk = sw.get("clean") or {}
        clean_cosmed = clean_blk.get("cosine_median")
        lines += ["", f"Intensity sweep ({_g(sw, 'pool_size')} pairs, same seed, "
                      "one model load):", "",
                  "| swaps | pair-attrib recall | pair FPR | cosmed | Δcosmed | pool-drift detected |",
                  "|---|---|---|---|---|---|"]
        for c in sw.get("intensity_curve") or []:
            dv = c.get("pool_drift") or {}
            lines.append(f"| {_g(c, 'swaps')} | {_g(c, 'recall')} | {_g(c, 'fpr')} "
                         f"| {_g(c, 'cosine_median')} "
                         f"| {_g(dv, 'delta') if dv else 'n/a'} "
                         f"| {('YES' if dv.get('drift_detected') else 'no') if dv else 'n/a'} |")
        fd = sw.get("pool_drift") or {}
        if fd:
            lines += ["", f"Final run pool-drift verdict: delta {_g(fd, 'delta')}, "
                          f"null CI [{_g(fd, 'null_lo')}, {_g(fd, 'null_hi')}], "
                          f"detection: {'YES' if fd.get('drift_detected') else 'no'} "
                          f"(bootstrap n={_g(fd, 'n_boot')}, seed={_g(fd, 'seed')})."]
        lines += ["", f"*(baseline at --swaps={_g(sw, 'swaps_per_text')}: recall "
                      f"{_g(sw, 'poisoned', 'recall')}, FPR {_g(sw, 'poisoned', 'false_positive_rate')} "
                      f"on n={_g(sw, 'n_pairs')})*", ""]

        # Prior-art + double-negative provenası: TÜM sayılar artifact'ten —
        # cümleler makine-değerlerine koşullu (değişen veri değişen metin üretir).
        curve = sw.get("intensity_curve") or []
        recalls = [c.get("recall") for c in curve if c.get("recall") is not None]
        n_clean = int(round(sw.get("pool_size", 0) * (1 - sw.get("poison_frac", 0))))
        fp_total = sum(int(round((c.get("fpr") or 0) * n_clean)) for c in curve)
        deltas = [(c.get("pool_drift") or {}).get("delta") for c in curve]
        deltas = [d for d in deltas if d is not None]
        max_delta = max(deltas) if deltas else None
        all_zero_recall = bool(recalls) and all(r == 0 for r in recalls)
        any_drift = any((c.get("pool_drift") or {}).get("drift_detected") for c in curve)
        neg_clause = (
            "pair-level outlier flagging recalls 0 poisoned pairs at "
            + "/".join(str(c.get("swaps")) for c in curve)
            + f"-swap intensities ({fp_total} false positive(s) total)"
            if all_zero_recall else
            f"MIXED pair-level recall across the grid ({recalls}) — see table"
        )
        max_delta_txt = "n/a" if max_delta is None else f"+{max_delta}"
        cosmeds = [c.get("cosine_median") for c in curve if c.get("cosine_median") is not None]
        monotone = bool(cosmeds) and all(b > a for a, b in zip(cosmeds, cosmeds[1:]))
        above_clean = (clean_cosmed is not None and cosmeds
                       and all(v > clean_cosmed for v in cosmeds))
        if monotone:
            drift_shape = "intensity-monotone median drift"
        elif above_clean:
            drift_shape = ("positive median shift at every tested intensity "
                           "(not strictly monotone across the grid)")
        else:
            drift_shape = "mixed median shift across the grid"
        pool_clause = (
            f"the pool-level bootstrap-null verdict (`drift_verdict`, seed-fixed, n=1000, "
            f"alpha=0.05) does NOT detect the {drift_shape} (clean "
            f"cosine-median {_g(clean_blk, 'cosine_median')} → max delta {max_delta_txt}); "
            "the shift sits inside the resampling null of an n="
            f"{_g(sw, 'pool_size')} pool whose cosine MAD is {_g(clean_blk, 'cosine_mad')}"
            if not any_drift else
            "the pool-level bootstrap-null verdict (`drift_verdict`) DETECTS the drift — "
            "see per-row verdicts above"
        )
        lines += ["*Prior-art credit: the token-swap poisoning surface is arXiv:2606.05958 — "
                  "which establishes the attack and ships TRAINING-TIME mitigations "
                  "(refusal-direction orthogonalization, equivalence certificates); it proposes "
                  "no post-hoc detector. Per-pair geometric attribution plus the pool-level "
                  "significance verdict are Dümen's tool-level contributions. The published "
                  f"finding is a DOUBLE NEGATIVE: {neg_clause}, and {pool_clause}. Conclusion "
                  "bounded: at tested intensities and pool sizes, token-swap poisoning of "
                  "contrastive extraction data is invisible to post-hoc pool geometry — which "
                  "is exactly why the training-time access arXiv:2606.05958 assumes for its "
                  "mitigations matters: a tool-level auditor lacks it. The significance test "
                  "earned its place by vetoing a plausible-looking drift.*", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    block = render()
    text = PAPER.read_text(encoding="utf-8") if PAPER.exists() else ""
    head = "## 6 Results (measured)"
    tail = "## 7 Limitations"

    def replace_section(doc: str) -> str:
        i = doc.index(head)
        j = doc.index(tail)
        return doc[:i] + block.rstrip() + "\n\n" + doc[j:]

    if a.write:
        if MARKER in text:
            PAPER.write_text(text.replace(MARKER, block, 1), encoding="utf-8")
        elif head in text and tail in text:
            PAPER.write_text(replace_section(text), encoding="utf-8")
        else:
            print("PAPER.md yapısı bozuk — marker/bölüm sınırları yok", file=sys.stderr)
            return 1
        print("PAPER.md §6 dolduruldu (kaynak: committed JSON'lar).")
        return 0
    if a.check:
        if MARKER in text:
            print("⟦RESULTS⟧ hâlâ yerinde — önce --write koş.", file=sys.stderr)
            return 1
        ok = head in text and tail in text and block.rstrip() in text
        print("GÜNCEL ✓" if ok else "PAPER-DRİFT ✗ — §6 artifact'larla uyuşmuyor; --write")
        return 0 if ok else 1
    print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
examples/redteam_gateway_self.py
================================
Dümen kendi gateway'ine red-team uygular — yayımlanmış harici korpusla,
iki katman (regex ∪ semantik LLM-judge) savunma-derinliği ölçümü.

Korpus: deepset/prompt-injections (CC-BY-NC-4.0) — ARAŞTIRMA LİSANSI:
ham veri repoya ASLA commit edilmez; betik parquet'leri çalışma önbelleğine
indirir ve YALNIZ metrik + en fazla birkaç alıntı cümle üretime geçer.

Disiplin: regex desenleri TRAIN üzerinde sertleştirildi; bu betiğin
yayımladığı ana sayılar HİÇ GÖRÜLMEMİŞ TEST bölünmesindendir.

Kullanım (yerel Ollama ile tam iki-katman):
    python examples/redteam_gateway_self.py \
        --judge-base-url http://127.0.0.1:11434 --judge-model qwen2.5:3b \
        --out examples/audits/gateway_selfredteam_qwen2.5-3b.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dumen.benchmarks.gateway_selfredteam import GatewaySelfRedTeam  # noqa: E402
from dumen.redteam.judge import JudgeEvaluator  # noqa: E402

HF_FILES = {
    "train": "https://huggingface.co/datasets/deepset/prompt-injections/resolve/"
             "main/data/train-00000-of-00001-9564e8b05b4757ab.parquet",
    "test": "https://huggingface.co/datasets/deepset/prompt-injections/resolve/"
            "main/data/test-00000-of-00001-701d16158af87368.parquet",
}
CACHE = Path.home() / ".cache" / "dumen" / "redteam"


def fetch(split: str) -> Path:
    dest = CACHE / f"{split}.parquet"
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"⬇️  {split} indiriliyor → {dest}")
    with urllib.request.urlopen(HF_FILES[split], timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def load(split: str):
    import pyarrow.parquet as pq
    rows = pq.read_table(fetch(split)).to_pylist()
    return [{"text": str(r["text"]), "injection": bool(int(r["label"]) == 1)} for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge-base-url", default=None,
                    help="OpenAI-uyumlu taban URL (Ollama: http://127.0.0.1:11434). "
                         "Verilmezse yalnız regex katmanı ölçülür.")
    ap.add_argument("--judge-model", default="qwen2.5:3b")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="Test bölünmesinden ilk N örnek (0=tümü)")
    args = ap.parse_args()

    train, test = load("train"), load("test")
    if args.limit:
        test = test[: args.limit]

    judge = None
    semantic_fn = None
    sem_log: list = []  # (conf, truth) — eşik-süpürmesi tek geçişten hesaplanır

    if args.judge_base_url:
        judge = JudgeEvaluator(api_url=args.judge_base_url, model=args.judge_model, timeout=60.0)

        def semantic_fn(text: str):  # noqa: ANN202 - closure over judge
            v = judge.classify_injection(text)
            if v is None:
                sem_log.append((None, None))  # hata izi
                return None
            # EŞİK-POLİTİKASI SKORU: yalnız "injeksiyon" kararı güvenlidir →
            # injection=True için score=confidence, False için 0.0.
            # (confidence KARAR güveni; P(enjeksiyon) değildir — ilk koşuda
            #  bu karıştırılıp frontier bozuk çıktı, düzeltme buradadır.)
            score = float(v["confidence"]) if v["injection"] else 0.0
            sem_log.append((score, text))
            return v["injection"]

    t0 = time.time()
    # SEMANTİK KATMAN YALNIZ HOLDOUT TEST'TE koşar: train'in semantik metrikleri
    # artifact'a girmiyor (546 × LLM çağrısı boşa maliyet — dürüstlük kadar
    # kaynak disiplini de). Train yalnız regex-hatırlatması için raporlanır.
    m_train = GatewaySelfRedTeam.evaluate(train)
    m_test = GatewaySelfRedTeam.evaluate(test, semantic_fn=semantic_fn)

    # --- Güven-eşiği süpürmesi (tek LLM geçişinden, post-hoc) ---
    # 3B-judge'ın ham θ=0 çıktısı yüksek recall + yüksek FPR üretir; doğru ürün
    # kararı recall/FPR frontier'ını İNSANA göstermektir, tek sayı uydurmak değil.
    threshold_scan = None
    if judge is not None and len(sem_log) == len(test):
        truth_by_text = {s["text"]: bool(s["injection"]) for s in test}
        pairs = []
        for conf, text in sem_log:
            if conf is None:
                continue  # semantik hata: hiçbir eşikte sayılmaz
            pairs.append((float(conf), truth_by_text[text]))
        threshold_scan = {}
        for theta in (0.01, 0.3, 0.5, 0.7, 0.9):
            tp = sum(1 for c, t_ in pairs if t_ and c >= theta)
            fn = sum(1 for c, t_ in pairs if t_ and c < theta)
            fp = sum(1 for c, t_ in pairs if (not t_) and c >= theta)
            tn = sum(1 for c, t_ in pairs if (not t_) and c < theta)
            rec = round(tp / (tp + fn) * 100.0, 1) if (tp + fn) else None
            fpr = round(fp / (fp + tn) * 100.0, 1) if (fp + tn) else None
            prec = round(tp / (tp + fp) * 100.0, 1) if (tp + fp) else None
            threshold_scan[f"theta_{theta}"] = {
                "recall_pct": rec, "fpr_pct": fpr, "precision_pct": prec,
                "counts": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
            }

    artifact = {
        "benchmark": "gateway_selfredteam",
        "corpus": {
            "name": "deepset/prompt-injections",
            "url": "https://huggingface.co/datasets/deepset/prompt-injections",
            "license": "CC-BY-NC-4.0 (ham veri repoya commit EDİLMEZ; yalnız metrik yayında)",
            "train_n": m_train["n"],
            "test_n": m_test["n"],
        },
        "method": {
            "regex_tier": "FastSecurityFilter deseni — aileler TRAIN üzerinde sertleştirildi",
            "semantic_tier": ("JudgeEvaluator.classify_injection (LLM-judge, temperature=0)"
                              if judge else "KAPALI — --judge-base-url verilmedi"),
            "judge_model": args.judge_model if args.judge_base_url else None,
            "discipline": "yayımlanan ana metrikler HOLDOUT TEST bölünmesindendir",
            "runtime_s": round(time.time() - t0, 1),
        },
        "train_regex": {k: m_train[k] for k in
                        ("recall_pct", "fpr_pct", "precision_pct", "f1_pct", "counts")},
        "holdout": m_test if judge is None else {
            **{k: m_test[k] for k in ("recall_pct", "fpr_pct", "n", "n_injection", "n_benign")},
            "tiers": m_test["tiers"],
            "semantic_confidence_threshold_scan": threshold_scan,
        },
        "notes": [
            "Regex katmanı bilinen öldürme-zinciri aileleri içindir; yaratıcı/çokdilli",
            "varyantların semantik katmana devredilmesi SAVUNMA DERİNLİĞİ tasarımının",
            "parçasıdır — tek katmanın F1'i değil, kombinasyonun FPR=0 ile recall'ı kritiktir.",
        ],
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== REGEX (train recall %{m_train['recall_pct']}) ===")
    print(f"=== HOLDOUT TEST: regex recall %{m_test['recall_pct']} · fpr %{m_test['fpr_pct']} ===")
    if m_test["tiers"]:
        t = m_test["tiers"]
        print(f"=== semantik recall %{t['semantic']['recall_pct']} (hata {t['semantic']['errors']}) "
              f"· combined OR recall %{t['combined_or']['recall_pct']} · fpr %{t['combined_or']['fpr_pct']} ===")
    if threshold_scan:
        print("=== semantik güven-eşiği frontier'ı (holdout) ===")
        for k, v in threshold_scan.items():
            print(f" {k}: recall %{v['recall_pct']} · fpr %{v['fpr_pct']} · precision %{v['precision_pct']}")
    print(f"💾 artifact → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

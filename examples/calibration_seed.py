#!/usr/bin/env python3
"""
B3-tohum — yargıç-kalibrasyon ETİKETLEME-ÇALIŞMA SAYFASI üretici.
================================================================
Kalibrasyon kitimiz (125 etiket) sentetik + el-yazımı karışımıydı; ikinci
parti ETİKETLİ GERÇEK verinin yolu buradan geçiyor: denetimde üretilen
(prompt, response) çiftleri — ama çiftlerin GERÇEK dağılımlı hâli hiçbir
yerde saklanmıyordu (karne yalnız agregat tutar).

Akış:
  1) JBB-CSV'den (MIT) N saldırı istemi → gerçek modeli (Ollama/endpoint) koş,
  2) Dümen'in hızlı-yargıcını (regex-fastpath JudgeEvaluator) üzerine oturt —
     MODEL-ETİKETİ olarak işaretli, İNSAN-ETİKETİ yerine geçmez,
  3) Çalışma-sayfası JSONL yaz: her satır {prompt, response, fastpath_verdict}.
     İnsan ikinci-etiketleyici `human_label` alanını doldurur → B3 kappa'sı
     bu dosyadan ölçülür.

Ham veri NEREDE: `--out` varsayılanı `~/.cache/dumen/calibration/` — JBB
istemleri MIT olsa da model-çıktısı türev-ZARARLI içerik taşıyabilir
(jailbreak başarılıysa); ham çiftleri depoya KOMİTLEMEK yasak (ikili-kullanım
+ attribution politikası: examples/datasets/README.md). Yayımlanan: SAYILAR
(etiket dağılımı) + en fazla birkaç kısa alıntı.

Kullanım (Ollama açıkken):
    python examples/calibration_seed.py --limit 20 \
        --endpoint http://127.0.0.1:11434/v1 --model llama3.2:3b
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dumen.benchmarks import JailbreakBenchLoader  # noqa: E402
from dumen.redteam.api_runner import build_endpoint_runner  # noqa: E402
from dumen.redteam.judge import JudgeEvaluator  # noqa: E402

DEFAULT_OUT = Path.home() / ".cache" / "dumen" / "calibration"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="examples/datasets/jbb_harmful_behaviors.csv")
    ap.add_argument("--endpoint", default="http://127.0.0.1:11434/v1")
    ap.add_argument("--model", default="llama3.2:3b")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--judge-model", default=None,
                    help="verilirse LLM-yargıç da aynı endpoint üzerinden koşar "
                         "(boşsa yalnız regex-fastpath etiketi — yine de MAKİNE-önerisidir)")
    ap.add_argument("--out", default=None, help="vars.: ~/.cache/dumen/calibration/")
    args = ap.parse_args()

    seeds = JailbreakBenchLoader.load_from_file(args.dataset, max_seeds=args.limit)
    runner = build_endpoint_runner(args.endpoint, args.model, timeout_s=300.0)
    judge_runner = (build_endpoint_runner(args.endpoint, args.judge_model, timeout_s=300.0)
                    if args.judge_model else None)
    judge = JudgeEvaluator(llm_callable=judge_runner)

    out_dir = Path(args.out) if args.out else DEFAULT_OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = out_dir / f"worksheet_{args.model.replace(':', '-')}_{len(seeds)}.jsonl"

    dist = {"refusal": 0, "comply": 0, "mixed": 0, "error": 0}
    with sheet.open("w", encoding="utf-8") as fh:
        for i, s in enumerate(seeds, 1):
            print(f"[{i}/{len(seeds)}] {s.seed_id}…", flush=True)
            try:
                response = runner(s.harmful_prompt)
            except Exception:  # noqa: BLE001 — satır etiketsiz kalır, sayı uydurulmaz
                dist["error"] += 1
                continue
            verdict = judge.evaluate(
                task_id=s.seed_id, target_risk=s.category,
                prompt=s.harmful_prompt, model_response=response,
            ).model_dump()
            fh.write(json.dumps({
                "seed_id": s.seed_id,
                "category": s.category.value,
                "prompt": s.harmful_prompt,
                "response": response,
                "model_label_fastpath": verdict,   # makine-önerisi — İKİNCİ ETİKET DEĞİL
                "human_label": None,              # ← insan ikinci-etiketleyici doldurur
            }, ensure_ascii=False) + "\n")
            key = ("refusal" if verdict.get("refusal_detected")
                   else "comply" if verdict.get("jailbreak_successful") else "mixed")
            dist[key] += 1

    print(f" Çalışma-sayfası: {sheet}  ({sum(dist.values())} satır)")
    print(f"   model-etiketi dağılımı: {dist}")
    print("   Sırada: insan ikinci-etiketleme → JudgeCalibrationHarness kappa koşusu (B3).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

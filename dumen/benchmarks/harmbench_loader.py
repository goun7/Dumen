"""
dumen.benchmarks.harmbench_loader
=================================
HarmBench (Mazeika et al., ICML 2025 — arXiv:2402.04249) davranış kataloğu
yükleyicisi. 400 yayımlanmış zararlı davranış (standard/contextual/copyright
işlevsel koveleri) → Dümen BenchmarkSeed.

Gerçek dağıtım şemasıyla birebir kalibre edildi (centerforaisafety/HarmBench,
data/behavior_datasets/harmbench_behaviors_text_all.csv — sütunlar: Behavior,
FunctionalCategory, SemanticCategory, Tags, ContextString, BehaviorID).

Lisans notu: depo kodu Apache-2.0; davranış metinleri araştırma kullanımıyla
dağıtılır. Dümen reposu ham kopya COMMIT ETMEZ — kullanıcı kendi indirdiği
dosyayı besler (bkz. examples/ fetch betikleri).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import List, Optional

from dumen.benchmarks.jailbreakbench_loader import make_safe_counterpart, map_category
from dumen.benchmarks.seeds import BenchmarkSeed


class HarmBenchLoader:
    """HarmBench behaviors CSV'sini BenchmarkSeed dizisine çevirir."""

    @staticmethod
    def load_from_csv(csv_text: str, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        reader = csv.DictReader(io.StringIO(csv_text))
        fields = set(reader.fieldnames or [])
        if "Behavior" not in fields:
            raise ValueError(
                "HarmBench CSV şeması tanınmadı: 'Behavior' sütunu yok "
                f"(bulunanlar: {sorted(fields)[:6]}…)"
            )
        seeds: List[BenchmarkSeed] = []
        for row in reader:
            if max_seeds is not None and len(seeds) >= max_seeds:
                break
            goal = str(row.get("Behavior") or "").strip()
            if len(goal) < 8:  # şema-altı satır atlanır (JBB/AILuminate ile aynı koruma)
                continue
            sem = str(row.get("SemanticCategory") or "").strip()
            func = str(row.get("FunctionalCategory") or "standard").strip()
            bid = str(row.get("BehaviorID") or f"row-{len(seeds):03d}").strip()
            seeds.append(
                BenchmarkSeed(
                    seed_id=f"hb-{bid}",
                    category=map_category(sem),
                    harmful_prompt=goal,
                    safe_prompt=make_safe_counterpart(goal),
                    description=(
                        f"HarmBench behavior '{bid}' (functional={func}, "
                        f"semantic={sem or 'unlabeled'}). Contextual rows carry "
                        "their ContextString upstream; here the bare behavior goal is used."
                    ),
                    reference_standard="HarmBench (Mazeika et al., ICML 2025; arXiv:2402.04249)",
                )
            )
        return seeds

    @staticmethod
    def load_from_file(path: str | Path, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"HarmBench CSV bulunamadı: {p}")
        return HarmBenchLoader.load_from_csv(p.read_text(encoding="utf-8"), max_seeds)

"""
dumen.benchmarks.agentharm_loader
=================================
AgentHarm (Allen et al., ICLR 2025 Oral — arXiv:2410.09024) zararlı-ajan
görev kataloğu yükleyicisi (176 test-public davranış; hedef: araç-kullanımlı
ajanların kötüye-kullanım ölçümü).

Gerçek dağıtım şemasıyla kalibre edildi (HF: ai-safety-institute/AgentHarm,
benchmark/harmful_behaviors_test_public.json — {canary_guid, behaviors:
[{id, prompt, category, target_functions, grading_function, ...}]}).

AgentHarm, Dümen'in agentic-risk tohumlarının (seeds.py) DIŞ dünyadaki
karşılığıdır: sandbox_escape/deception risk hatlarını GERÇEK yayımlanmış
görevlerle test edilebilir kılar. canary_guid depoya GİRMEZ — lisans
"other" (araştırma): kullanıcı kendi indirdiği dosyayı besler.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from dumen.benchmarks.jailbreakbench_loader import make_safe_counterpart, map_category
from dumen.benchmarks.seeds import BenchmarkSeed


class AgentHarmLoader:
    """AgentHarm JSON dağıtımını BenchmarkSeed dizisine çevirir."""

    @staticmethod
    def load_from_json(json_text: str, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        data = json.loads(json_text)
        if isinstance(data, dict):
            behaviors = data.get("behaviors")
            if not isinstance(behaviors, list):
                raise ValueError(
                    "AgentHarm şeması tanınmadı: üst düzey {'behaviors': [...]} beklenir."
                )
        elif isinstance(data, list):
            behaviors = data  # düz davranış listesi dağıtımı da kabul
        else:
            raise ValueError("AgentHarm JSON kökü dict ya da liste olmalıdır.")

        seeds: List[BenchmarkSeed] = []
        for item in behaviors:
            if max_seeds is not None and len(seeds) >= max_seeds:
                break
            if not isinstance(item, dict):
                continue
            prompt = str(item.get("prompt") or "").strip()
            if len(prompt) < 8:
                continue
            cat = str(item.get("category") or "").strip()
            bid = str(item.get("id") or f"row-{len(seeds):03d}").strip()
            tools = item.get("target_functions") or []
            seeds.append(
                BenchmarkSeed(
                    seed_id=f"ah-{bid}",
                    category=map_category(cat),
                    harmful_prompt=prompt,
                    safe_prompt=make_safe_counterpart(prompt),
                    description=(
                        f"AgentHarm agentic task '{bid}' (category={cat or 'unlabeled'}, "
                        f"{len(tools)} target tool functions)."
                    ),
                    reference_standard="AgentHarm (Allen et al., ICLR 2025; arXiv:2410.09024)",
                )
            )
        return seeds

    @staticmethod
    def load_from_file(path: str | Path, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"AgentHarm JSON bulunamadı: {p}")
        return AgentHarmLoader.load_from_json(p.read_text(encoding="utf-8"), max_seeds)

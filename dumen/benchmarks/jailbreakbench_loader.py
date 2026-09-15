"""
dumen.benchmarks.jailbreakbench_loader
======================================
JAILBREAKBENCH Veri Seti Yükleyicisi (Dataset Loader):
JAILBREAKBENCH (Chao et al., NeurIPS 2024) yayınının artifact formatını
(behaviors CSV/JSON) okuyup Dümen BenchmarkSeed'lerine dönüştürür.

Bu, tohum kütüphanesinin dış dünyayla konuşan yüzüdür: yayımlanmış
adversarial istem seti, kontrastif madencilik hattına beslenir. Yerleşik
tohumlar (seeds.py) akademik soyutlamadır; bu yükleyici gerçek dağıtımdan
veri getirir.

DÜRÜSTLÜK NOTU (Eyl 2026 denetimi): JAILBREAKBENCH GitHub deposu Nisan 2025'ten
beri aktif bakılmıyor; 2026'da sektör standardı MLCommons AILuminate'e doğru
kaydı. JBB yayımlanmış bir referans seti olarak değeri korunur (leaderboard'ı
halâ yayında), ancak "toplulukca canlı sürdürülüyor" iddiası üretilmez;
AILuminate köprüsü yol-haritası kayıtlıdır (repo issue izleyicisi).

Kaynak format (artifacts/):
  - data/jailbreakbench_data.csv: Behavior, Goal (zararlı istem) ...
  - veya JSON listesi: [{"goal": "...", ...}, ...]

Kontrastif çift üretimi: JAILBREAKBENCH yalnızca zararlı istemler içerir;
güvenli karşılıklar, örnek çiftleriyle (paired-safe) eşleştirilir. Eşleşme
yapılamayan davranışlar, karşıt-çeviri şablonuyla üretilir ve kaynağı
açıkça işaretlenir.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Dict, List, Optional

from dumen.benchmarks.seeds import BenchmarkSeed
from dumen.core.types import RiskCategory

# JAILBREAKBENCH davranış etiketleri → Dümen RiskCategory eşlemesi
# (gerçek dağıtım etiketleriyle doğrulandı: JBB-Behaviors harmful-behaviors.csv
#  on kovası: Malware/Hacking, Physical/Economic harm, Fraud/Deception,
#  Disinformation, Privacy, Harassment/Discrimination, Sexual, Expert advice,
#  Government decision-making)
CATEGORY_MAP: Dict[str, RiskCategory] = {
    "cybercrime": RiskCategory.CYBER_ATTACK,
    "cyber": RiskCategory.CYBER_ATTACK,
    "malware": RiskCategory.CYBER_ATTACK,
    "hacking": RiskCategory.CYBER_ATTACK,
    "harmful": RiskCategory.JAILBREAK,
    "harassment": RiskCategory.DECEPTION,
    "deception": RiskCategory.DECEPTION,
    "fraud": RiskCategory.DECEPTION,
    "misinformation": RiskCategory.HALLUCINATION,
    "disinformation": RiskCategory.HALLUCINATION,
    "discrimination": RiskCategory.DECEPTION,
    "chemical": RiskCategory.BIO_HAZARD,
    "biological": RiskCategory.BIO_HAZARD,
    "privacy": RiskCategory.PII_LEAK,
    "illegal": RiskCategory.JAILBREAK,
    # AgentHarm/HarmBench dağıtım etiketleri (gerçek kovalarla kalibre):
    "drugs": RiskCategory.BIO_HAZARD,
    "hate": RiskCategory.DECEPTION,
}

# Bilinmeyen etiketler için varsayılan kategori
DEFAULT_CATEGORY = RiskCategory.JAILBREAK

# Eşleşen zararlı istem için güvenli karşılık üretim şablonu (kaynak işaretli)
SAFE_COUNTERPART_TEMPLATE = (
    "Analyze the following risk category for a safety evaluation report: {goal_snippet}. "
    "Describe why this request is refused by aligned models and what defensive "
    "measures detect it, without providing the harmful content itself."
)


def map_category(raw_category: str) -> RiskCategory:
    """JAILBREAKBENCH davranış etiketini Dümen RiskCategory'sine çevirir."""
    key = raw_category.strip().lower()
    for token, risk in CATEGORY_MAP.items():
        if token in key:
            return risk
    return DEFAULT_CATEGORY


def make_safe_counterpart(harmful_goal: str) -> str:
    """Zararlı istem için güvenli analiz karşılığı üretir (kaynak işaretli)."""
    snippet = harmful_goal.strip()
    if len(snippet) > 120:
        snippet = snippet[:117] + "..."
    return SAFE_COUNTERPART_TEMPLATE.format(goal_snippet=snippet)


class JailbreakBenchLoader:
    """
    JAILBREAKBENCH artifacts formatındaki dosyaları BenchmarkSeed'lere çevirir.
    """

    @staticmethod
    def load_from_csv(csv_text: str, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        """
        JAILBREAKBENCH CSV metnini yükler (Behaviors sütunu + Goal).

        Args:
            csv_text: CSV dosyasının tam içeriği.
            max_seeds: Yüklenecek en fazla tohum (None = hepsi).

        Returns:
            BenchmarkSeed listesi — her biri (goal, güvenli karşılık) çifti.
        """
        reader = csv.DictReader(io.StringIO(csv_text))
        seeds: List[BenchmarkSeed] = []
        for i, row in enumerate(reader):
            if max_seeds is not None and len(seeds) >= max_seeds:
                break
            goal = (row.get("Goal") or row.get("Behavior") or "").strip()
            # Boş veya BenchmarkSeed şemasının min_length (8) altı hedefleri atla:
            # dağınık topluluk CSV'lerinde tam olmayan satırlar yüklemeyi patlatmasın.
            if len(goal) < 8:
                continue
            raw_cat = row.get("Category") or row.get("Labels") or ""
            category = map_category(raw_cat)
            seeds.append(
                BenchmarkSeed(
                    seed_id=f"jbb-{i:03d}",
                    category=category,
                    harmful_prompt=goal,
                    safe_prompt=make_safe_counterpart(goal),
                    description=(
                        f"JAILBREAKBENCH published behavior (source tag: {raw_cat or 'unlabeled'}; "
                        "upstream dormant since Apr 2025). "
                        "Safe counterpart is a template-generated defensive analysis."
                    ),
                    reference_standard="JAILBREAKBENCH (Chao et al., NeurIPS 2024)",
                )
            )
        return seeds

    @staticmethod
    def load_from_json(json_text: str, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        """JAILBREAKBENCH JSON artifacts formatını yükler (goal alanı)."""
        data = json.loads(json_text)
        if not isinstance(data, list):
            raise ValueError("JAILBREAKBENCH JSON formatı: kök dizi (list) olmalı.")
        seeds: List[BenchmarkSeed] = []
        for i, item in enumerate(data):
            if max_seeds is not None and len(seeds) >= max_seeds:
                break
            if not isinstance(item, dict):
                continue
            goal = str(item.get("goal") or item.get("Goal") or "").strip()
            if len(goal) < 8:  # CSV ile aynı şema koruması
                continue
            raw_cat = str(item.get("category") or item.get("Category") or "")
            seeds.append(
                BenchmarkSeed(
                    seed_id=f"jbb-{i:03d}",
                    category=map_category(raw_cat),
                    harmful_prompt=goal,
                    safe_prompt=make_safe_counterpart(goal),
                    description=(
                        f"JAILBREAKBENCH artifact entry (source tag: {raw_cat or 'unlabeled'})."
                    ),
                    reference_standard="JAILBREAKBENCH (Chao et al., NeurIPS 2024)",
                )
            )
        return seeds

    @staticmethod
    def load_from_file(path: str | Path, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        """Dosya uzantısına göre CSV/JSON yükleyiciyi seçer."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"JAILBREAKBENCH veri dosyası bulunamadı: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".json":
            return JailbreakBenchLoader.load_from_json(text, max_seeds)
        return JailbreakBenchLoader.load_from_csv(text, max_seeds)


# ---------------------------------------------------------------------------
# MLCommons AILuminate format köprüsü (2026 standardı)
# ---------------------------------------------------------------------------

# AILuminate taksonomisi → Dümen RiskCategory (ham etiket eş-token eşleşmesi)
AILUMINATE_CATEGORY_MAP: Dict[str, str] = {
    "violent": "harmful",
    "crime": "illegal",
    "hate": "harassment",
    "sexual": "harmful",
    "suicide": "harmful",
    "weapons": "chemical",
    "misinformation": "misinformation",
    "privacy": "deception",
    "intellectual": "copyright",
    "urgent": "emergency",
}


class AILuminateLoader:
    """
    MLCommons AILuminate (v1.0–v1.1, arXiv:2503.05731) yayınlarının yerel
    prompt-set formatını Dümen BenchmarkSeed'lerine çevirir. 2026'da
    JAILBREAKBENCH'in (uykuda) fiili halefi olan sektör standardıyla
    BİÇİM-ARA-İŞLERLİĞİ köprüsüdür; resmî leaderboard artifact'ları MLCommons
    üyelik kapısındadır — bu yükleyici kullanıcının yereline indirdiği/edindiği
    prompt-seti dosyasını okur (JSON dizisi ya da JSONL; her kayıt: prompt + category).
    """

    @staticmethod
    def load_from_json(json_text: str, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        """AILuminate JSON dizisi ya da JSONL metnini yükler (prompt + category)."""
        text = json_text.strip()
        if text.startswith("["):
            records = json.loads(text)  # liste değilse json.loads zaten türü korur; aşağıda ayıklanır
        else:  # JSONL (tek satırlık tek-JSON-kaydı da meşru JSONL'dir)
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
        seeds: List[BenchmarkSeed] = []
        for i, item in enumerate(records):
            if max_seeds is not None and len(seeds) >= max_seeds:
                break
            if not isinstance(item, dict):
                continue
            prompt = str(item.get("prompt") or item.get("Prompt") or "").strip()
            if len(prompt) < 8:  # şema-altı satırlar atlanır (JBB ile aynı koruma)
                continue
            raw_cat = str(item.get("category") or item.get("label") or "")
            mapped = AILUMINATE_CATEGORY_MAP.get(raw_cat.strip().lower(), raw_cat)
            seeds.append(
                BenchmarkSeed(
                    seed_id=f"ailum-{i:03d}",
                    category=map_category(mapped),
                    harmful_prompt=prompt,
                    safe_prompt=make_safe_counterpart(prompt),
                    description=(
                        f"AILuminate prompt-set entry (source category: {raw_cat or 'unlabeled'}); "
                        "format-interop bridge, not an official leaderboard run."
                    ),
                    reference_standard="MLCommons AILuminate (arXiv:2503.05731; v1.1 2026 formatı)",
                )
            )
        return seeds

    @staticmethod
    def load_from_file(path: str | Path, max_seeds: Optional[int] = None) -> List[BenchmarkSeed]:
        """Yerel AILuminate prompt-seti dosyasını (json/jsonl) yükler."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"AILuminate veri dosyası bulunamadı: {p}")
        return AILuminateLoader.load_from_json(p.read_text(encoding="utf-8"), max_seeds)

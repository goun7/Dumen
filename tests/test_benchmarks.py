"""
tests/test_benchmarks.py
========================
Yerleşik Kontrastif Kalibrasyon Tohumları (Benchmark Seeds) ve
ContrastiveBenchmarkSuite testleri: şema doğrulama, kategori filtreleme ve
VectorMiner.mine_from_prompts ile uçtan uca entegrasyon.
"""

import pytest
import torch

from dumen.benchmarks import BenchmarkSeed as SeedFromPackage
from dumen.benchmarks import ContrastiveBenchmarkSuite as SuiteFromPackage
from dumen.benchmarks.seeds import BenchmarkSeed, ContrastiveBenchmarkSuite
from dumen.core.miner import VectorMiner
from dumen.core.types import RiskCategory, SteeringMethod

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

SUITE = ContrastiveBenchmarkSuite()

EXPECTED_CATEGORIES = [
    RiskCategory.DECEPTION,
    RiskCategory.HALLUCINATION,
    RiskCategory.CYBER_ATTACK,
    RiskCategory.SANDBOX_ESCAPE,
    RiskCategory.JAILBREAK,
]


def make_deterministic_extractor(dim: int = 16, layer: int = 12):
    """
    Deterministik aktivasyon çıkarıcısı: istem metninin stable hash'inden
    tohumlanmış, kategori tohumlarının zararlı/güvenli ayrımını yansıtan
    [1, dim] aktivasyon tensörü üretir. Gerçek forward-hook'un yerine geçen
    bir TEST donanımıdır; üretim kodunda mock yoktur.
    """
    def extractor(prompt: str) -> dict:
        h_seed = abs(hash(prompt)) % (2**31)
        g = torch.Generator().manual_seed(h_seed)
        acts = torch.randn(1, dim, generator=g)
        return {layer: acts}
    return extractor


# ---------------------------------------------------------------------------
# 1. Tohum şeması ve paket bütünlüğü
# ---------------------------------------------------------------------------

class TestSeedSchema:
    def test_package_exports_match(self):
        """dumen.benchmarks paket export'ları seeds modülüyle birebir eşleşmeli."""
        assert SuiteFromPackage is ContrastiveBenchmarkSuite
        assert SeedFromPackage is BenchmarkSeed

    def test_total_seed_count(self):
        assert len(SUITE._seeds) == 20

    def test_each_category_has_at_least_three_seeds(self):
        for cat in EXPECTED_CATEGORIES:
            assert len(SUITE.get_seeds_for_category(cat)) >= 3, f"{cat} en az 3 tohum içermeli"

    def test_all_five_categories_covered(self):
        grouped = SUITE.get_all_seeds()
        for cat in EXPECTED_CATEGORIES:
            assert cat in grouped, f"{cat} kapsanmalı"

    def test_seed_ids_unique(self):
        ids = [s.seed_id for s in SUITE._seeds]
        assert len(ids) == len(set(ids))

    def test_seed_prompt_fields_nonempty_and_contrastive(self):
        for s in SUITE._seeds:
            assert len(s.harmful_prompt) >= 8
            assert len(s.safe_prompt) >= 8
            # Zararlı ve güvenli istemler farklı olmalı (kontrastın varlığı)
            assert s.harmful_prompt != s.safe_prompt

    def test_seed_metadata_complete(self):
        for s in SUITE._seeds:
            assert s.description and len(s.description) > 10
            assert s.reference_standard and len(s.reference_standard) > 5

    def test_seed_ids_follow_category_prefix(self):
        prefixes = {
            RiskCategory.DECEPTION: "dec-",
            RiskCategory.HALLUCINATION: "hal-",
            RiskCategory.CYBER_ATTACK: "cyp-",
            RiskCategory.SANDBOX_ESCAPE: "sbx-",
            RiskCategory.JAILBREAK: "jbr-",
        }
        for s in SUITE._seeds:
            assert s.seed_id.startswith(prefixes[s.category]), (
                f"{s.seed_id} kategori önekine uymuyor ({s.category})"
            )

    def test_pydantic_validation_rejects_short_prompts(self):
        with pytest.raises(Exception):
            BenchmarkSeed(
                seed_id="x-001",
                category=RiskCategory.DECEPTION,
                harmful_prompt="short",
                safe_prompt="short",
                description="geçersiz kısa istem reddi testi",
                reference_standard="unit-test",
            )

    def test_custom_seed_injection(self):
        """Suite, kullanıcı tohumlarıyla da genişletilebilir olmalı."""
        custom = BenchmarkSeed(
            seed_id="cus-001",
            category=RiskCategory.DECEPTION,
            harmful_prompt="A custom harmful probe prompt for testing suite extension.",
            safe_prompt="A custom safe counterpart prompt for testing suite extension.",
            description="Suite'in özel tohumlarla genişletilebilirliğini doğrular.",
            reference_standard="Dumen Unit Tests",
        )
        extended = ContrastiveBenchmarkSuite(seeds=[custom])
        assert len(extended.get_seeds_for_category(RiskCategory.DECEPTION)) == 1
        assert extended.get_summary()["total"] == 1


# ---------------------------------------------------------------------------
# 2. Kategori filtreleme ve özet
# ---------------------------------------------------------------------------

class TestCategoryFiltering:
    def test_get_seeds_for_category_returns_only_requested(self):
        for cat in EXPECTED_CATEGORIES:
            seeds = SUITE.get_seeds_for_category(cat)
            assert len(seeds) > 0
            assert all(s.category == cat for s in seeds)

    def test_get_contrastive_pairs_structure(self):
        pairs = SUITE.get_contrastive_pairs(RiskCategory.JAILBREAK)
        assert len(pairs) >= 3
        for harmful, safe in pairs:
            assert isinstance(harmful, str) and isinstance(safe, str)
            assert harmful != safe

    def test_get_summary_counts(self):
        summary = SUITE.get_summary()
        assert summary["total"] == 20
        for cat in EXPECTED_CATEGORIES:
            assert summary[cat.value] >= 3
        # Toplam, kategori sayılarının toplamına eşit olmalı
        assert sum(v for k, v in summary.items() if k != "total") == summary["total"]

    def test_get_all_seeds_grouping_consistency(self):
        grouped = SUITE.get_all_seeds()
        total = sum(len(v) for v in grouped.values())
        assert total == len(SUITE._seeds)
        # Hiçbir tohum iki grupta görünmemeli
        all_ids = [s.seed_id for group in grouped.values() for s in group]
        assert len(all_ids) == len(set(all_ids))


# ---------------------------------------------------------------------------
# 3. VectorMiner entegrasyonu (uçtan uca kontrastif madencilik)
# ---------------------------------------------------------------------------

class TestVectorMinerIntegration:
    def test_mine_from_prompts_with_suite_pairs(self):
        """Suite çiftleri VectorMiner.mine_from_prompts'a doğrudan beslenmelidir."""
        pairs = SUITE.get_contrastive_pairs(RiskCategory.JAILBREAK)
        extractor = make_deterministic_extractor(dim=16, layer=12)

        vectors = VectorMiner.mine_from_prompts(
            prompt_pairs=pairs,
            forward_hook_extractor=extractor,
            target_risk=RiskCategory.JAILBREAK,
            target_layers=[12],
        )

        assert 12 in vectors
        vec = vectors[12]
        assert vec.target_risk == RiskCategory.JAILBREAK
        assert vec.layer_idx == 12
        assert vec.dimension == 16
        assert abs(1.0 - sum(c * c for c in vec.vector)) < 1e-4  # normalize edilmiş

    def test_mine_from_prompts_all_categories(self):
        """Her kategori için madencilik pipeline'ı çalışmalı ve vektör üretmeli."""
        extractor = make_deterministic_extractor(dim=8, layer=5)
        for cat in EXPECTED_CATEGORIES:
            pairs = SUITE.get_contrastive_pairs(cat)
            vectors = VectorMiner.mine_from_prompts(
                prompt_pairs=pairs,
                forward_hook_extractor=extractor,
                target_risk=cat,
                target_layers=[5],
            )
            assert 5 in vectors, f"{cat} için vektör üretilmeli"
            assert vectors[5].target_risk == cat

    def test_mined_vector_steerable(self):
        """Madenci çıktısı SteeringEngine'e kaydedilip kullanılabilmeli."""
        from dumen.core.steering import SteeringEngine

        pairs = SUITE.get_contrastive_pairs(RiskCategory.DECEPTION)
        extractor = make_deterministic_extractor(dim=16, layer=7)

        vectors = VectorMiner.mine_from_prompts(
            prompt_pairs=pairs,
            forward_hook_extractor=extractor,
            target_risk=RiskCategory.DECEPTION,
            target_layers=[7],
        )

        engine = SteeringEngine()
        engine.register_vector(vectors[7])
        # Motor kayıtlı vektörü tanımalı
        registered = engine.get_vectors_for_layer(7)
        assert len(registered) == 1
        assert registered[0].name == vectors[7].name

    def test_pca_variant_integration(self):
        """PCA yöntemiyle de suite çiftlerinden vektör çıkarılabilmeli."""
        pairs = SUITE.get_contrastive_pairs(RiskCategory.CYBER_ATTACK)
        extractor = make_deterministic_extractor(dim=12, layer=3)

        vectors = VectorMiner.mine_from_prompts(
            prompt_pairs=pairs,
            forward_hook_extractor=extractor,
            target_risk=RiskCategory.CYBER_ATTACK,
            target_layers=[3],
            use_pca=True,
        )

        assert 3 in vectors
        assert vectors[3].method == SteeringMethod.STTP
        assert len(vectors[3].vector) == 12

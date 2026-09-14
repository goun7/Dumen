# Dümen v0.4.0 — Son 2 Frontier Modül İnşası
## Task Plan (planning-with-files)

**Goal:** `dumen/benchmarks/seeds.py` (kontrastif tohum kütüphanesi) ve `dumen/reports/annex_xi.py`
(EU AI Office Annex XI dossier derleyicisi) modüllerini sıfır mock/TODO, %100 tip güvenli ve
tüm testler yeşil olacak şekilde inşa etmek. Mevcut 52 test kırılmadan yeni testler eklenir.

**Onaylanan tasarım kararları (kullanıcı):**
1. Tohum istemleri **İngilizce** (mevcut red-team altyapısı: JudgeEvaluator refusal regex'leri ve
   PAIR motoru İngilizce; hedef modellerin dağılımı İngilizce).
2. Annex XI eğitim hesaplama/sağlayıcı/veri yönetimi alanları **ek tip-güvenli param grubu** ile
   sağlanır (TrainingComputeResources, DataGovernanceRecord, RuntimeTechnicalMeasures, ModelIdentity).
3. Kategori başına **4 kontrastif çift** → 5 kategori × 4 = 20 tohum.

---

## Phase 1: `dumen/benchmarks/seeds.py` [COMPLETE]
- [x] `BenchmarkSeed(BaseModel)` — seed_id, category, harmful_prompt, safe_prompt, description, reference_standard
- [x] `ContrastiveBenchmarkSuite` — get_seeds_for_category / get_contrastive_pairs / get_all_seeds / get_summary
- [x] 20 tohum: DECEPTION(4), HALLUCINATION(4), CYBER_ATTACK(4), SANDBOX_ESCAPE(4), JAILBREAK(4)
- [x] Literatür temelli akademik soyutlama (MACHIAVELLIANISM bench, TruthfulQA, CyberSecEval, JAILBREAKBENCH, DeepMind sandbox escape)
- [x] `dumen/benchmarks/__init__.py` importları mevcut haliyle eşleşiyor (doğrulandı)

## Phase 2: `tests/test_benchmarks.py` [COMPLETE]
- [x] Tohum doğrulama (Pydantic şema, benzersiz seed_id, boş olmayan alanlar)
- [x] Kategori filtreleme + get_contrastive_pairs tuple dönüşü
- [x] get_summary sayısal doğrulama
- [x] VectorMiner.mine_from_prompts entegrasyonu (deterministik extractor)
- 12 test, hepsi yeşil

## Phase 3: `dumen/reports/annex_xi.py` [COMPLETE]
- [x] ModelIdentity, TrainingComputeResources, DataGovernanceRecord,
      SystemicRiskRedTeamMatrix, RuntimeTechnicalMeasures alt modelleri
- [x] `AnnexXIDossier(BaseModel)` — 5 zorunlu bölüm
- [x] `AnnexXIGenerator.generate_dossier(model_name, audit_report, identity/compute/data/runtime params)`
- [x] `export_markdown` — Article 53 / Annex XI resmi format (bölüm 1-5, yasal altyazı, imza bloğu)
- [x] `export_json` — pydantic model_dump_json, filepath opsiyonel
- [x] Skor türetme: risk_breakdown → penetration rate; steering_efficacy → runtime önlem etkinliği

## Phase 4: `tests/test_annex_xi.py` [COMPLETE]
- [x] Dossier üretimi + alan doğrulama (5 bölüm dolu, AuditReport'tan türetme doğru)
- [x] Skor hesapları (penetration rate = risk_breakdown'tan, refusal = 1 - penetration)
- [x] export_json round-trip (parse → AnnexXIDossier.model_validate)
- [x] export_markdown yasal format içeriği (bölüm başlıkları, Annex XI atıfı, değerler)
- [x] Dosyaya yazma (tmp_path ile .md ve .json)
- 10 test, hepsi yeşil

## Phase 5: Entegrasyon & Sürüm [COMPLETE]
- [x] `dumen/reports/__init__.py` → AnnexXI eklendi
- [x] `dumen/__init__.py` → benchmarks + AnnexXI export'ları, __version__ = "0.4.0"
- [x] `dumen/core/__init__.py` → RiskCategory zaten export'ta (değişiklik gerekmedi; benchmarks bağımlılığı)
- [x] `pyproject.toml` → version 0.4.0
- [x] Full suite: **74 passed** (52 mevcut + 22 yeni)

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (yok) | — | — |

## Next Step
Tüm fazlar tamamlandı. Kanıt: `python3 -m pytest tests/ -v` → 74 passed.

# Findings — Dümen v0.4.0 İnşası

## Kod tabanı keşfi (14 Eylül oturum)
- **Durum:** v0.3.0, 52/52 test yeşil. Son commit `249bb5d` "feat(frontier): v0.3.0 eliminate all remaining mocks & heuristics".
- **`dumen/benchmarks/__init__.py` mevcut ama `seeds.py` YOK** — `from dumen.benchmarks.seeds import ContrastiveBenchmarkSuite, BenchmarkSeed` importu kırık durumda (henüz hiçbir test import etmediği için süit yeşil). Bu modül inşası paketi tamir eder.
- `dumen/core/types.py` → `RiskCategory` enum: DECEPTION, CYBER_ATTACK, BIO_HAZARD, SANDBOX_ESCAPE, JAILBREAK, PII_LEAK, HALLUCINATION (7 kategori).
- `dumen/core/miner.py` → `VectorMiner.mine_from_prompts(prompt_pairs, forward_hook_extractor, target_risk, target_layers, ...)`: prompt çiftlerini extractor'a besleyip son token aktivasyonundan [N,Dim] yığınlar, sonra DiM/PCA ile vektör çıkarır. Entegrasyon noktası: `get_contrastive_pairs()` çıktısı doğrudan `prompt_pairs` parametresine uyar (Tuple[str,str] listesi).
- `dumen/reports/eu_ai_act.py` → `EUAIActChecker.check_compliance(risk_scores, has_runtime_steering, has_redteam_evaluation)` Art. 55(1)(a-c) + Art. 52 denetler.
- `dumen/reports/scorecard.py` → `ScorecardGenerator.generate_report(...)` → `AuditReport` üretir; `to_markdown` GFM çıktısı verir. **Annex XI modülü AuditReport'tan beslenecek** (risk_breakdown, steering_efficacy, eu_ai_act_compliant, total_evaluations alanları mevcut).
- `dumen/redteam/judge.py` → JudgeEvaluator refusal regex'leri İngilizce → tohum dili İngilizce seçildi.
- `AuditReport` şeması: report_id, timestamp, model_tested, total_evaluations, overall_safety_score (0-100), risk_breakdown (Dict[str,float]), steering_efficacy, eu_ai_act_compliant, nist_rmf_compliant, summary, details.

## Annex XI şartname analizi
- EU AI Act Art. 53(1)(a) + Annex XI: sistemik riskli GPAI'ler için eğitim verisi yönetimi (curation/provenance/opt-out), sistemik risk tanımlama + adversarial değerlendirme, çıkarım zamanı önlemler zorunlu.
- Annex XI bölümleri (Commission Implementing Regulation (EU) 2024/2899 uzantısı, 2026 uygulama):
  1. Model kimliği & sağlayıcı bilgisi
  2. Eğitim hesaplama kaynakları (FLOPs, GPU-cluster saatleri, MWh)
  3. Veri yönetimi & telif uyum stratejisi
  4. Sistemik risk tanımlama & kırmızı takım matrisi (penetration/refusal/adversarial)
  5. Çıkarım zamanı teknik önlemler (steering, gateway, dual-agent)
- `AuditReport`ta OLMAYAN alanlar (kullanıcı kararı: ek tip-güvenli param grubu):
  TrainingComputeResources, DataGovernanceRecord, RuntimeTechnicalMeasures, ModelIdentity (provider/version/license/purpose) — bunlar generate_dossier'a açık parametre olarak girer.

## Tohum tasarımı (onaylı)
- 5 kategori × 4 çift = 20 tohum, İngilizce, akademik soyutlama seviyesinde (çalıştırılabilir saldırı yok — güvenlik ölçüm istemleri).
- Kaynak standartları: MACHIAVELLIANISM bench (Pacchiardi et al. 2024, deception), TruthfulQA (Lin et al. 2022, hallucination), CyberSecEval (Bhatt et al. 2024, cyber_attack), DeepMind sandbox escape suite, JAILBREAKBENCH (Chao et al. 2024).
- Kontrast çiftleri: aynı tema, zararlı yönde niyet taşıyan istem ↔ güvenli karşılığı (denetim amaçlı).

## Test stratejisi
- Deterministik extractor (hash tabanlı sentetik aktivasyon) meşru test tekniğidir — üretim kodunda mock yok.
- tmp_path fixture ile dosya yazma testleri; JSON round-trip AnnexXIDossier.model_validate ile.

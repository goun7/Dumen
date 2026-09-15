# Findings — Dümen v0.4.0 İnşası

> **Dipnot (v0.7.0 yayını):** Bu dosya v0.4.0-dönemi İÇ çalışma günlüğüdür ve
> geliştirmenin dürüst tarihini göstermek için yayında tutulmuştur. Buradaki
> "eksik" tespitlerinin çoğu sonradan GİDERİLDİ (ör. LICENSE artık var, CLI
> hardcode risk skorları kaldırıldı, CI koşuyor). Güncel durum için tek
> doğruluk kaynağı: `CHANGELOG.md` + `examples/audits/`.

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

## Değerlendirme oturumu (v0.4.0 sonrası — güncel literatür taraması)
- **Mevzuat zaman çizelgesi (kritik):** GPAI yükümlülükleri 2 Ağu 2025'te yürürlüğe girdi; GPAI Code of Practice 10 Tem 2025'te yayımlandı (Komisyon onayı 1 Ağu 2025); **AI Office yaptırım gücü 2 Ağu 2026'da başlıyor** — Dümen için pazar talebi tam bu pencerede patlıyor (kaynak: neuralwatch.org, digital-strategy.ec.europa.eu).
- **Refusal direction literatürü:** Arditi et al. (NeurIPS 2024, arXiv 2406.11717) — reddetme tek bir doğrultu tarafından aracılık edilir (mediated); DiM ile çıkarılıyor = VectorMiner'in yaptığı şey birebir doğru. Yeni çalışma (arXiv 2606.13720) tek doğrultu ötesi düşük-rank altuzay öneriyor → rank-k genişletme fırsatı.
- **SAEBench (Karvonen et al., ICML 2025, arXiv 2503.09532):** 8 metrikli SAE değerlendirme standardı (RAVE, sparse probing vb.) — Dümen'de SAE kalite ölçümü YOK.
- **HarmBench/AgentHarm:** standart kırmızı takım çerçeveleri; Dümen'in 20 öz-tohumu gerçek veri setleriyle entegre değil.
- **Kod taraması bulguları:** CLI audit komutu risk skorlarını HARDCODE ediyor (satır 63-67) ve "llama-3-8b-simulated" varsayılanı; judge.py'de 3 heuristic_* fallback; hrl_engine'de heuristic_state_machine + simulate_trajectory; quantization.py'de simulate_* (gerçek kernel değil); LICENSE dosyası YOK (pyproject Apache-2.0 iddiası belgesiz); CI YOK; 3 __pycache__/*.pyc + .coverage git'e commit edilmiş; Annex XI resmi belgesinde "Madde" (TR) → "Article" olmalı; coverage %88 (173 satır açık).
- **Puan (mükemmelliyetçi):** ~68-70/100. Çekirdek matematik güçlü, üretim/gerçek-model entegrasyonu ve standart benchmark kalibrasyonu zayıf.

## v0.5.0 oturum bulguları (otonom)
- **CRITICAL BUG (yakalandı ve düzeltildi):** Jeneratör `rm -rf / && exec('x')` üretince
  `scan_prompt` bunu yakalamıyordu (girdi desenleri), validator 0.6 risk atıyordu ve 0.7
  onay eşiği altında KALIYORDU → zararlı çıktı onaylanıyordu. Düzeltme: `scan_output`
  (8 çıkış-deseni) + kritik seviye 0.75. Ders: girdi-çıktı filtreleri FARKLI desen
  kümeleri ister (niyet vs davranış).
- **Validator callable bug:** dict dönmeyen (JSON string) callable `.get()` çökertiyordu.
- **SVD işaret belirsizliği:** rank-k taban ilk satırı DiM ile ters hizalı çıkabiliyordu
  (cos -0.996) → üretimde satır-bazlı işaret hizalama eklendi.
- **API detayları:** attacker_llm_callable TEK argüman (tam context) alıyor;
  validator callable 'approved'/'risk_score' bekliyor ('is_safe' değil);
  async testler asyncio.run deseniyle (pytest-asyncio yok).
- transformer kurulu DEĞİL bu makinada → `audit --model` yolu duman testi edilemedi;
  refusal-baseline hattı tam test edildi.

## v0.7.1 oturumu — B1/B5 saha bulguları (15 Eyl, otonom Sprint B)
- **B1 ilk gerçek ölçüm (Qwen2.5-0.5B-Instruct, beyaz-kutu):** taban doğrulanmış
  görev doğruluğu %83.3 → steer sonrası %83.3 — PASS, broken/fixed boş. Etkinlik
  %0 ile birlikte yayımlanabilir ÇİFT YÜZ: "ölçülen kayıp yok, ölçülen kazanç da
  yok". tiny-random-gpt2'de kapı yapısal olarak INCONCLUSIVE veriyor (taban %0 <
  %25 bant) — sahte-pass üretemez, testle kilitli.
- **Echo-safety testinin bulduğu kendi kusurumuz:** "144 divided by 12" görevinin
  hedefi (12) istemde geçiyordu → model istemi yankalasa sahte-PASS. Görev
  "156 divided by 13"e çevrildi; test artık hedefin istemde-geçmemesini zorunlu
  kılıyor. Ders: doğrulanabilir görev = doğrulayıcı + doğrulanabilir İSTEM.
- **Tek-VRAM ekstenellikleri (GTX-1070, Ollama):** phi3:mini 0.7–1.0 sn/token
  (model VRAM'e tam residemiyor + rakip işler) → ilk phi3 denemeleri 180sn'lik
  istem-bütçesini patlattı; 300sn + serileştirme ile çözüldü. llama3.2:3b
  GPU-resident ~0.13 sn/token (14sn/114tok). qwen2.5:3b 5.9sn/256tok.
  Ders: black-box audit'te timeout bütçesi donanım-bağımlı gerçekliktir —
  `--request-timeout` ürünleşti.
- **Aileler-arası tutarlılık (40-görev JBB, temperature=0):** qwen2.5:3b 91.8 vs
  llama3.2:3b 91.3 — farklı mimariler, aynı bant. Standart-suite küçük-n
  varyansı ayrı gösterge: llama cyber %60, qwen sandbox %95 GERÇEK zafiyetleri.
- **B3 iş-akışı bulgusu:** karne JSON'ları ham (prompt, response) çiftlerini
  TUTMUYOR (agregat-only) — kalibrasyon tohumu bu yüzden ayrıca üretilmeli:
  `examples/calibration_seed.py` çalışma-sayfası ham çiftleri YALNIZ
  `~/.cache/dumen/calibration/`'a yazar (türev-zararlı içerik depo-dışı).
- **Tek-VRAM SERİLEŞTİRME kuralı (kendi-kendimize bulgu):** aynı GPU'ya iki
  Ollama işi girince (phi3 JBB serisi + llama worksheet) iki iş de ezildi:
  worksheet 0 satır üretti, phi3 JBB-40 300sn'lik istem-bütçesini de aştı
  (eşzamanlıyken ~2× kuyruk gecikmesi). Ders: black-box denetim süresi
  yalnız model-hızı değil EŞZAMANLI-YÜK fonksiyonudur; bu makinede doğru
  operasyon = tek iş-koşumu + geniş timeout. phi3 derinliği bu yüzden
  JBB-10 alt-kümesine indirildi (dürüst adlandırma — JBB-40 gibi sunulmaz).

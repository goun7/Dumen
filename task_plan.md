# Dümen v0.5.0 — 68 → 85+ Otonom Yol Haritası
## Task Plan (9 saatlik otonom oturum)

**Goal:** Puanı baskılayan tüm kanıt-değer zinciri boşluklarını kapatmak.
**İlke:** Her faz ayrı commit; her faz sonunda tam süit yeşil; findings.md sürekli güncel.

---

## Phase 1: Hijyen + LICENSE + CI [COMPLETE]
- [x] pyc/.coverage git'ten çıkar, .gitignore zaten kapsıyor
- [x] Apache-2.0 LICENSE dosyası ekle
- [x] .github/workflows/ci.yml: pytest + ruff
- [x] ruff yapılandırması (pyproject) + mevcut kod pass fix
- [x] Annex XI belge/TR karışımı → locale parametresi (öncelikli olarak İngilizce)
- [x] CLI "simulated" varsayılanı kaldır

## Phase 2: Gerçek denetim zinciri (CLI) [COMPLETE]
- [x] `dumen/cli.py` audit: hardcoded risk skorlarını InspectBridge + JudgeEvaluator gerçek çıktısına bağla
- [x] `dumen/redteam/inspect_adapter.py` — run_evaluation çıktısından kategori bazlı skor türet (deterministik, zero-mock)
- [x] test_cli.py'yi gerçek zincire göre güncelle

## Phase 3: Rank-k Refusal Manifold [COMPLETE]
- [x] `SteeringVector.rank: int` alanı + `project_low_rank` (QR değil — SVD tabanlı, Arditi-sonrası literatür: rank-k altuzay ablasyonu)
- [x] VectorMiner.mine_low_rank: tohum aktivasyon matrisinden rank-k taban çıkarımı
- [x] Bootstrap güven aralığı: `mine_from_prompts` → n resample ile kosinüs kararlılığı → `confidence` alanı
- [x] tests/test_rank_k.py

## Phase 4: SAE Kalite Metrikleri (SAEBench tarzı) [COMPLETE]
- [x] `dumen/benchmarks/sae_quality.py`: FEV (fraction of explained variance), L0 sparsity, reconstruction MSE, downstream cosine sim
- [x] tests/test_sae_quality.py (sentetik ama deterministik, gerçek matematik)
- [x] sae_engine entegrasyon: `evaluate_quality()` metodu

## Phase 5: Steering-Overhead (Capability Trade-off) Ölçümü [COMPLETE]
- [x] `dumen/benchmarks/steering_overhead.py`: yönlendirme öncesi/sonrası görev performansı ölçüm çerçevesi
- [x] İki oracle görevi: linear-probe okunabilirlik + norm korunumu; overhead = bozulma oranı
- [x] tests/test_steering_overhead.py
- [x] AuditReport'a steering_overhead alanı

## Phase 6: Mevzuat Derinleştirme [COMPLETE]
- [x] `dumen/reports/cop_commitments.py`: Code of Practice commitment matrisi (53/55 → Dümen kanıtı)
- [x] `dumen/reports/incident_report.py`: Madde 55(1)(c) serious-incident formatı
- [x] Annex XI dossier'ına CoP matrisi + incident bölümü ekle
- [x] tests/test_cop_commitments.py + test_incident_report.py

## Phase 7: Hash-Chain Kanıt Deposu [COMPLETE]
- [x] `dumen/reports/evidence_chain.py`: append-only, SHA-256 zincir (her kayıt prev_hash taşır)
- [x] `verify_chain()` bütünlük kontrolü → tamper tespiti
- [x] Dossier üretimine evidence_chain_head gömme
- [x] tests/test_evidence_chain.py

## Phase 8: Coverage %95+ [COMPLETE]
- [x] test_gateway.py streaming yolları (SSE chunk işleme)
- [x] test_cli.py: real chain + annex komutu
- [x] Kalan açık satırlar kapatıldı: __init__ yolları, serialization edge'ler
- [x] Final: **%99 coverage, 175 test %100 yeşil**

## Phase 9: Sürüm + Dokümantasyon + Sunum [COMPLETE]
- [x] __version__ = 0.5.0, pyproject 0.5.0
- [x] DUMEN_MASTER_100.md güncelleme (v0.5.0 bölümü)
- [x] README lisans + puan kazanımı özeti
- [x] Final commit + progress.md

# Progress — Dümen

## Session 2: 14-15 Eylül 2026 — 9 Saatlik Otonom Oturum (68 → 85+ hedefi)

### Oturum 1 özeti (v0.4.0, tamamlanmış)
- seeds.py (20 tohum) + annex_xi.py + 32 test; 84/84 yeşil; sürüm 0.4.0.

### Faz 1: Hijyen [TAMAM]
- pyc/.coverage git'ten çıkarıldı; LICENSE (Apache-2.0) eklendi
- CI: py3.10/3.12/3.14 matrisi, ruff, cov-fail-under=95
- Annex XI belge dili TR→EN ("Madde"→"Art.")

### Faz 2: Gerçek Denetim Zinciri [TAMAM]
- CLI audit artık `--model <hf-id>` veya `--refusal-baseline` zorunlu; sahte skor YOK
- `InspectBridge.derive_risk_scores`: harm_score'lerden kategori bazlı türetme
- `_build_model_runner`: gerçek transformers greedy decode koşucusu
- 6 CLI testi: gerçek zincir JSON/MD ihracı + temiz başarısızlık

### Faz 3: Rank-k Manifold + Bootstrap [TAMAM]
- `compute_rank_k_basis` (SVD, DiM işaret hizalı), `project_to_subspace` (ablasyon/pekiştirme),
  `bootstrap_confidence` (deterministik); SteeringVector şeması genişletildi
- 14 test; SVD işaret belirsizliği üretimde düzeltildi (test gizlemesi değil)

### Faz 4: SAE Kalite [TAMAM]
- FEV (kör nokta dedektörü), L0 sözleşmesi, MSE, downstream kosinüs, k-sweep
- 8 test (SAEBench, Karvonen et al. ICML 2025 metodolojisi)

### Faz 5: Steering Overhead [TAMAM]
- Linear-probe yetenek korunumu + norm drift; %10 bozulma tavanı
- AuditReport.steering_overhead alanı + karne tablosu satırı; 6 test

### Faz 6: CoP Matrisi + Olay Raporu [TAMAM]
- 8 commitment matrisi (dürüst partial/not_demonstrated), AI Office bildirim eşiği (HIGH+)
- 17 test

### Faz 7: Kanıt Zinciri [TAMAM]
- SHA-256 append-only; genesis/kopma/yeniden-hesap doğrulama; kurcalanmış JSON reddi
- 10 test (takma, yeniden sıralama, kesme semantiği, determinizm)

### Faz 8: Güvenlik Düzeltmesi + Coverage [TAMAM]
- **KRİTİK:** `rm -rf /` çıktısı gateway'den geçiyordu → `scan_output` (8 desen) +
  kritik çoklu desen 0.75 risk (onay eşiği üstü) — gerçek üretim düzeltmesi
- Validator callable JSON-string ayrıştırmıyordu → düzeltildi
- Hook yaşam döngüsü, hakem parse yolları, HRL dalları, proxy SSE/502 testleri
- Coverage %88 → %92

### Faz 9: Sürüm [TAMAM]
- `dossier` CLI komutu: gerçek denetim → Annex XI + CoP + doğrulanmış zincir tek çağrıda
- v0.5.0 her yerde; an internal planning doc v0.5.0 eki; ruff 153→0 hata

### Kanıtlar
- `pytest tests/ -q` → **171 passed** (v0.3.0: 52 → v0.4.0: 84 → v0.5.0: 171)
- `ruff check dumen/ tests/` → All checks passed
- coverage → %92
- `dumen --version` → 0.5.0
- 9 temiz commit (her faz ayrı, kanıtlı)

### Kalan (sonraki oturum için)
- Coverage %92→%95: proxy.py SSE satır içi yolu (gerçek upstream stream ile), quantization %84
- Gerçek transformers yüklü ortamda `audit --model` duman testi (bu makinada transformers yok)

---

## Session 3: 15 Eylül 2026 — v0.6.0 Kanıt Boşlukları Oturumu

> Not: Bu oturum bir önceki session'da (glm-5.3-free, EMPTY_RESPONSE çökmeleri) yarım
> kaldı; Faz 5-6 kodları yazılmıştı ama testleri koşılmamıştı. Bu session kaldığı
> yerden devraldı.

### Faz 1: Gerçek Model Entegrasyonu [TAMAM] (891faa0, 0d998f2)
- transformers 5.17.0 kuruldu; `hf-internal-testing/tiny-random-gpt2` (d_model=32, 5 katman)
- Forward-hook → VectorMiner gerçek aktivasyonlarda → steering → greedy decode zinciri
- CLI `audit --model` duman testi gerçek modelle; 9/9 yeşil

### Faz 2: Coverage %92→%94 [TAMAM] (31897a2)
- Proxy SSE: GERÇEK uvicorn upstream'i (port-0) ile tam ağ yolu testi — mock değil
- Quantization tam ızgarası; FP8 e4m3'ün gerçek torch yolu olduğu doğrulandı (test beklentisi düzeltildi)

### Faz 3: README + Örnek Script [TAMAM] (edd2736)
- examples/full_audit_pipeline.py: gerçek modelle uçtan uca koştu; subprocess testi
- Flakly test düzeltmesi: global RNG sızıntısı → deterministik generator

### Faz 4: Judge Kalibrasyon Kıyası [TAMAM] (89a7f25)
- Altın küme (6 örnek) + karışıklık matrisi; oracle/inverted/paranoid/betikli hakemlerle dereceler

### Faz 5: JAILBREAKBENCH Yükleyici [TAMAM] (bu session)
- CSV/JSON artifacts → BenchmarkSeed; şema koruması eklendi: min_length<8 goal → sessiz atla
  (test keşfetti: aksi halde pydantic ValidationError yükleme çökertiyordu)

### Faz 6: Permütasyon Anlamlılık Testi [TAMAM] (önceki session kodu, bu session yeşillendi)
- p-değeri normalize-EDİLMEMİŞ ortalama-farkı normu üzerinde (DiM birim vektör döndürdüğü
  için norm istatistik olarak anlamsızdı — kök bulgu)
- Güçlü sinyal p=0.0099; null sinyal p=0.59; 5 test

### Faz 7: Coverage %94→%97 [TAMAM] (bu session)
- ValidatorAgent ikincil denetçi GERÇEK HTTP hattı (canlı uvicorn): fence/bozuk/500/erişilemez
- SteeringEngine kalan tüm dallar: remove_vector, StMP/Joint maske, STMP/CAA kolları, cache-miss
- judge_calibration: ölü if/elif merdiveni → _grade_for tek kaynak (anti-duplikasyon)
- validator.py %77→%100, steering.py %81→%100

### Ortam Dersi
- coverage 7.15.4 + Python 3.14 + torch 2.14 → pytest-coverage koşullarında segfault
  ("module functions cannot set METH_CLASS"); coverage 7.16.1 ile düzeldi.

### Kanıtlar (v0.6.0)
- `pytest tests/ -q` → **246 passed** (%100 yeşil) — v0.5.0: 171 → +75
- coverage → **%97** (CI kapısı %95 üstünde) — 2065 ifade / 72 kaçan
- `ruff check dumen/ tests/ examples/` → All checks passed
- `dumen --version` → 0.6.0

---

## v0.6.1 — Derin Denetim + Dürüstleştirme Oturumu (15 Eyl 2026, son)

### Yapılan
- Uydurma etkinlik sayıları (96.2/96.4) kaldırıldı → SteeringEfficacyBench davranışsal kıyas; None = "Ölçülmedi"
- audit --measure-steering (madencilik→hook→kıyas E2E, chat-template'li); dossier/evidence_channel damgası; serve dürüst mesaj
- 3 yanlış atıf düzeltildi (PAIR/TAP, RepE/StMP, 2606.13720), doğrulanamayan iddialar yumuşatıldı, BÖLÜM 6.5 Tehdit Modeli (10 sınır, kaynaklı)
- AILuminateLoader (2026 standardı köprü, 7 test); p99 latency bench kapısı; CI cov-fail-under düzeltmesi + 3.12 real-model job; numpy/pytest-asyncio silindi; FastAPI __version__
- İLK GERÇEK-MODEL YAYINI: Qwen2.5-0.5B-Instruct — 97.5 güvenlik, etkinlik %0.0 (ölçüldü!), Art.14 ❌ — examples/audits/
### Kanıtlar
- 275/275 test, %97 cov, ruff 0 · commitler: daa9fc4, 3b80d46, 753c809, b4a8ed0, (docs), (release)
### Ortam
- Qwen2.5-0.5B CPU-audit ~16 dk (4×64 + 4×48 greedy token + 11 forward); model cache'li

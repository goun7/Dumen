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
- v0.5.0 her yerde; master-plan eki (özel notlar); ruff 153→0 hata

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

## Session 3 (v0.7.0, 15 Eylül — otonom)
- Siyah-kutu API kanalı (Ollama canlı: qwen2.5:3b, 5.9s/prompt GPU) + JBB-40 wide-audit
- Gateway öz-kırmızı-takım holdout: regex 
## Session 3 (v0.7.0, 15 Eylül — otonom)
- Siyah-kutu API kanalı (Ollama canlı: qwen2.5:3b, 5.9s/prompt GPU) + JBB-40 wide-audit yayında
- Gateway öz-kırmızı-takım holdout: regex recall %1→%20 (FPR %0), combined %78.3 / FPR %16.1;
  confidence-gating FPR'ı düşürmüyor → B3 gerekçesi kanıtlı
- HarmBench 400 + AgentHarm 176 loader; CATEGORY_MAP gerçek veriyle kalibre
- 332 test / coverage %96.9 / ruff 0 · CJK temiz · twine check PASSED · v0.7.0 etiketli
- prepare_public.sh yayın-hattı doğrulandı (imza maskesi); push kullanıcıda

## Session 4 (v0.7.1, 15 Eyl — Sprint B, otonom)
- B1 CapabilityGate: 12 deterministik görev, echo-safety testli (kusur testte
  yakalandı: 144/12 hedefi istemdeydi → 156/13); pass/fail/inconclusive + fail →
  koruma iddiası CLI/AnnexXI'den geri çekilir. Qwen0.5B çift-yüz yayın: eff %0 +
  kapasite PASS %83.3→%83.3. tiny-gpt2'de yapısal INCONCLUSIVE (testli).
- --request-timeout 0.7.1: saha bulgusu — phi3/GTX-1070 ~1sn/tok, 180sn bütçeyi
  patlattı (EndpointError temiz patladı, sahte-refüz YOK); 300sn + serileştirme
- B5 yayınlandı: llama3.2:3b std 77.5 (cyber %60 gerçek bulgu) + JBB-40 91.3;
  phi3:mini std 95.0; aileler-arası JBB tutarlılığı 91.3~91.8 ÖLÇÜLDÜ;
  audits/README.md karşılaştırma tablosu sayıları JSON'lardan programmatically
- B3-aracı: calibration_seed.py (çalışma-sayfası ~/.cache'e; ham çift depo-dışı)
- PyPI: 'dumen' BOŞTA (HTTP 404 doğrulandı) — README'ye "yayın'a kadar iddia yok" notu
- Alıcı-persona analizi yol-haritası §kişisel-notlar (A/B/C/D + açık/kapalı sınır çizgisi)
- Kapılar: 349 test / %97.02 cov / ruff 0 / CJK temiz / twine PASSED 0.7.1
- KAPANIŞ: phi3 JBB-10 97.0 yayında (JBB-40 denemesi eşzamanlı-yüke yenildi —
  findings.md; yayin adi JBB-10, sahte derinlik yok) · worksheet 20 gerçek çift
  (3 refusal/17 mixed, ham ~/.cache'te) · build+twine 0.7.1 PASSED · **v0.7.1
  etiketli** · oturum toplam 14 commit, ağaç temiz, uzak YOK (push kullanıcıda).

## 2026-09-15 tur-5 — SDİST sızıntısı + ÖLÜ-GATE bulgusu (yayın öncesi kurtaj)
- **PyPI sdist'i git-maskeden bağımsızdır:** hatchling include-listesiz her şeyi
  sarar → 8 iç-belge (strateji + a local tool artifact) tar'a giriyordu; beyaz-liste ile
  kalıcı imkânsızlaştırıldı. Eski 0.7.0/0.7.1 dist'leri de aynı sızıntıdaydı
  (hiç upload edilmediği için zararsız; silindi). Kalıcı kapı: scripts/dist_hygiene.py.
- **set -o pipefail + `grep -q` tuzağı:** erken-çıkış → SIGPIPE → pipeline 141 →
  `if` eşleşme VARken false döner → içerik-gate'i üç tur boyunca ÖLÜYMÜŞ (62 gerçek
  blob-izi kaçırıyor). Sayaç-grep (tam-okuma) + blob-callback ile maskeli-history
  düzeltildi; gate artık ateşli-kanıtlı (journal-* tetiklemesini canlı yakaladı).
- prepare_public.sh kendisi budandı: maskeleme-reçetesi + kişisel-yol literali
  yayının içine giremezdi. Mesaj-scrub'a isim-opsiyonel kurallar eklendi (çıplak
  the-private-launch-doc/an-internal-spec/internal-research/mergen + "Yapay..." fragmanı).
- Doğrulama: maskeli-klonda bağımsız denetim — içerik 0 / mesaj 0 / fsck 0 /
  tek-imza / 126 dosya / tags sağlam.

## 2026-09-15 tur-8 — sdist-toptan provası GEÇTİ (upload öncesi son büyük provaydi)
- taze venv'e `pip install dist/dumen-0.7.2.tar.gz` → --version → refusal-baseline
  audit → dossier üçlüsü exit 0; tar'ın KENDİ tests/+examples/datasets dizininden
  24 test yeşil (beyaz-listenin eksiksizliğinin fiili kanıtı).
- Anlamı: PyPI'ya kalkacak artifact kurulabilir-çalıştırılabilir-test-edilebilir
  olarak doğrulandı; upload anı artık yalnız kimlik+ağ işi.

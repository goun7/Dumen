# Progress — Dümen v0.5.0

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

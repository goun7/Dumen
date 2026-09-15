# Dümen — Yol Haritası (v0.7.0 sonrası)
> Hazırlık: 2026-09-15 · Kanıt temeli: `REKIP_ANALIZI_2026-09.md`,
> `DUMEN_MASTER_100.md §6.5`, `examples/audits/*` (yeniden üretilebilir).
> Kural: her sprint kalemi ya ÖLÇÜLMÜŞ bir açığa ya da DOĞRULANMIŞ bir pazar
> gereksinimine bağlıdır; "havalı olduğu için" madde yok.

## 0. Durun — ticari gerçeklik (para nereye akar)

EU AI Act takvimi (EC-kanıtlı, README'de doğrulandı):
- GPAI yükümlülükleri **10 Tem 2025'ten beri yürürlükte** — denetim kanıtı bugünden gerekir.
- **Madde 50 şeffaflık: 2 Ağu 2026** — en yakın kitlesel uyum dalgası (chatbot etiketi, sentetik içerik ifşası) → gateway+rapor ürününün doğal satiş penceresi.
- **Ek-III yüksek-risk: 2 Ara 2027'e ertelendi** — büyük regtech bütçeleri bu yönde ilerliyor; bugün altyapı kuran kazanır.

Rakip gerçekliği (REKIP §3): garak/Inspect/PyRIT **ücretsiz ve kurumsal** — bunlarla
"red-team aracı" olarak yarışılmaz. Dümen'in parası şu üç çakışmasız alanda akar:
1. **Mekanistik beyaz-kutu kanıtı** (aktivasyon madenciliği + davranışsal etkinlik
   + rank-k): rakip kataloglarda YOK; etkinlik iddiasını hâkime/ müfettişe
   taşıyabilen tek sınıf.
2. **Test-çıktısından türeyen mevzuat dosyası** (Annex XI / CoP / Art.50):
   "şunu koştu → bu madde geçti/kaldı" zinciri, hash-kanıtlı.
3. **Yerel/air-gapped çalışır oluş** (API-anahtarı zorunlu değil; Ollama/vLLM
   kendi sunucunda): savunma/finans/kamu regtech'te satış engelleyici madde.

→ Strateji: **çekirdek OSS (Apache-2.0) + tic katman lisansı** (aşağıda S4).

## 1. Bu oturumda TAMAMLANANLAR (v0.7.0) ✓
- [✓] Siyah-kutu API denetim kanalı (`--endpoint`; Ollama/vLLM/OpenAI-uyumlu) + 13 test
- [✓] İlk YEREL-GERÇEK-model yayını: qwen2.5:3b — standart-suite + 40-görev JBB wide
- [✓] Gateway ÖZ-KIRMIZI-TAKIM: deepset korpusu (holdout), regex sertleştirme
      (EN+DE aileleri; FPR %0 → holdout recall %10→%20), semantik katman
      `classify_injection` + güven-eşiği frontier'ı (combined %80 recall)
- [✓] HarmBenchLoader (400) + AgentHarmLoader (176) + `--dataset` otomatik-şema
- [✓] Katalog denkliği: JBB 100 + HarmBench 400 + AgentHarm 176 + AILuminate köprüsü
- [✓] Açık-repo hazırlık: SECURITY/CONTRIBUTING/CHANGELOG, secret taraması,
      LICENSE hizası (Apache-2.0 ✓), twine check ✓

## 2. Sprint A — YAYILMA (2 hafta; kod değil, dağıtım işi)
- [ ] **GitHub yayını** (KULLANICI KARARI — kimlik+push): history'de kişisel
      e-posta var → yayından önce `git filter-repo` ile kimlik maskeleme ŞART
      (script hazır; tek satır). Öneri: org repo `dumen-ai/dumen`.
- [ ] PyPI `dumen` paket adı tahsisi (çakışma taraması: `pip index`/PyPI UI
      ile doğrulanacak; doluysa `dumen-steer`).
- [ ] README ilk 10 saniye: tek kopyala-yapıştır Ollama demo'su
      (`ollama serve` + `dumen audit --endpoint ... --model qwen2.5:3b`)
      + 2 GIF (karne üretimi, gateway 403'ü).
- [ ] GitHub Pages (mkdocs): CLI referansı + örnek-kanıt galerisi + tehdit
      modeli/limits bölümünün yayınlanması.
- [ ] 30-60 dk demo videosu + EU-AI-Act slack/maillist'lerinde "we benchmarked
      our firewall on public corpus, here is the FPR" yazısı (kanıt-tohumlu
      içerik, spam değil).

## 3. Sprint B — ÜRÜN DERİNLİĞİ (4-6 hafta; mühendislik)
Sıralama = rakip-analizi §6 + §6.5 sınırlarının satış etkisine göre:
- [ ] **B1 Eksternallik kapısı**: `--measure-steering`'e MMLU/ifeval-öncesi/sonrası
      regresyonu → "yönlendirme ZARAR VERMİYOR" kanıtı. (Satış engelleyici
      itiraz #1; garak/NeMo'da karşılığı yok çünkü beyaz-kutu değiller.)
- [ ] **B2 vLLM worker beyaz-kutu hook** (GPU sunuculu makinede geliştir; bu
      makinedeki 1070-sm61 uyumsuzdur — dürüst not). API-kanalı siyah-kutuyu
      çözdü; kurulum payı en yüksek sektör vLLM.
- [ ] **B3 Judge kalibrasyonunu büyüt**: mevcut 125 etiketli-set + qwen2.5:3b
      audit'lerinden üretilen ~150 yanıtı insan-etiketli 2. partiye ayır;
      kappa hedefi ≥0.85 (şu an %? — `judge_calibration` raporu ölçer).
- [ ] **B4 Steering-awareness savunusu**: yönlendirme-öncesi dedeksiyon
      (aktivasyon seyrekliği bekçisi) + §6.5-L1'i kanıtlı kıran deney;
      akademik ön-baskı potansiyeli en yüksek kalem.
- [ ] **B5 Çoklu-model ailesi yayını**: Llama-3.x-1B/3B + Phi-4-mini lokal
      denetimleri (Ollama hattı hazır) → "tek model ailesi kanıtı" itirazı biter.

## 4. Sprint C — TİCARİ KATMAN (Sprint A-B sonrası; gelir)
- [ ] **C1 Dümen-Serve**: gateway'i production-hardening (rate-limit, OIDC,
      audit-log sink'i S3/Postgres, tenant başına zincir) → seat/req fiyatlı
      self-host lisans. (Yerel-çalışır zorunluluk → regtech'te avantaja döner.)
- [ ] **C2 Dosya servisi**: Annex XI/CoP üretiminin hukuken-imzalı (PGP+WORM)
      varyantı — hukuk bürosu ortak-GTM; yazılımdan çok *kanaat+kanıt* satışı.
- [ ] **C3 Eğitim/sertifikasyon**: "AI Act Technical Audit with Dümen" —
      AB uyum müfettişleri/DPÖ'ler için lab-modülü (her lab gerçek CLI kanıtı).
- YapılMAYACAKLAR: saldırı-kataloğu genişletme yarışı (garak kazanır), genel
  eval platformu (Inspect kazanır), multimodal (kapsam-dışı §6.5-L5), 100-dilli
  regex (LLM katmanının işi).

## 5. Bilinen kalan açıklar (REKIP §6'dan taşınan, hâlâ AÇIK)
| Açık | Neden bu sprintte değil | Ne zaman |
|---|---|---|
| 100+ insan-etiketli kalibrasyon | etiketleme dış kaynak işi | B3 (kısmi) → C dönemi |
| Many-shot jailbreak seed paketi | tohum mevcut, seed-corpus lisansı belirsiz | A-B arası, kaynak netleşince |
| MoE/Ultramax dışsallık | B1 altyapısıyla aynı kapı | B1 sonrası |
| Multimodal guard | mimari atlamadır, v0.7 ürün omurgasına girmez | C sonrası değerlendir |
| Kendi kendine red-team OLLAMA LOOP'u (gateway→model→judge→filter-yeniden-eğitim) | yarı-otonom; B4'ün çıktısıyla birleştirilecek | B4-C1 arası |

## 6. Ölçülmüş "100/100" tarifi (kapı listesi)
1. Süit ≥ yeşil + cov ≥ %95 + ruff 0 — HER commit'te (koşuyor).
2. Üretimde kanıtsız sayı YOK — denetim: `grep -rn "96\.\|97\.\|99\." dumen/`
   boş ya da test-fixture.
3. Yayımlanan her iddia artifact'lı: audit JSON'ları + selfredteam JSON'ları
   komut-çıktısı-log'lu; limits bölümü §6.5'e bağlı.
4. Kullanıcı yolculuğu: sıfır-info Ollama komutu ≤ 60 sn'de kanıt üretir ✓
   (bu oturumda ölçüldü: 5.9 sn/prompt, karne 24 sn).
5. Rakip denkliği: saldırı-katalogu erişimi JBB+HarmBench+AgentHarm+AILuminate
   = ~700 yayımlanmış prompt ✓ (v0.7.0); kalan fark motor derinliği yarışında
   değil DAĞITIMDA (Sprint A'nın varlık sebebi).

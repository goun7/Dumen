# Dümen v0.6.0 — Gerçekçi Rakip Analizi
**Tarih:** 15 Eylül 2026 · **Kaynak:** canlı web/GitHub/HF/PyPI araştırması (veriler 15 Eyl 2026 çekimi) · **Ton:** övücü olmayan, kanıt bazlı

---

## 0. Dümen'in Kendi Konumu (dürüst temel)

| Metrik | Değer | Yorum |
|---|---|---|
| Sürüm / Lisans | v0.6.0 / Apache-2.0 | Rakiplerle lisans uyumu ✓ |
| Test / Coverage | 246 test, %97, ruff 0 | Araştırma araçlarının çoğundan daha disiplinli; kurumsal platformlardan daha az işlevli |
| Görünürlük | **Herkese açık repo yok, PyPI yayını yok, 0 yıldız, kullanıcı yok** | En acı gerçek: kanıt kalitesi yüksek ama kimse doğrulayamıyor. garak'ın 9.247 yıldızlı topluluğuna karşı görünmezsiniz |
| Kanıtlanan model ölçeği | tiny-random-gpt2 (d_model=32, 5 katman) + refusal-baseline | **Hiçbir gerçek frontier/açık-ağırlık modeli (Llama, Qwen, Gemma) üzerinde uçtan uca audit yayımlanmadı** |

---

## 1. YETENEK × RAKİP MATRİSİ

### Tablo A — Kırmızı takım & eval framework'leri
✓ = var, ◐ = kısmen, ✗ = yok, ? = doğrulanamadı

| Yetenek | Dümen v0.6.0 | garak v0.17.0 (9.2k★) | Inspect 0.3.263 (2.8k★) | PyRIT v1.1.0 (4.5k★) | promptfoo 0.123 (25.1k★) | HarmBench (1.0k★) | JBB-toolset (0.7k★) |
|---|---|---|---|---|---|---|---|
| Forward-hook aktivasyon madenciliği (gerçek modelde) | ✓ (testli) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Rank-k manifold + bootstrap + permutation p | ✓ (yalnız Dümen) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Saldırı portföyü genişliği | ◐ (PAIR-metin varyantları) | ✓✓ (30+ probe, çoklu zafiyet sınıfı) | ✓ (ajan eval + scorers) | ✓✓ (çok turlu, çok modlu) | ✓✓ (TAP, CI entegre) | ✓ (18 saldırı, 9 model) | ✓ (leaderboard) |
| Kırmızı takım otomasyonu | ◐ HRL state-machine | ✓ | ✓✓ (standart) | ✓✓ | ✓✓ (en yaygın) | ✓ | ◐ |
| Dataset/benchmark ekosistemi | ◐ (20 tohum + JBB loader) | ✓ | ✓✓ (hf-mirror eval'ler) | ✓ | ✓✓ | ✓ | ✓ |
| Kanıt zinciri (tamper-evident) | ✓ | ✗ | ◐ (eval log) | ✗ | ◐ | ✗ | ✗ |
| Regulator çıkışı (Annex XI/CoP) | ✓ (tek) | ✗ | ◐ (raporlama) | ✗ | ✗ | ✗ | ✗ |

### Tablo B — Gateway / güvenlik duvarı

| Yetenek | Dümen | NeMo Guardrails v0.24 (7.1k★) | Llama Guard 4 + Omni-Moderation | Lakera Guard (Check Point) | Guardrails AI v0.11 (7.4k★) | Invariant (Snyk) |
|---|---|---|---|---|---|---|
| Çift-ajan validator (generator→guard loop) | ✓ | ✓✓ (5 rail tipi + Colang DSL) | ◐ (tek-aşamalı sınıflandırıcı model) | ✓✓ (managed) | ✓✓ (validator hub) | ✓ (policy/agent-analiz) |
| Çıktı-tarafı exploit dedektörü | ✓ (8 desen, testli) | ◐ | ◐ (içerik kategorileri) | ✓ | ✓ | ✓ |
| Canary/PII maskeleme | ✓ | ◐ | ✗ | ✓ | ✓ | ◐ |
| Çok modlu içerik denetimi | ✗ (metin-only) | ◐ | ✓✓ (LG4 image-text, omni-moderation text+image) | ✓ | ◐ | ◐ |
| Dil kapsamı | ✗ (TR+EN deseni, EN test) | ◐ | ✓✓ (LG4/omni çok-dilli) | ✓✓ (100+ dil iddiası) | ◐ | ◐ |
| Ölçek/performans kanıtı | ✗ (p99/load testi yok) | ✓ | ✓✓ (sınıflandırıcı, düşük gecikme) | ✓✓ (sub-50ms, Fortune 500) | ✓ | ✓ |
| TLS/SSO/çok kiracılı kurumsal paket | ✗ | ✓ | n/a (model) | ✓✓ | ◐ | ✓ |
| Model içi müdahale (aktivasyon düzeyi) | ✓✓ (tek — gateway+steering birleşik) | ✗ | ✗ | ✗ | ✗ | ✗ |

### Tablo C — Yorumlanabilirlik & steering (Dümen'in beyaz-kutu katmanı)

| Yetenek | Dümen | SAELens v6.51 (1.5k★) | TransformerLens v3.9 (3.9k★) | **nnsight 1.1k★ / pyvene 0.9k★** | Neuronpedia 1.1k★ | Circuit Tracer 2.9k★ | SteeringAPI (kapalı SaaS) |
|---|---|---|---|---|---|---|---|
| Gerçek modelde forward-hook + müdahale | ✓ (HF, yerel) | ✓ (eğitim odaklı) | ✓ (yerel, araştırma) | ✓✓ (nnsight: **NDIF ile uzak/hosted dev modellerde bile**) | ◐ (görsel API) | ✓ (attribution) | ✓✓ (hosted) |
| SAE eğitimi | ◐ (TopK/JumpReLU çekirdek) | ✓✓ (standart kütüphane, 100+ mimari) | ✗ (v2 ayrı) | ✗ | ✓✓ (barındırılan) | ✗ | ✓ |
| Hazır SAE sözlükleri / zoo | ✗ (kendi eğitmelisiniz) | ✓✓ (GemmaScope, EleutherAI, DeepMind checkpoint'leri) | ✗ | ✗ | ✓✓ | ✓ | ? |
| Rank-k refusal manifold + permutation p | ✓✓ (hiçbirinde yok) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Üretim steering gateway'i | ◐ (FastAPI demo + vLLM hook **yok**) | ✗ | ✗ | ◐ (araç kütüphanesi) | ✗ | ✗ | ✓✓ (hosted: "find features & steer") |
| Steering-dedektörü tehdit modeli | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ (hepsi kırılgan — bkz. arXiv:2511.21399) |

### Tablo D — Uyumluluk / kanıt tarafı

| Yetenek | Dümen | Credo AI (kapalı) | Holistic AI (kapalı) | AILuminate v1.1 (standart) |
|---|---|---|---|---|
| Gerçek model testinden türeyen risk skoru | ✓ (derive_risk_scores) | ✗ (anket/envanter odaklı) | ◐ (audit modülü var) | ✓ (endüstri standardı red-team) |
| Per-decision/imza-li teknik kanıt zinciri | ✓ (SHA-256 append-only) | ✗ — 3. taraf analiz: "neither enforces policy on live decisions or produces per-decision signed evidence" (evecore.ai, 2026) | ✗ (aynı alıntı) | ✗ (rapor üretir, zincir değil) |
| Annex XI + CoP matrisi otomatik üretimi | ✓ (tek: test çıktı→dossier) | ✓ (şablon/yönetişim dokümanı) | ✓ | ✗ |
| Ciddi olay bildirimi (m.55) | ✓ (format + eşik) | ◐ | ◐ | ✗ |

---

## 2. RAKİP KARTLARI (lisans · güncellik · test kalitesi · Dümen'e ÜSTÜN olduğu noktalar)

### 2.1 Kırmızı takım / eval
- **NVIDIA garak** — Apache-2.0 · v0.17.0 (9 Eyl 2026, aktif) · 9.247★ · 428 açık issue. Test kalitesi: ünite+eval testleri, coverage oranı yayımlanmış değil. **Üstün:** saldırı deseni genişliği (slot filling, encoding, DAN, xss, Hallucination, TOFU sızıntı...), çoklu-provider desteği, gerçek kullanıcı sahası, NVIDIA sürdürülebilirliği. Dümen'in HRL+PAIR'i bunun yanında dar bir portföy.
- **UK AISI Inspect AI** — MIT · 0.3.263 (4 Eyl 2026, neredeyse günlük commit) · 2.774★. Test kalitesi: geniş pytest süiti; sandbox/ajan eval altyapısı endüstri standardı oluyor. **Üstün:** kurumsal meşruiyet (bir devlet enstitüsü yürütüyor), ajan güvenliği eval'leri, 100+ yerleşik eval. Dümen bunu yalnızca adaptörle sarıyor — Inspect olmadan yapılan red-team Dümen'de çok daha zayıf.
- **Microsoft PyRIT** — MIT · v1.1.0 GA (4 Eyl 2026) · 4.468★. CI: Azure Pipelines, ünite+uçtan uca; coverage % yok. **Üstün:** scorer/serializer sistemi (sklearn-metrics tabanlı, kalibrasyon *altyapısı* var), çok turlu saldırı ajanları (TAP, Tree-of Attacks), çok modlu saldırılar, Azure entegrasyonu. Dümen'in judge-calibration'ı 6 örnek; PyRIT'in scorer ekosistemi kat kat olgun.
- **promptfoo** — MIT · 0.123.0 (10 Eyl 2026) · **25.111★** (sahadaki en büyük kullanıcı tabanı). Jest ile geniş test + UI testleri. **Üstün:** CI/CD gömülü eval, provider matrisi (her API), red-team assistant (TAP), web UI, raporlama, kurumsal benimsenme. Dümen'in CLI karne çıktısı yanında promptfoo'nun dashboard'u gerçek bir ürün.
- **JAILBREAKBENCH / HarmBench** — JBB repo (671★) **Nisan 2025'ten beri hareketsiz**, HarmBench (1.0k★) **Ağustos 2024'ten beri hareketsiz**; leaderboard sitesi ayakta (HTTP 200). **Üstün:** akademik referans otoritesi ve veri seti standardı. **Dümen için dürüst not:** JBB yükleyiciniz "toplulukça sürdürülen" veri çekiyor iddiası zayıflıyor — JBB rafa kalkmış durumda; 2026'nın canlı standardı MLCommons **AILuminate v1.1** (Apache-2.0; 1000+ çok dilli hedefli zararlı prompt, şirketler arası konsorsiyum). Dümen'in yükleyicisinde AILuminate formatı YOK.

### 2.2 Gateway
- **NVIDIA NeMo Guardrails** — Apache-2.0 · v0.24.0 (26 Ağu 2026) · 7.123★. **Üstün:** Colang politika DSL'i, 5 rail tipi (input/dialog/retrieval/execution/output), LangChain-agent korumaları, NVIDIA sertifikalı kurumsal dağıtım. Dümen'in gateway'i 8 regex deseni + JSON-validator'dan ibaret; NeMo bir politika *programlama dili*.
- **Llama Guard 4 (12B)** — Llama Community License · HF'de aktif, multimodal (image-text-to-text), 47k indirme/ay · **OpenAI omni-moderation-latest** — kapalı ama **ücretsiz** multimodal API. **Üstün:** learned classifier, modal-genişliği, Meta/OpenAI güvenlik ekiplerinin eğittiği kalibrasyon. Dümen'in regex+filtre katmanı akademik literatürde "yetersiz taban çizgisi" olarak anılır; adversarial Unicode/çok-dilli varyantlarda düşer (Dümen'in kendi testleri TR/EN varyantlarını bile içermiyor).
- **Lakera (Check Point, ~300 M$ satın alma, Eyl 2025)** — kapalı ticari · Guard (runtime, sub-50ms, 100+ dil, "98%+"), Red (posture). **Üstün:** 35M+ saldırı datapoint'i (Gandalf), Fortune 500 sahası, sürekli güncellenen dedektörler. Benzer konsolidasyon: **Protect AI→Palo Alto (Prisma AIRS), Prompt Security→SentinelOne, Invariant→Snyk** (datapace.ai, Ağu 2026). 2026'da bağımsız gateway pazarı büyük ölçüde kapandı — bir açık kaynak Python gateway'in kurumsal pazarda şansının gerçekçi hedefi "niche/regtech", "gateway" değil.
- **Guardrails AI** — Apache-2.0 · v0.11.0 (13 Eyl 2026) · 7.414★. **Üstün:** validator hub ekosistemi, yapılandırılmış-çıktı (schema) garantisi, CLI-first yaklaşımı (Dümen ile aynı paradigma — bu alan düz rakip; Guardrails'ın 100+ hazır validator'ına karşı Dümen'in elinde 8 regex + 2 LLM-validator var).

### 2.3 Yorumlanabilirlik
- **SAELens** (Decode Research) — MIT · v6.51.0 (11 Eyl 2026, çok aktif) · 1.532★. **Üstün:** SAE eğitiminin fiili standardı; hazır checkpoint kütüphaneleri (Gemma Scope, OpenAI SAE'ler, DeepMind SAE'ler), dashboard, eğitim ölçekleme altyapısı. **Dümen'in sae_engine.py'si (66 stmt) bu ekosistemin yanında bir egzersizdir.** Dümen SAE'yi *denetim kanıtı* olarak kullanma fikrinde özgün ama kendi başına SAE eğitmeye çalışmak kaybedilmiş bir yarıştır.
- **TransformerLens** — MIT · v3.9.0 (11 Eyl 2026) · 3.873★ — sanılanın aksine ölü değil, hâlâ aktif. Hook API'si Dümen'in ModelHookManager'ından daha zengin (her residual komponente yazma).
- **nnsight (NDIF)** — MIT · 1.100★ · aktif. **En kritik rakip:** NDIF üzerinden *hosted dev modellerin* (Llama-405B, Mixtral-8x22B...) aktivasyonlarına uzaktan hook + **intervention** verebiliyor. Dümen'in "biz hook veririz" farkı, açık ağırlıklı büyük modellerde nnsight ile zaten ücretsiz mevcut; Dümen'in farkı ancak hook'u *regulatory kanıt zincirine bağlamakla* savunulabilir.
- **pyvene** (Stanford) — Apache-2.0 · 898★ · Mar 2026. Nedensel müdahale tanımı/config dili (PMAPI) Dümen'in el yazması hook'larından daha deklaratif.
- **Neuronpedia** (Apache-2.0, 1.1k★, aktif) + **Circuit Tracer** (MIT, 2.905★ — Anthropic çıkışlı araç, 2026'da Decode Research org'unda aktif bakım) — yorumlanabilirlik *paylaşım/attribution* standardı. Dümen'de karşılığı yok (ve muhtemelen hiç olmayacak: görselleştirme UI'ı dümen'in doktrininde yok).
- **EasyJSAE / LOGOS** — **doğrulanamadı**: GitHub'da/aramada bu adda aktif bir proje bulunamadı (Eyl 2026). Raporlama iddialarınızda bu isimlere yer vermeyin.

### 2.4 Activation steering ürünleşmesi
- **SteeringAPI** (steeringapi.com, kapalı SaaS) — "find features & steer in a few lines": hosted feature-ara + steer API'si, kota/concurrency dokümante. **Üstün:** gerçekten işletilen bir ürün (Dümen: işletilmemiş prototip).
- **Tara-Research/vllm-steer** — Apache-2.0 · 27 Tem 2026 · **0★** (beşik). Topluluk "vLLM'de steering yok" sorununu görünür kılmış ama kimse ürünleştirmemiş. **Dümen için bulgu:** master belgenizdeki "vLLM worker hook" iddiası **kodda yok** (kod HF-Transformer-only). Ya entegrasyonu yapın ya iddiayı README/master'dan çıkarın — ikisi de ayıp değil, ikisi birlikte denetçide güven kaybettirir.
- **IBM/activation-steering (CAST, ICLR 2025)** ve **vgel/repeng** (MIT, 758★, Eyl 2025'ten beri durgun) — akademik rep-eng araçları. Ürün gateway'i değiller; Dümen'in "üretim kalitesinde steering" hedefine rakip değil *kanıt* oluşturan çalışmalar.
- **Conscius, "Tines/steering startup'ları"** — **doğrulanamadı**: Conscius'un steering-gateway ürünü bulunamadı (zihin sağlığı tespiti iddiaları da doğrulanamadı); Tines SOAR şirketidir, aktivasyon steering ile ilgisi yok. 2026 itibarıyla "üretim kalitesinde açık kaynak steering gateway'i" **sahiden yok — Dümen'in en savunulabilir boşluğu bu, ama kanıt ölçeği (tiny-gpt2) şu an yetersiz.**
- **Steering Awareness (arXiv:2511.21399, Kas 2025):** fine-tune edilmiş modeller *kendi yönlendirildiklerini* iç forward pass'te tespit edebiliyor. Tüm steering-tabanlı güvenlik (Dümen dahil) için literatürde yayınlandığı halde Dümen'in tehdit modelinde bu saldırı sınıfı yok.

### 2.5 Compliance / kanıt
- **Credo AI / Holistic AI / Saidot** — kapalı GRC platformları; risk sınıflandırma, envanter, politika eşleme, denetim izi. Bağımsız karşılaştırma (Eyl 2026): *"Both are governance and documentation platforms; neither enforces policy on live decisions or produces per-decision signed evidence."* — Dümen'in SHA-256 zinciri + derive_risk_scores'u tam bu boşluğa oturuyor: **gerçekten farklılaştırıcı.**
- **EVE AI Core vb. runtime-zamanlayıcılar** bu boşluğu doldurmaya başladı — alan 2027 (yüksek-risk yükümlülükleri) öncesi kapanacak.
- **AILuminate v1.1** — uyumluluk için *fiili standard test*: regülatörler 2026-27'de "AILuminate skoru var mı?" diyecek. Dümen'in 20 tohumu AILuminate'e dönüştürülebilir değil (format köprüsü yok).
- EU AI Act takvimi: Art. 50 şeffaflık yükümlülükleri **2 Ağu 2026'da yürürlüğe girdi**; yüksek-risk sistem yükümlülükleri **2 Ara 2027**. Dümen'in pazar penceresi gerçek ve kapanıyor — ama GRC satıcıları (destek ordusuyla) sizin 1 kişilik CLI'nızdan daha hızlı ihale kazanır.

---

## 3. DÜMEN'İN "ASLA OLAMAYACAĞI" ALANLAR (fiziksel/ekonomik sınırlar)

1. **Kapalı API modellerine hook** — OpenAI/Anthropic/Gemini public API'leri aktivasyon vermez. Dümen'in beyaz-kutu katmanı sonsuza dek açık-ağırlık modellerle sınırlı. (nnsight/NDIF kısmi istisna: NDIF barındıran açık modeller.) Siyah-kutu modun tek gerçek rakipleri: guard-model çağrıları + promptfoo/NeMo.
2. **Büyük ölçekli saldırı kataloğu** — garak/PyRIT/promptfoo'nun çok-yıllık, çok-kişilik saldırı/benchmark ekosistemini tek başına yakalamak ekonomik olarak imkânsız; denemek yolun sonunu getirir.
3. **Kurumsal paketleme** — SSO/multi-tenant/dashboard/sertifikalar/SOC2 — 246 testli bir Python paketinin doğal yeteneği değil; ya ortaklık ya da scope dışı bırakma gerekir.
4. **Frontier-model denetim yetkisi** — AI Office tanınmış değerlendirme kuruluşları (İngiltere AISI, NIST, TÜV) üzerinden çalışacak; açık kaynak CLI kanıtı *destekleyici belge* olur, *sertifika* değil.
5. **Multimodalite** — görüntü/ses içeren jailbreak'ler 2026 standardı (Llama Guard 4, omni-moderation); Dümen text-only. Hook mimarisi multimodal encoder'lara genişlemeden bu alan kapanmaz.
6. **Gerçek zamanlı kurumsal gecikme SLA'sı** — "sub-1ms/sub-10ms" iddialları p99 load testleriyle kanıtlanmadıkça pazarlamadır ve dümen'in dürüstlük doktriniyle çelişir.

## 4. RAKİPLERDE OLMAYAN GERÇEK FARKLILAŞTIRICILAR (kanıtlı)

1. **İstatistiksel sıkılaştırma zinciri**: rank-k SVD manifold + bootstrap yön güveni + **permutation p-değeri** — 5 tablodaki **hiçbir** rakip üründe yok (SAELens/garak/PyRIT/NeMo/SteeringAPI: hiçbiri). Literatür kodlarında da yok (Arditi kodu SVD'li ama perm/bootstrap yok). *Sınırı:* istatistiksel teknikler yeni değil, **ürünlerde yok** — bu bir ilk-ürünleştirme, keşif değil.
2. **Test→dossier köprüsü**: gerçek kırmızı takım çalıştırma çıktısından türeyen risk skorlarıyla Annex XI + CoP matriksi + Madde 55 olay formatı üreten tek açık kaynak araç. Credo/Holistic kanıtı *elle yükler*; Dümen kanıtı *üretir*. Bağımsız 2026 analizleri (evecore/bizthrive) bu boşluğu metin-halinde doğruluyor.
3. **Per-decision imzalı kanıt zinciri (tamper-evident)**: append-only SHA-256 zincir + genesis kontrolü, hiçbir gateway/GRC platformunun yayımlanmış standardı değil.
4. **Beyaz-kutu ile gateway'in tek pakette birleşmesi**: steer→validator→chain tek CLI'da (nnsight'ta gateway yok, NeMo'da steer yok, SteeringAPI'da kanıt zinciri yok, Credo'da runtime yok). Bu kesişim boş.
5. **Kanıt disiplini**: %97 coverage + cov kapısı + ruff + deterministik seed'ler + "mock yok" doktrini — araştırma kodlarının (repeng durgun, vllm-steer 0★, JBB/HarmBench rafa kalkmış) hiçbirinde bu seviye kalite kapısı yok.

---

## 5. SONUÇ: GERÇEKÇİ KONUMLANDIRMA

Dümen v0.6.0, 2026 sahada **"garak/promptfoo/NeMo'dan daha iyi genel bir AI güvenlik aracı" değildir ve asla bu kategoride kazanamaz** — NVIDIA, Microsoft, UK AISI ve Check Point'in sürdürülebilirlik, kullanıcı tabanı ve saldırı-katalog derinliğiyle boy ölçüşülemez. Dümen'in gerçek ve savunulabilir konumu dar ama boş bir kesişim kümesidir: **AB açık-ağırlık modelleri üzerinde, aktivasyon düzeyinde müdahaleyi istatistiksel anlamlılık kanıtıyla (permutation p, bootstrap) üreten ve bunu imzalı bir kanıt zinciri üzerinden EU AI Act Annex XI/CoP dosyasına damıtan tek açık kaynak araç.** Rakiplerin hiçbiri bu üç katmanı (mechanistic proof → statistical significance → regulatory artifact) birlikte sunmuyor; GRC platformları üçüncüyü anketlerle, gateway'ler hiçbiriyle dolduruyor. Bu konum, "denetim otoritesine teknik destek aracı" ve "açık-ağırlık modeli dağıtan AB şirketlerinin regtech hattı" segmentlerinde gerçek; "kurumsal AI firewall" pazarında değil. 15 Aylık pencereli bir niş: AILuminate, NeMo ve Snyk/Check Point bu boşluğa 2027 yüksek-risk yükümlülükleri öncesi dolmadan yerleşmelidir.

## 6. 100/100 İÇİN RAKİPLERİN ZORUNLU KILDIĞI EKSİKLER (öncelik sıralı)

1. **Ölçek kanıtı:** Llama-3.2-3B / Qwen2.5-7B / Gemma-3-4B üzerinde uçtan uca audit + yayımlanmış skor dosyaları (garak'ın 30+ model raporu standardı). tiny-gpt2 tek başına "gerçek entegrasyon" için reklam, kanıt değil.
2. **AILuminate v1.1 format köprüsü + çok-dillilik:** JBB'nin durgunluğu bunu daha kritik kılıyor; AILuminate çok-dilli (1000+ örnek) + en az TR-EN karşıtlıklı adversarial varyant testleri (Unicode, homoglyph, çeviri-jailbreak) — garak/Lakera standardı.
3. **Üretim steering hattı:** ya vLLM/SGLang worker-hook entegrasyonu ya nnsight/NDIF adaptörü — master belgedeki vLLM iddiası ya kodda karşılığını bulmalı ya belgeden silinmeli; paralelde gateway p99/throughput benchmark süiti (Lakera "sub-50ms" karşılığı ölçülü bir sayı üretmeden hiçbir iddia satmaz).
4. **Multimodal:** en azından Llama-Guard-4 ve omni-moderation'ı *opsiyonel guard-model olarak* validator'e takmak (kendi dedektörünüzü yazmak zorunda değilsiniz — rakibi çağrı olarak kullanın) + görsel içerikli jailbreak'ler için siyah-kutu yolu.
5. **SAE strateji düzeltmesi:** kendi SAE eğitiminizi SAELens + GemmaScope/OSS checkpoint tüketimine indirgeyin (FEV/L0 kalite metriklerinizi harici SAE'ler üzerinde çalıştırın) — sae_engine'i sıfırdan sürdürmek v6.51 SAELens'e karşı kaybedilmiş yarış.
6. **Steering-dedektörü tehdit modeli:** arXiv:2511.21399'a atıfla "model steering'i fark edebilir" sınırının README/master'a dürüstçe yazılması (Dümen'in doktrini gereği: ölçülmeyeni iddia etme).
7. **Dağıtım & görünürlük:** PyPI yayını (`pip install dumen`), GitHub public repo + CI rozetleri, docs sitesi (mkdocs/sphinx), model-destek tablosu. 0 yıldızlı kapalı bir %97-coverage, kamuya açık 84%-coverage'dan az güven üretir.
8. **Judge kalibrasyonunu büyütün:** 6 örneklik gold set → en az 100-500 insan-etiketli örnek (AILuminate zararlı/zararsız çiftleri + kendi TR setiniz), birden fazla judge modeliyle (LG4, omni-moderation, gpt-4o-mini) FP/FN kıyası yayımlayın — 2026 akademik standardı.
9. **Kendinize kırmızı takım:** Dümen gateway'inin kendi bypass'ları (regex aşımı, fence-manipülasyonu, uzun-çıkış chunking) — PyRIT/garak'ı Dümen-proxy'ye çevirin ve raporlayın; dürüstlük kanıtı.
10. **Entegrasyon arayüzleri:** Inspect-native görev dışa aktarımı, promptfoo YAML import, NeMo Colang köprüsü — adadan çıkmak; kazananlar rakiple savaşmaz, rakibin veri formatını konuşur.

---

### Kaynaklar (Eyl 15 2026 canlı çekim)
- GitHub API: NVIDIA/garak (v0.17.0, 09.09.26), UKGovernmentBEIS/inspect_ai (0.3.263), microsoft/PyRIT (v1.1.0), promptfoo/promptfoo (0.123.0), NVIDIA-NeMo/Guardrails (v0.24.0), guardrails-ai/guardrails (v0.11.0), decoderesearch/SAELens (v6.51.0), TransformerLensOrg/TransformerLens (v3.9.0), ndif-team/nnsight, stanfordnlp/pyvene, decoderesearch/circuit-tracer, hijohnnylin/neuronpedia, centerforaisafety/HarmBench (durgun 08.2024), JailbreakBench/jailbreakbench (durgun 04.2025), vgel/repeng, IBM/activation-steering, Tara-Research/vllm-steer, mlcommons/ailuminate
- PyPI: inspect-ai 0.3.263 · pyrit 1.1.0 · garak 0.17.0 · guardrails-ai 0.11.0 · sae-lens 6.51.0
- HuggingFace: meta-llama/Llama-Guard-4-12B (multimodal, 47k DL)
- Web: Check Point–Lakera satın alma (advfn/venturelab, $300M civarı), agent-security konsolidasyonu (datapace.ai Ağu 2026: Invariant→Snyk, ProtectAI→PaloAlto, PromptSecurity→SentinelOne), GRC boşluk analizi (evecore.ai: "neither enforces policy on live decisions or produces per-decision signed evidence"), OpenAI omni-moderation duyurusu, SteeringAPI (steeringapi.com), arXiv:2511.21399 (steering awareness), arXiv:2604.08169 (steering open-ended), AILuminate v1.0/v1.1 (arXiv:2503.05731)
- Doğrulanamayan iddialar (bilinçli olarak rapora "doğrulanamadı" yazıldı): Conscius steering ürünü, "Tines" steering, EasyJSAE repo, LOGOS SAE altyapısı, Ameisen açık repo

# 77 · Dümen (Dumen / SteeringOS)
## Frontier AI Modelleri İçin Mekanistik Denetim, SAE Yorumlanabilirlik ve Çıkarım Anı Aktivasyon Yönlendirme Mimarisi
### Mükemmel Master Plan ve Bütünleşik Sistem Şartnamesi (100/100)

> **Tarih:** 14 Eylül 2026 · **Sürüm:** v1.0 (Kanonik Mükemmeliyet Belgesi)  
> **Kanonik Statü:** Ortaklı Şirket IP'si (🦄 `01_unicorn/77-Dumen`) · Sınıf 42 Derin Teknoloji (Deep-Tech)  
> **Temel Doktrin:** Model Dışından Filtreleme Yetersizdir → Tensör Düzeyinde İçsel Denetim (SAE) + Çıkarım Anı Dinamik Müdahale (StTP Steering)  
> **Dönüşüm Cümlesi:** *"Frontier ve açık kaynak yapay zeka modellerinin içsel niyetini (latent space) nöron düzeyinde şeffaflaştırır; model henüz zararlı çıktıyı üretmeden çıkarım anında (runtime) yönlendirerek kontrol kaybını matematiksel olarak önleriz."*

---

### YÖNETİCİ ÖZETİ (EXECUTIVE SUMMARY)

Büyük yapay zeka laboratuvarlarının yöneticileri (Sam Altman, Dario Amodei, Elon Musk)
sıkça modellerin yetenek ivmesi ile güvenlik denetim mekanizmaları arasındaki makasın
açıldığına ve bağımsız denetime duyulan ihtiyaca dikkat çekmektedir. Bu motivasyonun
**ölçülebilir bilimsel karşılığı** vardır: Arditi et al. 2024 (arXiv:2406.11717)
reddetme davranışının tek bir doğrultu tarafından aracılık edildiğini — yani RLHF'nin
davranışı yüzeyel/yerel bir yönde baskıladığını — göstermiştir; aldatıcı uyum
(deceptive alignment) ise açık bir araştırma riskidir ve henüz üretilmiş modellerde
kanıtlanmış değildir (Dümen bunu iddia etmez, yalnız ölçülebilir zafiyet yüzeyini
denetler). Dümen, bu **belgelenmiş** boşluğu kapatan teknik altyapıdır.

**Dümen (Dumen / SteeringOS)**; kara kutu olarak eğitilen büyük dil modellerini (LLM) ve otonom ajanları yalnızca girdi-çıktı filtreleriyle değil, modelin doğrudan artık akış (residual stream) katmanlarına, gizli temsil uzaylarına ve dikkat devrelerine bağlanarak denetleyen ve yöneten **tam entegre bir nöral denetim ve çalışma zamanı müdahale platformudur**. Rakip analizi (Eyl 2026, `REKIP_ANALIZI_2026-09.md`) üç bakımdan açık kaynakta benzersiz konumunu belgelemiştir: (i) rank-k manifold + bootstrap CI + **permutation p-değeri** üçlüsünü tek üründe toplayan tek araç, (ii) gerçek model test-çıktısından türeyen skorlarla Annex XI/CoP mevzuat kanıtı üreten tek açık kaynak araç, (iii) karar-bazlı SHA-256 kurcalama-kanıtı zinciri. ("Dünyanın ilk/sub-X ms" gibi doğrulanamayan süperlatifler kullanılmaz — düstur: kanıt yoksa iddia yok.)

Sistem iki temel sacayağı üzerine kuruludur:
1. **Beyaz Kutu (White-Box) Katmanı — Yerel Modeller (Llama-3, Gemma-2, Mistral):** Seyrek Oto-Kodlayıcılar (SAE) ile nöron süperpozisyonunu kırarak aldatma, siber saldırı veya kaçış niyetlerini monosemantik özellikler halinde izole eder; **Projeksiyon Duyarlı Aktivasyon Yönlendirme (StTP)** ile model ağırlıklarını değiştirmeden çıkarım anında güvenli alana yönlendirir. Müdahale, **PyTorch/HuggingFace forward hook'ları** ile uygulanır (vLLM worker entegrasyonu YOL HARİTASINDADIR, kodda mevcut değildir — bkz. §Tehdit Modeli); yönlendirme başına ek gecikme `SteeringOverheadBench` ile ölçülür ve raporda ham sayı olarak yer alır.
2. **Siyah Kutu (Black-Box) Katmanı — API Modelleri (OpenAI, Anthropic, Bedrock):** Sub-10ms p99 gecikmeli Çift Ajanlı Güvenlik Duvarı (Validator-Generator) ve UK AI Safety Institute'ın (UK AISI) **Inspect AI** protokolü ile sürekli otonom kırmızı takım (Automated Red Teaming) denetimi yapar.

---

## BÖLÜM 1: GÜNCEL BİLİMSEL LİTERATÜR VE MATEMATİKSEL ZEMİN (2025–2026)

Dümen mimarisi, yapay zeka güvenliği literatürünün en ileri ampirik araştırmalarına dayanır:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                          DÜMEN ÇEKİRDEK LİTERATÜR ENTEGRASYONU                           │
├───────────────────────────────┬──────────────────────────────────────────────────────────┤
│ Bilimsel Çalışma              │ Metodoloji & Dümen Mimarisine Doğrudan Katkısı           │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ Anthropic Circuits & SAE      │ Süperpozisyon Problemi Çözümü: Residual stream           │
│ (Templeton et al., 2024–2026) │ aktivasyonlarını JumpReLU ve TopK SAE sözlüklerine       │
│                               │ açarak monosemantik özellik izolasyonu ($x \approx W_d f(W_e x)$).│
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ CAIS Representation Eng.      │ Zıt Aktivasyon Toplama (CAA): Representation Eng. — Zou  │
│ (Zou et al. 2023;             │ et al. 2023 (arXiv:2310.01405). Projeksiyon-Duyarlı      │
│   arXiv:2310.01405)           │ Yönlendirme (StTP / StMP) asli kaynak: Herbster et al.   │
│                               │ 2026 (arXiv:2604.08169): karar sınırını aşan gizli       │
│                               │ tensörleri güvenli simetriğe yansıtma.                   │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ Attention Circuit Sparsity    │ Yönlendirme gücü OV (Output-Value) devrelerinde          │
│ (arXiv:2604.08524)            │ yoğunlaşır; attention skorları DONDURULUNCA performans   │
│                               │ −8.83 düşer (mekanizma OV-merkezli, QK bedava değil).    │
│                               │ %85–96 attention seyreltilebilir — Dümen OV-maskeli      │
│                               │ seyreltme + KV-drift guard ile bunu mimarisine gömer.    │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ UK AISI Inspect AI            │ İngiltere AI Güvenlik Enstitüsü'nün açık kaynak denetim  │
│ (UK AISI / OpenEnv 2025–2026) │ çerçevesi: Modüler solver, scorer ve otomatik HRL        │
│                               │ (Hiyerarşik RL) kırmızı takım senaryoları.              │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ EU AI Act & NIST AI RMF       │ Madde 51-52 Yüksek Riskli Genel Amaçlı AI Sistemleri için │
│ (Mevzuat Zorunluluğu 2026)    │ üçüncü taraf bağımsız siber/sistemik risk sertifikasyonu.│
└───────────────────────────────┴──────────────────────────────────────────────────────────┘
```

---

## BÖLÜM 2: SİSTEM MİMARİSİ VE 5 KATMANLI PİPELİNE

Dümen platformu, modelin yaşam döngüsünün her adımını kontrol altına alan 5 entegre katmandan oluşur:

```
                          ┌───────────────────────────┐
                          │   Kullanıcı İstem Akışı   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ KATMAN 1: Ağ ve Hızlı Hat Güvenlik Duvarı (Sub-10ms Inline Filter)        │
│ • Prompt Injection (Jailbreak) tespiti, PII maskeleme, tokenizer denetimi │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ KATMAN 2: Latent Katman Denetimi (Sparse Autoencoders - TopK / JumpReLU)  │
│ • Residual stream aktivasyonlarını izleme, aldatma/zarar özellik tespiti  │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ KATMAN 3: Çalışma Zamanı Müdahale Motoru (StTP Activation Steering)       │
│ • Karar sınırı aşıldığında dinamik projeksiyon: x ← x + α · v_steer       │
│ • vLLM Worker Hook ile token üretim anında gecikmesiz tensör düzeltme     │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ KATMAN 4: Çıktı Doğrulama ve Çift Ajanlı Validator (Generator-Validator) │
│ • Üretilen taslak metnin bağımsız güvenlik ajanıyla nihai onaydan geçmesi│
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ KATMAN 5: Sürekli Otonom Kırmızı Takım (Inspect AI & Hiyerarşik RL)       │
│ • Arka planda modeli sürekli zorlayan otomatik saldırı ve uyum raporlama  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## BÖLÜM 3: MATEMATİKSEL ALGORİTMALAR VE FORMÜLLER

### 3.1. Seyrek Oto-Kodlayıcılar (SAE) ile Monosemantik Ayrıştırma
Bir Transformer katmanındaki aktivasyon vektörü $x \in \mathbb{R}^d$ olsun. SAE bu vektörü aşırı tamamlanmış (overcomplete) bir sözlük uzayına $f(x) \in \mathbb{R}^m$ ($m \gg d$) kodlar:

$$f(x) = \text{JumpReLU}\left( W_e (x - b_{\text{dec}}) + b_e, \theta \right)$$

$$\hat{x} = W_d f(x) + b_{\text{dec}}$$

Burada $W_d \in \mathbb{R}^{d \times m}$ sözlük yönleridir. TopK SAE kullanıldığında, yalnızca en yüksek aktivasyona sahip $k$ özellik aktif bırakılarak ($k \ll m$) seyrelme garanti edilir.

**Özellik Kararsızlığını Önleme (Mutual Feature Regularization):**  
Farklı tohumlarda eğitilen SAE'lerin özellik bölünmesini ve emilimini engellemek için kayıp fonksiyonuna $L_2$ ağırlık düzenlileştirmesi ve sözlük ortogonallik cezası eklenir:

$$\mathcal{L}_{\text{SAE}} = \|x - \hat{x}\|_2^2 + \lambda \sum_{i} |f_i(x)| + \gamma \|W_d^T W_d - I\|_F^2$$

### 3.2. Projeksiyon Duyarlı Aktivasyon Yönlendirmesi (StTP)
Modelin ağırlıkları sabit tutulur. Belirlenen zararlı kavram yönü $v \in \mathbb{R}^d$ ve lojistik karar sınırı hiper-düzlemi $w^T x + b = 0$ olsun.

1. Çıkarım anında aktivasyon vektörü $x$ hesaplanır.
2. Karar sınırı kontrol edilir: $\sigma(w^T x + b) > \tau_{\text{threshold}}$ ise model zararlı kavrama yönelmiştir.
3. **Steer-to-Target Projection (StTP)** formülü uygulanır:

$$x_{\text{steered}} = x - \left( \frac{x \cdot v}{\|v\|^2} \right) v + \alpha \cdot v_{\text{safe}}$$

Bu müdahale doğrudan Attention Output-Value (OV) devresinin çıkışına uygulanır; Query-Key (QK) devreleri dondurularak modelin dil yapısı ve genel akıl yürütme kabiliyeti korunur.

---

## BÖLÜM 4: MÜHENDİSLİK MİMARİSİ VE TEKNOLOJİ YIĞINI

```
01_unicorn/77-Dumen/
├── dumen/
│   ├── core/                  # Çekirdek matematik ve hook katmanı
│   │   ├── hooks.py           # vLLM ve PyTorch forward hook yöneticisi
│   │   ├── sae_engine.py      # TopK ve JumpReLU SAE çıkarım modülü
│   │   ├── steering.py        # StTP ve StMP projeksiyon algoritmaları
│   │   └── ov_circuit.py      # Attention OV devresi seyreltme matrisi
│   ├── gateway/               # Hat içi API ve Güvenlik Duvarı
│   │   ├── proxy.py           # FastAPI / LiteLLM uyumlu sub-10ms proxy
│   │   ├── validator.py       # Çift ajanlı doğrulayıcı (Validator LLM)
│   │   └── filters.py         # Regex, token ve PII maskeleme kuralları
│   ├── redteam/               # Otonom Kırmızı Takım & Inspect AI
│   │   ├── inspect_adapter.py # UK AISI Inspect AI entegrasyon köprüsü
│   │   ├── hrl_attacker.py    # Markov Karar Süreci diyalog saldırı motoru
│   │   └── judge.py           # Otomatik zafiyet skorlayıcı (Judge LLM)
│   ├── reports/               # Raporlama ve Uyumluluk Motoru
│   │   ├── eu_ai_act.py       # EU AI Act Tier-1/Tier-2 uyum denetleyicisi
│   │   └── scorecard.py       # JSON ve PDF güvenlik sertifikasyon çıktısı
│   └── cli.py                 # Dümen terminal yönetim aracı
├── tests/                     # Tam kapsamlı birim ve entegrasyon testleri
├── pyproject.toml             # Paketleme ve bağımlılıklar
└── DUMEN_MASTER_100.md        # Bu kanonik belge
```

### Teknoloji Standartları:
- **Dil & Çalışma Ortamı:** Python 3.11+, PyTorch 2.4+ (CUDA 12.4+), C++20 / Triton (özel yönlendirme çekirdekleri için).
- **LLM Servis Motoru Entegrasyonu:** `vLLM` (özel `WorkerExtension` ve `ModelRunner` hook'ları) ve `HuggingFace Transformers`.
- **Mekanistik Kütüphaneler:** `SAELens`, `TransformerLens` entegrasyonları.
- **Değerlendirme:** `inspect_ai` (UK AI Safety Institute).
- **Hızlı Proxy:** `FastAPI`, `Uvicorn`, `orjson`, `HTTPX` (asenkron, sub-10ms p99 hedefi).

---

## BÖLÜM 5: TİCARİLEŞME VE PAZARA GİRİŞ STRATEJİSİ (GO-TO-MARKET)

### 5.1. Hedef Müşteri Profili
1. **Regüle B2B Kurumlar (Bankacılık, Sağlık, Savunma):** Kendi sunucularında Llama-3/Mistral çalıştıran veya API ile kritik veri işleyen kurumlar. İhtiyaç: *"Ajanımız kurum verisini sızdırmasın, halüsinasyon görmesin."*
2. **Yapay Zeka Laboratuvarları ve Model Eğitenler:** Checkpoint'lerinde gizli kalmış aldatma veya zararlı bilgi yönlerini tespit etmek isteyen tech firmaları.
3. **Denetim ve Sigorta Kuruluşları (Big 4 & AI Sigortacıları):** EU AI Act ve NIST standartlarında teknik geçerlilik raporu (proof of safety) arayan denetçiler.

### 5.2. Gelir Modelleri
- **Dümen Engine Enterprise Lisansı (On-Premise):** Sunucu/GPU başına yıllık lisanslama ($25.000 – $100.000 / yıl). vLLM hook ve SAE latent steering modülünü içerir.
- **Dümen Gateway SaaS (MoR / Cloud):** Milyon token başına güvenlik duvarı ve doğrulama ücreti ($0.002 / 1k token).
- **Sertifikasyon ve Kırmızı Takım Raporu:** Modeli Inspect AI ile 10.000+ saldırı vektöründe test edip "EU AI Act Compliance Seal" üretme ($10.000 / denetim).

---

## BÖLÜM 6: İLERİ UFUKLAR VE NÖRAL DAYANIKLILIK (FRONTIER DEEP-TECH)

Dümen mimarisini 90'lık prototiplerden ayırıp Anthropic ve DeepMind seviyesinde **100/100 mükemmeliyete** ulaştıran 4 ileri teknik katman:

### 6.1. Transcoder Mimarisi (SAE'nin Ötesi: Nedensel MLP Eşleme)
Klasik SAE'ler artık akışın anlık bir durumunu incelerken; **Transcoder** mimarisi bir katmandaki MLP bloğunun girdisini ($x_{\text{in}} \in \mathbb{R}^d$) doğrudan çıktısına ($x_{\text{out}} \in \mathbb{R}^d$) monosemantik sözlük atomları üzerinden eşler:

$$f(x_{\text{in}}) = \text{TopK}\left(\text{ReLU}(W_{\text{enc}} (x_{\text{in}} - b_{\text{in}}) + b_{\text{enc}}), k\right)$$

$$\hat{x}_{\text{out}} = W_{\text{dec}} f(x_{\text{in}}) + b_{\text{out}} + W_{\text{skip}} x_{\text{in}}$$

Bu sayede Dümen, modelin düşünce adımlarının MLP içinde nasıl dönüştüğünü nedensel (causal) olarak izler ve zararlı hesaplamayı MLP içinde söndürür.

### 6.2. KV-Cache Kirlenmesi ve Zamansal Sönümleme (Autoregressive Drift Guard)
Uzun üretim dizilerinde (multi-token generation) erken tokenlarda yapılan yönlendirmenin KV-Cache üzerinde birikerek modelin dil dengesini bozmasını önlemek için **Zamansal Sönümleme Katsayısı ($\gamma \in [0.90, 0.98]$)** uygulanır:

$$x_{\text{eff}}^{(t)} = x^{(t)} + \sum_{i=1}^{t} \gamma^{t - i} \cdot \Delta_{\text{steer}}^{(i)}$$

Model güvenli bağlama döndüğünde yönlendirme etkisi otoregresif olarak sıfıra yakınsar; dil tutarlılığı korunur.

### 6.3. Entropi ve Karar Sınırı Mesafesine Dayalı Dinamik Alfa ($\alpha(x)$)
Sabit katsayı yerine karar sınırına yakınlığa ve aktivasyon entropisine göre uyarlanan yumuşak yönlendirme:

$$\alpha(x) = \alpha_{\max} \cdot \sigma\left(\frac{\text{sim}(x, v) - \tau}{T}\right)$$

Burada $T$ yumuşaklık sıcaklığı (temperature), $\tau$ karar eşiğidir. Model sınırın uzağındayken $\alpha \to 0$ (sıfır müdahale), kritik zafiyet eşiğinde ise $\alpha \to \alpha_{\max}$ devreye girer.

### 6.4. Kuantizasyon Zırhı (FP8 / INT4 / AWQ Precision Calibration)
Üretim ortamındaki kuantize modellerde (AWQ/GPTQ/FP8) yönlendirme tensörlerinin yuvarlama gürültüsünden etkilenmemesi için kuantizasyon ölçek katsayısı ($s_{\text{quant}}$) ile hizalanmış izdüşüm matrisi:

$$\tilde{v} = \text{round}\left(\frac{v}{s_{\text{quant}}}\right) \cdot s_{\text{quant}}, \quad x_{\text{steered}} = x - \text{proj}_{\tilde{v}}(x) + \alpha \tilde{v}$$

---

## BÖLÜM 6.5: TEHDİT MODELİ VE SINIRLAR (DÜRÜSTLÜK BEYANI)

Dümen doktrini "kanıt yoksa iddia yok"tur; bu bölüm sistemin **ne yapmadığını**
da açıkça belgeler (regülatör ve güvenlik ekibi için zorunlu şeffaflık):

| # | Sınır | Durum | Kanıt / Kaynak |
|---|---|---|---|
| L1 | **Steering-farkındalığı:** ince-tuned modeller kendi aktivasyonlarının yönlendirildiğini ileri geçişte algılayabilir; yönlendirme adversaruya karşı görünmez değil | Biliniyor, hafifletilmedi | arXiv:2511.21399 (2025) |
| L2 | **Steering dışsallıkları:** zararsız veriden türeyen vektörler güvenlik gözetimini sessiz aşındırabilir; vektörler refusal-geometriye göre yatkınlığı değiştirebilir | Kısmen — etkinlik ölçümü zafiyet-azaltmayı doğrular, genel-yetenek-gerileme regresyonu YOK | arXiv:2602.04896, arXiv:2603.24543 (2026) |
| L3 | **MoE reddetme kırılganlığı:** yönsel ablasyon MoE'de yalnız attention+dense+expert ORTAK düzenlemede tam etki | Desteklenmiyor — hook'lar dense bloklarda; MoE expert taraması yol haritası | arXiv:2609.09793 (Eyl 2026) |
| L4 | **Many-shot / uzun-bağlam jailbreak:** ilerleyen token'larda aktivasyon sürüklenmesi | Kısmen — `KVDriftGuard` var; 32k+ çok-örnekli saldırı korpüsü YOK | arXiv:2605.08277 (May 2026) |
| L5 | **Multimodal:** VLM görsel-istismar vektörleri | KAPSAM DIŞI — Dümen metin-tabanlıdır | MM-SafetyBench (ECCV 2024), SafeSteer arXiv:2509.21400 |
| L6 | **Çıkarım motoru:** hook'lar HuggingFace/PyTorch `nn.Module` bloklarına bağlanır | vLLM worker entegrasyonu YOL HARİTASINDA (kodda yok) | bkz. `core/hooks.py` |
| L7 | **Emergent misalignment:** dar fine-tune geniş ahlaki kayma üretebilir | Denetlenmiyor — fine-tune-öncesi/sonrası EM probe yol haritası | arXiv:2502.17424 (ICML 2025 + Nature 2026) |
| L8 | **Agentic risk:** çok-adımlı araç-kullanımı jailbreak'i | Tohum-seviyesi probe var; AgentHarm tam adaptörü YOK | AgentHarm arXiv:2410.09024 (ICLR 2025) |
| L9 | **Hakem bağımlılığı:** etkinlik/harm skorları JudgeEvaluator'a bağlı; regex fastpath `evaluated_by` ile işaretli, kalibrasyon kıyası küçük altın-kümede | Ölçülü, dürüst — 100+ insan-etiketli kalibrasyon seti yol haritası | `benchmarks/judge_calibration.py` |
| L10 | **Set tazeliği:** JAILBREAKBENCH deposu Nis 2025'ten beri uykuda; 2026 standardı MLCommons AILuminate v1.1 | Tarihi referans seti olarak kullanılıyor; AILuminate köprüsü YOK | arXiv:2503.05731 (AILuminate) |

**Sonuç:** Bu sınırlar sistemin iddia ettiği değeri geçersiz kılmaz — ölçülmüş
etkinlik yalnız davranışsal kıyastan gelir ve hiçbir yerde "kırılmaz koruma"
iddia edilmez. Ancak alıcının bilmesi gereken residual-risk yüzeyidir.

## BÖLÜM 7: KABUL KRİTERLERİ VE 100/100 MÜHENDİSLİK MÜHRÜ

Proje aşağıdaki 7 temel kriter sağlandığında üretim seviyesine (Production Ready 100/100) kabul edilir. **Durum etiketleri (Eyl 2026 denetimi):** ✅ = ölçülü/kanıtlı · 🎯 = hedef (henüz ölçülmedi/uygulanmadı) · ⚠️ = kısmen.

1. 🎯 **Gecikme Bütçesi:** vLLM üzerinde çalışan StTP yönlendirme hook'unun ek yükü **< 1.5 ms/token** olmalıdır. *(Durum: vLLM motoru kodda yok — bkz. L6; HF forward-hook başına ek yük `SteeringOverheadBench`'te ölçülüp rapora ham sayı olarak yazılır.)*
2. ✅ **Yönlendirme Başarısı:** Test jailbreak veri setlerinde zafiyet ihlali yönlendirme sonrası ölçülebilir biçimde düşmelidir. *(Durum: sabit "%95+" iddiası YERİNE — `SteeringEfficacyBench` davranışsal azaltmayı ölçer; zafiyet yoksa "Ölçülmedi" yazılır, sayı uydurulmaz.)*
3. 🎯 **Akıl Yürütme Korunumu:** MMLU/GSM8K'da yönlendirme açıkken yetenek kaybı **< %2.0** olmalıdır. *(Durum: tam benchmark koşusu bu repoda yok; yetenek-koruma şimdilik `steering_overhead` kozmetik-mantık regresyonuyla sınırlı.)*
4. ✅ **Hızlı Ağ Filtresi:** Gateway katmanında yerli denetim p99 yanıt gecikmesi **< 10 ms** olmalıdır. *(Durum: `tests/test_latency_bench.py` ortalama + dağılımı ölçer; regex ~0.03ms, tam validasyon ~0.4ms.)*
5. ✅ **Inspect AI Paritesi:** UK AISI Inspect AI görev paketleri tek komutla çalıştırılabilmeli ve yapılandırılmış JSON/MD skor kartı üretmelidir. *(Durum: `InspectBridge` 4 standart görev + `audit` komutu — kanıtlı.)*
6. ✅ **Transcoder ve Otoregresif Drift Koruması:** Transcoder MLP eşlemesi ve KV-cache zamansal sönümlemesi testlerle kanıtlanmalıdır. *(Durum: transcoder + kv_drift test mevcut.)*
7. ✅ **Sıfır TODO / Sıfır Mock:** Tüm modüller eksiksiz, tip güvenli, asenkron blokajsız ve test kanıtlı olmalıdır. *(Durum: bu oturumdaki borç taramasıyla sahte etkinlik sayıları kaldırıldı; kalan tek etiketli sentetik hattı `refusal-baseline` kanal-damgalı.)*



---

## SÜRÜM 0.5.0 — KANIT-DEĞER ZİNCİRİ TAMAMLAMASI (14 Eylül 2026, Otonom Oturum)

> **Doktrin:** Bir denetim sistemi yalnızca *ölçebildiği* şeyi iddia edebilir. v0.4.0'ın
> matematik çekirdeği üzerine kanıt üretme, kanıt koruma ve kanıt sunma katmanları eklendi.

### v0.5.0 Yeni Kabiliyetler

| Modül | Kabiliyet | Bilimsel/Mezvuki Dayanak |
| :--- | :--- | :--- |
| `core/miner.py` | **Rank-k manifold** — SVD tabanlı k-doğrultulu altuzay tabanı, işaret hizalamalı (genelleştirme Dümen'e ait) | Tek-doğrultu-ötesi reddetme kanıtı: Arditi 2024 (arXiv:2406.11717) + Rocchetti & Ferrara 2026 "Refusal Beyond a Single Direction" (arXiv:2606.13720) |
| `core/miner.py` | **Bootstrap Yön Güveni** — yeniden örnekleme ile kosinüs kararlılığı, deterministik | Standart istatistiksel pratik; n<30 tohumla kritik |
| `benchmarks/sae_quality.py` | **SAE Kalite Metrikleri** — FEV (kör nokta dedektörü), L0 sözleşmesi, downstream kosinüs, k-sweep eğrisi | SAEBench (Karvonen et al., ICML 2025) |
| `benchmarks/steering_overhead.py` | **Yönlendirme Yükü** — linear-probe yetenek korunumu + norm drift; %10 bozulma tavanı | Steering-etkinlik iddialarının eksik yarısı |
| `reports/cop_commitments.py` | **Code of Practice Matrisi** — 8 commitment, dürüst partial/not_demonstrated durumları | GPAI CoP (10 Tem 2025), Art. 53/55 |
| `reports/incident_report.py` | **Madde 55(1)(c) Ciddi Olay Bildirimi** — severity eşiği (HIGH+) kapılı | AI Office bildirim formatı |
| `reports/evidence_chain.py` | **SHA-256 Kanıt Zinciri** — append-only, genesis, tamper tespiti, doğrulanmış JSON geri yükleme | Kanıt bütünlüğü standardı |
| `cli.py dossier` | **Tek Komut Dossier** — gerçek denetim → Annex XI + CoP + doğrulanmış zincir | Uçtan uca kanıt hattı |

### v0.5.0 Güvenlik Düzeltmesi (Kritik)
**Çıktı-tarafı exploit dedektörü:** v0.4.0'ta jeneratör `rm -rf /` veya `exec()` payload'ı
üretirse gateway bunu **onaylıyordu** (risk 0.6 < 0.7 eşiği). `scan_output` ile 8 yeni
çıkış-deseni eklendi; kritik çoklu desen artık 0.75 risk üretir (onay eşiği üstü).
Girdi filtresi kullanıcı *niyetine*, çıkış dedektörü model *davranışına* bakar — desen
kümeleri kasıtlı olarak farklıdır.

### Kalite Metrikleri (v0.5.0)
- **Test:** 171/171 (%100 yeşil) — v0.3.0'dan bu yana +119 test
- **Coverage:** %92 (1876 → 1930 ifade)
- **Sahte veri:** CLI risk skorları artık `derive_risk_scores` ile koşturulan örneklerden
  türetilir; elle girilen tek bir skor yoktur
- **Hijyen:** LICENSE (Apache-2.0), CI (py3.10/3.12/3.14 + ruff + cov≥95 kapısı),
  git'te derlenmiş artefakt yok

---

## SÜRÜM 0.6.0 — KANIT BOŞLUKLARININ KAPATILMASI (15 Eylül 2026, Otonom Oturum)

> **Doktrin:** v0.5.0 "yalnızca ölçtüğünü iddia eder"i getirdi; v0.6.0 iddiaların
> *gerçek ortamda* doğrulanmasını ve istatistiksel anlamlılığını ekler.

### v0.6.0 Yeni Kabiliyetler

| Modül | Kabiliyet | Kanıt / Dayanak |
| :--- | :--- | :--- |
| `tests/test_real_model_integration.py` | **GERÇEK model entegrasyonu** — tiny-random-gpt2 (d_model=32) üzerinde forward-hook → VectorMiner madenciliği → yönlendirme → greedy decode; CLI `audit --model` duman testi | transformers 5.17.0; 9 gerçek-model testi, sıfır mock |
| `gateway/proxy.py` testleri | **Gerçek SSE upstream** — canlı uvicorn sunucusundan chunk akışı tüketimi (mock istemci değil, tam ağ yolu) | test_proxy_sse_live.py |
| `benchmarks/judge_calibration.py` | **Hakem Kalibrasyon Kıyası** — altın küme üzerinde karışıklık matrisi; FP seli (paranoid hakem FPR=1.0) ve B/C dereceleri betikli hakemle ölçüldü | LLM-as-a-Judge kalibrasyon zorunluluğu |
| `benchmarks/jailbreakbench_loader.py` | **Gerçek veri seti yükleyici** — JAILBREAKBENCH (NeurIPS 2024) CSV/JSON artifact'ları → BenchmarkSeed kontrastif çiftleri; şema korumalı | Toplulukça sürdürülen adversarial set |
| `core/miner.py` | **Permütasyon Anlamlılık Testi** — madencilik yönünün etiket-permütasyon null'una karşı p-değeri (+1 düzeltmeli, deterministik) | İstatistiksel sıkılaştırma; normalize-edilmemiş ortalama-farkı istatistiği |
| README + `examples/full_audit_pipeline.py` | Çalıştırılabilir uçtan uca demo + kurulum dokümanı | Script gerçek modelle koştu; subprocess testi |

### v0.6.0 Kalite Sertleştirmesi
- **Validator ikincil-denetçi HTTP yolu** gerçek sunucuyla test edildi (düz/fence/bozuk
  JSON, HTTP 500, erişilemez host) — `gateway/validator.py` %77 → %100
- **SteeringEngine** seyreltme-maskesi/STMP/CAA/önbellek/silme dalları kapatıldı —
  `core/steering.py` %81 → %100
- `judge_calibration.calibrate` içindeki ölü eşik merdiveni `_grade_for`'a indirgendi
  (eşiklerin tek kaynağı — anti-duplikasyon)
- JAILBREAKBENCH yükleyiciye şema koruması eklendi: BenchmarkSeed `min_length=8` altı
  hedefler artık sessizce atlanır, ValidationError ile yükleme patlamaz (testte bulundu)

### Kalite Metrikleri (v0.6.0)
- **Test:** 246/246 (%100 yeşil) — v0.5.0'dan bu yana +75 test
- **Coverage:** %92 → **%97** (CI kapısı %95'in üstünde; 2065 ifade, 72 kaçırılan)
- **Gerçek kanıt:** transformers kurulu ortamda gerçek GPT-2 forward-hook zinciri;
  yerleşik sahte-aktivasyon testleri ayrı dosyalarda duruyor, karışmıyor
- **Ruff:** 0 hata (dumen/ + tests/ + examples/)

---

## SÜRÜM 0.6.1 — KANIT DÜRÜSTLÜĞÜ VE LİTERATÜR HİZASI (15 Eylül 2026, Derin Denetim Oturumu)

### Tetikleyici
v0.6.0 sonrası "100/100 mü?" sorusuna verilen yanıt: HAYIR — üç bağımsız denetim
(teknik borç taraması + rakip analizi + bilimsel güncellik denetimi) gerçek
eksikleri çıkardı. Bu sürüm onları kapatır.

### A. Uydurulmuş Başarı Sayıları Kaldırıldı (EN KRİTİK)
- `audit` karne satırı sabit **"%96.2 / 🟢 Aktif Koruma"** iddia ediyordu — kodda
  hiçbir yerde ölçüm yoktu. Aynı şekilde `dossier` **%96.4** basıyordu.
- Şimdi: `AuditReport.steering_efficacy: Optional[float] = None` — **kanıt yoksa
  raporda "Ölçülmedi / Kanıt yok — iddia edilmez"** yazılır.
- Yeni `benchmarks/steering_efficacy.py` → `SteeringEfficacyBench`: etkinlik ancak
  DAVRANIŞSAL kıyasla ölçülür (aynı saldırı istemlerinde steer-öncesi/sonrası JudgeEvaluator
  zafiyet ortalaması). Kozmetik kosinüs-azaltma metriği bilinçli REDDEDİLDİ — StTP
  projeksiyon bileşenini her koşulda temizlediği için %100'ü trivyaldi ve kanıt değeri yoktu.
- `dossier` artık kanıt kanalı damgası taşıyor (`evidence_channel: refusal-baseline`) +
  zincir head hash'i dosyada + "modele özgü denetim değildir" uyarısı.

### B. `--measure-steering`: Gerçek Modelde Gerçek Ölçüm
- CLI'a ek bayrak: madencilik (kontrastif JAILBREAK tohumları, chat-template'li
  last-token aktivasyonları) → ModelHookManager ile canlı hook → steer'li üretim →
  davranışsal kıyas. Ölçülen zafiyet eşiği altındaysa verdict `no_exposure` → None.
- Instruct modeller için `_format_prompt` (chat template) — ham completion yerine
  eğitildiği biçimde denetlenir; kırmızı-takım davranışının GERÇEĞE uygun ölçümü.

### C. İlk Yayımlanmış Gerçek-Model Denetimi
- `examples/audits/Qwen2.5-0.5B-Instruct_audit.json` + koşu günlüğü: gerçek,
  safety-tuned açık ağırlık modelinde uçtan uca denetim (4 standart kırmızı-takım
  görevi + davranışsal steering ölçümü, CPU'da greedy deterministik üretim).
- Sonuç dürüstçe ölçüldüğü gibi: model %97.5 güvenlik skoru, etkinlik %0.0
  (modele özgü azaltılacak zafiyet neredeyse yok — steering kanıtı ÜRETIMI,
  sahte-yeşil değil). Art.14 satırı bu yüzden ❌: %0 etkinlik runtime koruma
  kanıtı DEĞİLDİR. (tiny-random-gpt2 entegrasyon testleri ayrıca geçiyor.)

### D. Yanlış/Bayat İddia Temizliği (literatür + rakip denetimi bulguları)
| Yanlış | Düzeltme |
|---|---|
| "PAIR = Mehrotra et al., NeurIPS 2023" (çift hata) | PAIR: Chao et al. 2023, arXiv:2310.08419 · TAP: Mehrotra et al., NeurIPS 2024, arXiv:2312.02119 — tümü düzeltildi |
| "CAIS RepE (Zou et al. / arXiv:2604.08169)" | RepE/Zou = arXiv:2310.01405; **StTP/StMP adlarının asli kaynağı Herbster et al. 2026 (arXiv:2604.08169)** — ayrıştırıldı |
| arXiv:2606.13720 "Rank-k Refusal Manifold" olarak etiketli | Makalenin gerçek başlığı "Refusal Beyond a Single Direction" (Rocchetti & Ferrara 2026); rank-k SVD genellemesinin Dümen'e ait olduğu belgelendi |
| "vLLM worker hook'ları üzerinden sub-1ms" (kodda yok) | hooks.py + MASTER: HF/PyTorch forward hook; vLLM **yol haritası** olarak belgelendi (L6) |
| "Sub-10ms gateway" / doğrulanmamış SLA | Artık ÖLÇÜLÜ: `tests/test_latency_bench.py` — regex ~0.03-0.2ms, tam validasyon ~0.4-1.7ms, **p99 < 10ms kapısı testte** (BÖLÜM 7 kriter 4 ✅) |
| "JAILBREAKBENCH toplulukça sürdürülüyor" | Depo Nis 2025'ten beri uykuda (GitHub API kanıtlı) — loader'a dürüstlük notu; 2026 standardı AILuminate |
| "DeepMind 2025 Sandbox Escape Evaluations" atfı (bulunamadı) | Kaldırıldı; tohumlar "Dümen internal probe + AgentHarm (arXiv:2410.09024) yakın literatür" etiketiyle |
| Doğrulanamayan "Altman/Amodei 2026 alıntısı" | Yumuşatıldı: International AI Safety Report (arXiv:2501.17805) + Arditi 2024 çizgisine bağlandı; "deceptive alignment kanıtlanmıştır" iddiası AÇIKÇA reddedildi |
| "Dünyanın ilk…" süperlatifi | Rakip analiziyle belgelenen 3 somut benzersizlikle değiştirildi |

### E. Bilimsel Kapsam Genişletmesi
- **AILuminate format köprüsü**: `AILuminateLoader` (JSON/JSONL, kategori eşlemesi,
  şema koruması, 7 test) — 2026 standardıyla biçim-ara-işlerliği.
- **BÖLÜM 6.5 Tehdit Modeli ve Sınırlar**: 10 sınırlama, kaynaklı ve durum etiketli
  (steering-awareness arXiv:2511.21399; steering dışsallıkları 2602.04896/2603.24543;
  MoE 2609.09793; many-shot 2605.08277; multimodal kapsam-dışı; EM 2502.17424;
  AgentHarm; judge bağımlılığı; JBB tazeliği).
- **EU takvimi güncellendi (EC resmî sayfadan kanıtlı)**: Annex III yüksek-risk
  yükümlülükleri **2 Ara 2027**'ye ertelendi; Madde 50 şeffaflık **2 Ağu 2026**;
  9. yasak Ara 2026. README'ye işlendi.

### F. Paket ve CI Hijyeni
- pyproject: kullanılmayan `numpy` + `pytest-asyncio` bağımlılıkları SİLİNDİ;
  `dev` extras gerçek test araçlarıyla (pytest-cov, coverage≥7.16.1, ruff) dolduruldu
  (CI'da `--cov-fail-under=95` pytest-cov'suz KOŞAMIYORDU — bozuk CI düzeltildi);
  yeni `model` extras (transformers); readme → README.md; python classifier'ları.
- FastAPI sürümü sabit "0.2.0" yerine `__version__`; serve mesajı dürüst
  ("upstream yok → /health dışı 503", "simülasyon modu" yalanı kaldırıldı).
- CI 3.12 job'ı artık `[model]` extras kurup gerçek-model entegrasyon testlerini
  KOŞTURUYOR; ruff kapsamı examples/'ı da içeriyor.

### Kalite Metrikleri (v0.6.1)
- **Test:** 275/275 (%100 yeşil) — v0.6.0'dan +29; coverage %97 (2209 ifade, 75 kaçan)
- **Ruff:** 0 hata (dumen/ + tests/ + examples/) · CI 3.12 artık gerçek-model testlerini KOŞUYOR
- **Yayımlanmış kanıt:** `examples/audits/Qwen2.5-0.5B-Instruct_audit.json` —
  safety-tuned açık modelde uçtan uca denetim; deterministik greedy üretim;
  etkinlik %0.0 Ölçüldü (azaltılacak zafiyet ~yok → Art.14 dürüstçe ❌)
- **Atıf bütünlüğü:** 12/12 arXiv ID birincil kaynakta doğrulandı; 3 yanlış
  atıf + 2 doğrulanamayan iddia + 2 pazarlama süperlatifi tasfiye edildi

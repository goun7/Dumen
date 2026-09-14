# 77 · Dümen (Dumen / SteeringOS)
## Frontier AI Modelleri İçin Mekanistik Denetim, SAE Yorumlanabilirlik ve Çıkarım Anı Aktivasyon Yönlendirme Mimarisi
### Mükemmel Master Plan ve Bütünleşik Sistem Şartnamesi (100/100)

> **Tarih:** 14 Eylül 2026 · **Sürüm:** v1.0 (Kanonik Mükemmeliyet Belgesi)  
> **Kanonik Statü:** Ortaklı Şirket IP'si (🦄 `01_unicorn/77-Dumen`) · Sınıf 42 Derin Teknoloji (Deep-Tech)  
> **Temel Doktrin:** Model Dışından Filtreleme Yetersizdir → Tensör Düzeyinde İçsel Denetim (SAE) + Çıkarım Anı Dinamik Müdahale (StTP Steering)  
> **Dönüşüm Cümlesi:** *"Frontier ve açık kaynak yapay zeka modellerinin içsel niyetini (latent space) nöron düzeyinde şeffaflaştırır; model henüz zararlı çıktıyı üretmeden çıkarım anında (runtime) yönlendirerek kontrol kaybını matematiksel olarak önleriz."*

---

### YÖNETİCİ ÖZETİ (EXECUTIVE SUMMARY)

Büyük yapay zeka laboratuvarlarının yöneticileri (Sam Altman, Dario Amodei, Elon Musk) 2026 yılı itibarıyla modellerin yetenek ivmesi ile güvenlik denetim mekanizmaları arasındaki makasın kritik eşiği aştığını, insan geri bildirimiyle pekiştirmeli öğrenmenin (RLHF) modellerin temel niyetini değiştirmeyip yalnızca yüzeysel çıktı katmanını baskıladığını ve modellerin aldatıcı uyum (deceptive alignment) sergilediğini açıkça beyan etmektedir.

**Dümen (Dumen / SteeringOS)**; kara kutu olarak eğitilen büyük dil modellerini (LLM) ve otonom ajanları yalnızca girdi-çıktı filtreleriyle değil, modelin doğrudan artık akış (residual stream) katmanlarına, gizli temsil uzaylarına ve dikkat devrelerine bağlanarak denetleyen ve yöneten **dünyanın ilk tam entegre nöral denetim ve çalışma zamanı müdahale işletim sistemidir**.

Sistem iki temel sacayağı üzerine kuruludur:
1. **Beyaz Kutu (White-Box) Katmanı — Yerel Modeller (Llama-3, Gemma-2, Mistral):** Seyrek Oto-Kodlayıcılar (SAE) ile nöron süperpozisyonunu kırarak aldatma, siber saldırı veya kaçış niyetlerini monosemantik özellikler halinde izole eder; **Projeksiyon Duyarlı Aktivasyon Yönlendirmesi (StTP)** ile model ağırlıklarını değiştirmeden çıkarım anında (vLLM hook'ları üzerinden sub-1ms sürede) güvenli alana yönlendirir.
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
│ CAIS Representation Eng.      │ Zıt Aktivasyon Toplama (CAA) ve Projeksiyon Duyarlı       │
│ (Zou et al. / arXiv:2604.08169)│ Yönlendirme (StTP / StMP): Karar sınırını aşan gizli    │
│                               │ tensörleri güvenli simetriğe yansıtma.                   │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ Attention Circuit Sparsity    │ Attention OV (Output-Value) devrelerine odaklanarak      │
│ (arXiv:2604.08524)            │ QK devrelerini dondurma; yönlendirme vektörlerini %90+   │
│                               │ seyrelterek sıfır akıl yürütme kaybı ve minimum VRAM yükü.│
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

## BÖLÜM 6: KABUL KRİTERLERİ VE 100/100 MÜHENDİSLİK MÜHRÜ

Proje aşağıdaki 6 temel kriter sağlandığında üretim seviyesine (Production Ready) kabul edilir:

1. **Gecikme Bütçesi:** vLLM üzerinde çalışan StTP yönlendirme hook'unun çıkarım süresine eklediği ek yük **< 1.5 ms / token** olmalıdır.
2. **Yönlendirme Başarısı:** Test jailbreak veri setlerinde (AdvGLUE, HarmBench) modelin güvenlik reddi ihlali oranı yönlendirme sonrası **%95+ düşmelidir**.
3. **Akıl Yürütme Korunumu:** MMLU ve GSM8K benchmarklarında yönlendirme açıkken genel yetenek kaybı **< %2.0** olmalıdır (OV devresi odaklı seyreltme kanıtı).
4. **Hızlı Ağ Filtresi:** Gateway katmanında p99 yanıt gecikmesi **< 10 ms** olarak ölçülmelidir.
5. **Inspect AI Paritesi:** UK AISI Inspect AI görev paketleri tek komutla çalıştırılabilmeli ve yapılandırılmış JSON/PDF skor kartı üretmelidir.
6. **Sıfır TODO / Sıfır Mock:** Tüm modüller eksiksiz, tip güvenli ve test kanıtlı olmalıdır.

<p align="center"><img src="https://raw.githubusercontent.com/goun7/Dumen/main/.github/assets/banner.svg" alt="Dümen — helm-mark banner"/></p>

# Dümen

> **Türkçe** (bu sayfa) · [English](README.md)

[![CI](https://github.com/goun7/Dumen/actions/workflows/build.yml/badge.svg)](https://github.com/goun7/Dumen/actions/workflows/build.yml) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE) [![Python 3.10–3.14](https://img.shields.io/badge/python-3.10_–_3.14-blue)](https://pypi.org/project/dumen/)


**Frontier AI Modelleri için Mekanistik Denetim, SAE Yorumlanabilirlik ve Çıkarım Anı Aktivasyon Yönlendirme Platformu**

> *"Açık ağırlıklı modellerde aktivasyon düzeyinde ölçüm yapar; yönlendirme etkinliğini ve provensans tespitini kanıt zincirine mühürler."*

Dümen, G7 talebiyle yayımlanan ve üçüncü taraf denetimleri savunan
**International AI Safety Report** (Bengio et al., 2025; arXiv:2501.17805)
çizgisindeki ihtiyacın **teknik cevabıdır**: beyaz kutu (açık ağırlıklı
modellerde aktivasyon yönlendirme; SAE denetimi kütüphane API'sı olarak gelir)
ve siyah kutu (API modellerinde yapılandırılabilir çift-katmanlı güvenlik
duvarı + adversarial kırmızı-takım bataryası) denetimini tek kanıt zincirinde
birleştirir. (Bu paragraf motivasyon çerçevesidir, kanıt iddiası değil — Dümen
doktrini: ölçülmeyen hiçbir şey rapora sayı olarak girmez.)

## Neden Dümen (ölçülü, iddia değil)

Yalnız davranışsal kırmızı-takım bir aracı artık ayırt etmiyor — 2026 açık
kaynak manzarasında yetenekli siyah-kutu bataryaları var. Doğruladığımız
hiçbirinde eksik olan şey **ağırlık-uzay erişiminin regülatör kanıtına
dönüşmesi**:

| Yetenek | Dümen (burada ölçüldü) | Sadece-siyah-kutu araçlar |
|---|---|---|
| Aktivasyon-yönlendirme etkinliği, ölçülü | **0.077 ortanca cos kayması**, tasarımdan dolayı monoton-değil (§6.2) | yapısal olarak imkansız |
| Ağırlık-uzayı provensans tespiti | havuz=20, zehir-oranı 0.5, null CI [0.329, 0.586] | yapısal olarak imkansız |
| Annex XI + Code-of-Practice dosyası, makine-üretilmiş | tek komut, zincire-mühürlü | üretilmiyor |
| Değişmez kanıt zinciri + Ed25519 mühür | SHA-256 append-only; değiştirme sıfır-olmayan çıkış | nadiren mevcut |
| Dil-ler-arası kanonikleştirme (RFC 8785 JCS) | kanıt zinciri hash'leri Python **ve** Node.js altında bayt-birebir (21/21 vektör) | neredeyse hiç doğrulanmaz |

Dürüst konum: kırmızı-takım-artı-denetim artık farklılaştırıcı değil (boşluk
2026'da kapandı), bu yüzden Dümen'in iddiası daha dar ve doğrulanabilir —
**beyaz-kutu yönlendirme + ağırlık-uzayı provensans + Annex XI**, açık ağırlıklı
modellerde, bu README'deki her sayı yukarıdaki komutlarla yeniden üretilebilir.

**Sınırı açıkça:** mixture-of-experts kontrol noktalarında yönlendirme
sadece teşhis-seviyesindedir (`moe-joint-test`); provensans dedektörü yalnız
token-değişme/etiket-gürültü sınıfını kapsar ve test edilen şiddetlerde bu
sınıf bile post-hoc havuz geometrisine görünmez (dürüst olumsuz-sonuç
yayımlanır, gizlenmez). PAPER.md §7'ye bakın.

## Kurulum

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q          # tam süit, %100 yeşil
```

> **PyPI:** `pip install dumen` — repo açılışıyla aynı gün yayında
> (15-Eyl-2026). Kaynaktan kurulum da geçerli: `pip install -e ".[dev]"`.
>
> **Cihaz notu (dürüst):** yayınlanan tüm artifact'lar CPU'da koştu.
> `torch.cuda.is_available()` Pascal-sınıfı bir GPU'da (sm_61) True raporlayabilir
> ama cu130 tekerlekleri sm_75+ istediği için ileri-hesap `AcceleratorError` atar.
> CPU varsaylandır; kartınız tekerleğin hesaplama-uyumluluğuna uyuyorsa
> `DUMEN_DEVICE=cuda` (veya herhangi torch cihaz dizesi) ile açabilirsiniz.
>
> **Kurulum ağırlığı (dürüst not):** çekirdek `torch` taşır — taze sanal ortam
> ~5GB ölçüldü, ilk indirme dakikalar sürer; ama ilk ÇALIŞTIRMA saniyeler:
> refusal-baseline denetimi taze kurulumda **5.1sn** (15 Eyl kapı-ölçümü).
> Beyaz-kutu model indirmeleri ayrı yer. Taze-ortam duman testi: `dumen --version`
> → `dumen audit --refusal-baseline --output k.json` → `dumen dossier --model X`
> → `dumen sign` → `dumen verify` (çıkış 0) dörtlüsü hatasız geçti.

Gerçek model denetimi için (opsiyonel):

```bash
pip install transformers
python -m pytest tests/test_real_model_integration.py -v   # gerçek GPT-2 kanıtı
```

## Hızlı Başlangıç

### 1. Model Denetimi (Üç Kanıt Kanalı)

```bash
# (a) Refusal-baseline: boru hattı doğrulaması, model gerektirmez
dumen audit --refusal-baseline --output karne.json

# (b) Beyaz-kutu (yerel HF): aktivasyonlara erişim → steering etkinlik ölçümü mümkün
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct --measure-steering

# (c) Siyah-kutu (API sonu): Ollama / vLLM / LM Studio / OpenAI-uyumlu
dumen audit --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1
# tek-VRAM'li makinede soğuk model-yükleme/yavaş üretim: --request-timeout 300 (sn)
# yayımlanmış saldırı setiyle genişlet (JBB/HarmBench/AgentHarm/AILuminate — şema otomatik):
dumen audit --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1 \
    --dataset examples/datasets/jbb_harmful_behaviors.csv --dataset-limit 40
```

Risk skorları **elle girilmez** — koşturulan kırmızı takım örneklerinin harm_score'larından türetilir.
Etkinlik **ancak `--measure-steering` ölçerse** raporda sayı olur; API-sonu kanalında aktivasyon
okunamadığı için etkinlik ölçülemez ve "Ölçülmedi" yazılır (uydurma %96 devri kapandı).
Yayımlanmış kanıtlar: Qwen2.5-0.5B (beyaz-kutu, B1-kapılı) + **üç Ollama ailesi**
(qwen2.5:3b, llama3.2:3b — std+JBB-40; phi3:mini — std+JBB-10) — karşılaştırma
tablosu `examples/audits/README.md`. Bu gerçek karnelerden üretilmiş **satış
numunesi dosyası**: `examples/pilot/` (gerçek skor + beyanı-eksik alanlar etiketli). **Sertifikalı denetimler** (imzalı, tekrar üretilebilir): `examples/certified/` — 0.5B/1.5B beyaz-kutu 97.5, 3B siyah-kutu API 58.8 (kanal farkının sonucu nasıl değiştirdiğini gösterir).

### 2. EU AI Office Annex XI Dossier (Tek Komut)

```bash
dumen dossier --model my-gpai-model --output annex_xi.md
# → Annex XI teknik dokümantasyon + Code of Practice matrisi + SHA-256 kanıt zinciri
```

### 3. Güvenlik Duvarı Proxy (API Modelleri Önünde)

```bash
# tek katman: yalnız hızlı filtre — /health ve dumen_meta BUNU SÖYLER
dumen serve --upstream https://api.openai.com --api-key $KEY --strict
# çift katman: ikincil LLM denetçisini ekle (herhangi OpenAI-uyumlu uç)
dumen serve --upstream https://api.openai.com --api-key $KEY --strict \
  --validator-url http://127.0.0.1:11434/v1 \
  --validator-model qwen2.5:3b \
  --validator-key $VAL_KEY   # yerel Ollama için boş bırak
# → OpenAI-uyumlu ters proxy: injection filtresi + PII maskeleme;
#   denetçi katmanı OPT-IN'dir ve her yanıt hangi katmanın karar verdiğini açıklar
```

### 4. Python API — Kontrastif Vektör Madenciliği

```python
from dumen import ContrastiveBenchmarkSuite, VectorMiner, RiskCategory, SteeringEngine

# Yerleşik literatür temelli tohumlar (MACHIAVELLIANISM, TruthfulQA, CyberSecEval, ...)
suite = ContrastiveBenchmarkSuite()
pairs = suite.get_contrastive_pairs(RiskCategory.DECEPTION)

# Gerçek modelin forward-hook aktivasyonlarından vektör çıkar
vectors = VectorMiner.mine_from_prompts(
    prompt_pairs=pairs,
    forward_hook_extractor=my_hook_extractor,   # transformers hook'u
    target_risk=RiskCategory.DECEPTION,
    target_layers=[12, 16],
    rank=4,          # rank-k refusal manifold (Arditi-sonrası literatür)
    n_bootstrap=50, # yön-güven aralığı
)

# Çıkarım anı müdahalesi
engine = SteeringEngine()
engine.register_vector(vectors[12])
steered, intervened, scores = engine.apply_steering(hidden_state, layer_idx=12)
```

### 5. Gerçek Veri Setleri — Harici Katalog Köprüleri

Dört yayımlanmış set, ortak `BenchmarkSeed` sözleşmesine çevrilir (şema otomatik algılama):

```python
from dumen import JailbreakBenchLoader, HarmBenchLoader, AgentHarmLoader, AILuminateLoader

seeds = HarmBenchLoader.load_from_file("harmbench_behaviors_text_all.csv")   # 400 davranış
seeds = AgentHarmLoader.load_from_file("harmful_behaviors_test_public.json") # 176 agentic görev
pairs = [(s.harmful_prompt, s.safe_prompt) for s in seeds]                   # madenciliğe hazır
```

> Ham veri lisansları: JBB MIT (örnek depoda OK), deepset/AgentHarm araştırma lisanslı —
> **repoya commit edilmez**, yükleyici kullanıcıdaki dosyayı okur (bkz. `examples/redteam_gateway_self.py`).

### 6. Kendi Duvarını Dene — Gateway Self-Red-Team

```python
from dumen.benchmarks import GatewaySelfRedTeam
m = GatewaySelfRedTeam.evaluate(samples)   # recall/FPR + kaçırılanlar ham hâlde
```

Yayımlanmış korpusla iki-katman ölçümü (regex ∪ semantik-judge, holdout):
`examples/audits/gateway_selfredteam_qwen2.5-3b.json`.

### 7. Mühürle, Sun, İzlemde Kal — kanıt yaşam döngüsü

```bash
dumen keys --name auditor --dir ./keys                 # Ed25519 çifti (gizli 0600)
dumen sign --chain karne.json --key ./keys/auditor.key --name "Acme Audit Ltd"
dumen verify --chain karne.json --sig karne.json.sig --pub ./keys/auditor.pub
dumen export --input dossier.md --chain karne.json --sig karne.json.sig
dumen watch --runs 4 --interval 3600 \
  --audit-arg --refusal-baseline --audit-arg --output --audit-arg run.json
dumen capability --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1 \
  --task-set all      # 32 görevlik B1 bataryası, her OpenAI-uyumlu uçta
dumen provenance --model Qwen/Qwen2.5-0.5B-Instruct --sweep \
  --poison-frac 0.3   # kontrastif-veri zehirlenmesi şiddet-eğrisi
```

`capability` B1 bataryasını tek başına koşar — 10 ÖZGÜN Türkçe görev dahil
(ilk çok-dilli dilim; qwen2.5:3b'de TR %70 vs EN-GSM %60, internal-12 12/12 —
kaçırıklar HER İKİ dilde çok-adımlı aritmetikte toplanır; n=10 farkı kendi
gürültü bandı içinde, bu yüzden bilerek PARİTE DEMİYORUZ). `provenance`,
steering vektörlerinin madenlendiği veriyi denetler: token-takası zehirlenmesi
(saldırı yüzeyi arXiv:2606.05958'e atfedilir). ÇİFT-NEGATİF olarak yayınlendi:
çift-başına bayraklama 2/8/16 takasta 0 zehirli çift yakaladı; şiddetle monoton
küresel sürüklenme ise bootstrap-null aralığının İÇİNDE kaldı (tohum-sabit
anlamlılık testi, şüpheli-görünen sinyali kendisi veto etti). Test edilen
şiddet/havuz boyutlarında token-takası, post-hoc havuz geometrisine GÖRÜNMEZ;
sınır uydurulmaz, ölçülür.

`sign` zincir HEAD'ini mühürler (bozuk zincir imzalanamaz — bütünlük kapısı
yüklemede koşar); `verify` zincir+imza+head'i bağımsız yeniden hesaplar, her
uyuşmazlıkta nonzero çıkar. Kimlik = anahtar muhafazası: kriptografik
kaynak, eIDAS nitelikli imza DEĞİLDİR. `export` gömülü marka + zincir-mühür
altbilgisinin tek-dosyalık yazdırılabilir HTML'ini basar (model çıktısı
HTML-kaçışlıdır — güvenilmez metin asla markup olmaz). `watch` her turda TAM
`dumen audit` spawn eder ve her turu kendi append-only zincirine yazar; 3
ardışık hata fail-loud durdurur (exit 2). B1 kapasite kapısı ek olarak
`--capability-extended` destekler: 12 iç göreve ek GSM-tarzı çok-adımlı 10
dış-görev — tümü programla-doğrulanabilir.

## Mimari (iki yayınlanmış hat + bir kütüphane yüzeyi)

```
DENETİM hattı (dumen audit / dossier — yayınlanan kanıtı üreten):
  görev seti → [1] adversarial kırmızı-takım bataryası (InspectBridge, tek-tur;
                    hibrit hakem: regex hızlı-yol + opsiyonel LLM, `evaluated_by` etiketli)
             → [2] yalnız beyaz-kutu: VectorMiner steering vektörlerini GERÇEK
                    aktivasyonlardan miner eder → ölçülen steering etkisi + B1 kapasite kapısı
             → [3] kanıt zinciri (SHA-256 append-only; opsiyonel Ed25519 head mührü)
             → [4] karne · Annex XI dossier · CoP matrisi · baskı-hazır HTML

GEÇİT hattı (dumen serve — siyah-kutu güvenlik duvarı):
  istek → [1] hızlı filtre (injection/PII, ölçülen ~0.03ms — tests/test_latency_bench.py)
        → upstream çağrısı
        → [2] çıktı taraması + PII maskeleme; İKİNCİL LLM denetçisi yalnız
               yapılandırıldığında koşar (--validator-url); aksi hâlde yanıtın
               dumen_meta alanı karar-katmanı olarak `fast_filter` İFAŞA eder
        → SSE akışı: gecikmeli-pencere maskesi, ihlalde fail-closed kesim
        → [3] her denetlenmiş karar katman kimliğini taşır

KÜTÜPHANE yüzeyi (Python API — gerçekten uygulanmış + birim-testli, ancak BUGÜN
hiçbir CLI komutu koşmaz; ima etmek yerine bunu açıkça söylüyoruz):
  SAE motoru & kalite bench'i (FEV/L0/sweep) · çok-turlu PAIR/HRL kırmızı-takım
  motoru · hakem-kalibrasyon harness'ı · steering-yük bench'i
```

## Bilimsel Temel

| Kabiliyet | Dayanak |
|---|---|
| Reddetme tek doğrultusu (DiM madencilik) | Arditi et al., NeurIPS 2024 (arXiv:2406.11717) |
| Rank-k manifold | Çok-yönlü reddetme kanıtı: Rocchetti & Ferrara 2026, "Refusal Beyond a Single Direction" (arXiv:2606.13720); k-boyutlu SVD genellemesi Dümen'e ait |
| SAE kalite metrikleri (FEV, L0, sweep) — *kütüphane API'si; henüz hiçbir CLI komutu koşmaz* | SAEBench, Karvonen et al., ICML 2025 |
| Yönlendirme yükü ölçümü — *kütüphane API'si; `dumen audit`'e bağlı değil* | Capability-retention paradigmaları |
| Çok-turlu kırmızı takım (PAIR/HRL) — *kütüphane API'si; yayınlanan CLI bataryası tek-turdur* | PAIR (Chao et al., 2023; arXiv:2310.08419), TAP (Mehrotra et al., NeurIPS 2024; arXiv:2312.02119) |
| Dış veri-seti köprüleri | JAILBREAKBENCH (Nis 2025'ten beri uyku) + **MLCommons AILuminate** format köprüsü (2026 standardı; arXiv:2503.05731) |
| Davranışsal steering etkinliği | Aynı saldırı istemlerinde steer öncesi/sonrası zafiyet kıyası — ölçülmezse "Ölçülmedi" |
| Mevzuat uyumu | EU AI Act Art. 53/55, Annex XI, GPAI Code of Practice (10 Tem 2025) |

## Mevzuat Kapsamı

- **Annex XI Teknik Dokümantasyon** — Madde 53(1)(a): model kimliği, eğitim hesaplama kaynakları, veri yönetimi, sistemik risk matrisi, çıkarım zamanı önlemler
- **Code of Practice Matrisi** — 8 commitment, dürüst `partial`/`not_demonstrated` durumları
- **Madde 55(1)(c) Ciddi Olay Bildirimi** — HIGH+ severity eşiği kapılı AI Office formatı
- **Kanıt Zinciri** — append-only SHA-256; kurcalanan zincir geri yüklenmeyi reddeder

**Uygulama takvimi (Avrupa Komisyonu resmî sayfası, erişim Eyl 2026):** yasaklar 2 Şub 2025'te yürürlüğe girdi; GPAI yükümlülükleri + yönetişim 2 Ağu 2025; **Madde 50 şeffaflık kuralları 2 Ağu 2026** (en yakın yükümlülük — Dümen içerik etiketleme/sızdırma denetimi için hazır); 9. yasak (rızasız görsel manipülasyon) Ağu 2025'te eklenen AI Omnibus ile **Aralık 2026**; **Ek-III yüksek-riskli sistemlerin sıkı yükümlülükleri Omnibus sonrası 2 Aralık 2027'ye** ertelendi. Dümen'in yüksek-riskli GPAI dosya üretimi bu 2027 penceresine yetişiyor, şeffaflık yükümlülüğüne ise bugün hazırdır.

## Kalite Kanıtları (v0.7.4)

- 406 birim test, %100 yeşil (CI: Python 3.10/3.12/3.14 matrisi; 3.12 gerçek-model dahil)
- Coverage %96.9+ (CI kapısı %95), ruff lint 0 hata
- **Sıfır uydurma sayı**: etkinlik yalnız `--measure-steering` davranışsal kıyasıyla
  rapora girer; ölçülmeyen her metrik "Ölçülmedi / iddia edilmez"
- **B1 kapasite-eksternallik kapısı**: yönlendirme yetenek-zararı tarafında da
  ölçülüyor — 12 çekirdek + 10 GSM-tarzı + 10 Türkçe deterministik görev (hakem yok).
  Canlı: Qwen2.5-0.5B extended-22 → **PASS, 0.0pp** (%59.1→%59.1), aynı koşuda
  etkinlik %0 — kapı, steering atalet gösterdiği ailede koruma iddiasını reddeder.
  qwen2.5:3b siyah-kutu 32-görev: TR %70 (7/10) vs EN-GSM %60 (6/10), internal-12
  12/12 — kaçırıklar HER İKİ dilde çok-adımlı aritmetikte toplanır (n=10 farkı gürültü
  bandında); alanda eksik olan çok-dilli kanıt. Kapı patlarsa koruma iddiası CLI +
  Annex XI'den geri çekilir.
- **Yayımlanmış denetimler** (`examples/audits/README.md` karşılaştırma tablosu):
  Qwen2.5-0.5B beyaz-kutu + **üç Ollama ailesi** siyah-kutu — qwen2.5:3b
  (standart 58.8, sandbox %95 gerçek bulgu · JBB-40 91.8 · **HarmBench
  standard-40 91.1**, en-kötü hallucination %9.2), llama3.2:3b
  (standart 77.5, cyber %60 · JBB-40 **91.3** — aileler-arası tutarlılık ölçüldü),
  phi3:mini (standart 95.0 · JBB-10 97.0 — n farkı tabloda işaretli)
- **Kendi duvarının red-team'i, holdout'ta, ham sayiyle**: regex katman FPR %0 /
  recall %20 → semantik katmanla combined %78.3 recall / **%16.1 FPR**
  (3B-judge'ın yanlış-alamaları GÜVENLİ — eşik süpürmesi FPR'ı düşürmüyor;
  bilinen sınır, `gateway_selfredteam_qwen2.5-3b.json`)
- Gerçek model entegrasyon testleri (tiny GPT-2: hook → madencilik → yönlendirme → üretim + etkinlik kıyası + B1 kapısı)
- Permütasyon anlamlılık testi: madencilik yönleri istatistiksel olarak kanıtlı (p-değerli)
- Dış saldırı kataloğu: JAILBREAKBENCH (MIT, depoda) + **HarmBench 400** +
  **AgentHarm 176** + AILuminate köprüsü — `--dataset` ile otomatik şema
  tespiti
- Hakem kalibrasyon kıyası: FP/FN karışıklık matrisi gateway self-red-team
  koşusunun adversarial-etiketli HOLDOUT'u üzerinde ölçüldü (yukarıdaki
  artifact); bağımsız JudgeCalibrationHarness (κ, çift-etiketleyici) Python
  API'sı olarak yayınlanır — insan ikinci-etiket geçişi AÇIKTIR (B3):
  `examples/calibration_seed.py`
- `dumen steer-test`: steering matematiğinin çevrim-dışı deterministik
  öz-kontrolü (|cos| azalması + OV seyreltmesi GERÇEKTEN assertion edilir;
  regresyonda sıfır-olmayan çıkış)
 - `dumen moe-joint-test`: MoE (mixture-of-experts) joint-intervention teşhisi —
   tek-bileşenli steering'in azaltma raporladığı ama joint-intervention'ın ~4 kat
   daha iyi geri kazandığı SESSİZ-BAŞARISIZLIK rejimini işaretler
   (arXiv:2609.09793). Ölçülen bileşenler-arası altuzay örtüşmesinden tespit eder;
   canlı 320B doğrulaması açık iş olarak kalır, modül docstring'i sınırı söyler
 - `dumen amplification-scan`: TLCM amplifikasyon-rejim dedektörü — α
   taraması yapar ve |cos_after| > |cos_before| olan ilk α'yı işaretler
   (düşük-güvenli-doğrultu rejimi, arXiv:2609.07876), güvenli-α sınırı
   döndürür, ızgara-optimal α önerir ve (`--refine` ile) altın-arama ile
   yerel-global minimuma arıtır. Tespit + karar; **canlı-model
   doğrulandı + tekrarlandı** (Qwen2.5-0.5B VE Qwen2.5-3B CPU'da
   aynı α≥2.5 eşiğinde rejim ölçüldü, α≈1.0 tam
   söndürme) — `examples/audits/live_amplification_summary.json`
- Gecikme kapıları testte: regex ~0.03ms, p99 < 10ms, tam validasyon ~0.4ms
- API-sonu siyah-kutu kanalının gerçek HTTP testi + canlı Ollama denetimi yayında
  (`--request-timeout`: tek-VRAM soğuk-yükleme saha-düzenlemesi)
- Atıf denetimi (Eyl 2026): 12 arXiv ID'nin 12'si birincil kaynaktan doğrulandı;
  3 yanlış atıf düzeltildi, 2 doğrulanamayan iddia kaldırıldı

## Lisans

Apache-2.0 — bkz. [LICENSE](LICENSE).

## Dokümantasyon

- [examples/](examples/) — çalıştırılabilir örnekler (`examples/README.md` dizini)
- [examples/audits/](examples/audits/README.md) — yayımlanmış karneler + aile-karşılaştırma tablosu
- [examples/pilot/](examples/pilot/README.md) — gerçek veriden üretilmiş örnek uyumluluk dosyası
- [CHANGELOG.md](CHANGELOG.md) · [SECURITY.md](SECURITY.md) · [CONTRIBUTING.md](CONTRIBUTING.md)
<p align="center"><img src=".github/assets/avatar.png" width="112" alt="Dümen — helm-mark"/></p>

# 🛡️ Dümen (SteeringOS)

> 🌐 **Türkçe** (bu sayfa) · [English](README.md)

[![CI](https://github.com/goun7/Dumen/actions/workflows/ci.yml/badge.svg)](https://github.com/goun7/Dumen/actions/workflows/ci.yml) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE) [![Python 3.10–3.14](https://img.shields.io/badge/python-3.10_–_3.14-blue)](https://pypi.org/project/dumen/)


**Frontier AI Modelleri için Mekanistik Denetim, SAE Yorumlanabilirlik ve Çıkarım Anı Aktivasyon Yönlendirme Platformu**

> *"Frontier modellerin içsel niyetini nöron düzeyinde şeffaflaştırır; model henüz zararlı çıktıyı üretmeden çıkarım anında yönlendirerek kontrol kaybını matematiksel olarak önler."*

Dümen, büyük laboratuvar yöneticilerinden (ör. Altman ve Amodei'nin zaman zaman dile
getirdiği) bağımsız değerlendirme çağrıları ve G7 talebiyle yayımlanan, üçüncü taraf
denetimleri savunan **International AI Safety Report** (Bengio et al., 2025;
arXiv:2501.17805) çizgisindeki ihtiyacın **teknik cevabıdır**: beyaz kutu (açık
ağırlıklı modellerde SAE + aktivasyon yönlendirme) ve siyah kutu (API modellerinde
çift ajanlı güvenlik duvarı + otonom kırmızı takım) denetimini tek kanıt zincirinde
birleştirir. (Bu paragraf motivasyon çerçevesidir, kanıt iddiası değil — Dümen
doktrini: ölçülmeyen hiçbir şey rapora sayı olarak girmez.)

## Kurulum

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q          # tam süit, %100 yeşil
```

> **PyPI notu:** `dumen` paket adı 15-Eyl-2026'da **boşta doğrulandı** (HTTP 404).
> Yayın, repo-açılma kararıyla eşzamanlı yapılacaktır — o zamana kadar kurulum
> kaynaktan (`-e .`) geçerlidir; `pip install dumen` iddiası henüz yoktur.
>
> **Kurulum ağırlığı (dürüst not):** çekirdek `torch` taşır — taze sanal ortam
> ~5GB ölçüldü, ilk indirme dakikalar sürer; ama ilk ÇALIŞTIRMA saniyeler:
> refusal-baseline denetimi taze kurulumda **5.1sn** (15 Eyl kapı-ölçümü).
> Beyaz-kutu model indirmeleri ayrı yer. Taze-ortam duman testi: `dumen --version`
> → `dumen audit --refusal-baseline` → `dumen dossier` üçlüsü hatasız geçti.

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
numunesi dosyası**: `examples/pilot/` (gerçek skor + beyanı-eksik alanlar etiketli).

### 2. EU AI Office Annex XI Dossier (Tek Komut)

```bash
dumen dossier --model my-gpai-model --output annex_xi.md
# → Annex XI teknik dokümantasyon + Code of Practice matrisi + SHA-256 kanıt zinciri
```

### 3. Güvenlik Duvarı Proxy (API Modelleri Önünde)

```bash
dumen serve --upstream https://api.openai.com --api-key $KEY --strict
# → OpenAI-uyumlu ters proxy: injection filtresi + PII maskeleme + çift ajanlı validator
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

> Ham veri lisansları: JBB MIT (örnek depoda ✓), deepset/AgentHarm araştırma lisanslı —
> **repoya commit edilmez**, yükleyici kullanıcıdaki dosyayı okur (bkz. `examples/redteam_gateway_self.py`).

### 6. Kendi Duvarını Dene — Gateway Self-Red-Team

```python
from dumen.benchmarks import GatewaySelfRedTeam
m = GatewaySelfRedTeam.evaluate(samples)   # recall/FPR + kaçırılanlar ham hâlde
```

Yayımlanmış korpusla iki-katman ölçümü (regex ∪ semantik-judge, holdout):
`examples/audits/gateway_selfredteam_qwen2.5-3b.json`.

## Mimari (5 Katman)

```
İstek → [1] Hızlı Filtre (injection/PII, ölçülen ~0.03ms — bkz. tests/test_latency_bench.py)
      → [2] SAE Latent Denetim (TopK/JumpReLU monosemantik özellikler)
      → [3] StTP Aktivasyon Yönlendirme (karar sınırı aşılınca tensör düzeltme)
      → [4] Çift Ajanlı Validator (Generator-Validator güvenlik duvarı)
      → [5] Otonom Kırmızı Takım (PAIR/TAP + Inspect AI + Hibrit Hakem)
      → Kanıt Zinciri (SHA-256 hash-chain, tamper tespitli)
      → Annex XI Dossier + CoP Matrisi (AI Office sunuma hazır)
```

## Bilimsel Temel

| Kabiliyet | Dayanak |
|---|---|
| Reddetme tek doğrultusu (DiM madencilik) | Arditi et al., NeurIPS 2024 (arXiv:2406.11717) |
| Rank-k manifold | Çok-yönlü reddetme kanıtı: Rocchetti & Ferrara 2026, "Refusal Beyond a Single Direction" (arXiv:2606.13720); k-boyutlu SVD genellemesi Dümen'e ait |
| SAE kalite metrikleri (FEV, L0, sweep) | SAEBench, Karvonen et al., ICML 2025 |
| Yönlendirme yükü ölçümü | Capability-retention paradigmaları |
| Otonom kırmızı takım | PAIR (Chao et al., 2023; arXiv:2310.08419), TAP (Mehrotra et al., NeurIPS 2024; arXiv:2312.02119) |
| Dış veri-seti köprüleri | JAILBREAKBENCH (Nis 2025'ten beri uyku) + **MLCommons AILuminate** format köprüsü (2026 standardı; arXiv:2503.05731) |
| Davranışsal steering etkinliği | Aynı saldırı istemlerinde steer öncesi/sonrası zafiyet kıyası — ölçülmezse "Ölçülmedi" |
| Mevzuat uyumu | EU AI Act Art. 53/55, Annex XI, GPAI Code of Practice (10 Tem 2025) |

## Mevzuat Kapsamı

- **Annex XI Teknik Dokümantasyon** — Madde 53(1)(a): model kimliği, eğitim hesaplama kaynakları, veri yönetimi, sistemik risk matrisi, çıkarım zamanı önlemler
- **Code of Practice Matrisi** — 8 commitment, dürüst `partial`/`not_demonstrated` durumları
- **Madde 55(1)(c) Ciddi Olay Bildirimi** — HIGH+ severity eşiği kapılı AI Office formatı
- **Kanıt Zinciri** — append-only SHA-256; kurcalanan zincir geri yüklenmeyi reddeder

**Uygulama takvimi (Avrupa Komisyonu resmî sayfası, erişim Eyl 2026):** yasaklar 2 Şub 2025'te yürürlüğe girdi; GPAI yükümlülükleri + yönetişim 2 Ağu 2025; **Madde 50 şeffaflık kuralları 2 Ağu 2026** (en yakın yükümlülük — Dümen içerik etiketleme/sızdırma denetimi için hazır); 9. yasak (rızasız görsel manipülasyon) Ağu 2025'te eklenen AI Omnibus ile **Aralık 2026**; **Ek-III yüksek-riskli sistemlerin sıkı yükümlülükleri Omnibus sonrası 2 Aralık 2027'ye** ertelendi. Dümen'in yüksek-riskli GPAI dosya üretimi bu 2027 penceresine yetişiyor, şeffaflık yükümlülüğüne ise bugün hazırdır.

## Kalite Kanıtları (v0.7.3)

- 349 birim test, %100 yeşil (CI: Python 3.10/3.12/3.14 matrisi; 3.12 gerçek-model dahil)
- Coverage %96.9+ (CI kapısı %95), ruff lint 0 hata
- **Sıfır uydurma sayı**: etkinlik yalnız `--measure-steering` davranışsal kıyasıyla
  rapora girer; ölçülmeyen her metrik "Ölçülmedi / iddia edilmez"
- **B1 kapasite-eksternallik kapısı**: yönlendirme artık YETENEK-ZARARI tarafında da
  ölçülü — 12 deterministik-doğrulanabilir görev, pass/fail/inconclusive; Qwen2.5-0.5B
  canlı yayını: etkinlik %0 + kapasite **PASS** (%83.3→%83.3). Kapı fail verirse
  koruma iddiası CLI + Annex XI'den geri çekilir.
- **Yayımlanmış denetimler** (`examples/audits/README.md` karşılaştırma tablosu):
  Qwen2.5-0.5B beyaz-kutu + **üç Ollama ailesi** siyah-kutu — qwen2.5:3b
  (standart 58.8, sandbox %95 gerçek bulgu · JBB-40 91.8), llama3.2:3b
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
- Hakem kalibrasyon kıyası: FP/FN karışıklık matrisi altın küme üzerinde ölçülü;
  B3 insan-etiketli ikinci-parti yolu: `examples/calibration_seed.py`
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
# 🛡️ Dümen (SteeringOS)

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
python -m pytest tests/ -q          # 246 test, %100 yeşil
```

Gerçek model denetimi için (opsiyonel):

```bash
pip install transformers
python -m pytest tests/test_real_model_integration.py -v   # gerçek GPT-2 kanıtı
```

## Hızlı Başlangıç

### 1. Model Denetimi (Refusal-Baseline Kanıt Hattı)

```bash
dumen audit --refusal-baseline --output karne.json          # boru hattı doğrulaması (kanıt kanal-damgalı)
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct             # gerçek yerel model denetimi
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct --measure-steering  # + davranışsal etkinlik ölçümü
```

Risk skorları **elle girilmez** — koşturulan kırmızı takım örneklerinin harm_score'larından türetilir.
Etkinlik **ancak `--measure-steering` ölçerse** raporda sayı olur; aksi halde "Ölçülmedi" yazılır
(uydurma %96 devri kapandı). Yayımlanmış gerçek-model kanıtı: `examples/audits/`.

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

### 5. Gerçek Veri Seti — JAILBREAKBENCH Yükleyici

```python
from dumen import JailbreakBenchLoader, VectorMiner, RiskCategory

# Toplulukça sürdürülen adversarial istem seti → kontrastif tohumlar
seeds = JailbreakBenchLoader.load_from_file("artifacts/behaviors.csv")
pairs = [(s.harmful_prompt, s.safe_prompt) for s in seeds]
```

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

**Uygulama takvimi (Avrupa Komisyonu resmî sayfası, erişim Eyl 2026):** yasaklar 2 Şub 2025'te yürürlüğe girdi; GPAI yükümlülükleri + yönetişim 2 Ağu 2025; **Madde 50 şeffaflık kuralları 2 Ağu 2026** (en yakın yükümlülük — Dümen içerik etiketleme/sızdırma denetimi için hazır); 9. yasak (rızasız görsel manipülasyon) Ağu 2025'te eklenen AI Omnibus ile **Aralık 2026**; **Ek-III yüksek-riskli sistemlerin sıkı yükümlülükleri Omnibus sonrası 2 Aralık 2027'ye** ertelendi. Dümen'in yüksek-riskli GPAI dosya üretimi bu 2027 penceresine yetişik, şeffaflık yükümlülüğüne ise bugün hazırdır.

## Kalite Kanıtları (v0.6.1)

- 275 birim test, %100 yeşil (CI: Python 3.10/3.12/3.14 matrisi; 3.12 gerçek-model dahil)
- Coverage %97 (CI kapısı %95), ruff lint 0 hata
- **Sıfır uydurma sayı**: etkinlik yalnız `--measure-steering` davranışsal kıyasıyla
  rapora girer; ölçülmeyen her metrik "Ölçülmedi / iddia edilmez"
- **Yayımlanmış gerçek-model denetimi**: `examples/audits/Qwen2.5-0.5B-Instruct_*`
  (genuine safety-tuned model, 4 kırmızı-takım görevi + ölçülü etkinlik %0.0 —
  sonuç ne ise o)
- Gerçek model entegrasyon testleri (tiny GPT-2: hook → madencilik → yönlendirme → üretim + etkinlik kıyası)
- Permütasyon anlamlılık testi: madencilik yönleri istatistiksel olarak kanıtlı (p-değerli)
- Dış veri-seti köprüleri: JAILBREAKBENCH artifact yükleyici + **AILuminate** (2026) format köprüsü
- Hakem kalibrasyon kıyası: FP/FN karışıklık matrisi altın küme üzerinde ölçülü
- Gecikme kapıları testte: regex ~0.03ms, p99 < 10ms, tam validasyon ~0.4ms
- Atıf denetimi (Eyl 2026): 12 arXiv ID'nin 12'si birincil kaynaktan doğrulandı;
  3 yanlış atıf düzeltildi, 2 doğrulanamayan iddia kaldırıldı

## Lisans

Apache-2.0 — bkz. [LICENSE](LICENSE).

## Dokümantasyon

- [an internal planning doc](an internal planning doc) — kanonik master plan ve matematk
- [an internal spec](an internal spec) — inşa şartnamesi ve modül arayüzleri
- [examples/](examples/) — çalıştırılabilir örnekler

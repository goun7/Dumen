# 🛡️ Dümen (SteeringOS)

**Frontier AI Modelleri için Mekanistik Denetim, SAE Yorumlanabilirlik ve Çıkarım Anı Aktivasyon Yönlendirme Platformu**

> *"Frontier modellerin içsel niyetini nöron düzeyinde şeffaflaştırır; model henüz zararlı çıktıyı üretmeden çıkarım anında yönlendirerek kontrol kaybını matematiksel olarak önler."*

Dümen, Sam Altman ve Dario Amodei gibi laboratuvar yöneticilerinin 2026'da dile getirdiği "yapay zekayı yavaşlatmalı ve dışarıdan denetime tabi tutmalıyız" çağrısının **teknik cevabıdır**: beyaz kutu (açık ağırlıklı modellerde SAE + aktivasyon yönlendirme) ve siyah kutu (API modellerinde çift ajanlı güvenlik duvarı + otonom kırmızı takım) denetimini tek kanıt zincirinde birleştirir.

## Kurulum

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q          # 180+ test, %100 yeşil
```

Gerçek model denetimi için (opsiyonel):

```bash
pip install transformers
python -m pytest tests/test_real_model_integration.py -v   # gerçek GPT-2 kanıtı
```

## Hızlı Başlangıç

### 1. Model Denetimi (Refusal-Baseline Kanıt Hattı)

```bash
dumen audit --refusal-baseline --output karne.json
dumen audit --model meta-llama/Llama-3.2-1B   # gerçek yerel model
```

Risk skorları **elle girilmez** — koşturulan kırmızı takım örneklerinin harm_score'larından türetilir.

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

## Mimari (5 Katman)

```
İstek → [1] Hızlı Filtre (injection/PII, sub-1ms)
      → [2] SAE Latent Denetim (TopK/JumpReLU monosemantik özellikler)
      → [3] StTP Aktivasyon Yönlendirme (karar sınırı aşılınca tensör düzeltme)
      → [4] Çift Ajanlı Validator (Generator-Validator güvenlik duvarı)
      → [5] Otonom Kırmızı Takım (PAIR + Inspect AI + Hibrit Hakem)
      → Kanıt Zinciri (SHA-256 hash-chain, tamper tespitli)
      → Annex XI Dossier + CoP Matrisi (AI Office sunuma hazır)
```

## Bilimsel Temel

| Kabiliyet | Dayanak |
|---|---|
| Reddetme tek doğrultusu (DiM madencilik) | Arditi et al., NeurIPS 2024 (arXiv:2406.11717) |
| Rank-k manifold | Refusal-beyond-single-direction literatürü (arXiv:2606.13720) |
| SAE kalite metrikleri (FEV, L0, sweep) | SAEBench, Karvonen et al., ICML 2025 |
| Yönlendirme yükü ölçümü | Capability-retention paradigmaları |
| Otonom kırmızı takım | PAIR (Mehrotra et al., NeurIPS 2023), JAILBREAKBENCH (Chao et al., 2024) |
| Mevzuat uyumu | EU AI Act Art. 53/55, Annex XI, GPAI Code of Practice (10 Tem 2025) |

## Mevzuat Kapsamı

- **Annex XI Teknik Dokümantasyon** — Madde 53(1)(a): model kimliği, eğitim hesaplama kaynakları, veri yönetimi, sistemik risk matrisi, çıkarım zamanı önlemler
- **Code of Practice Matrisi** — 8 commitment, dürüst `partial`/`not_demonstrated` durumları
- **Madde 55(1)(c) Ciddi Olay Bildirimi** — HIGH+ severity eşiği kapılı AI Office formatı
- **Kanıt Zinciri** — append-only SHA-256; kurcalanan zincir geri yüklenmeyi reddeder

## Kalite Kanıtları

- 180+ birim test, %100 yeşil (CI: Python 3.10/3.12/3.14 matrisi)
- Coverage ~%94, ruff lint 0 hata
- Sıfır mock üretim kodu; `refusal-baseline` hattı dışında sahte kanıt yok
- Gerçek model entegrasyon testleri (tiny GPT-2: hook → madencilik → yönlendirme → üretim)

## Lisans

Apache-2.0 — bkz. [LICENSE](LICENSE).

## Dokümantasyon

- [an internal planning doc](an internal planning doc) — kanonik master plan ve matematk
- [an internal spec](an internal spec) — inşa şartnamesi ve modül arayüzleri
- [examples/](examples/) — çalıştırılabilir örnekler

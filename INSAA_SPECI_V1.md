# 77 · Dümen (Dumen) — İnşa ve Kodlama Şartnamesi (v1.0)
## Teknik Sözleşmeler, Modül Arayüzleri ve Doğrulama Matrisi

> **Kanonik Statü:** `01_unicorn/77-Dumen/INSAA_SPECI_V1.md`  
> **Hedef:** Sıfır-Placeholder, Sıfır-Mock, %100 Tip Güvenli ve Asenkron Blokajsız Mimari.

---

### 1. DİZİN VE PAKET YAPISI

```
01_unicorn/77-Dumen/
├── dumen/
│   ├── __init__.py            # Paket kökü (v0.1.0, versiyon ve dışa aktarılan API'ler)
│   ├── core/                  # Çekirdek matematik ve hook katmanı
│   │   ├── __init__.py
│   │   ├── types.py           # Pydantic v2 ve PyTorch tensör veri modelleri
│   │   ├── hooks.py           # PyTorch & vLLM model_runner hook yöneticisi
│   │   ├── steering.py        # StTP / StMP projeksiyon ve yönlendirme algoritmaları
│   │   ├── sae_engine.py      # TopK & JumpReLU SAE çıkarım motoru
│   │   └── ov_circuits.py     # Attention OV devresi seyreltme matrisi
│   ├── gateway/               # Hat içi API & Çift Ajanlı Güvenlik Duvarı
│   │   ├── __init__.py
│   │   ├── proxy.py           # FastAPI asenkron ters proxy (sub-10ms)
│   │   ├── validator.py       # Çift Ajanlı Doğrulayıcı (Validator LLM)
│   │   └── filters.py         # Fast tokenizer & regex injection filtresi
│   ├── redteam/               # Otonom Kırmızı Takım & Inspect AI
│   │   ├── __init__.py
│   │   ├── inspect_adapter.py # UK AISI Inspect AI köprüsü
│   │   ├── hrl_engine.py      # Çok turlu saldırı yörünge planlayıcısı (MDP)
│   │   └── judge.py           # Otomatik zafiyet skorlayıcı (Judge LLM)
│   ├── reports/               # Denetim ve Mevzuat Uyumluluk Motoru
│   │   ├── __init__.py
│   │   ├── eu_ai_act.py       # EU AI Act Tier-1/Tier-2 uyum denetleyicisi
│   │   └── scorecard.py       # JSON ve Markdown denetim sertifikası üreticisi
│   └── cli.py                 # `dumen` CLI komut satırı arayüzü
├── tests/                     # Kapsamlı test süiti (pytest)
│   ├── test_types.py
│   ├── test_steering.py
│   ├── test_ov_circuits.py
│   ├── test_sae_engine.py
│   ├── test_gateway.py
│   ├── test_inspect_adapter.py
│   └── test_cli.py
├── pyproject.toml             # Hatchling / uv paketleme tanımları
├── DUMEN_MASTER_100.md        # Kanonik master plan
└── INSAA_SPECI_V1.md          # Bu inşaat belgesi
```

---

### 2. VERİ TİPLERİ VE MODELLER (`dumen/core/types.py`)

```python
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

class SteeringMethod(str, Enum):
    CAA = "contrastive_activation_addition"
    STTP = "steer_to_target_projection"
    STMP = "steer_to_mirror_projection"

class RiskCategory(str, Enum):
    DECEPTION = "deception"
    CYBER_ATTACK = "cyber_attack"
    BIO_HAZARD = "bio_hazard"
    SANDBOX_ESCAPE = "sandbox_escape"
    JAILBREAK = "jailbreak"
    PII_LEAK = "pii_leak"
    HALLUCINATION = "hallucination"

class SteeringVector(BaseModel):
    layer_idx: int
    dimension: int
    vector: List[float]
    target_risk: RiskCategory
    threshold: float = Field(default=0.5, description="Karar sınırı eşik değeri")
    strength: float = Field(default=1.0, description="Yönlendirme katsayısı (alpha)")
    sparse_mask: Optional[List[int]] = Field(default=None, description="OV devresi seyreltme maskesi")

class InspectionResult(BaseModel):
    timestamp: str
    model_name: str
    is_safe: bool
    risk_scores: Dict[RiskCategory, float]
    active_features: List[int]
    steered: bool
    latency_ms: float
    output_text: str

class AuditReport(BaseModel):
    report_id: str
    model_tested: str
    total_evaluations: int
    overall_safety_score: float  # 0.0 - 100.0
    risk_breakdown: Dict[RiskCategory, float]
    eu_ai_act_compliant: bool
    nist_rmf_compliant: bool
    details: List[Dict[str, Any]]
```

---

### 3. MODÜL İŞLEYİŞ SÖZLEŞMELERİ

#### 3.1. `dumen.core.steering.SteeringEngine`
- **Girdi:** `hidden_states: torch.Tensor` $[B, S, D]$, `layer_idx: int`, `vectors: List[SteeringVector]`.
- **İşlem:**
  1. Karar hiper-düzlemi kontrolü: $s = \sigma(w^T x + b)$.
  2. Eğer $s > \tau$, ortogonal izdüşüm uygulanır:
     $$x_{\text{proj}} = x - \frac{x \cdot v}{\|v\|^2} v$$
     $$x_{\text{steered}} = x_{\text{proj}} + \alpha v_{\text{safe}}$$
  3. Attention OV devresi maskesi varsa sadece ilgili indisler güncellenir.
- **Çıktı:** Müdahale edilmiş `torch.Tensor` $[B, S, D]$.

#### 3.2. `dumen.gateway.proxy.DumenProxy`
- **Hedef:** API modellerinin (OpenAI, Anthropic) önüne geçebilen sub-10ms gecikmeli ters proxy.
- **Protokol:** OpenAI `/v1/chat/completions` ile birebir uyumlu.
- **Pipeline:**
  1. Girdi token/regex filtresi (Hızlı Prompt Injection kontrolü).
  2. Hedef modele asenkron HTTP çağrısı (`httpx.AsyncClient`).
  3. Çıktı Validator ajanına paralel iletim (PII + Harm değerlendirmesi).
  4. Eğer çıktı zararlıysa fallback güvenli yanıt döndürülür.

#### 3.3. `dumen.redteam.inspect_adapter.InspectBridge`
- **Protokol:** UK AISI `inspect_ai` paketini çalıştırabilen modüler wrapper.
- **Görevler:** Modeli çok turlu jailbreak ve sandbox kaçış senaryolarında test eder.
- **Çıktı:** Standardize `EvalLog` ve skor özeti.

---

### 4. BİRİM TEST VE KABUL MATRİSİ

| Test Dosyası | Hedeflenen Davranış | Başarı Eşiği |
| :--- | :--- | :--- |
| `test_types.py` | Pydantic modelleri ve serileştirme doğrulaması | %100 tip geçerliliği |
| `test_steering.py` | StTP formülü ve tensor izdüşüm matematiği | Cosine similarity < 0.05 (ortogonalite kanıtı) |
| `test_ov_circuits.py` | Attention OV devre seyreltme maskesi | %85+ seyreltmede yönlendirme etkinliği |
| `test_sae_engine.py` | TopK SAE sözlük kodlama ve yeniden inşa | TopK sparsite katsayısı $k \le 64$ |
| `test_gateway.py` | FastAPI proxy gecikme ve güvenlik duvarı filtreleri | Sub-10ms p99 ve injection yakalama |
| `test_inspect_adapter.py` | Inspect AI görev koşturma ve rapor üretimi | Yapılandırılmış JSON uyum çıktısı |
| `test_cli.py` | `dumen audit` ve `dumen serve` komutları | Çıkış kodu 0 ve terminal raporlama |

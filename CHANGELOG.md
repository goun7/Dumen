# Değişiklik Günlüğü (Changelog)

Biçim: Keep a Changelog · Bu proje SemVer kullanır. Sürümlerin *kanıtları*
`examples/audits/` altında yeniden-üretilebilir artifact'larla durur.

## [Unreleased]

## [0.7.2] - 2026-09-15

Kamuya-açılma öncesi taze-ortam kontrolü ve ilk satış numunesi.

- **Paketleme düzeltmesi (taze-sanal-ortam duman-testi bulgusu):** `numpy`
  dolaylı-değil doğrudan bağımlılık olarak bildirildi — yeni kullanıcıda
  torch'un "Failed to initialize NumPy" ilk-koşum uyarısı kesildi (ölçüldü:
  taze ortam 5.4GB, refusal-baseline denetimi **5.1sn**, üçlü CLI dumanı hatasız).
  README'ye dürüst "kurulum ağırlığı" notu eklendi.
- **Satış numunesi (`examples/pilot_dossier.py` + `examples/pilot/`):**
  YAYIMLANMIŞ gerçek karne (qwen2.5:3b JBB-40, safety 91.8) üzerinden tam
  Annex XI dosyası + CoP matrisi (%62 — eksik satırlar bilinçli: müşteri
  beyanı + olay-hattı) + karne-hash'ini mühürleyen SHA-256 kanıt zinciri.
  Hesaplama alanı 6·N·D sıra-tahmini olarak ETİKETLİ (3.34e23 < 1e25 →
  Madde 3(63) eşik-altı; D=18T arXiv:2412.15115'ten canlı doğrulandı);
  doğrulanamayan her alan köşeli-parantez [beyan bekliyor].
- Değişen API/şema YOK — semantik-sürüm tek sebebi paketleme bulgusu.

## [0.7.1] - 2026-09-15 — B1 kapasite-eksternallik kapısı + B5 çoklu-aile yayını
### Eklendi
- **B1 `CapabilityGate`**: steering'in model YETENEĞİNE verdiği zarar artık
  ölçülüyor — 12 deterministik-doğrulanabilir görev (LLM-hakem yok, döngüsel
  kanıt yok; echo-safety testli). pass/fail/inconclusive; **fail → koruma
  iddiası CLI ve AnnexXI'den geri çekilir** (zarar veren müdahale müdahale
  değildir). İlk canlı eş: Qwen2.5-0.5B etkinlik %0 + kapasite PASS (%83.3→%83.3).
- `--request-timeout` (audit; vars. 300sn) — saha bulgusu: tek-VRAM'de soğuk
  model yükleme + yavaş üretim, 180sn'lik bütçeyi patlattı (phi3:mini/GTX-1070,
  ~1sn/tok). Zaman aşımı hâlâ temiz `EndpointError`; sahte-refüz üretilmez.
- **B5 çoklu-aile yayınları** (`examples/audits/` + karşılaştırma tablosu):
  llama3.2:3b (std 77.5 · JBB-40 **91.3**) ve phi3:mini (std 95.0 · JBB-10
  97.0 — n-farkı tabloda ayrı işaretli) — qwen2.5:3b JBB-40 91.8 ile
  aynı-derinlik aileler-arası tutarlılık ÖLÇÜLDÜ; llama std'de cyber %60
  GERÇEK zafiyet bulgusu.
- **B3 süreç aracı**: `examples/calibration_seed.py` — gerçek (prompt, response)
  çiftlerinden insan-ikinci-etiketli B3 çalışma-sayfası üretir; ilk canlı çıktı:
  llama3.2:3b × 20 çift (3 refusal / 17 mixed — fastpath'in zor bölgesi). Ham
  çiftler depo-dişi (ikili-kullanım politikası), yayımlanan yalnız dağılım.
### Değişen yok
- Siyah-kutu/refusal-baseline kanalları, API yüzeyi, rapor şeması (yalnız
  `capability_regression` alanı eklendi — eski artifact'lar şema-kırılmaz).

## [0.7.0] - 2026-09-15 — API-sonu denetimi + gerçek-katalog red-teaming
### Eklendi
- **Siyah-kutu API denetim kanalı** (`dumen audit --endpoint`): Ollama /
  vLLM / LM Studio / OpenAI-uyumlu her sunucudan denetim; deterministik
  temperature=0, HTTP hatası SAHTE-REFÜZ üretmez (EndpointError patlar).
- **İlk yerel-gerçek-model denetimi yayında**: Ollama qwen2.5:3b —
  standart-suite karne (`safety 58.8`, sandbox %95) + 40-görev JBB wide-audit
  (`safety 91.8`, %0 jailbreak) — `examples/audits/qwen2.5-3b_ollama_*.json`.
- **Gateway öz-kırmızı-takım kıyası** (`GatewaySelfRedTeam`): yayımlanmış
  deepset/prompt-injections korpusunda İKİ KATMAN (regex ∪ semantik LLM-judge)
  recall/FPR matrisleri; regex desenleri EN+DE aileleriyle sertleştirildi
  (holdout FPR %0, precision %100); `JudgeEvaluator.classify_injection`.
- **Harici saldırı kataloğu köprüleri**: HarmBenchLoader (400 gerçek
  davranış) + AgentHarmLoader (176 agentic görev) + `--dataset` CLI
  otomatik-şema algılama (JBB CSV · HarmBench CSV · AgentHarm JSON ·
  AILuminate JSON/JSONL).
### Düzeltildi
- JBB/AILuminate `CATEGORY_MAP`: gerçek dağıtım etiketleriyle kalibre
  (Malware/Hacking→cyber_attack, Disinformation→hallucination, Privacy→pii_leak).

## [0.6.1] - 2026-09-15 — Kanıt bütünlüğü sürümü
### Düzeltildi (derin denetim bulguları)
- Uydurma başarı sayıları tasfiye: "%96.2 Aktif Koruma" → üç-durumlu
  ölçülmüş etkinlik (Ölçülmedi ⚪ / %0 🟠 / +%X 🟢) — davranışsal
  `SteeringEfficacyBench` (before/after judge-kıyası; kozmetik kosinüs reddi).
- `--measure-steering` gerçek ölçüm hattı (madencilik + canlı hook + steer'li üretim).
- vLLM/sub-1ms/Anthropicnative/JBB-canlı iddiaları → doğrulanmış metinler;
  SLA iddiası ÖLÇÜLMÜŞ latency bench'iyle (`test_latency_bench.py`) değiştirildi.
- 3 yanlış akademik atıf düzeltildi (PAIR/TAP; RepE↔StMP; 2606.13720 başlığı);
  doğrulanamayan alıntılar yumuşatıldı; EU takvimi EC-kanıtlı güncellendi.
- dossier/serve kanalları: refusal-baseline damgası + `evidence_channel` +
  zincir-head'i Annex XI'de; Art.14 ❌ için bağlam notu.
### Altyapı
- CI coverage kapısı gerçekten koşar hale getirildi (pytest-cov eksikti);
  3.12-job gerçek-model testleri; kullanılmayan bağımlılıklar silindi;
  AILuminate format köprüsü; tehdit-modeli & sınırlar bölümü (§6.5).

## [0.6.0] - 2026-09-14 — Evidence-gap closure
- rank-k altuzay madenciliği + bootstrap güven aralığı + permutation p;
  joint-nullspace steering; InspectBridge red-team; evidence-chain raporları.

## [0.5.0] - 2026-09-13 — Mekanistik çekirdek doğrulaması
- OV-devre maskesi, çıktı-filtresi kritik-bug düzeltmesi, StTP/StMP birleşik hat.

## [0.4.0] ve öncesi — Prototip
- Temel madencilik/hook/rapor hattı; 52–173 test aralığı.

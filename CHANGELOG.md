# Değişiklik Günlüğü (Changelog)

Biçim: Keep a Changelog · Bu proje SemVer kullanır. Sürümlerin *kanıtları*
`examples/audits/` altında yeniden-üretilebilir artifact'larla durur.

## [Unreleased]

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

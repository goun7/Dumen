# Harici Veri-Setleri — Lisans Politikası

Bu dizinde **yalnız dağıtım-lisansı repo politikamızla uyumlu** ham veriler
bulunur:

| Dosya | Kaynak | Lisans | Durum |
|---|---|---|---|
| `jbb_harmful_behaviors.csv` | JailbreakBench/JBB-Behaviors (HF) | **MIT** ✓ | commit'li (100 davranış) |

## Commit EDİLMEYENLER (bilinçli)

- **deepset/prompt-injections** (CC-BY-NC-4.0) — ham veri depoya girmez;
  `examples/redteam_gateway_self.py` indirip önbelleğe (`~/.cache/dumen/`)
  yazar, yayımlanan yalnız METRİKLER + en fazla birkaç kısa alıntıdır.
- **HarmBench** (centerforaisafety) ve **AgentHarm** (ai-safety-institute,
  lisans "other" + canary-guid) — aynı politika: yükleyiciler şemayı
  sabitler, veri kullanıcıdadır.

Gerekçe: NC/other lisanslı ham veriyi redistribüze etmek, "yerel/air-gapped
çalışır" ürün iddiamızı hukuki çelişkiye düşürürdü. Kanıt-bütünlüğü = kaynak
doğruluğu demektir; yükleme komutları README'de ve artifact log'larında.

## Yeniden üretme

```bash
# JBB (MIT — depoda)
curl -sL -o examples/datasets/jbb_harmful_behaviors.csv \
  https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main/data/harmful-behaviors.csv
# HarmBench
curl -sL -o harmbench.csv \
  https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/data/behavior_datasets/harmbench_behaviors_text_all.csv
# AgentHarm
curl -sL -o agentharm.json \
  https://huggingface.co/datasets/ai-safety-institute/AgentHarm/resolve/main/benchmark/harmful_behaviors_test_public.json
```

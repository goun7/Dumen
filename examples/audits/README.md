# Yayımlanmış Kanıt Artifact'ları (Dümen)

Her dosya bir DENETİM KANITIDIR: komutuyla, zaman damgasıyla, ham kaçırmayla.
Karne sayıları elle girilemez — `details`/agregatlar koşturulan örneklerden
türetilir; ölçülmeyen alan `None`/"Ölçülmedi" kalır (v0.6.1 doktrini).

## Model karneleri — üç aile × iki kanal

| Artifact | Model | Kanal | Görev | Safety | En yüksek risk | Steering etkinlik | B1 kapasite kapısı |
|---|---|---|---|---|---|---|---|
| `Qwen2.5-0.5B-Instruct_audit.json` | Qwen2.5-0.5B-Instruct | beyaz-kutu HF | 4 | 97.5 | sandbox %10 | %0.0 (ölçüldü, kazanç yok) | **PASS** %83.3→%83.3 (0.0pp) |
| `qwen2.5-3b_ollama_standard.json` | qwen2.5:3b | siyah-kutu API | 4 | 58.8 | **sandbox_escape %95** 🔴 | Ölçülmedi (aktivasyon yok) | — |
| `qwen2.5-3b_ollama_jbb40.json` | qwen2.5:3b | siyah-kutu API | 40 (JBB) | 91.8 | deception %9 | Ölçülmedi | — |
| `llama3.2-3b_ollama_standard.json` | llama3.2:3b | siyah-kutu API | 4 | 77.5 | **cyber_attack %60** 🔴 | Ölçülmedi | — |
| `llama3.2-3b_ollama_jbb40.json` | llama3.2:3b | siyah-kutu API | 40 (JBB) | 91.3 | cyber %10 | Ölçülmedi | — |
| `phi3-mini_ollama_standard.json` | phi3:mini | siyah-kutu API | 4 | 95.0 | bio %10 | Ölçülmedi | — |

**Aileler-arası tutarlılık (ölçülmüş bulgu):** iki mimari-farklı 3B modelin
JBB-40 wide-audit skorları 91.3 / 91.8 — kırmızı-takım skorlaması model-ailesine
karşın stabil görünüyor; standart-suite'te çıkan %58.8/%77.5'lik farklılık ise
küçük-n (4 görev) + suite-bağımlılığı ile açıklanır, abartılmaz.

## Davranış kıyasları

| Artifact | Ne kanıtlar |
|---|---|
| `gateway_selfredteam_qwen2.5-3b.json` | Kendi duvarımızın deepset HOLDOUT'unda üç-katman karışım matrisleri: regex recall %20 (FPR %0), semantik %76.7 (FPR %16.1), combined %78.3 — kaçırmalar/FP'ler HAM METİNLE; eşik süpürmesi FPR'ı düşürmüyor (3B-judge sınırı, B3 gerekçesi) |

## Yeniden üretme

```bash
# siyah-kutu (Ollama açıkken; tek-VRAM'de --request-timeout soğuk yüklemeye karşı)
dumen audit --model llama3.2:3b --endpoint http://127.0.0.1:11434/v1 \
    --request-timeout 300 --output karne.json
dumen audit --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1 \
    --dataset examples/datasets/jbb_harmful_behaviors.csv --dataset-limit 40

# beyaz-kutu + etkinlik + B1 kapasite kapısı (transformers gerekli; yavaş)
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct --measure-steering

# gateway öz-kırmızı-takımı (deepset verisi ~/.cache'e inder, commit'lenmez)
python examples/redteam_gateway_self.py
```

## Politika

- Ham CC-BY-NC / research-lisanslı girdi YALNIZ `~/.cache/dumen/` altında;
  depoda metrik + MIT-lisanslı JBB CSV (`examples/datasets/`).
- Model-çıktısı türev-zararlı içerik (başarılı jailbreak yanıtları) yayımlanmaz;
  B3 etiketleme-çalışma-sayfaları da ham hâliyle dışa aktarılmaz
  (`examples/calibration_seed.py` başlığındaki politika).
- Bu dizindeki hiçbir sayı elle yazılmadı; şüphe → komutu koşt, karşılaştır.

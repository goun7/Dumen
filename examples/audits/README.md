# Yayımlanmış Kanıt Artifact'ları (Dümen)

> EN: every file here is a published AUDIT EVIDENCE artifact (command + timestamp + raw misses); the comparison table below is generated from the JSONs, not typed.

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
| `phi3-mini_ollama_jbb10.json` | phi3:mini | siyah-kutu API | **10** (JBB) | 97.0 | deception %3 | Ölçülmedi | — |
| `qwen2.5-3b_harmbench40.json` | qwen2.5:3b | siyah-kutu API | **40 (HarmBench standard)** | **91.1** | hallucination %9.2 | Ölçülmedi (aktivasyon yok) | — |
| `Qwen2.5-0.5B-Instruct_extended.json` | Qwen2.5-0.5B-Instruct | beyaz-kutu HF | 4 (+22 B1 koşusu) | 97.5 | sandbox %10 | %0.0 (ölçüldü, kazanç yok) | **PASS** %59.1→%59.1 (0.0pp, 22 görev: internal-12+gsm-10) |
| `qwen2.5-3b_capability32_blackbox.json` | qwen2.5:3b | siyah-kutu API (yetenek kanalı) | 32 B1 görevi | — (güvenlik karnesi DEĞİL) | — | — | TR %70 ↔ EN-GSM %60 — aşağıda |

**Çok-dillilik bulgusu (ilk TR-B1 kanıtı, 16-Eyl-2026):** aynı model/kanal/görev
sınıflarında çok-adımlı aritmetik doğruluğu TR **7/10** ↔ EN-GSM
**6/10** (internal-12: 12/12). 2-adımlı görevler
her iki dilde geçiliyor; 3-işlemli görevler iki dilde de kaçar — yani
yetenek-yüzeyi dil-eşdeğer görünüyor. Bu, refusal-yönü dil-evrenselliği
sonucunun (arXiv:2505.17306) yetenek tarafıyla tutarlıdır; n=10×2 ile SINIRLI
bir ölçümdür ve yayınlanmış ilk TR/B1-kapı kanıtı olarak değil, **bu depoda
ölçülmüş ilk kendi kanıtımız** olarak raporlanır.

**HarmBench standard-40 (kamu kataloğu formatı):** qwen2.5:3b → **91.1**
güvenlik skoru, en-kötü hallucination %9.2. Ham davranış
kataloğu lisans nedeniyle dağıtılmaz; `--dataset` yerel kopyayla yeniden üretilir
(komut dosyanın başında).

**Aileler-arası tutarlılık (ölçülmüş bulgu):** aynı-derinlik kıyası JBB-**40**'ta:
qwen2.5:3b 91.8 vs llama3.2:3b 91.3 — iki mimari-farklı model, aynı bant.
phi3:mini'nin JBB yayını **10**-görevlik (tek-VRAM eşzamanlı-yük bütçesi — bkz.
`phi3-mini_ollama_run.log` içindeki başarısız JBB-40 denemesi); 97.0 sayısı
farklı-n ile KARŞILAŞTIRILMAZ, ayrı saturda tutulur. Standart-suite'te çıkan
%58.8/%77.5'lik farklılık küçük-n (4 görev) + suite-bağımlılığı ile açıklanır,
abartılmaz.

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

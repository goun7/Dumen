# Örnekler Dizini

| Betik / dosya | Ne yapar | Ne gerektirir |
|---|---|---|
| `audits/` | **Yayımlanmış kanıt artifact'ları**: 6 karne + öz-kırmızı-takım kıyası + karşılaştırma tablosu (`audits/README.md`) | — (salt-okunur kanıt) |
| `datasets/jbb_harmful_behaviors.csv` | MIT-lisanslı JBB-Behaviors (100 yayımlanmış saldırı isteği) — `--dataset` ile gerçek saldırılarla genişlet | lisanslı ham veri politikası: `datasets/README.md` |
| `redteam_gateway_self.py` | **Kendi duvarının kırmızı takımı**: deepset/prompt-injections holdout'unda regex ∪ semantik-yargıç karışım matrisleri + güven-eşiği süpürmesi; ham kaçırmalarla JSON artifact | `pip install datasets pyarrow`; CC-BY-NC ham veri `~/.cache/dumen/`'e iner, commit'lenmez |
| `calibration_seed.py` | **B3 süreç aracı**: endpoint'ten gerçek (prompt, response) çiftleri + fastpath makine-etiketi → insan-ikinci-etiketli ÇALIŞMA-SAYFASI (JSONL) | çalışan Ollama/vLLM; ham çiftler depo-dışı (ikili-kullanım politikası) |
| `full_audit_pipeline.py` | Uçtan uca denetim hattı: tohumlar → aktivasyon → rank-k+bootstrap madencilik → yönlendirme+yük → kırmızı-takım → Annex XI → SHA-256 kanıt zinciri | opsiyonel HF model; transformers yoksa sentetik-çıkarıcıya düşer (etiketli) |

Kural (doktrin): buradaki hiçbir betik ölçmediği bir sayıyı yayımlamaz;
örnek çıktıların tamamı `audits/` altında komut-log'lu artifact olarak durur ve
`audits/README.md`'deki komutlarla yeniden üretilebilir.

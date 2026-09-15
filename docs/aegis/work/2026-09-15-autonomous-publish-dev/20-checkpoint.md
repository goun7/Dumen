# CHECKPOINT (her dilim sonrası güncelle — RESUME BURADAN)
## Tamamlanan dilimler (hub commit'leri)
- A1 ca41861 signing (keys/sign/verify, 19 test) ✓
- A2 d29114e export HTML (mistune escape=True v3 içtihadı; XSS testi; paket-varlığı) ✓
- A3 9f92bc6 watch (-m dumen.cli tuzağı; halt=exit2; injectables) ✓
- B1-gsm (test 22✓, LIVE KOŞU BEKLİYOR) — commit kapıda
## Devam eden
- /tmp/gate_r9a.log tam-kapı (362 test + cov≥95) ~21:0x
## Sonraki adımlar (sıra)
1. gate → GSM commit → LIVE extended audit (Qwen2.5-0.5B, nohup, /tmp/live_ext.log)
2. HarmBench-40: indir → /tmp (DEPOYA SOKMA) → qwen2.5:3b ollama karne → examples/audits JSON commit
3. PAPER.md (yalnız ölçülmüş; referansları subagent B4 listesiyle birleştir, doğrulanmamışı alma)
4. awesome-ai-safety + awesome-eu-ai-act PR (fork→branch→PR; metrik=API'den okunabilen gerçek)
5. Yüzey: README EN+TR yeni komutlar (sign/verify/export/watch) + B1 dış-görev satırı + parite
6. 0.7.4: version bump, CHANGELOG, build, dist_hygiene, twine check → public cherry-pick'leri → public kapıları → push → release → PyPI → temiz-oda pip teyit
## Drift kontrolü
Hedefe hizalı; yeni sahiplik yok (watch spawn=re-use); retirement: yok.

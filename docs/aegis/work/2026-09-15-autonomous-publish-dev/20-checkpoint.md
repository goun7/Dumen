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

## 2026-09-16T02:2x (checkpoint-2 — provenance+paper+community slice)
- Hub commits: e1277a7 provenance auditor (robust-median+token-swap dedektörü, 10 synth test+tiny-gpt2 CLI schema test), b920120 PAPER.md iskelet+§6 makine-render motoru (SAEBench ID bellek-hatasi YAKALANDI→2503.09532), 8dd2ad5 dossier --provider/--contact honest-placeholder.
- Community: PR GenAI-Gurus/awesome-eu-ai-act#76 (Dümen entry, disclosure'lı) + Giskard issue#36 (tools-section onerisi). dapurv5 listedisi paper-only → uygun-degil (zorlamadim).
- Live queue bash-38: gate r11 belirsiz-RC (makine-yarisi; FINAL gate queue bitince) → EXT koşuyor → HB40 → PROV-live. Sonra: render --write, README sayfa-lari, CI paper-check adimi, FINAL tam gate, E-release.
- Kullanicidan-onay-li kalanlar: arXiv gonderimi (hesap), OG.png upload, outreach GONDERIMI (taslaklar hazir, gonderim yok).

## 2026-09-16T05:0x (checkpoint-3 — canlı sayılar YAYINDA, release zinciri başlamak üzere)
- ÖLÇÜLDÜ & commited: extended-22 PASS %59.1→%59.1 0.0pp + efficacy %0 (aynı koşu, tutarlı) | HB-40 91.1 (en-kötü hallucination %9.2) | CAP32: TR %70 / EN-GSM %60 / iç-12 %100 — 'parity' DENMEDİ (gürültü bandı dürüst dili) | provensans n=8 NEGATİF'i artifact (recall 0 — kalibrasyon sınırı yayında), 20-çiftli --sweep eğrisi + FINAL gate = chain bash-44'te otomatik (q3watch.log → PROVS_RC, gate_final.log).
- Hub HEAD 223f8e2..: +paper/README/CHANGELOG/sürüm 0.7.4 çakmaları. 402 test. Parite 210 ✓.
- KALAN İŞ (sırayla): (1) sweep+gate sonuçlarını oku → README/karne provenance satırı + render --write PAPER §6 + CI'ye paper-check adımı ekle; (2) public clone content-sync (~/tmp_verify/sync_to_public.sh HAZIR — allowlist; progress/findings.md git-rm; karne README'sı + PAPER + assets senkron; IDENTITY: clone-local goun7 ayarla) + tree-diff kontrol; (3) push main + tag v0.7.4 + gh release (NOTLAR: /tmp/release_notes_074.md) + twine upload + temiz-venv pip doğrulaması (~/tmp_verify, venv'te --system-site-packages YOK); (4) goal'u complete yap (veya PROGRESSDUMP).
- Kullanıcı-bağlı kalanlar: arXiv gönderimi (30-submission-plan.md), outreach GÖNDERİMİ (outreach_letters.md hazır), og.png UI-upload.
- Dersler bu pencerede: gate-log'a sed -i YASAK (kanıt-bozulması kanıtlandı); CHANGELOG'a ölçülmemiş sayı yazmıştım (424→402 kendi-denetim); .to(cuda) tuzak (sm_61); _yesno EN-only mayını.

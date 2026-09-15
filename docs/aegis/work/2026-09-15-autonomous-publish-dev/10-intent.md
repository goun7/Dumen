# Otonom Yayın-Sonrası Geliştirme Penceresi — 15 Eyl 2026 23:50 → ~08:00
## İstenen sonuç
v0.7.4: imzalama + denetçi-HTML + watch + GSM-dış-görev B1 + HarmBench canlı karne
+ PAPER.md taslağı + outreach (İÇ) + awesome-list PR'ları — hepsi kapılı, public'te CI-yeşil.
## Kapsam çiti
hub'da geliştir → public clone'a cherry-pick → public'te tam kapı → push → 0.7.4 release+PyPI.
YASAK: gerçek-dışı sayı; iç-belge sızıntısı; Ollama servisine dokunma; force-push.
## Non-goals
Hosting katmanı, TSA zaman-mühürü (gelecek sürüm), eIDAS iddiası, ham lisanslı corpus depoya.
## Risk işaretleri
- PyPI upload geri-alınamaz → hijyen kapısı her push'tan ÖNCE (dist_hygiene + sdist listeleme).
- GPU: beyaz-kutu canlı koşuları ~6dk; pytest ile ÇAKIŞTIRMA (sıraya koy).
- Subagent'lar: cop_targets + b4_literature (araştırma_cop_targets.md, research_b4_literature.md hedef yolları).
## Baseline okuma
goal-ae37a732 rev1; KAMUYA_ACMA.md kapanış; progress.md içtihatları; capability_gate.py; evidence_chain.py; cli.py desenleri.

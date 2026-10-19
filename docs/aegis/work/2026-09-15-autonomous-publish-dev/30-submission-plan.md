# YAYIN PLANI — arXiv + topluluk (HAZIR-METİN; gönderim kullanıcı onayına bağlı)

## arXiv (cs.CR ana; cs.AI/cs.CL cross-list)
- Dosya: PAPER.md → LaTeX çevirisi GEREKMEZ; arXiv markdown→PDF yüklemeyi
  kabul etmiyor → iki yol: (a) Overleaf-lite: pandoc ile tex (repo'da
  `scripts/` ekle: `pandoc PAPER.md -o paper.pdf --pdf-engine=xelatex`
  Xelatex kutuda YOK — kurulum `apt texlive-xetex` ~700MB; kullanıcı kararı),
  (b) arXiv'e PDF + source: tex iskeleti PAPER.md'den üretilmiş ayrı dosya.
  → Kullanıcıya sun: (b) için hazır tex-iskeleti üretilebilir; gönderim
  hesabı kullanıcının (kurucu kimliği — makale yazarlığı kimlik işi).
- Kanıt paketi: repo tag v0.7.4 + examples/audits/ (sweep + TR + HB dahil).
- "First" iddiaları kill-kriter: gönderimden ÖNCE §4 taraması + 3.6/3.5
  claim-cümleleri için 15-Eyl corpus'una rakip eklenmiş mi kontrolü
  (ara alt-süre: `research_b4_literature.md` §4 DOĞRULANAMADI listesi).
- Öneri tam başlık: "Dümen: an open-source, evidence-first audit engine for the
  EU AI Act's general-purpose AI obligations" (PAPER.md §başlık ile birebir).

## Hacker News (Show HN) — hazır-taslak (sayılar yüzey-gününde doldurulur)
Title: Show HN: Dümen – open-source EU AI Act audit engine with SHA-256 evidence chains
Body:
> Apache-2.0, `pip install dumen`. Measures models (black-box red-team
> batteries + white-box activation-steering probes on ≤3B open weights,
> consumer GPU/CPU), gates capability harm with deterministic tasks (now with
> an original Turkish task set — multilingual evidence is missing everywhere),
> and writes every step into a tamper-evident chain rendered into Annex XI/CoP
> docs. The repo ships its own negatives: 0% steering efficacy on one family;
> a data-provenance detector that measurably does NOT fire at low poisoning
> intensity (intensity curve published). No fabricated numbers: unmeasured
> fields print as "Not measured". [repo link] [paper link]
Zamanlama: v0.7.4 + HB/TR sayıları yayında + PR#76 merge sonrası (güvenilir
dağıtım izlenimi). Hafta içi 14:00-16:00 UTC.

## awesome-listler
- PR#76 (GenAI-Gurus) bekliyor — merge olursa Giskard issue#36'ya "already
  listed elsewhere" referansı eklenir (sosyal kanıt).
- Üçüncü hedef: hari-sikchi/awesome-ai-safety TOOLS bölümü yok → issue yerine
  CONTRIBUTING'i okunur; uygunsa tek PR.

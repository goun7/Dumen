# OUTREACH — GÖNDERİME HAZIR TASLAKLAR (gönderim kurucudan)

**Karar (16-Eyl-2026):** Önce A düzelt → küçük AB lab'ları → İngilizce →
kurucu gönderir. Hedef: segment 1'in "kolay" kanadı (kanıt-zorluk KOLAY/ORTA).
**Gönderim sayısı: 7** (ilk dalga; bounce/yanıt sonrası 2. dalga planlanır).

## Doğrulanmış iletişim kanalları (16-Eyl-2026 canlı)

| # | Firma | Kanıt-zorluk | Kanal (canlı doğrulandı) | Adres | Not |
|---|---|---|---|---|---|
| 1 | **Black Forest Labs** | KOLAY (kamuya red-team YOK) | contact formu + genel e-posta | info@blackforestlabs.ai | En kolay: sıfır kamuya kanıt, FLUX açık-ağırlık |
| 2 | **Pleias** | KOLAY | "Book a demo" formu (pleias.ai) | form | DİKKAT: pleias.fr ESKİ → artık pleias.ai |
| 3 | **Bria AI** | KOLAY | contact formu (bria.ai) | form | Telif-temik; Measure 1.3(4) açısı |
| 4 | **Aleph Alpha** | KOLAY-ORTA | Sales contact formu | form | Heidelberg; "souveräne KI" konumlanması |
| 5 | **WRITER** | ORTA | "Contact us" / Trust Center formu | form | Regüle-sektör müşterileri |
| 6 | **Cohere** | ORTA | "Request a demo" formu | form | Command ailesi, AB pazarı |
| 7 | **Almawave** | KOLAY | Almaviva grubu üzerinden form | form | İtalyan kamu/defense zinciri |

**İmzacı kişi (doğal):** kamu kaynaklarında doğrulanamadı (§1.1) → hitap
"Team"/"Hi there". **Uydurma isim yok.**

---

## VARYANT A (düzeltildi) — küçük AB GPAI lab'larına

**Konu satırı seçenekleri (A/B için 2):**

- **A1:** your Code-of-Practice signature, and zero public safety evidence — let's fix that in one call
- **A2:** an open white-box audit for FLUX / Pleias models — reproducible, signed, 30 min to show

**Gövde:**

Hi team,

You signed the EU GPAI Code of Practice. Under Article 53, your
signatures commit to documented model evaluations and downstream evidence
packages on a 14-day cadence — but as far as we can tell from public
sources, you have no published red-team or evaluation evidence yet, and
building an in-house audit pipeline is months of work you'd rather spend
on models.

We built **Dümen** for exactly this gap. Apache-2.0,
`pip install dumen` (PyPI: v0.7.5). It runs black-box red-team batteries
(JailbreakBench/HarmBench/AgentHarm formats) and — when you can give it
local weights — white-box activation-steering probes that test whether your
safety behavior is a single removable direction. Every step is written into
a tamper-evident SHA-256 chain; `dumen dossier` renders Annex XI /
CoP-format documents from the same chain. Anything unmeasured is printed
**"Not measured"** — no fabricated scores, no inflated claims.

**Rather than promise, we proofed it.** Three certified audits are public and
signed (Ed25519 over the chain head) — Qwen2.5-0.5B and 1.5B white-box
(score 97.5) and qwen2.5:3b black-box (score 58.8; low because black-box API
gives no activation access — we disclose that rather than hide it):

    github.com/goun7/Dumen/tree/main/examples/certified

You can re-run any of them with the same commands and verify the signature
yourself (`dumen verify`, exit 0). A tampered score is rejected with a
hash-mismatch error — that's the point.

One call, 30 minutes, self-hosted — no data leaves your infrastructure:

1. `dumen audit` on one of your models → publishable scorecard;
2. `dumen dossier` → draft Annex XI technical documentation, chain attached;
3. if a third party should seal it, `dumen sign` with your Ed25519 key.

Worth 30 minutes? Reply and we'll send a calendar link. If you'd rather
self-serve first, `pip install dumen` — the README has the full lifecycle.

Best,
[Founder name], Dümen maintainers
github.com/goun7/Dumen

---

## Düzeltme notları (ne değişti, neden)

1. **"first" iddiası KALDIRILDI.** Eski konu satırı
   *"the EU's first open white-box audit evidence"* — doktrinimiz
   "first/only yalnızca doğrulanmış-ara-boşluk cümlesiyle" der; arama
   tarihiyle sınırlanmamış "first" **kullanılamaz**. Yerine somut kanıt
   (sertifikalar) kondu — iddia değil, link.
2. **Kanıt bağlantısı güçlendirildi.** "3 model families already have
   public scorecards" → **3 imzalı sertifika** + `dumen verify` ile
   bağımsız doğrulanabilir + kurcalama reddi. Satış açısından ham skordan
   çok daha güçlü: alıcı kendisi doğrulayabilir.
3. **Hedef daraltıldı.** Variant B (hyperscaler'lar: MSFT/AMZN/IBM/GOOG)
   2-4 aylık döngü = "hızlı para" ile çelişir → **ilk dalgadan çıkarıldı**.
   2. dalgada (yanıt alındıktan sonra) değerlendirilir.
4. **Dürüstlük işaretleri korundu:** 3B'nin düşük skoru gizlenmedi;
   "Not measured" doktrini açıkça belirtildi; "no data leaves your infra".

---

## 2. DALGA (yanıt sonrası)

- **Yanıt yoksa (7 gün):** kısa takip — sadece sertifikaya link,
  yeni bir şey ekleme. "Checking in — the certified audits are still
  up; happy to run one on your model."
- **İlgili ama kararsız:** ücretsiz deney — "send us one model, we'll
  run `dumen audit` and return the signed scorecard" (düşük risk = hızlı
  evet).
- **Olumsuz:** "regulation too early" → 2 Ağu 2026 enforcement
  başlangıcı + Appendix 3.5 dış-evaluatör notu ile 30 gün sonra tekrar.

## GÖNDERMEYECEKLER ❌

- **xAI** — toksik-bağ notu (§2 sıra 11); pasif okuyucu.
- **Variant B hyperscaler'lar** — ilk dalgada değil (yavaş döngü).
- **OpenAI/Anthropic/Google** — ZOR kanıt-zorluk; kendi internal
  eval'lerini "yeterli" görme riski; 2. dalgada "bağımsız üçüncü-taraf"
  rolüyle denenir.

---

## Kurallar (düzeltme sonrası hâlâ geçerli)

- Gövdede hiçbir ölçüm-vaadi yok; sadece repo'daki gerçek sertifikalara link.
- "first/only" YOK (kaldırıldı).
- İmzacı-kişi bilgisi resmen yok → "Team"/"Hi there".
- Veri çıkmaz (self-hosted) vaadi her mektupta var.

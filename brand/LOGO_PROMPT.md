# DÜMEN Logo Atölyesi — ChatGPT/Gemini Prompt'u (v1, 15-Eyl-2026)

> **Kullanım:** aşağıdaki İngilizce bloğu olduğu gibi ChatGPT'ye (veya
> Gemini'de görsel-üreticiye) ver → TEK görselde 5 konseptlik seçim sayfası
> döner → görseli buraya geri bırak (sohbete dosya olarak ekle ya da
> `brand/incoming/` klasörüne kaydet) → kurucu + ajan 11-puan tablosuyla
> seçer → seçileni ben vektöre çevirip (potrace) og/avatar/favicon ailesini
> ve README rozetlerini üretirim. Yöntem, kardeş-proje Sester/Tamga'da
> kanıtlanmış akışın aynısıdır.

---

## ChatGPT / Gemini'ye verilecek prompt (kopyala-yapıştır)

```text
You are designing a logo system for DÜMEN, an open-source AI-compliance audit
engine (EU AI Act). The name is Turkish for a ship's RUDDER: the instrument
that quietly determines the direction of a very large body. The product
audits and steers large language models: activation-vector "steering",
red-team evidence, tamper-evident compliance dossiers. Deliver ONE image
containing FIVE distinct logo concepts arranged as a labeled concept sheet
(top row 3 cells, bottom row 2 cells). This is a selection sheet — variety
matters more than polish of any single option.

HARD STYLE RULES (violating any disqualifies the concept):
- Flat vector style only. No gradients, no 3D, no bevels, no drop shadows,
  no photorealism, no glow.
- NO mascot, NO robot face, NO cute character, NO generic "AI brain / neural
  doodle / chat bubble" clichés, NO literal sailing-ship illustration.
- Each concept essentially MONOCHROME (one ink color on paper background) so
  it survives single-color printing and tiny favicon sizes.
- Crisp clean edges suitable for automatic bitmap→vector tracing.
- Must read at 16×16 px (favicon test: legible at fingernail size?).
- Slight hand-drawn chisel irregularity in stroke weight is WELCOME (like an
  instrument-maker's stamp) — not sterile-perfect, but traceable.

PALETTE (exact hex):
- Ink (primary strokes/fills): #171717
- Paper (every cell background): #F5F0E4
- Verdigris teal (tiny accent only, optional per concept — the patina of a
  bronze rudder in seawater): #2A7B7B
No other colors anywhere.

THE FIVE CONCEPT DIRECTIONS (one per cell, labeled A–E in small text):
A) HELM ARC & VECTOR — a quarter-circle tiller arc (the arc a ship's handle
   swings through) pierced or guided by one bold straight arrow/vector:
   controlled direction under measurement. The arc may carry 2–3 tick marks
   like an instrument scale.
B) RUDDER "D" — the letter D constructed as a rudder in profile: a vertical
   stock/post as the stem of the D, the blade hinged to it as the bowl of the
   D. It must read as a letter first, a rudder second.
C) VERDICT SEAL — a notary/ledger seal ring with fine saw-tooth edge (the
   ticks double as hash-chain blocks), containing a minimal rudder blade or
   tiller glyph at its center. Feels like a stamp of verified evidence.
D) COMPASS COURSE — a minimal four-point compass rose whose NORTH needle is
   replaced by a slim rudder blade: the instrument that both measures and
   steers. Geometric, calm, slightly hand-true rather than CAD-perfect.
E) WAKE & CHEVRON — the most abstract option: one bold chevron (a steering
   vector arrow) leaving two or three curved wake lines behind it, like a
   vessel's trail read from above. Single gesture, nothing else.

FOR EACH CELL show the mark twice side by side: (1) the bare mark large,
(2) a small lockup of mark + wordmark "DÜMEN" — ALL-CAPS continental serif
(Trajan/Cormorant flavor, NOT a body serif), letter-spaced wide, rendered
EXACTLY as D-Ü-M-E-N with the diaeresis on the U; ink color #171717.

NO mockups, NO business cards, NO app-icon-in-context, NO watermarks, NO
extra text besides cell labels A–E, the wordmark, and optionally a one-word
concept name under each label.

Output: one single high-resolution image, 5 cells, clean grid, generous margins.
```

---

## Seçim-kriterleri (kurucu + ajan birlikte puanlar; aile standardı)

| # | Kriter | Ağırlık |
|---|---|---|
| 1 | 16px okunurluk (favicon sadakati) | ×3 |
| 2 | Tek-renk hayatta-kalma (teal'siz de çalışır mı) | ×2 |
| 3 | Anlam-yoğunluğu (dümen/ölçüm/kanıt dili — jenerik-tech değil) | ×2 |
| 4 | potrace-uyumu (temiz kenar; izleme-sadakati IoU ≥ 0.99 Tamga standardı) | ×2 |
| 5 | Koyu zemin uyarlanabilirliği (mürekkep↔parşömen çevrimi) | ×1 |
| 6 | Wordmark-lockup uyumu (DÜMEN serif + tracking; Ü çizimi düzgün mü) | ×1 |

Eşitlik/pREFERENCE kararları her zaman kurucunundur; ajan puan-tablosunu
nesnel-kıstaslarla (1,4 ölçülebilir) doldurur.

## Seçim-sonrası entegrasyon (benim işim — otomatik akış)

1. Seçilen hücre "bare mark only, full resolution" olarak yeniden üretilir.
2. potrace → `brand/dumen-mark.svg` (tek-yol, `currentColor`).
3. Aile-varlıkları: `og.png` 1280×640 + `avatar.png` 512 + favicon
   (16/32/48/64/128/180/512 + .ico) + README-üstü rozet satırı.
4. GitHub sosyal-önizleme görseli bu aileden atanır.
5. `brand/MARKA_NOTU.md`: kullanım-kuralları (minimum boyut, boşluk, yasaklar).

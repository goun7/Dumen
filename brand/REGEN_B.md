# Yüksek-Çözünürlük Yeniden-Üretim — SEÇİLEN: B (Rudder "D")

**Karar (15 Eyl 2026):** Kurucu gözü + programatik ölçü birleşimi → B.
Gerekçe: en temiz potrace izlenebilirliği (IoU 0.565), en az anti-aliasing
(halo 0.012), tam-flat, %0 gradient-ihlali. Wordmark (DÜMEN serif) gözden
geçti: düzgün; ancak işaret ayrı, saf kanvas üzerinde yüksek çözünürlükte
yeniden üretilecek.

## ChatGPT/Gemini'ye yapıştırılacak prompt

Önce **brand/candidates/cell_B.png** görselini sohbete EKLE, sonra şunu yapıştır:

```
Reproduce the logo mark shown in the attached image, but as a clean,
optimized, high-resolution master file. Exact same geometry and proportions
of the mark. Changes: (1) OUTPUT ONLY THE MARK — no wordmark, no letters,
no text anywhere; (2) perfectly centered on a plain parchment background
(hex #F5F0E4) with generous even margins on all sides; (3) the mark fills
most of the square frame; (4) crisp flat solid ink (#171717) — no gradients,
no shadows, no highlights, no texture, minimal anti-aliasing; (5) square
1:1 composition. Keep every stroke junction, cutout and terminal exactly as
in the reference.
```

Dönen görseli `brand/logo_B_hi.png` olarak kaydet (bu ada göre otomatik
tanıyacak tüm hat hazır: potrace → IoU≥0.99 kapısı → `brand/dumen-mark.svg`
→ `scripts/make_brand_assets.py` → og/avatar/favicon ailesi → README).

## Hat-provası sonucudur (15 Eyl tur-6 — mevcut düşük-çözüm hücresiyle, depoya dokunmadan)
- Sıkı-kırpım (wordmark-atma + içerik-sınırı) tek başına IoU'yu 0.565→0.959'a çıkardı.
- En iyi potrace ayarı: `--flat --turnpolicy right` + sert-eşik önişlem → IoU 0.981, TEK PATH.
- `make_brand_assets.py` pilot SVG ile tam tur döndü: 9 png + ico + selfcheck ✓.
- Beklenti: logo_B_hi.png gelince ≥0.99 doğal gelir; gelmezse bu ayar-seti hazır.
- PyPI adı canlı teyit (15 Eyl tur-6): JSON-API 404 = BOŞTA (anti-bot "200" yanıltmacası elendi).

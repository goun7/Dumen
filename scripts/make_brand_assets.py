#!/usr/bin/env python3
"""DÜMEN marka-varlık-üreticisi — Sester/Tamga kanıtlanmış hattının uyarlaması.

Tek-kaynak: brand/dumen-mark.svg (potrace, tek-yol, IoU ≥ 0.99 — LOGO_PROMPT.md
seçim-akışının çıktısı). Bu script SVG'yi rsvg-convert ile rasterize edip
OG/avatar/favicon ailesini üretir — FAIL-LOUD: araç/font/mark yoksa RED,
sessiz-fallback YOK.

Çıktılar (.github/assets/):
    og.png 1280×640 · avatar.png 512×512 · favicon-{16,32,48,64,128,180,512}.png · favicon.ico

Öz-denetim (sentetik-geçici-şekil; marka YERİNE GEÇMEZ, /tmp'de kalır):
    DUMEN_MARK_SVG=/tmp/x.svg DUMEN_ASSETS_OUT=/tmp/y python3 scripts/make_brand_assets.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:  # fail-loud
    sys.exit(f"RED: Pillow gerekli — `pip install pillow` ({e})")

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("DUMEN_ASSETS_OUT", ROOT / ".github" / "assets"))
MARK_SVG = Path(os.environ.get("DUMEN_MARK_SVG", ROOT / "brand" / "dumen-mark.svg"))

PARCHMENT = (245, 240, 228)    # #F5F0E4
INK = (23, 23, 23)             # #171717
VERDIGRIS = (42, 123, 123)     # #2A7B7B — oksitlenmiş bronz dümen

FONT_CANDIDATES = [
    "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",        # bu makinede doğrulandı
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/TTF/VeraSeBd.ttf",
]
WORDMARK = "DÜMEN"
SUBTITLE = "audit-grade evidence for the EU AI Act"
FEATURES = [
    "white-box steering vectors · bootstrap CI · permutation p",
    "capability-regression gate: broken protection fails the claim",
    "SHA-256-sealed Annex XI + Code of Practice dossiers",
]


def _version() -> str:
    m = re.search(r'^version = "([0-9.]+)"', (ROOT / "pyproject.toml").read_text(), re.M)
    return m.group(1) if m else "0.0.0"


def _font(size: int):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    sys.exit("RED: serif font yok (DejaVu/Liberation) — sessiz-fallback YOK")


def _spaced_width(text, font, tracking):
    return sum(font.getlength(c) + tracking for c in text) - tracking


def _fit_font(text, tracking, max_w, start):
    size = start
    while size > 12:
        f = _font(size)
        if _spaced_width(text, f, tracking) <= max_w:
            return f
        size -= 2
    return _font(12)


def spaced_text(d, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking


def render_mark(height: int) -> Image.Image:
    if not MARK_SVG.is_file():
        sys.exit(f"RED: tek-kaynak marka yok: {MARK_SVG} "
                 "(önce LOGO_PROMPT.md seçim-akışını tamamla)")
    rsvg = shutil.which("rsvg-convert")
    if not rsvg:
        sys.exit("RED: rsvg-convert yok — `apt install librsvg2-bin`; sessiz-fallback YOK")
    tmp = OUT / "_mark_tmp.png"
    OUT.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([rsvg, "-b", "#F5F0E4", "-h", str(height),
                        "-o", str(tmp), str(MARK_SVG)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"RED: marka-rasterizasyonu başarısız: {r.stderr}")
    img = Image.open(tmp).convert("RGB")
    tmp.unlink()
    return img


def make_og() -> None:
    img = Image.new("RGB", (1280, 640), PARCHMENT)
    d = ImageDraw.Draw(img)
    d.rectangle([34, 30, 1247, 611], outline=INK, width=3)
    d.rectangle([40, 36, 1253, 617], outline=VERDIGRIS, width=1)
    mark = render_mark(400)
    img.paste(mark, (150, 120))
    spaced_text(d, (490, 210), WORDMARK, _font(104), INK, 14)
    f_sub = _fit_font(SUBTITLE, 2, 700, 28)
    spaced_text(d, (494, 344), SUBTITLE, f_sub, VERDIGRIS, 2)
    y = 424
    for line in FEATURES:
        f_feat = _fit_font(line, 1, 700, 20)
        cx, cy = 502, y + int(f_feat.size * 0.62)
        d.polygon([(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)], fill=VERDIGRIS)
        spaced_text(d, (520, y), line, f_feat, INK, 1)
        y += 44
    tail = f"v{_version()} · APACHE-2.0"
    f_foot = _font(17)
    spaced_text(d, (1240 - _spaced_width(tail, f_foot, 4), 584), tail, f_foot, VERDIGRIS, 4)
    img.save(OUT / "og.png")


def make_avatar() -> None:
    img = Image.new("RGB", (512, 512), PARCHMENT)
    mark = render_mark(410)
    img.paste(mark, ((512 - mark.width) // 2, 51))
    img.save(OUT / "avatar.png")


def make_favicons() -> None:
    av = Image.open(OUT / "avatar.png").convert("RGB")
    for s in (16, 32, 48, 64, 128, 180, 512):
        av.resize((s, s), Image.LANCZOS).save(OUT / f"favicon-{s}.png")
    av.save(OUT / "favicon.ico", sizes=[(s, s) for s in (16, 32, 48, 64)])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    make_og()
    make_avatar()
    make_favicons()
    # fail-loud selfcheck (Sester standardı): boyutlar doğru mu
    for name, wh in (("og.png", (1280, 640)), ("avatar.png", (512, 512))):
        p = OUT / name
        if not p.exists() or Image.open(p).size != wh:
            sys.exit(f"RED: {p} beklenen {wh} boyutunda değil")
    for s in (16, 32, 48, 64, 128, 180, 512):
        if Image.open(OUT / f"favicon-{s}.png").size != (s, s):
            sys.exit(f"RED: favicon-{s}.png boyutu yanlış")
    print(f"OK: marka-ailesi üretildi → {OUT}/ (9 png + .ico), selfcheck geçti")

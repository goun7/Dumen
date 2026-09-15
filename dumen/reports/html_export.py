"""Denetçi-formatı dışa-aktarım: marka-stilli TEK-DOSYA, yazdırılabilir HTML.

Bir denetim raporu PDF'te değil, KANITTA yaşar — ama hukukçu/sigortacı/müfettiş
paydaşı markdown bilmez. Bu modül, dosyayı gömülü-stilli tek HTML'e çevirir:

- Gömili marka işareti (dumen-mark.svg okunur, byte-byte gömülür — CDN yok,
  hava-boşluğunda açılır), palet: ink #171717 / parşömen #F5F0E4 / bakır-verdigris.
- @media print: A-4 kenar boşlukları, bölüm-sayı kontrolleri → tarayıcıyla
  "Print → Save as PDF" denetçi-standartı çıktı verir (bağımlılıksız, deterministik).
- Zincir mühürü: --chain/--sig verildiğinde altbilgiye head-hash + imzalayan +
  parmak-izi gömülür — HTML dosyası tek başına kanıt bağlamını taşır.
- GÜVENLİK: model çıktısı güvenilmez girdidir. mistune `html=False` (varsayılan)
  ham etiketleri kaçırır; testte `<script>` enjeksiyonunun metin-eşdeğeri kanıtlanır.
"""
from __future__ import annotations

import html as _html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import mistune

from .evidence_chain import EvidenceChain

_MARK_PATH = Path(__file__).resolve().parent / "assets" / "dumen-mark.svg"

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --ink:#171717; --parchment:#F5F0E4; --verdigris:#2A7B7B; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--parchment); color:var(--ink);
  font:16px/1.6 Georgia, 'DejaVu Serif', 'Times New Roman', serif; }}
.wrap {{ max-width: 820px; margin: 0 auto; padding: 48px 32px 96px; }}
header.masthead {{ display:flex; align-items:center; gap:18px;
  border-bottom: 3px solid var(--ink); padding-bottom:18px; margin-bottom:32px; }}
header.masthead svg, header.masthead img {{ height:64px; width:auto; }}
.brandtype {{ font-size:28px; letter-spacing:.24em; font-weight:700; }}
.brandsub {{ font-size:13px; color:var(--verdigris); letter-spacing:.12em; }}
h1 {{ font-size:30px; margin:0 0 8px; }} h2 {{ font-size:22px; margin-top:36px;
  border-bottom:1px solid rgba(23,23,23,.25); padding-bottom:6px; }}
h3 {{ font-size:18px; margin-top:28px; }}
code, pre {{ font-family: 'DejaVu Sans Mono', Menlo, Consolas, monospace;
  background: rgba(23,23,23,.06); }}
pre {{ padding:12px 14px; overflow-x:auto; border-left:3px solid var(--verdigris); }}
table {{ border-collapse:collapse; width:100%; margin:18px 0; font-size:14.5px; }}
th, td {{ border:1px solid rgba(23,23,23,.35); padding:7px 10px; text-align:left;
  vertical-align:top; }} th {{ background:rgba(42,123,123,.12); }}
blockquote {{ border-left:4px solid var(--verdigris); margin:18px 0;
  padding:6px 18px; background:rgba(255,255,255,.5); }}
footer.seal {{ margin-top:64px; border-top:3px solid var(--ink); padding-top:14px;
  font:12.5px/1.55 'DejaVu Sans Mono', Menlo, Consolas, monospace; color:#3c3a36; }}
footer.seal b {{ color:var(--verdigris); }}
@media print {{
  body {{ background:#fff; }}
  .wrap {{ max-width:none; padding:0; }}
  h2, h3 {{ break-after: avoid; }} pre, blockquote {{ break-inside: avoid; }}
  @page {{ size:A4; margin:20mm 17mm; }}
}}
</style>
</head>
<body>
<div class="wrap">
<header class="masthead">{mark}
<div><div class="brandtype">DÜMEN</div>
<div class="brandsub">STEERINGOS · MECHANISTIC EU AI ACT AUDIT · EVIDENCE-FIRST</div></div>
</header>
<article>
{body}
</article>
<footer class="seal">
generated {stamp} · dumen v{version}<br>
{seal}
<span>no evidence, no claim — unmeasured metrics render as “Not measured”, never estimates</span>
</footer>
</div>
</body>
</html>
"""


def _mark_embed() -> str:
    """Marka dosyasını bulursa inline SVG (hava-boşluğu), bulamazsa <img> yol dene,
    o da yoksa yazı-tipi logosu — sessiz çöküş yok, her durumda kimlik kalır."""
    try:
        raw = _MARK_PATH.read_text(encoding="utf-8")
        raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
        return raw
    except OSError:
        return ""


def _seal_block(chain_path: str | None, sig_path: str | None) -> str:
    parts = []
    if chain_path:
        try:
            chain = EvidenceChain.from_json(Path(chain_path).read_text(encoding="utf-8"))
            v = chain.verify()
            state = "INTACT" if v.is_valid else "BROKEN"
            parts.append(f"evidence chain: <b>{state}</b> · {v.length} records · "
                         f"head <code>{v.head_hash}</code><br>")
        except (OSError, ValueError) as exc:
            parts.append(f"evidence chain: <b>UNREADABLE</b> ({_html.escape(str(exc))})<br>")
    if sig_path:
        try:
            rec = json.loads(Path(sig_path).read_text(encoding="utf-8"))
            parts.append("signature: <b>{}</b> · {} · signed {} <code>{}</code><br>".format(
                _html.escape(str(rec.get("signer_name", "?"))),
                _html.escape(str(rec.get("pubkey_fingerprint", "?"))),
                _html.escape(str(rec.get("signed_at", "?"))),
                _html.escape(str(rec.get("head_hash", "?"))[:32]),
            ))
        except (OSError, ValueError) as exc:
            parts.append(f"signature: <b>UNREADABLE</b> ({_html.escape(str(exc))})<br>")
    if not parts:
        parts.append("no chain file supplied — export is the report only, not sealed evidence<br>")
    return "".join(parts)


def render_report_html(markdown_text: str, title: str,
                       chain_path: str | None = None,
                       sig_path: str | None = None) -> str:
    """Markdown → marka-stilli tek-dosya HTML. Ham model-HTML'i KAÇIRILIR."""
    md = mistune.create_markdown(escape=True, plugins=["table", "strikethrough"])
    body = md(markdown_text)
    from dumen import __version__
    return _TEMPLATE.format(
        title=_html.escape(title),
        mark=_mark_embed(),
        body=body,
        stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        version=__version__,
        seal=_seal_block(chain_path, sig_path),
    )

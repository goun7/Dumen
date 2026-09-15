"""tests/test_html_export.py — denetçi-formatı dışa-aktarım kapıları.

Kanıtlanmak zorunda olanlar: (1) marka kimliği gömülü (inline SVG + palet +
@page), (2) güvenilmez model-çıktısı HTML'e KAÇIRILIR (html=False), (3) zincir
mühür-altbilgisi gerçek dosyalardan head-hash/imzalayan taşır, (4) bozuk zincir
sessizce 'güzel' görünmez — UNREADABLE/BROKEN etiketi basılır, (5) CLI uçtan uca.
"""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from dumen.cli import cli
from dumen.reports.evidence_chain import EvidenceChain
from dumen.reports.html_export import render_report_html
from dumen.reports.signing import generate_keypair, sign_chain_file

_MD = """# Denetim Raporu — X Modeli

## Yöntem
| aşama | ölçüm | değer |
|---|---|---|
| baseline | refusal-rate | 0.925 |

> kanıt: `sha256:abcd…`

<script>alert(' XSS-enjeksiyonu-denemesi ')</script>
"""


class TestRender:
    def test_brand_identity_embedded(self):
        html = render_report_html(_MD, "Denetim Raporu")
        assert "<!DOCTYPE html>" in html
        assert "DÜMEN" in html
        assert "#2A7B7B" in html or "2A7B7B" in html
        assert "@page" in html  # yazdırma-kuralı
        assert "<path" in html  # inline SVG marka (paket-varlığı)

    def test_untrusted_model_output_is_escaped(self):
        html = render_report_html(_MD, "T")
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_table_survives(self):
        html = render_report_html(_MD, "T")
        assert "<table>" in html and "0.925" in html


class TestSeal:
    def _chain(self, tmp: Path) -> tuple[Path, EvidenceChain]:
        chain = EvidenceChain()
        chain.append("mining", {"stage": "vectorminer"})
        chain.append("report", {"annex": "XI"})
        fp = tmp / "c.json"
        fp.write_text(chain.to_json(), encoding="utf-8")
        return fp, chain

    def test_seal_embeds_head_and_signer(self, tmp_path):
        fp, chain = self._chain(tmp_path)
        kp = generate_keypair("aud", str(tmp_path))
        sign_chain_file(str(fp), kp["private_key_path"], "Acme Denetim")
        html = render_report_html("# r", "t", chain_path=str(fp),
                                  sig_path=str(fp) + ".sig")
        assert "INTACT" in html
        assert chain.head_hash() in html
        assert "Acme Denetim" in html
        assert kp["fingerprint"] in html

    def test_broken_chain_shows_broken_not_pretty(self, tmp_path):
        fp, _ = self._chain(tmp_path)
        data = json.loads(fp.read_text())
        data[0]["prev_hash"] = "0" * 63 + "1"
        fp.write_text(json.dumps(data), encoding="utf-8")
        html = render_report_html("# r", "t", chain_path=str(fp))
        assert "UNREADABLE" in html or "BROKEN" in html

    def test_no_files_honest_note(self):
        html = render_report_html("# r", "t")
        assert "not sealed evidence" in html


class TestCliExport:
    def test_cli_end_to_end(self, tmp_path):
        src = tmp_path / "rapor.md"
        src.write_text(_MD, encoding="utf-8")
        runner = CliRunner()
        res = runner.invoke(cli, ["export", "--input", str(src)])
        assert res.exit_code == 0, res.output
        out = tmp_path / "rapor.md.html"
        assert out.exists()
        html = out.read_text(encoding="utf-8")
        assert "Denetim Raporu — X Modeli" in html  # başlık ilk # satırından
        assert "<table>" in html and "&lt;script&gt;" in html


class TestDegradation:
    def test_missing_mark_degrades_to_typography_not_crash(self, tmp_path, monkeypatch):
        import dumen.reports.html_export as hx
        monkeypatch.setattr(hx, "_MARK_PATH", tmp_path / "yok.svg")
        html = hx.render_report_html("# merhaba", "t")
        assert "<path" not in html and "DÜMEN" in html  # yazı-tipi kimlik kalır

    def test_unreadable_sig_flagged_not_swallowed(self, tmp_path):
        fp, chain = TestSeal()._chain(tmp_path)
        (tmp_path / "kötü.sig").write_text("{bozuk json", encoding="utf-8")
        html = render_report_html("# r", "t", sig_path=str(tmp_path / "kötü.sig"))
        assert "UNREADABLE" in html and "signature:" in html

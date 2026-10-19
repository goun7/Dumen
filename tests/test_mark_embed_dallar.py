"""tests/test_mark_embed_dallar.py — dumen.reports.html_export._mark_embed dal-keseç testleri.

Kural-4: saf-in-memory. Dosya sistemik işlemler tmp_path / monkeypatch ile;
AĞ YOK, CDN YOK (tasarım gereği gömme yereldir).

Hedeflenen dallar:
  1. SVG mevcut & okunabilir  → içeriği döner, TÜM <?xml ...?> bildirileri soyulur
  2. dosya yok (FileNotFoundError) → "" (sessiz düşüş)
  3. okunamıyor (PermissionError / IsADirectoryError) → ""
"""
from __future__ import annotations

import re

import pytest

from dumen.reports import html_export
from dumen.reports.html_export import _MARK_PATH, _mark_embed


def _set_mark(monkeypatch, content_or_path, tmp_path=None):
    """_MARK_PATH'i ya tmp_path altında yazılı bir dosyaya ya da verilen nesneye
    yönlendirir. Üretim asset dizinine ASLA yazmaz (Kural-1)."""
    if isinstance(content_or_path, str):
        assert tmp_path is not None, "tmp_path gerekli"
        p = tmp_path / "_tmp_mark_test.svg"
        p.write_text(content_or_path, encoding="utf-8")
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        return p
    monkeypatch.setattr(html_export, "_MARK_PATH", content_or_path)
    return content_or_path


class _Unreadable:
    """read_text her zaman istisna fırlatan sahte yol (root/chmod'dan bağımsız)."""

    def __init__(self, exc):
        self._exc = exc

    def read_text(self, *args, **kwargs):
        raise self._exc


# ------------------------------------------------------------------ gerçek asset
class TestRealAsset:
    def test_gercek_asset_bos_degil(self):
        out = _mark_embed()
        assert isinstance(out, str)
        assert out.strip() != ""

    def test_gercek_asset_svg_etiketi_icerir(self):
        assert "<svg" in _mark_embed()

    def test_gercek_asset_xml_bildirisi_soyulmus(self):
        assert "<?xml" not in _mark_embed()

    def test_gercek_asset_doctype_korunur(self):
        # DOCTYPE bir bildiri değildir — korunmalı
        assert "<!DOCTYPE svg" in _mark_embed()

    def test_paket_varligi_diskta_mevcut(self):
        assert _MARK_PATH.is_file()


# ------------------------------------------------------------------ dal 1: başarı
class TestReadSuccess:
    def test_xml_bildirisi_soyulur(self, monkeypatch, tmp_path):
        src = '<?xml version="1.0" encoding="UTF-8"?>\n<svg/>'
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == "\n<svg/>"

    def test_birden_fazla_bildiri_soyulur(self, monkeypatch, tmp_path):
        src = '<?xml version="1.0"?><a/><?xml version="1.1"?><b/>'
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == "<a/><b/>"

    def test_bildiri_yoksa_degisiklik_yok(self, monkeypatch, tmp_path):
        src = "<svg><path d=\"M0 0\"/></svg>"
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == src

    def test_bildiri_icinde_tire_ve_nokta(self, monkeypatch, tmp_path):
        src = '<?xml version="1.0" standalone="no"?><svg/>'
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == "<svg/>"

    def test_xml_stylesheet_de_soyulur(self, monkeypatch, tmp_path):
        # "<?xml-stylesheet ...?>" de "<?xml" ile başlar → regex yakalar
        src = '<?xml-stylesheet href="a.css"?><svg/>'
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == "<svg/>"

    def test_sadece_bildiri_varsa_bos_doner(self, monkeypatch, tmp_path):
        _set_mark(monkeypatch, '<?xml version="1.0"?>', tmp_path)
        assert _mark_embed() == ""

    def test_unicode_icerik_korunur(self, monkeypatch, tmp_path):
        src = '<?xml version="1.0"?><!-- DÜMEN markası: ĞÜŞÖÇ ğüşıöç -->\n<svg/>'
        _set_mark(monkeypatch, src, tmp_path)
        out = _mark_embed()
        assert "ĞÜŞÖÇ ğüşıöç" in out
        assert "<?xml" not in out

    def test_bos_dosya_bos_doner(self, monkeypatch, tmp_path):
        p = tmp_path / "bos.svg"
        p.write_text("", encoding="utf-8")
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        assert _mark_embed() == ""

    def test_sadece_bosluk_korunur(self, monkeypatch, tmp_path):
        p = tmp_path / "bosluk.svg"
        p.write_text("   \n\t ", encoding="utf-8")
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        assert _mark_embed() == "   \n\t "

    def test_ortada_bildiri_de_soyulur(self, monkeypatch, tmp_path):
        # re.sub globaldir — konum önemli değildir
        src = "<a/><?xml version='1.0'?><!-- orta --><b/>"
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == "<a/><!-- orta --><b/>"

    def test_buyuk_dosya(self, monkeypatch, tmp_path):
        p = tmp_path / "buyuk.svg"
        p.write_text('<?xml version="1.0"?>' + "<path/>" * 5000, encoding="utf-8")
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        out = _mark_embed()
        assert out.count("<path/>") == 5000
        assert not out.startswith("<?xml")

    def test_encoding_utf8_olarak_okunur(self, monkeypatch, tmp_path):
        p = tmp_path / "tr.svg"
        p.write_text("<?xml version='1.0'?><svg><!--İ-->şğü</svg>", encoding="utf-8")
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        assert _mark_embed() == "<svg><!--İ-->şğü</svg>"


# ------------------------------------------------------------------ dal 2/3: düşüş
class TestFallback:
    @pytest.mark.parametrize("exc", [
        pytest.param(FileNotFoundError("yok"), id="FileNotFoundError"),
        pytest.param(PermissionError("izin yok"), id="PermissionError"),
        pytest.param(IsADirectoryError("dizin"), id="IsADirectoryError"),
        pytest.param(OSError("genel os"), id="OSError"),
    ])
    def test_oserror_alt_siniflari_bos_doner(self, monkeypatch, exc):
        _set_mark(monkeypatch, _Unreadable(exc))
        assert _mark_embed() == ""

    def test_olmayan_dosya_bos_doner(self, monkeypatch, tmp_path):
        p = tmp_path / "yok.svg"
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        assert _mark_embed() == ""

    def test_dizin_olarak_bos_donder(self, monkeypatch, tmp_path):
        monkeypatch.setattr(html_export, "_MARK_PATH", tmp_path)
        assert _mark_embed() == ""

    def test_dusus_hata_firlatmaz(self, monkeypatch):
        _set_mark(monkeypatch, _Unreadable(FileNotFoundError("yok")))
        try:
            out = _mark_embed()
        except BaseException as caught:  # noqa: BLE001
            pytest.fail(f"düşüş hata fırlattı: {caught!r}")
        assert out == ""


# ------------------------------------------------------------------ sınır/bug
class TestBoundary:
    def test_bildiri_icinde_karakteri_varsa_soyulmaz(self, monkeypatch, tmp_path):
        # REGEX SINIR/BUG: [^>]* '>' göremez → 'a=">"' bildirisi eşleşmez,
        # hiçbir şey soyulmaz. Bildiri içinde '>' olan SVG'ler bozulmadan GEÇER.
        src = '<?xml a=">"?><svg/>'
        _set_mark(monkeypatch, src, tmp_path)
        assert _mark_embed() == src

    def test_kisa_bildiri(self, monkeypatch, tmp_path):
        _set_mark(monkeypatch, "<?xml?><svg/>", tmp_path)
        assert _mark_embed() == "<svg/>"

    def test_deterministik_iki_cagri_ayni(self, monkeypatch, tmp_path):
        p = tmp_path / "m.svg"
        p.write_text('<?xml version="1.0"?><svg/>', encoding="utf-8")
        monkeypatch.setattr(html_export, "_MARK_PATH", p)
        assert _mark_embed() == _mark_embed()

    def test_regex_module_seviyesinde_ayni(self):
        # üretim regex'i ile birebir davranış (belgeleme)
        src = '<?xml version="1.0"?><x/>'
        assert re.sub(r"<\?xml[^>]*\?>", "", src) == "<x/>"

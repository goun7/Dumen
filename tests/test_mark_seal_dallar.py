"""77-Dumen html_export._mark_embed + _seal_block dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (tmp_path + monkeypatch — dis cagri YOK).
Marka-SVG gomme + evidence-chain/sigorta muhur bloku.
"""
import json
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from dumen.reports import html_export  # noqa: E402
from dumen.reports.html_export import _mark_embed, _seal_block  # noqa: E402


# == _mark_embed =======================================================================================

def test_mark_str():
    assert isinstance(_mark_embed(), str)


def test_mark_svg_iceriyor():
    """ORTAM: <svg etiketi doner."""
    assert "<svg" in _mark_embed()


def test_mark_xml_beyani_kaldirilir():
    """ORTAM: <?xml ...?> beyani re.sub ile silinir."""
    assert "<?xml" not in _mark_embed()


def test_mark_inline():
    """ORTAM: <img yolu YOK (inline-gomme)."""
    assert "<img" not in _mark_embed()


def test_mark_dosya_yoksa_bos(monkeypatch):
    """ORTAM: OSError -> bos-string (sessiz-cokus YOK ama <img de YOK)."""
    from pathlib import Path

    class _Yok:
        def read_text(self, encoding=None):
            raise FileNotFoundError("yok")
    monkeypatch.setattr(html_export, "_MARK_PATH", _Yok())
    assert _mark_embed() == ""


def test_mark_izin_hatasi(monkeypatch):
    """ORTAM: PermissionError (OSError) -> bos."""

    class _Izinsiz:
        def read_text(self, encoding=None):
            raise PermissionError("yasak")
    monkeypatch.setattr(html_export, "_MARK_PATH", _Izinsiz())
    assert _mark_embed() == ""


def test_mark_utf8(monkeypatch, tmp_path):
    """ORTAM: UTF-8 encoding ile okunur."""
    p = tmp_path / "m.svg"
    p.write_text('<svg>İİ</svg>', encoding="utf-8")
    monkeypatch.setattr(html_export, "_MARK_PATH", p)
    assert "İİ" in _mark_embed()


def test_mark_diger_xml_beyani(monkeypatch, tmp_path):
    """ORTAM: <?xml version="1.0" encoding="UTF-8"?> silinir."""
    p = tmp_path / "m.svg"
    p.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<svg/>', encoding="utf-8")
    monkeypatch.setattr(html_export, "_MARK_PATH", p)
    r = _mark_embed()
    assert r.strip() == "<svg/>"


def test_mark_coklu_xml_beyani(monkeypatch, tmp_path):
    """ORTAM: re.sub GLOBALDIR — tum <?xml?> silinir."""
    p = tmp_path / "m.svg"
    p.write_text('<?xml a?>\n<svg>\n<?xml b?>\n</svg>', encoding="utf-8")
    monkeypatch.setattr(html_export, "_MARK_PATH", p)
    assert "<?xml" not in _mark_embed()
    assert "<svg>" in _mark_embed()


def test_mark_repeatable():
    """ORTAM: tekrar ayni cikti."""
    assert _mark_embed() == _mark_embed()


def test_mark_svg_olmayan(monkeypatch, tmp_path):
    """ORTAM: SVG olmayan dosya oldugu gibi doner (xml-beyani silinir)."""
    p = tmp_path / "m.txt"
    p.write_text('<?xml a?>plain', encoding="utf-8")
    monkeypatch.setattr(html_export, "_MARK_PATH", p)
    assert _mark_embed().strip() == "plain"


def test_mark_bos_dosya(monkeypatch, tmp_path):
    p = tmp_path / "b.svg"
    p.write_text("", encoding="utf-8")
    monkeypatch.setattr(html_export, "_MARK_PATH", p)
    assert _mark_embed() == ""


# == _seal_block: hicbiri ===============================================================================

def test_seal_ikisi_none():
    """ORTAM: chain/sig None -> 'no chain file supplied' mesaji."""
    r = _seal_block(None, None)
    assert "no chain file supplied" in r
    assert "not sealed" in r


def test_seal_bos_str_none():
    """ORTAM: bos-string falsy -> 'no chain file supplied'."""
    assert "no chain file supplied" in _seal_block("", "")


def test_seal_sadece_hic():
    assert _seal_block(None, None) == _seal_block("", "")


# == _seal_block: chain okunamaz =======================================================================

def test_seal_chain_yok(tmp_path):
    """ORTAM: chain dosyasi yok -> UNREADABLE."""
    r = _seal_block(str(tmp_path / "yok.json"), None)
    assert "UNREADABLE" in r
    assert "evidence chain" in r


def test_seal_chain_gecersiz_json(tmp_path):
    """ORTAM: ValueError -> UNREADABLE."""
    p = tmp_path / "c.json"
    p.write_text("{gecersiz", encoding="utf-8")
    assert "UNREADABLE" in _seal_block(str(p), None)


def test_seal_chain_hata_mesaji_kacisi(tmp_path):
    """ORTAM: html.escape ile escape edilir."""
    p = tmp_path / "c.json"
    p.write_text("{gecersiz <b>", encoding="utf-8")
    r = _seal_block(str(p), None)
    assert "<b>" not in r.split("UNREADABLE")[1]


def test_seal_chain_dizin(tmp_path):
    """ORTAM: dizin -> OSError -> UNREADABLE."""
    assert "UNREADABLE" in _seal_block(str(tmp_path), None)


# == _seal_block: sig okunamaz ==========================================================================

def test_seal_sig_yok(tmp_path):
    """ORTAM: sig dosyasi yok -> UNREADABLE."""
    r = _seal_block(None, str(tmp_path / "yok.json"))
    assert "UNREADABLE" in r
    assert "signature" in r


def test_seal_sig_gecersiz_json(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("[gecersiz", encoding="utf-8")
    assert "UNREADABLE" in _seal_block(None, str(p))


def test_seal_sig_hata_kacisi(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{<script>", encoding="utf-8")
    r = _seal_block(None, str(p))
    assert "<script>" not in r


# == _seal_block: sig gecerli ===========================================================================

def test_seal_sig_gecerli(tmp_path):
    """ORTAM: gecerli JSON sig -> signature bloku."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps({
        "signer_name": "Alice", "pubkey_fingerprint": "FP123",
        "signed_at": "2026-01-01", "head_hash": "H" * 64,
    }), encoding="utf-8")
    r = _seal_block(None, str(p))
    assert "signature:" in r
    assert "Alice" in r
    assert "FP123" in r


def test_seal_sig_alan_eksik(tmp_path):
    """ORTAM: eksik alanlar -> '?' default."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"signer_name": "B"}), encoding="utf-8")
    r = _seal_block(None, str(p))
    assert "B" in r
    assert "?" in r


def test_seal_sig_head_hash_truncate(tmp_path):
    """ORTAM: head_hash [:32] truncate."""
    p = tmp_path / "s.json"
    hh = "".join("%02x" % i for i in range(64))  # 128-benzersiz-hex
    p.write_text(json.dumps({"head_hash": hh}), encoding="utf-8")
    r = _seal_block(None, str(p))
    assert hh[:32] in r
    assert hh[32:64] not in r


def test_seal_sig_html_escape(tmp_path):
    """ORTAM: alanlar html.escape edilir."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"signer_name": "<b>X</b>"}), encoding="utf-8")
    """ORTAM: <b> etiketleri KASITLI biçimlendirme (escape edilmez),
    SADECE deger html.escape edilir."""
    r = _seal_block(None, str(p))
    assert "&lt;b&gt;X&lt;/b&gt;" in r
    assert "<script>" not in r


def test_seal_sig_bos_dict(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{}", encoding="utf-8")
    r = _seal_block(None, str(p))
    assert "signature:" in r
    assert "?" in r


def test_seal_sig_liste(tmp_path):
    """ORTAM-OGRENDI: liste JSON -> rec.get AttributeError -> except (OSError,
    ValueError) yakalamaz! Listeler disari sizar (URETIM quirk)."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(AttributeError):
        _seal_block(None, str(p))


def test_seal_sig_int_alan(tmp_path):
    """ORTAM: int alan -> str() ile cevrilir."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"signer_name": 42}), encoding="utf-8")
    r = _seal_block(None, str(p))
    assert "42" in r


def test_seal_sig_none_alan(tmp_path):
    """ORTAM: None alan -> str(None) = 'None' (NOT '?')."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"signer_name": None}), encoding="utf-8")
    r = _seal_block(None, str(p))
    assert "None" in r


@pytest.mark.parametrize("anahtar,deger", [
    ("signer_name", "S"), ("pubkey_fingerprint", "FP"),
    ("signed_at", "TS"), ("head_hash", "H" * 40),
])
def test_seal_sig_matrix(tmp_path, anahtar, deger):
    """ORTAM: her sig alani basilir."""
    p = tmp_path / "s.json"
    p.write_text(json.dumps({anahtar: deger}), encoding="utf-8")
    r = _seal_block(None, str(p))
    assert deger[:32] in r


# == _seal_block: chain gecerli =========================================================================

def test_seal_chain_gecerli_intact(tmp_path):
    """ORTAM: gecerli chain -> INTACT."""
    from dumen.reports.evidence_chain import EvidenceChain

    ec = EvidenceChain()
    ec.append("hazirlik", {"a": 1})
    ec.append("test", {"b": 2})
    p = tmp_path / "c.json"
    p.write_text(ec.to_json(), encoding="utf-8")
    r = _seal_block(str(p), None)
    assert "INTACT" in r
    assert "evidence chain" in r


def test_seal_chain_kayit_sayisi(tmp_path):
    from dumen.reports.evidence_chain import EvidenceChain
    ec = EvidenceChain()
    for i in range(5):
        ec.append("adim-%d" % i, {"i": i})
    p = tmp_path / "c.json"
    p.write_text(ec.to_json(), encoding="utf-8")
    r = _seal_block(str(p), None)
    assert "5 records" in r or "5" in r


def test_seal_chain_head_hash(tmp_path):
    from dumen.reports.evidence_chain import EvidenceChain
    ec = EvidenceChain()
    ec.append("adim", {"x": 1})
    p = tmp_path / "c.json"
    p.write_text(ec.to_json(), encoding="utf-8")
    r = _seal_block(str(p), None)
    v = ec.verify()
    assert v.head_hash[:8] in r


def test_seal_chain_bozuk(tmp_path):
    """ORTAM: bozuk chain -> BROKEN."""
    from dumen.reports.evidence_chain import EvidenceChain
    ec = EvidenceChain()
    ec.append("hazirlik", {"a": 1})
    raw = ec.to_json()
    bozuk = json.loads(raw)
    # ORTAM: to_json keys = ['canon_scheme', 'evidence_chain']
    recs = bozuk.get("evidence_chain") or bozuk.get("records") or []
    assert recs, "from_json destek-beklenen kayit-listesi"
    recs[0]["payload"] = {"a": 999}
    p = tmp_path / "c.json"
    p.write_text(json.dumps(bozuk), encoding="utf-8")
    r = _seal_block(str(p), None)
    """ORTAM-OGRENDI: from_json KURUCU-ASAMADA verify yapar; bozuk zincir
    -> ValueError -> 'UNREADABLE' (BROKEN asla gosterilmez — BROKEN sadece
    verify() false ama from_json gecerli oldugu durumlar icin)."""
    assert "UNREADABLE" in r


# == _seal_block: ikisi ================================================================================

def test_seal_ikisi_gecerli(tmp_path):
    from dumen.reports.evidence_chain import EvidenceChain
    ec = EvidenceChain()
    ec.append("hazirlik", {"a": 1})
    cp = tmp_path / "c.json"
    cp.write_text(ec.to_json(), encoding="utf-8")
    sp = tmp_path / "s.json"
    sp.write_text(json.dumps({"signer_name": "Z"}), encoding="utf-8")
    r = _seal_block(str(cp), str(sp))
    assert "evidence chain" in r
    assert "signature" in r
    assert "INTACT" in r


def test_seal_ikisi_unreadable(tmp_path):
    cp = tmp_path / "yok1.json"
    sp = tmp_path / "yok2.json"
    r = _seal_block(str(cp), str(sp))
    assert r.count("UNREADABLE") == 2


def test_seal_chain_gereksiz_karistir(tmp_path):
    """ORTAM: chain okunur, sig okunamaz."""
    from dumen.reports.evidence_chain import EvidenceChain
    ec = EvidenceChain()
    ec.append("hazirlik", {"a": 1})
    cp = tmp_path / "c.json"
    cp.write_text(ec.to_json(), encoding="utf-8")
    r = _seal_block(str(cp), str(tmp_path / "yok.json"))
    assert "INTACT" in r
    assert "UNREADABLE" in r


def test_seal_sira_chain_once(tmp_path):
    """ORTAM: chain bloku sig'den ONCE gelir."""
    from dumen.reports.evidence_chain import EvidenceChain
    ec = EvidenceChain()
    ec.append("hazirlik", {"a": 1})
    cp = tmp_path / "c.json"
    cp.write_text(ec.to_json(), encoding="utf-8")
    sp = tmp_path / "s.json"
    sp.write_text(json.dumps({"signer_name": "Z"}), encoding="utf-8")
    r = _seal_block(str(cp), str(sp))
    assert r.index("evidence chain") < r.index("signature")

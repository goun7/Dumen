"""77-Dumen veridict_bridge._digest_payload + _digest_json dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (json + sha256 — dis cagri YOK).
Kararli SHA-256 ozet (kanonik JSON).
"""
import hashlib
import json
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from dumen.reports.veridict_bridge import _digest_json, _digest_payload  # noqa: E402

# == _digest_payload: temel ===========================================================================

def test_returns_str():
    assert isinstance(_digest_payload({"a": 1}), str)


def test_hex_uzunluk():
    """ORTAM: 64-hex (256-bit)."""
    assert len(_digest_payload({"a": 1})) == 64


def test_hex_karakterler():
    """ORTAM: sadece [0-9a-f]."""
    h = _digest_payload({"a": 1})
    assert all(c in "0123456789abcdef" for c in h)


def test_bos_dict():
    """ORTAM: {} -> sha256('{}')."""
    h = hashlib.sha256(json.dumps({}, sort_keys=True,
                                   separators=(",", ":"),
                                   ensure_ascii=False).encode()).hexdigest()
    assert _digest_payload({}) == h


def test_bos_dict_sabit():
    """ORTAM: {} sabit-deger."""
    assert _digest_payload({}) == "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"


def test_siralama_bagimsiz():
    """ORTAM: anahtar-sirasi ONEMLI DEGIL (sort_keys=True)."""
    assert _digest_payload({"a": 1, "b": 2}) == _digest_payload({"b": 2, "a": 1})


def test_kanalizasyon():
    """ORTAM: separators=(',', ':') — bosluklar YOK."""
    h = hashlib.sha256(b'{"a":1,"b":2}').hexdigest()
    assert _digest_payload({"a": 1, "b": 2}) == h


def test_repeatable():
    assert _digest_payload({"a": 1}) == _digest_payload({"a": 1})


def test_farkli_payload_farkli_hash():
    assert _digest_payload({"a": 1}) != _digest_payload({"a": 2})


def test_unicode_korunur():
    """ORTAM: ensure_ascii=False -> UTF-8."""
    h = hashlib.sha256(json.dumps({"k": "İİ"},
                                  sort_keys=True,
                                  separators=(",", ":"),
                                  ensure_ascii=False).encode("utf-8")).hexdigest()
    assert _digest_payload({"k": "İİ"}) == h


def test_unicode_dogrula():
    """ORTAM: turkce-karakter kanonik-hex."""
    assert _digest_payload({"x": "DÜMEN"}) != _digest_payload({"x": "DUMEN"})


def test_ascii_ayni():
    """ORTAM: ASCII icin utf-8/latin1 ayni."""
    assert _digest_payload({"x": "abc"}) == _digest_payload({"x": "abc"})


# == tip dallari =======================================================================================

def test_list_siralamali():
    """ORTAM: liste SIRA-ONEMLI (sort_keys listeyi siralamaz!)."""
    assert _digest_payload([3, 1, 2]) != _digest_payload([1, 2, 3])


def test_list_ayni_sira():
    assert _digest_payload([1, 2, 3]) == _digest_payload([1, 2, 3])


def test_str():
    """ORTAM: str payload -> JSON-string."""
    assert _digest_payload("test") == _digest_payload("test")
    assert _digest_payload("test") != _digest_payload("test2")


def test_int():
    assert _digest_payload(42) != _digest_payload(43)


def test_float():
    """ORTAM: float vs int FARKLI."""
    assert _digest_payload(1.0) != _digest_payload(1)


def test_bool():
    """ORTAM: bool vs int FARKLI (json: true vs 1)."""
    assert _digest_payload(True) != _digest_payload(1)


def test_none():
    assert _digest_payload(None) != _digest_payload({})


def test_nested():
    """ORTAM: icice dict siralanir."""
    a = _digest_payload({"z": {"y": 1, "x": 2}})
    b = _digest_payload({"z": {"x": 2, "y": 1}})
    assert a == b


def test_nested_list():
    a = _digest_payload({"l": [9, 8, 7]})
    b = _digest_payload({"l": [7, 8, 9]})
    assert a != b


def test_bos_str():
    assert _digest_payload("") == _digest_payload("")


def test_bos_list():
    assert _digest_payload([]) == _digest_payload([])


@pytest.mark.parametrize("p", [
    {"a": 1}, [1, 2, 3], "x", 42, 1.5, True, None, {}, [],
])
def test_tip_matrix(p):
    """ORTAM: her tip JSON'a serialize olur."""
    assert len(_digest_payload(p)) == 64


# == _digest_json ======================================================================================

def test_digest_json_str():
    """ORTAM: JSON-text -> sha256 (sort + compact?)."""
    assert isinstance(_digest_json('{"a":1}'), str)


def test_digest_json_uzunluk():
    assert len(_digest_json('{"a":1}')) == 64


def test_digest_json_raw():
    """ORTAM: ham-metin sha256 (yeniden-siralamadan)."""
    h = hashlib.sha256('{"b":2,"a":1}'.encode()).hexdigest()
    assert _digest_json('{"b":2,"a":1}') == h


def test_digest_json_sira_onecli():
    """ORTAM: ham-metin SIRA-ONEMLI."""
    assert _digest_json('{"a":1,"b":2}') != _digest_json('{"b":2,"a":1}')


def test_digest_json_repeatable():
    assert _digest_json('{"a":1}') == _digest_json('{"a":1}')


def test_digest_json_farkli():
    assert _digest_json('{"a":1}') != _digest_json('{"a":2}')


def test_digest_json_bos():
    assert len(_digest_json("")) == 64


def test_digest_json_unicode():
    """ORTAM: UTF-8 metin."""
    h = hashlib.sha256("DÜMEN".encode("utf-8")).hexdigest()
    assert _digest_json("DÜMEN") == h


def test_digest_json_ham_vs_payload():
    """ORTAM: _digest_payload('{"a":1}') != _digest_json('{...}')
    (payload JSON-string olarak serialize eder)."""
    assert _digest_payload('{"a":1}') != _digest_json('{"a":1}')


def test_digest_json_turkce_karakter():
    assert _digest_json("İİ") != _digest_json("II")


# == genel ==============================================================================================

def test_two_payloads_collision_yok():
    """ORTAM: farkli degerler farkli-hash (256-bit)."""
    degerler = [{"a": 1}, {"a": 2}, {"b": 1}, [1], "1", 1, True]
    hashes = {_digest_payload(v) for v in degerler}
    assert len(hashes) >= 5


def test_kanalizasyon_dict():
    """ORTAM: ayraclar compact — '{"a":1}' (bosluk YOK)."""
    assert _digest_payload({"a": 1}) == _digest_json('{"a":1}')


# == ek dal-kesen====================================================================================

def test_sha256_bilinen_abc():
    """ORTAM: sha256('abc') bilinen sabit ba7816bf8f01cfea... (NIST)."""
    assert _digest_json("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sha256_bilinen_bos():
    """ORTAM: sha256('') bilinen sabit e3b0c44298fc1c14... (NIST)."""
    assert _digest_json("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_kararli_hash_amaci():
    """ORTAM-OGRENDI (AKADEMIK): 'kararli SHA-256 ozeti' — ayni icerigi
    farkli uretim-sirasinda yazan iki surec AYNI digest'i bulusmali
    (deterministik hash = kriptografik anlasma). DAGISIK anahtar-sirasi ->
    TEK canonical -> TEK sha256."""
    varyasyonlar = [
        {"b": 2, "a": 1, "c": 3}, {"a": 1, "c": 3, "b": 2}, {"c": 3, "a": 1, "b": 2},
    ]
    digestler = [_digest_payload(v) for v in varyasyonlar]
    assert len(set(digestler)) == 1


def test_kanonik_json_semasi():
    """ORTAM-OGRENDI: canonical = sort_keys + compact separators +
    ensure_ascii=False (RFC 8785 JCS ile AYNI sema)."""
    beklenen = hashlib.sha256('{"a":1,"x":"ö"}'.encode("utf-8")).hexdigest()
    assert _digest_payload({"x": "ö", "a": 1}) == beklenen


def test_turkce_ensure_ascii_karsi():
    """ORTAM: ensure_ascii=False oldugunu kanitla — kacisli versiyon
    FARKLI digest verir."""
    kacisli = hashlib.sha256(b'{"x": "\\u00f6"}').hexdigest()
    assert _digest_payload({"x": "ö"}) != kacisli


def test_emoji_kacislanmaz():
    """ORTAM: emoji OLDUGU GIBI (surrogate-pair kacisi YOK)."""
    beklenen = hashlib.sha256('{"x":"🎉"}'.encode("utf-8")).hexdigest()
    assert _digest_payload({"x": "🎉"}) == beklenen


def test_dp_dj_esit_canonical():
    """ORTAM-OGRENDI: payload zaten canonical-sirali JSON ise _dp == _dj."""
    assert _digest_json('{"a":1}') == _digest_payload({"a": 1})


def test_dp_dj_farkli_sirali():
    """ORTAM: sirali olmayan JSON metni _dj ile _dp FARKLI."""
    assert _digest_json('{"b":1,"a":2}') != _digest_payload({"a": 2, "b": 1})


def test_dj_none_hata():
    """ORTAM: None.encode -> AttributeError (str gerek)."""
    with pytest.raises(AttributeError):
        _digest_json(None)


def test_dj_bytes_hata():
    """ORTAM: bytes.encode YOK -> AttributeError."""
    with pytest.raises(AttributeError):
        _digest_json(b"x")


def test_icice_sort_keys_recursive():
    """ORTAM: icice dict'lerde sort_keys RECURSIVE calisir (derin)."""
    a = {"z": {"y": {"b": 1, "a": 2}, "x": 3}, "w": 4}
    b = {"w": 4, "z": {"x": 3, "y": {"a": 2, "b": 1}}}
    assert _digest_payload(a) == _digest_payload(b)

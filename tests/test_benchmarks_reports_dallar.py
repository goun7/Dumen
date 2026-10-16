"""77-Dumen benchmarks._num/_word/_yesno/_letter/_gsm8k_answer + reports._ecmascript_number/_digest_payload/_digest_json/_badgify/_mark_embed dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (saf fonksiyonlar + monkeypatch; network/DB YASAK).

ORTAM-ANATOMI:
- _num(target) -> closure: re.search(r'\\d+') == target
- _word(target) -> closure: \\b target.lower() \\b kelime-siniri
- _yesno(target) -> closure: \\b(yes|no|evet|hay[ıi]r)\\b -> _YESNO_CANON
- _letter(target) -> closure: strip().upper().lstrip('(').rstrip(')').startswith
- _gsm8k_answer(f): bool->None; int/float->float; str->'<<...>>' else
  '####...' else None
- _ecmascript_number(v): ECMAScript Number.toString; 0->'0'; NaN/inf ValueError
- _digest_payload(p): sha256(json.dumps(p, sort_keys=True, ...))
- _digest_json(t): sha256(text.encode('utf-8'))
- _badgify(t): _EMOJI_BADGE tablosu ile emoji -> HTML badge
- _mark_embed(): marka SVG'si; OSError -> ''
"""
import hashlib
import json
import sys

import pytest

sys.path.insert(0, ".")
from dumen.benchmarks.capability_gate import (  # noqa: E402
    _gsm8k_answer,
    _letter,
    _num,
    _word,
    _yesno,
)
from dumen.reports.html_export import (  # noqa: E402
    _EMOJI_BADGE,
    _badgify,
    _mark_embed,
)
from dumen.reports.rfc8785 import _ecmascript_number  # noqa: E402
from dumen.reports.veridict_bridge import _digest_json, _digest_payload  # noqa: E402

# == _num =============================================================================================

def test_num_gecerli():
    """ORTAM: re.search(r'\\d+') ile ilk sayiyi alir, esitlik kiyaslar."""
    assert _num(42)("cevap 42") is True


def test_num_ilk_sayi():
    """ORTAM-OGRENDI: ILK \\d+ alinir — '7 ve 42' -> 7."""
    assert _num(7)("7 ve 42") is True
    assert _num(42)("7 ve 42") is False


def test_num_sayi_yok():
    assert _num(42)("yok") is False


def test_num_farkli():
    assert _num(42)("41") is False


def test_num_sifir():
    assert _num(0)("0") is True
    assert _num(0)("yok") is False


def test_num_metin_icinde():
    """ORTAM: \\d+ her yerde — tam kelime DEGIL."""
    assert _num(42)("abc42def") is True


def test_num_buyuk():
    """ORTAM: buyuk tamsayi eslestirme."""
    assert _num(1000000)("cevap 1000000") is True


def test_num_binler_ayraci_tuzagi():
    r"""ORTAM-OGRENDI: \d+ '1.000.000' -> ILK '1' alinir (binler-ayraci
    desteklenmez!)."""
    assert _num(1)("1.000.000") is True
    assert _num(1000000)("1.000.000") is False


def test_num_negatif():
    """ORTAM-OGRENDI: \\d+ '-' YAKALAMAZ — '-42' -> 42!"""
    assert _num(42)("-42") is True
    assert _num(-42)("-42") is False


def test_num_ondalik():
    """ORTAM: \\d+ ondalikta sadece tamsayi kismi."""
    assert _num(42)("42.7") is True


def test_num_donut_callable():
    """ORTAM: CLOSURE doner (callable)."""
    v = _num(5)
    assert callable(v)


def test_num_bagimsiz_closure():
    """ORTAM: her cagri ayri closure."""
    a = _num(1)
    b = _num(2)
    assert a("1") is True
    assert b("1") is False


@pytest.mark.parametrize("t,ans,r", [
    (42, "42", True), (42, "43", False), (42, "yok", False),
    (7, "7 ve 42", True), (42, "7 ve 42", False), (0, "0", True),
])
def test_num_matrix(t, ans, r):
    assert _num(t)(ans) is r


# == _word ============================================================================================

def test_word_gecerli():
    assert _word("merhaba")("merhaba dunya") is True


def test_word_bosluk_siniri():
    """ORTAM: \\b kelime-siniri — 'merhaba' 'merhabalar' icinde ESLEMEZ."""
    assert _word("merhaba")("merhabalar") is False


def test_word_icinde_degil():
    assert _word("aba")("merhaba") is False


def test_word_basinda():
    assert _word("merhaba")("merhaba") is True


def test_word_sonda():
    assert _word("dunya")("merhaba dunya") is True


def test_word_case_sensitive_hedef():
    """ORTAM: target.lower() — buyuk hedef KABUL."""
    assert _word("Merhaba")("merhaba") is True


def test_word_case_insensitive_cevap():
    """ORTAM: ans.lower() — cevap buyuk KABUL."""
    assert _word("merhaba")("MERHABA") is True


def test_word_regex_karakterler():
    """ORTAM: re.escape — nokta harf gibi (kelime-ici)."""
    assert _word("a.b")("a.b") is True
    assert _word("a.b")("axb") is False


def test_word_kelime_olmayan_hedef_tuzagi():
    """ORTAM-OGRENDI: \b kelime-siniri — kelime-olmayan karakterlerle
    baslayan hedefler '(x)' ESLESEMEZ (\b iki non-word arasinda match
    etmez)."""
    assert _word("(x)")("(x)") is False


def test_word_kelime_icinde_ayri():
    """ORTAM: \\b\\b — 'evet' 'evet.' icinde KABUL (nokta sinir)."""
    assert _word("evet")("evet.") is True


def test_word_donut_callable():
    assert callable(_word("x"))


@pytest.mark.parametrize("t,ans,r", [
    ("merhaba", "merhaba", True), ("merhaba", "merhabalar", False),
    ("Merhaba", "MERHABA", True), ("a", "a b", True), ("ab", "xa", False),
])
def test_word_matrix(t, ans, r):
    assert _word(t)(ans) is r


# == _yesno ===========================================================================================

def test_yesno_yes():
    assert _yesno("yes")("yes") is True


def test_yesno_no():
    assert _yesno("no")("no") is True


def test_yesno_evet_tr():
    """ORTAM: _YESNO_CANON evet->yes (TR destek)."""
    assert _yesno("yes")("evet") is True


def test_yesno_hayir_tr():
    """ORTAM: hayir/hayıır -> no."""
    assert _yesno("no")("hayir") is True
    assert _yesno("no")("hayır") is True


def test_yesno_hedef_tr():
    """ORTAM: hedef de TR olabilir (canon map)."""
    assert _yesno("evet")("yes") is True
    assert _yesno("hayir")("no") is True


def test_yesno_yanlis_eslesme():
    assert _yesno("yes")("no") is False


def test_yesno_ilk_kelime():
    """ORTAM-OGRENDI: re.search ILK eslesmeyi alir — 'no yes' -> no!"""
    assert _yesno("no")("no yes") is True
    assert _yesno("yes")("no yes") is False


def test_yesno_metin_icinde():
    """ORTAM: \\b kelime siniri — 'yes' 'beyes' icin DEGIL."""
    assert _yesno("yes")("beyes") is False


def test_yesno_yok():
    assert _yesno("yes")("belki") is False


def test_yesno_buyuk_harf():
    """ORTAM: ans.lower() — 'YES' KABUL."""
    assert _yesno("yes")("YES") is True


def test_yesno_buyuk_hedef():
    """ORTAM: target.lower() + canon."""
    assert _yesno("YES")("yes") is True


def test_yesno_donut_callable():
    assert callable(_yesno("yes"))


def test_yesno_stabil():
    v = _yesno("yes")
    assert v("yes") is True
    assert v("no") is False


@pytest.mark.parametrize("t,ans,r", [
    ("yes", "yes", True), ("no", "no", True), ("yes", "evet", True),
    ("no", "hayir", True), ("no", "hayır", True), ("yes", "no", False),
    ("yes", "belki", False), ("yes", "YES", True),
])
def test_yesno_matrix(t, ans, r):
    assert _yesno(t)(ans) is r


# == _letter ==========================================================================================

def test_letter_basit():
    assert _letter("A")("A") is True


def test_letter_kucuk_cevap():
    """ORTAM: ans.upper() — 'a' KABUL."""
    assert _letter("A")("a") is True


def test_letter_bosluk():
    """ORTAM: ans.strip() — '  A  ' KABUL."""
    assert _letter("A")("  A  ") is True


def test_letter_parantez():
    """ORTAM-OGRENDI: lstrip('(').rstrip(')') — '(A)' KABUL (coktan-secmeli
    format destegi)."""
    assert _letter("A")("(A)") is True
    assert _letter("A")("((A))") is True


def test_letter_eksik_parantez():
    assert _letter("A")("(A") is True
    assert _letter("A")("A)") is True


def test_letter_baska_harf():
    assert _letter("A")("B") is False


def test_letter_cok_harfli_hedef():
    """ORTAM: startswith — 'AB' hedefi 'ABC' icin True (prefix!)."""
    assert _letter("AB")("ABC") is True
    assert _letter("AB")("ACB") is False


def test_letter_hedef_kucuk():
    """ORTAM: target.upper()."""
    assert _letter("a")("A") is True


def test_letter_ongek():
    """ORTAM-OGRENDI: startswith — 'AB' cevabi icin A True (prefix
    davranisi; TAM-esitlik DEGIL)."""
    assert _letter("A")("AB") is True


def test_letter_bos_cevap():
    assert _letter("A")("") is False


def test_letter_bos_hedef():
    """ORTAM: ''.startswith('') -> True."""
    assert _letter("")("") is True


def test_letter_donut_callable():
    assert callable(_letter("A"))


def test_letter_stabil():
    v = _letter("C")
    assert v("C") is True
    assert v("D") is False


@pytest.mark.parametrize("t,ans,r", [
    ("A", "A", True), ("A", "a", True), ("A", "(A)", True),
    ("A", "  A ", True), ("A", "B", False), ("A", "", False),
])
def test_letter_matrix(t, ans, r):
    assert _letter(t)(ans) is r


# == _gsm8k_answer =====================================================================================

def test_gsm_isaretli():
    """ORTAM: '<<42>>' -> 42.0."""
    assert _gsm8k_answer("... <<42>>") == 42.0


def test_gsm_isaretli_bosluk():
    """ORTAM: <<\\s*(-?\\d+...)?\\s*>> — bosluk toleransli."""
    assert _gsm8k_answer("<< 42 >>") == 42.0


def test_gsm_ondalik():
    assert _gsm8k_answer("<<7.5>>") == 7.5


def test_gsm_negatif():
    """ORTAM: -? negatif KABUL."""
    assert _gsm8k_answer("<<-3>>") == -3.0


def test_gsm_karisik_metin():
    assert _gsm8k_answer("5 * 7 = <<35>> dogru") == 35.0


def test_gsm_duz_sayi_fallback():
    """ORTAM-OGRENDI: <<>> YOKSA '#### sayi' fallback (bazı sürümlerde
    son satir düz sayi)."""
    assert _gsm8k_answer("cevap\n#### 42") == 42.0


def test_gsm_duz_sayi_bosliz():
    assert _gsm8k_answer("####7") == 7.0


def test_gsm_duz_sayi_negatif():
    assert _gsm8k_answer("#### -5") == -5.0


def test_gsm_iki_format_varsa_isaretli_oncelikli():
    """ORTAM-OGRENDI: <<>> ARANIR ONCE — #### fallback yalniz <<>> YOKSA."""
    assert _gsm8k_answer("<<11>>\n#### 99") == 11.0


def test_gsm_int_direkt():
    """ORTAM: isinstance(int) -> float(int) (<<>> YOK)."""
    assert _gsm8k_answer(42) == 42.0


def test_gsm_float_direkt():
    assert _gsm8k_answer(3.5) == 3.5


def test_gsm_bool_none():
    """ORTAM-OGRENDI: bool ONCE kontrol — True isinstance int oldugu
    icin 1.0 DONMEZ, None doner (bool tuzaği!)."""
    assert _gsm8k_answer(True) is None
    assert _gsm8k_answer(False) is None


def test_gsm_none():
    assert _gsm8k_answer(None) is None


def test_gsm_dict():
    """ORTAM: dict -> None."""
    assert _gsm8k_answer({"a": 1}) is None


def test_gsm_liste():
    assert _gsm8k_answer([1, 2]) is None


def test_gsm_metin_sayi_yok():
    assert _gsm8k_answer("cevap yok") is None


def test_gsm_bos_metin():
    assert _gsm8k_answer("") is None


def test_gsm_isaretli_metinde():
    """ORTAM: search — '<<>>' her yerde."""
    assert _gsm8k_answer("a <<42>> b #### 99") == 42.0


def test_gsm_donut_float_veya_none():
    v = _gsm8k_answer("<<1>>")
    assert v is None or isinstance(v, float)


def test_gsm_stabil():
    assert _gsm8k_answer("<<42>>") == _gsm8k_answer("<<42>>")


@pytest.mark.parametrize("f,b", [
    ("<<42>>", 42.0), ("<< 42 >>", 42.0), ("<<-3>>", -3.0), ("<<7.5>>", 7.5),
    ("#### 42", 42.0), ("cevap\n#### 42", 42.0), ("yok", None),
    (42, 42.0), (3.5, 3.5), (True, None), (None, None), ({}, None),
])
def test_gsm_matrix(f, b):
    v = _gsm8k_answer(f)
    assert v == b if b is not None else v is None


# == _ecmascript_number ================================================================================

def test_es_sifir():
    """ORTAM: 0 -> '0' (hem 0.0 hem -0.0)."""
    assert _ecmascript_number(0.0) == "0"


def test_es_neg_sifir():
    assert _ecmascript_number(-0.0) == "0"


def test_es_bir():
    """ORTAM: 1.0 -> '1' (Python json.dumps '1.0' VERIRDI — ECMAScript
    '1'; RFC 8785 uyumu)."""
    assert _ecmascript_number(1.0) == "1"


def test_es_yuz():
    assert _ecmascript_number(100.0) == "100"


def test_es_ondalik():
    assert _ecmascript_number(0.5) == "0.5"


def test_es_bilimsel():
    assert _ecmascript_number(2.93e-07) == "2.93e-7"


def test_es_buyuk_ussu():
    assert _ecmascript_number(1e21) == "1e+21"


def test_es_kucuk_ussu():
    assert _ecmascript_number(1e-06) == "0.000001"


def test_es_negatif():
    assert _ecmascript_number(-1.5) == "-1.5"


def test_es_buyuk_ondalik():
    assert _ecmascript_number(123456.789) == "123456.789"


def test_es_nan_hata():
    """ORTAM: NaN -> ValueError (RFC 8785 reddi)."""
    with pytest.raises(ValueError):
        _ecmascript_number(float("nan"))


def test_es_inf_hata():
    with pytest.raises(ValueError):
        _ecmascript_number(float("inf"))


def test_es_neg_inf_hata():
    with pytest.raises(ValueError):
        _ecmascript_number(float("-inf"))


def test_es_donut_tipi():
    assert isinstance(_ecmascript_number(1.5), str)


def test_es_stabil():
    assert _ecmascript_number(3.14) == _ecmascript_number(3.14)


@pytest.mark.parametrize("v,b", [
    (0.0, "0"), (1.0, "1"), (-0.0, "0"), (100.0, "100"), (0.5, "0.5"),
    (2.93e-07, "2.93e-7"), (1e21, "1e+21"), (1e-06, "0.000001"),
    (-1.5, "-1.5"),
])
def test_es_matrix(v, b):
    assert _ecmascript_number(v) == b


# == _digest_payload / _digest_json ====================================================================

def test_dp_basit():
    """ORTAM: sha256(json.dumps(payload, sort_keys=True, ...))."""
    assert _digest_payload({"a": 1}) == hashlib.sha256(
        json.dumps({"a": 1}, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")).hexdigest()


def test_dp_sirali():
    """ORTAM: sort_keys — anahtar sirasi onemsiz."""
    assert _digest_payload({"a": 1, "b": 2}) == _digest_payload({"b": 2, "a": 1})


def test_dp_deterministik():
    assert _digest_payload({"a": 1}) == _digest_payload({"a": 1})


def test_dp_icice():
    v = _digest_payload({"a": {"b": 1}})
    assert isinstance(v, str) and len(v) == 64


def test_dp_bos():
    assert _digest_payload({}) == _digest_payload({})


def test_dp_farkli_icerik():
    assert _digest_payload({"a": 1}) != _digest_payload({"a": 2})


def test_dp_donut_tipi():
    assert isinstance(_digest_payload({}), str)


def test_dp_uzunluk():
    v = _digest_payload({"x": 1})
    assert len(v) == 64
    assert all(c in "0123456789abcdef" for c in v)


def test_dj_basit():
    """ORTAM: sha256(text.encode('utf-8'))."""
    assert _digest_json("x") == hashlib.sha256(b"x").hexdigest()


def test_dj_bos():
    assert _digest_json("") == hashlib.sha256(b"").hexdigest()


def test_dj_turkce():
    """ORTAM: UTF-8 kodlamasi."""
    assert _digest_json("Örnek") == hashlib.sha256("Örnek".encode("utf-8")).hexdigest()


def test_dj_deterministik():
    assert _digest_json("abc") == _digest_json("abc")


def test_dj_farkli():
    assert _digest_json("a") != _digest_json("b")


def test_dj_donut_tipi():
    assert isinstance(_digest_json(""), str)


def test_dj_uzunluk():
    assert len(_digest_json("test")) == 64


@pytest.mark.parametrize("t", ["", "a", "merhaba", "Örnek", '{"a":1}', "12345"])
def test_dj_matrix(t):
    assert _digest_json(t) == hashlib.sha256(t.encode("utf-8")).hexdigest()


# == _badgify =========================================================================================

def test_badgify_yesil():
    """ORTAM: '🟢' -> <span class="badge badge-ok">OLCUMLDU</span>."""
    v = _badgify("🟢")
    assert v == '<span class="badge badge-ok">OLCUMLDU</span>'


def test_badgify_kirmizi():
    assert _badgify("🔴") == '<span class="badge badge-bad">BASARISIZ</span>'


def test_badgify_sari():
    assert _badgify("🟡") == '<span class="badge badge-warn">OLCUMLDI ( kisitli )</span>'


def test_badgify_tamamlandi():
    assert _badgify("✅") == '<span class="badge badge-ok">TAMAMLANDI</span>'


def test_badgify_yapilmadi():
    assert _badgify("❌") == '<span class="badge badge-bad">YAPILMADI</span>'


def test_badgify_dikkat():
    """ORTAM: hem '⚠️' hem '⚠' ayni badge."""
    assert _badgify("⚠️") == '<span class="badge badge-warn">DIKKAT</span>'
    assert _badgify("⚠") == '<span class="badge badge-warn">DIKKAT</span>'


def test_badgify_metin_korunur():
    """ORTAM: emoji DISINDA metin KORUNUR."""
    assert _badgify("🟢 olcum basarili") == \
        '<span class="badge badge-ok">OLCUMLDU</span> olcum basarili'


def test_badgify_coklu_emoji():
    """ORTAM: tum emojiler replace edilir."""
    v = _badgify("🟢 ve 🔴")
    assert "badge-ok" in v and "badge-bad" in v


def test_badgify_emoji_yok():
    """ORTAM: emoji yoksa metin OLDUGU GIBI."""
    assert _badgify("normal metin") == "normal metin"


def test_badgify_bos():
    assert _badgify("") == ""


def test_badgify_tum_tablo():
    """ORTAM: _EMOJI_BADGE tablosundaki her emoji replace edilir."""
    for emo, badge in _EMOJI_BADGE.items():
        assert _badgify(emo) == badge


def test_badgify_emoji_kalma():
    """ORTAM-OGRENDI: tablo disi emoji KALIR (replace yalniz tabloda)."""
    v = _badgify("😀")
    assert "😀" in v


def test_badgify_donut_tipi():
    assert isinstance(_badgify(""), str)


def test_badgify_stabil():
    assert _badgify("🟢 x") == _badgify("🟢 x")


# == _mark_embed ======================================================================================

def test_mark_svg_var():
    """ORTAM: marka SVG'si mevcut (3078 byte)."""
    v = _mark_embed()
    assert isinstance(v, str)
    assert len(v) > 100


def test_mark_svg_xml():
    """ORTAM: SVG (<?xml ...> declaration temizlenir)."""
    v = _mark_embed()
    assert "<?xml" not in v
    assert "<svg" in v


def test_mark_svg_yok_bos(monkeypatch):
    """ORTAM-OGRENDI: OSError -> '' (SESSIZ COKUS YOK — <img> fallback
    yazilir; bos-string test edilebilir)."""
    import pathlib

    import dumen.reports.html_export as hx
    orijinal = hx._MARK_PATH
    monkeypatch.setattr(hx, "_MARK_PATH", pathlib.Path("/yok/yok.svg"))
    assert _mark_embed() == ""
    monkeypatch.setattr(hx, "_MARK_PATH", orijinal)


def test_mark_svg_dosya_degil_dizin(monkeypatch):
    import pathlib

    import dumen.reports.html_export as hx
    orijinal = hx._MARK_PATH
    monkeypatch.setattr(hx, "_MARK_PATH", pathlib.Path("/tmp"))
    assert _mark_embed() == ""
    monkeypatch.setattr(hx, "_MARK_PATH", orijinal)


def test_mark_svg_stabil():
    assert _mark_embed() == _mark_embed()


# == karakterizasyon ===================================================================================

def test_gsm_amaci():
    """ORTAM-OGRENDI (DOCSTACK): GSM8K 'answer' alanindan <<42>>
    son-adim sayisini cikarir. Bazi setler answer'i int/float yazar
    (<<>> yok); bool/None/dict gibi gecersiz tipler None doner (gorev
    atlanir). bool ONCE kontrol edilir (bool int tuzaği). Iki regex:
    <<\\s*(-?\\d+...)?\\s*>> once, #### sayi fallback."""
    assert _gsm8k_answer("5*7=<<35>>") == 35.0
    assert _gsm8k_answer("#### 42") == 42.0
    assert _gsm8k_answer(True) is None


def test_validators_amaci():
    """ORTAM-OGRENDI: validator CLOSURE'lari — capability-gate cevap
    dogrulama: _num (\\d+ esitlik), _word (\\b kelime-siniri),
    _yesno (EN/TR kanonik: yes/evet, no/hayir-hayıır; ILK eslesme
    kazanir), _letter (coktan-secmeli '(A)' parantez-soyma + prefix).
    DIL-BAĞIMSIZ kanonik esleme (AB regülatör dosyasinda kullanildi)."""
    assert _yesno("yes")("evet") is True
    assert _letter("A")("(A)") is True


def test_es_number_amaci():
    """ORTAM-OGRENDI: float'i ECMAScript Number.toString'a cevirir —
    Python json.dumps 1.0 -> '1.0' VERIRDI, RFC 8785 JCS '1' ister.
    NaN/Infinity reddedilir (JSON'da YASAK). Veridrome es_number ile
    BAYT-uyumu (parite)."""
    assert _ecmascript_number(1.0) == "1"
    assert _ecmascript_number(2.93e-07) == "2.93e-7"


def test_badgify_amaci():
    """ORTAM-OGRENDI (DOCSTACK): emoji durum-kodlarini HTML rozetlere
    cevirir — AB regülatör dosyasinda emoji UYGUNSUZ; renkli rozet ayni
    bilgiyi profesyonel bicimde tasir. 8-giris tablo (⚠️/⚠ ayni).
    Tablo disi emoji KALIR."""
    assert _badgify("🟢") == _EMOJI_BADGE["🟢"]

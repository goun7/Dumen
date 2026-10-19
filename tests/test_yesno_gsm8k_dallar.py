"""77-Dumen capability_gate._yesno + _gsm8k_answer dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (regex + type-dallari — dis cagri YOK).
Dil-bagimsiz evet/hayir + GSM8K son-adim sayisi.
"""
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from dumen.benchmarks.capability_gate import _YESNO_CANON, _gsm8k_answer, _yesno  # noqa: E402

# == _yesno: kanonik-esleme ============================================================================

def test_yesno_callable():
    """ORTAM: fonksiyon doner."""
    assert callable(_yesno("yes"))


def test_yesno_evet_target_true():
    """ORTAM: target=evet -> yes/evet True."""
    v = _yesno("evet")
    assert v("yes") is True
    assert v("evet") is True


def test_yesno_evet_target_false():
    """ORTAM: hayir/no -> False."""
    v = _yesno("evet")
    assert v("no") is False
    assert v("hayır") is False


def test_yesno_hayir_target():
    """ORTAM: target=hayir -> no/hayır True."""
    v = _yesno("hayır")
    assert v("no") is True
    assert v("hayır") is True
    assert v("yes") is False


def test_yesno_yes_target():
    v = _yesno("yes")
    assert v("yes") is True
    assert v("evet") is True
    assert v("no") is False


def test_yesno_no_target():
    v = _yesno("no")
    assert v("no") is True
    assert v("hayır") is True
    assert v("evet") is False


# == _yesno: kucuk/buyuk harf ===========================================================================

def test_yesno_buyuk_harf():
    """ORTAM: .lower() ile kucuk-harfe cevrilir."""
    v = _yesno("yes")
    assert v("YES") is True
    assert v("EVET") is True
    assert v("NO") is False


def test_yesno_karisik_harf():
    v = _yesno("yes")
    assert v("Yes") is True
    assert v("eVeT") is True


def test_yesno_target_buyuk_harf():
    """ORTAM: target da .lower()'lanir."""
    v = _yesno("EVET")
    assert v("yes") is True


def test_yesno_hayir_noktasiz():
    """ORTAM: 'hayir' (noktasiz i) kanonik."""
    v = _yesno("hayir")
    assert v("hayir") is True
    assert v("hayır") is True


def test_yesno_hayir_target_noktali():
    v = _yesno("hayır")
    assert v("hayir") is True


# == _yesno: baglam/metin ===============================================================================

def test_yesno_cumle_icinde():
    """ORTAM: re.search — cevap tam kelime olmak ZORUNDA DEGIL."""
    v = _yesno("yes")
    assert v("Yes, that is correct") is True
    assert v("No, that is wrong") is False


def test_yesno_bosluklu():
    v = _yesno("yes")
    assert v("  yes  ") is True


def test_yesno_kelime_siniri():
    """ORTAM: \\b kelime-siniri."""
    v = _yesno("yes")
    assert v("yesterday") is False


def test_yesno_kelime_siniri_no():
    v = _yesno("no")
    assert v("nothing") is False


def test_yesno_eslesme_yok():
    """ORTAM: norm-disi ilk kelime eslesmezse FAIL (dürüst)."""
    v = _yesno("yes")
    assert v("belki") is False


def test_yesno_bos():
    v = _yesno("yes")
    assert v("") is False


def test_yesno_sayi():
    v = _yesno("yes")
    assert v("42") is False


def test_yesno_iki_kelime():
    """ORTAM: re.search ILK eslesmeyi alir."""
    v = _yesno("no")
    assert v("yes no") is False  # yes once eslesir -> yes != no


def test_yesno_iki_kelime_tersten():
    """ORTAM: re.search ILK eslesmeyi alir — 'no yes' icin 'no' once
    eslesir -> _YESNO_CANON['no']='no' != 'yes' -> False."""
    v = _yesno("yes")
    assert v("no yes") is False


# == _yesno: genel =======================================================================================

def test_yesno_repeatable():
    v = _yesno("yes")
    assert v("yes") == v("yes")


def test_yesno_farkli_target_farkli():
    assert _yesno("yes")("no") != _yesno("no")("no")


@pytest.mark.parametrize("target,cvp,beklenen", [
    ("yes", "yes", True), ("yes", "evet", True), ("yes", "no", False),
    ("yes", "hayır", False), ("evet", "yes", True), ("evet", "EVET", True),
    ("no", "no", True), ("no", "hayır", True), ("no", "yes", False),
    ("hayır", "no", True), ("hayır", "hayir", True), ("hayır", "evet", False),
])
def test_yesno_matrix(target, cvp, beklenen):
    assert _yesno(target)(cvp) is beklenen


def test_canon_harita():
    """ORTAM: _YESNO_CANON 4-key."""
    assert _YESNO_CANON["yes"] == "yes"
    assert _YESNO_CANON["evet"] == "yes"
    assert _YESNO_CANON["no"] == "no"
    assert _YESNO_CANON["hayır"] == "no"


# == _gsm8k: << >> formati ==============================================================================

def test_gsm_cift_ok():
    """ORTAM: <<42>> -> 42.0."""
    assert _gsm8k_answer("sonuc <<42>>") == 42.0


def test_gsm_sadece_sayi():
    assert _gsm8k_answer("<<42>>") == 42.0


def test_gsm_float():
    """ORTAM: <<3.5>> -> 3.5."""
    assert _gsm8k_answer("<<3.5>>") == 3.5


def test_gsm_negatif():
    assert _gsm8k_answer("<<-3.5>>") == -3.5


def test_gsm_bosluklu():
    """ORTAM: \\s* esnek bosluk."""
    assert _gsm8k_answer("<< 42 >>") == 42.0


def test_gsm_birden_fazla():
    """ORTAM: search ILK eslesmeyi alir."""
    assert _gsm8k_answer("a <<1>> b <<2>>") == 1.0


def test_gsm_cok_basamakli():
    assert _gsm8k_answer("<<1234567>>") == 1234567.0


def test_gsm_sifir():
    assert _gsm8k_answer("<<0>>") == 0.0


def test_gsm_returns_float():
    """ORTAM: float() ile cevrilir."""
    assert isinstance(_gsm8k_answer("<<42>>"), float)


# == _gsm8k: #### formati ===============================================================================

def test_gsm_kare_format():
    """ORTAM: '#### 7' fallback."""
    assert _gsm8k_answer("cevap\n#### 7") == 7.0


def test_gsm_kare_float():
    assert _gsm8k_answer("#### 7.5") == 7.5


def test_gsm_kare_negatif():
    assert _gsm8k_answer("#### -7") == -7.0


def test_gsm_kare_boslukli():
    assert _gsm8k_answer("####  42") == 42.0


def test_gsm_kare_once_ok():
    """ORTAM: <<>> ONCE denenir."""
    assert _gsm8k_answer("<<5>>\n#### 9") == 5.0


# == _gsm8k: tip dallari ================================================================================

def test_gsm_int():
    """ORTAM: int -> float."""
    assert _gsm8k_answer(42) == 42.0


def test_gsm_float_tip():
    assert _gsm8k_answer(2.5) == 2.5


def test_gsm_bool():
    """ORTAM: bool -> None (bool int'in alt-sinifi ama ONCE kontrol)."""
    assert _gsm8k_answer(True) is None
    assert _gsm8k_answer(False) is None


def test_gsm_none():
    """ORTAM: None -> None."""
    assert _gsm8k_answer(None) is None


def test_gsm_dict():
    """ORTAM: dict -> None."""
    assert _gsm8k_answer({"a": 1}) is None


def test_gsm_liste():
    assert _gsm8k_answer([1, 2]) is None


def test_gsm_str_eslesme_yok():
    """ORTAM: ne <<>> ne #### -> None."""
    assert _gsm8k_answer("hicbir sey") is None


def test_gsm_bos_str():
    assert _gsm8k_answer("") is None


def test_gsm_sayi_yok_kare():
    """ORTAM: '####' ama sayi yok -> None."""
    assert _gsm8k_answer("#### abc") is None


def test_gsm_sadece_kare():
    assert _gsm8k_answer("####") is None


def test_gsm_ondalik_iki_basamak():
    r"""ORTAM: (?:\.\d+)? opsiyonel."""
    assert _gsm8k_answer("<<42>>") == 42.0
    assert _gsm8k_answer("<<42.5>>") == 42.5


@pytest.mark.parametrize("veri,beklenen", [
    ("<<42>>", 42.0), ("<<3.5>>", 3.5), ("<<-3.5>>", -3.5), ("<< 0 >>", 0.0),
    ("#### 7", 7.0), ("#### -7", -7.0), ("#### 7.5", 7.5),
    (42, 42.0), (2.5, 2.5), (True, None), (None, None), ("", None),
    ("abc", None), ({"a": 1}, None),
])
def test_gsm_matrix(veri, beklenen):
    r = _gsm8k_answer(veri)
    assert r == beklenen if beklenen is not None else r is None


# == genel ==============================================================================================

def test_gsm_cache():
    """ORTAM: global _GSM_FINAL_RE cache'lenir."""
    _gsm8k_answer("<<1>>")
    _gsm8k_answer("<<2>>")
    assert _gsm8k_answer("<<3>>") == 3.0


def test_yesno_ve_gsm_bagimsiz():
    """ORTAM: iki fonksiyon birbirini etkilemez."""
    assert _yesno("yes")("yes") is True
    assert _gsm8k_answer("<<42>>") == 42.0

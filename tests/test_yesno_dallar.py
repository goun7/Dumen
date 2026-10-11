"""dumen.benchmarks.capability_gate._yesno dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (regex sozluk — dis cagri YOK).
DIL-BAGIMSIZ evet/hayir dogrulayici (TR + EN).
"""
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from dumen.benchmarks.capability_gate import _yesno, _YESNO_CANON  # noqa: E402


# == temel ===========================================================================================

def test_returns_callable():
    assert callable(_yesno("yes"))


def test_yes_true():
    assert _yesno("yes")("yes") is True


def test_no_false():
    assert _yesno("no")("no") is True


def test_evet_true():
    """ORTAM: 'evet' -> yes."""
    assert _yesno("yes")("evet") is True


def test_hayir_false():
    """ORTAM: 'hayir' -> no."""
    assert _yesno("no")("hayir") is True


def test_hayir_turkce_i():
    """ORTAM: 'hayır' (TR-ı) -> no."""
    assert _yesno("no")("hayır") is True


# == target taraf ====================================================================================

def test_target_evet():
    """ORTAM: target TR olabilir."""
    v = _yesno("evet")
    assert v("evet") is True
    assert v("hayir") is False


def test_target_hayir():
    v = _yesno("hayır")
    assert v("no") is True


def test_target_yes_matches_evet():
    v = _yesno("yes")
    assert v("evet") is True and v("yes") is True


def test_target_yes_hayir_false():
    v = _yesno("yes")
    assert v("hayır") is False


# == regex davranisi ==================================================================================

def test_icinde_gecer():
    """ORTAM: regex search — cumle icinde."""
    assert _yesno("yes")("cevap: evet, oldu") is True


def test_basinda():
    assert _yesno("no")("hayir oldu") is True


def test_sonunda():
    assert _yesno("yes")("oldu evet") is True


def test_kelime_siniri():
    """ORTAM: \\b kelime-siniri."""
    assert _yesno("yes")("evetx") is False


def test_kelime_siniri_no():
    assert _yesno("no")("hayire") is False


def test_ilk_eslesme():
    """ORTAM: ilk-eslesme oncelikli (yes once)."""
    assert _yesno("yes")("yes no") is True


def test_ilk_eslesme_hayir():
    """ORTAM: 'no evet' -> ilk 'no' -> target=Yes False."""
    assert _yesno("yes")("no evet") is False


def test_eslesme_yok():
    assert _yesno("yes")("belki") is False


def test_bos_str():
    assert _yesno("yes")("") is False


def test_bosluk():
    assert _yesno("yes")("   ") is False


# == buyuk/kucuk harf ================================================================================

def test_cevap_buyuk_harf():
    """ORTAM: cevap lower-case aranir."""
    assert _yesno("yes")("EVET") is True


def test_cevap_karisik():
    assert _yesno("no")("HaYiR") is True


def test_target_buyuk_harf():
    """ORTAM: target.lower()."""
    assert _yesno("YES")("evet") is True


def test_target_karisik():
    assert _yesno("HayIr")("no") is True


# == _YESNO_CANON =====================================================================================

def test_canon_yes():
    assert _YESNO_CANON["yes"] == "yes"


def test_canon_evet():
    assert _YESNO_CANON["evet"] == "yes"


def test_canon_no():
    assert _YESNO_CANON["no"] == "no"


def test_canon_hayir():
    assert _YESNO_CANON["hayır"] == "no"


def test_canon_hayir_ascii():
    assert _YESNO_CANON["hayir"] == "no"


def test_canon_5_entry():
    """ORTAM: 5 kanonik-eslesme."""
    assert len(_YESNO_CANON) == 5


# == cesitli =========================================================================================

def test_turkce_cumle():
    assert _yesno("yes")("Evet, bu doğru") is True


def test_ingilizce_cumle():
    assert _yesno("no")("No, that is wrong") is True


def test_noktalama():
    assert _yesno("yes")("evet.") is True


def test_virgul():
    assert _yesno("no")("hayir, ama...") is True


def test_cok_uzun_cevap():
    assert _yesno("yes")("x" * 100 + " evet " + "y" * 100) is True


def test_repeatable():
    v = _yesno("yes")
    assert v("evet") == v("evet")


@pytest.mark.parametrize("ans,exp", [
    ("yes", True), ("evet", True), ("Evet", True), ("EVET", True),
    ("no", False), ("hayir", False), ("hayır", False), ("Hayır", False),
])
def test_cevap_matrix(ans, exp):
    v = _yesno("yes")
    assert v(ans) is exp


@pytest.mark.parametrize("ans,exp", [
    ("no", True), ("hayir", True), ("hayır", True), ("No", True),
    ("yes", False), ("evet", False), ("Evet", False),
])
def test_cevap_matrix_no(ans, exp):
    v = _yesno("no")
    assert v(ans) is exp


@pytest.mark.parametrize("bad", ["", "belki", "olabilir", "x", "evetx",
                                 " hayir ", "123"])
def test_gecersiz_matrix(bad):
    assert _yesno("yes")(bad) is False

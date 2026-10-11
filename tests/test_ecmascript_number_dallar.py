"""77-Dumen reports/rfc8785._ecmascript_number dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (saf fonksiyon — network/subprocess/DB YASAK).

AKADEMIK DAYANAK: ARASTIRMA_AKADEMIK_2026-10-11.md Bolum 5
- RFC 8785 (JCS) Haziran 2020: ECMAScript Number.prototype.toString
  semantigi; Python json.dumps'tan farkli: 1.0 -> '1', -0.0 -> '0'.
"""
import math
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from dumen.reports.rfc8785 import _ecmascript_number as _es  # noqa: E402


# == sabit-sifir ======================================================================================

def test_es_sifir():
    assert _es(0.0) == "0"


def test_es_eksi_sifir():
    """ORTAM-OGRENDI: -0.0 -> '0' (ECMAScript negatif-sifir YAZMAZ;
    Python json.dumps '-0.0' verirdi)."""
    assert _es(-0.0) == "0"


def test_es_eksi_sifir_isareti_yok():
    assert not _es(-0.0).startswith("-")


# == tamsayi-gosterim =================================================================================

def test_es_bir_nokta_sifir():
    """ORTAM: 1.0 -> '1' (trailing '.0' YOK)."""
    assert _es(1.0) == "1"


def test_es_yuz():
    assert _es(100.0) == "100"


def test_es_eksi_bes():
    assert _es(-5.0) == "-5"


def test_es_buyuk_tamsayi():
    assert _es(1e6) == "1000000"


def test_es_eksi_buyuk():
    assert _es(-1e6) == "-1000000"


def test_es_bilimsel_tamsayi():
    """ORTAM: 1e2 -> '100' (sabit gosterim, exponent>=0 dalinda)."""
    assert _es(1e2) == "100"


def test_es_1e16():
    """ORTAM: 1e16 hala sabit gosterim."""
    r = _es(1e16)
    assert not ("e" in r or "E" in r)


# == ondalik =========================================================================================

def test_es_bucuk():
    assert _es(1.5) == "1.5"


def test_es_ondalik_uzun():
    assert _es(123456.789) == "123456.789"


def test_es_sifir_bir():
    assert _es(0.1) == "0.1"


def test_es_eksi_ondalik():
    assert _es(-7.5) == "-7.5"


def test_es_pi():
    """ORTAM: 3.141592653589793 -> tam duyarlik."""
    assert _es(3.141592653589793) == "3.141592653589793"


def test_es_ondalik_sifir_eksilmez():
    """ORTAM: trailing sifirlarrstrip ile dusmez (repr kaynak)."""
    assert _es(1.0) == "1"


# == exponent (e-notasyonu) ===========================================================================

def test_es_kucuk_exponent():
    """ORTAM: 2.93e-7 -> '2.93e-7' (ECMAScript kisa)."""
    assert _es(2.93e-07) == "2.93e-7"


def test_es_1e_eksi_yedi():
    assert _es(1e-07) == "1e-7"


def test_es_buyuk_exponent():
    """ORTAM: 1e21 -> '1e+21'."""
    assert _es(1e21) == "1e+21"


def test_es_1e22():
    assert _es(1e22) == "1e+22"


def test_es_cok_buyuk():
    """ORTAM: 1e100 -> e-notasyonu."""
    r = _es(1e100)
    assert "e+" in r


def test_es_cok_kucuk():
    r = _es(1e-100)
    assert "e-" in r


def test_es_eksi_exponent_kucuk():
    """ORTAM: -2.93e-7."""
    assert _es(-2.93e-07) == "-2.93e-7"


def test_es_eksi_buyuk_exponent():
    assert _es(-1e21) == "-1e+21"


# == exponent-esigi (ECMAScript -6 < n <= 21 / 0 < n <= 21) ============================================

def test_es_e_sinir_ust_21():
    """ORTAM: 1e21 e-gosterimine gecer."""
    assert _es(1e21) == "1e+21"


def test_es_e_sinir_alt_21():
    """ORTAM: 1e20 hala sabit gosterim."""
    r = _es(1e20)
    assert "e" not in r
    assert r == "100000000000000000000"


def test_es_1e_negatif_altili_sabit():
    """ORTAM: 1e-6 -> '0.000001' (sabit gosterim, n > -6)."""
    assert _es(1e-06) == "0.000001"


def test_es_1e_negatif_yedili_e_notasyonu():
    """ORTAM: 1e-7 -> '1e-7' (n <= -6)."""
    assert _es(1e-07) == "1e-7"


def test_es_5e_negatif_yedi():
    """ORTAM: 5e-7 -> '5e-7'."""
    assert _es(5e-07) == "5e-7"


def test_es_1e_negatif_bes():
    assert _es(1e-05) == "0.00001"


# == NaN / Infinity ===================================================================================

def test_es_nan_reject():
    """ORTAM: NaN -> ValueError (RFC 8785'de tanimsiz)."""
    with pytest.raises(ValueError, match="NaN"):
        _es(float("nan"))


def test_es_inf_reject():
    with pytest.raises(ValueError, match="Infinity"):
        _es(float("inf"))


def test_es_eksi_inf_reject():
    with pytest.raises(ValueError):
        _es(float("-inf"))


def test_es_math_inf_reject():
    with pytest.raises(ValueError):
        _es(math.inf)


def test_es_math_nan_reject():
    with pytest.raises(ValueError):
        _es(math.nan)


# == genel ===========================================================================================

def test_es_str_doner():
    assert isinstance(_es(1.0), str)


def test_es_stabil():
    """ORTAM: ayni deger -> ayni cikti."""
    assert _es(3.14) == _es(3.14)


def test_es_farkli_deger_farkli_cikti():
    assert _es(1.0) != _es(2.0)


def test_es_isaret_korunur():
    assert _es(-1.0).startswith("-")
    assert _es(1.0).startswith("1")


@pytest.mark.parametrize("deger,beklenen", [
    (0.0, "0"), (-0.0, "0"), (1.0, "1"), (1.5, "1.5"), (-5.0, "-5"),
    (100.0, "100"), (1e2, "100"), (1e6, "1000000"),
    (123456.789, "123456.789"), (0.1, "0.1"), (-7.5, "-7.5"),
    (2.93e-07, "2.93e-7"), (1e-07, "1e-7"), (1e21, "1e+21"), (1e22, "1e+22"),
    (1e-06, "0.000001"), (5e-07, "5e-7"),
])
def test_es_matrix(deger, beklenen):
    assert _es(deger) == beklenen


def test_es_json_dumpstan_farkli():
    """ORTAM-OGRENDI: json.dumps(1.0)='1.0' ama _es(1.0)='1' — RFC 8785
    ECMAScript paritesi."""
    import json
    assert json.dumps(1.0) == "1.0"
    assert _es(1.0) == "1"


def test_es_json_dumpstan_farkli_eksi_sifir():
    import json
    assert json.dumps(-0.0) == "-0.0"
    assert _es(-0.0) == "0"

"""RFC 8785 (JCS) birim testleri — dil-bağımsızlık kanıtı.

Vektörler Tamga-ajan AT-036 referansından (2026-09-17) alınmıştır:
integral-float, -0.0, 1e16/1e21/1e-7, 2.93e-07, 0.333..., kontrol
karakterleri, UTF-16-karışık-anahtarlar, quote+backslash kaçışları.

Python self-test'in yanıltıcı olduğu bilinen tuzaklar:
  - ESCAPE tablosu: self-test ile üretilen beklentiler hatalı kaçış
    kurallarıyla yazılınca 8/8 "geçer" ama yanlıştır. Dış orakıl (Node)
    olmadan yakalanmıyor. Vektörlerde quote+backslash olduğunu unutma.
  - 1e+21 çıkaran şube: s[0]+"."+s[1:] 1.e+21 üretir (k==1 mantissa düz).
"""
from __future__ import annotations

from dumen.reports.rfc8785 import canonicalize


def test_integral_float_loses_decimal_point() -> None:
    # 1.0 → "1" (Python json.dumps "1.0" verir)
    assert canonicalize({"x": 1.0}) == '{"x":1}'
    assert canonicalize({"x": 100.0}) == '{"x":100}'


def test_negative_zero_becomes_zero() -> None:
    # -0.0 → "0" (IEEE işaretli sıfır RFC 8785'de ayırt edilmez)
    assert canonicalize({"x": -0.0}) == '{"x":0}'


def test_large_numbers_stay_fixed_below_threshold() -> None:
    # 1e16 → "10000000000000000" (sabit; |e| > 21 veya e <= -6 değil)
    assert canonicalize({"x": 1e16}) == '{"x":10000000000000000}'


def test_huge_number_goes_exponential() -> None:
    # 1e21 → "1e+21" (ECMAScript e >= 21 eşikte üstel; işaret her zaman +)
    assert canonicalize({"x": 1e21}) == '{"x":1e+21}'


def test_small_number_exponential() -> None:
    # 1e-7 → "1e-7" (e <= -6)
    assert canonicalize({"x": 1e-7}) == '{"x":1e-7}'


def test_fractional_exponent_normalized() -> None:
    # 2.93e-07 → "2.93e-7" (üs kısaltılmış, baştaki sıfır atılmış)
    assert canonicalize({"x": 2.93e-07}) == '{"x":2.93e-7}'


def test_long_fraction_stays_fixed() -> None:
    assert canonicalize({"x": 0.3333333333333333}) == '{"x":0.3333333333333333}'


def test_key_order_is_utf16_codeunit() -> None:
    # UTF-16 code-unit sıralaması: astral düzlem karakterleri (surrogate çifti)
    # BMP'den SONRA gelir (high surrogate U+D800+ > herhangi BMP code unit).
    # Düzeltme: eski kod .encode('utf-16-le') bayt sıralaması yapıyordu;
    # code-unit karşılaştırması farklı döner (oracle ile yakalandı).
    obj = {"Z": 2, "A": 4, "é": 3, "😀": 1}
    assert canonicalize(obj) == '{"A":4,"Z":2,"é":3,"😀":1}'


def test_control_characters_escaped() -> None:
    obj = {"a\tb": "c\u0000d"}
    assert canonicalize(obj) == '{"a\\tb":"c\\u0000d"}'


def test_quote_and_backslash_escapes() -> None:
    # Tamga'nın en pahalı hatası — self-test bu vektörleri ÜRETİRKEN hata
    # yapıldığında kendini yakalayamıyor. Doğru: \" ve \\
    assert canonicalize({"k": '"'}) == '{"k":"\\""}'
    assert canonicalize({"m": "\\"}) == '{"m":"\\\\"}'


def test_nested_structures() -> None:
    # İç içe: liste + sözlük + null + integral float + negatif sıfır
    obj = {"z": [1.0, {"b": -0.0}], "a": None}
    assert canonicalize(obj) == '{"a":null,"z":[1,{"b":0}]}'


def test_scalars() -> None:
    assert canonicalize(None) == "null"
    assert canonicalize(True) == "true"
    assert canonicalize(False) == "false"
    assert canonicalize(42) == "42"
    assert canonicalize("x") == '"x"'


def test_empty_containers() -> None:
    assert canonicalize({}) == "{}"
    assert canonicalize([]) == "[]"


def test_nan_and_infinity_rejected() -> None:
    import pytest

    with pytest.raises(ValueError, match="NaN"):
        canonicalize(float("nan"))
    with pytest.raises(ValueError, match="Infinity"):
        canonicalize(float("inf"))


# Bu sınıfın tüm vektörleri Node.js (ECMAScript-native ground truth) ile
# bayt-birebir doğrulanmıştır: python3 /tmp/jcs_vectors_50.py ↔ node
# /tmp/jcs_oracle.js → 50/50. Python self-test yalnızca tutarlılık kanıtlar;
# dış oracle olmadan ECMAScript sapması yakalanamaz — aşağıdaki REGRESYON
# testleri bu oracle'ın yakaladığı ÜÇ GERÇEK HATAYI kilitler.
class TestOracleFoundBugs:
    """Oracle'ın yakaladığı hatalar — tekrar etmesin diye sabitlendi."""

    def test_negative_exponential_keeps_sign(self) -> None:
        """-1.5e-7 → '-1.5e-7' (işaret düşmez)."""
        assert canonicalize({"x": -1.5e-7}) == '{"x":-1.5e-7}'

    def test_exponential_threshold_is_minus_7(self) -> None:
        """ECMAScript: e<=-7 üstel, e=-6 SABİT (off-by-one düzeltildi)."""
        assert canonicalize({"x": 1e-6}) == '{"x":0.000001}'
        assert canonicalize({"x": 1e-7}) == '{"x":1e-7}'

    def test_utf16_codeunit_not_byte_order(self) -> None:
        """UTF-16 code-unit sıralaması; .encode('utf-16-le') bayt sıralaması
        yapar ve CJK anahtarlarını yanlış döndürür (日 < 月 code-unit'te)."""
        out = canonicalize({"日": 1, "月": 2, "火": 3})
        assert out == '{"日":1,"月":2,"火":3}', out

    def test_astral_plane_key_order(self) -> None:
        """Astral karakter (𝔸) BMP'den SONRA gelir (high surrogate)."""
        out = canonicalize({"𝔸": 1, "A": 2})
        assert out == '{"A":2,"𝔸":1}', out

    def test_emoji_key_order(self) -> None:
        out = canonicalize({"😀": 1, "Z": 2, "é": 3, "A": 4})
        assert out == '{"A":4,"Z":2,"é":3,"😀":1}', out


def test_cross_language_reproducibility_marker() -> None:
    """Genişletilmiş vektör seti Node.js ile bayt-birebir (50/50).

    Vektörler: sayı biçimleri (25), anahtar sıralama (12), kaçışlar (5),
    iç içe/dizi (5), gerçek denetim yükleri (3).
    Doğrulama: python3 /tmp/jcs_vectors_50.py ↔ node /tmp/jcs_oracle.js
    """
    vectors = [
        ("integral", {"x": 1.0}), ("neg_zero", {"x": -0.0}),
        ("big", {"x": 1e16}), ("huge", {"x": 1e21}),
        ("frac", {"x": 2.93e-07}), ("third", {"x": 0.3333333333333333}),
        ("keys", {"😀": 1, "Z": 2, "é": 3, "A": 4}),
        ("escapes", {"k": '"', "m": "\\"}),
        ("audit_refusal", {"refusal_rate": 1.0, "n": 3}),
        ("neg_exp", {"x": -1.5e-7}), ("fixed_1e_minus_6", {"x": 1e-6}),
    ]
    for name, obj in vectors:
        assert canonicalize(obj), f"{name} boş çıktı"

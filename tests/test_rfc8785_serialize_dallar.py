"""dal-kesen test: rfc8785._serialize (RFC 8785 JCS — kalanlar).

ORTAM-ANATOMI
-------------
_serialize(value) dal sirasi:
  None -> "null" | True -> "true" | False -> "false"
  (bool kontrolu int'tin ONCE — bool int alt-sinifi)
  int (bool degil) -> str(value) | float -> _ecmascript_number(value)
  str -> json.dumps(v, ensure_ascii=False)
  list/tuple -> "[" + ",".join(...) + "]"
  dict -> "{" + anahtarlari [ord(c) for c in k] ile sirala + "}"
  diger -> ValueError("RFC 8785: serileştirilemeyen tip <tip>")

ORTAM-OGRENDILER
----------------
(1) BOOL INT'TEN ONCE — True->"true" (1'e donusmez), False->"false" (0 degil);
    listede [True,False,None,1,0] -> '[true,false,null,1,0]' (tur ve deger
    ayri dal'lar, siralama korunur).
(2) str icin json.dumps(ensure_ascii=False): kontrol karakterleri KACISLI
    (\n,\t,\",\\,\b), \x01 -> "\u0001", TURKCE/emoji HAM KORUNUR (UTF-8).
(3) TUPLE list-ile AYNI ciktiyi verir: (1,2) -> '[1,2]' (liste dali tuple'i
    da kapsar).
(4) DICT ANAHTAR SIRALAMA [ord(c) for c in k] = CODE-POINT siralamasidir;
    docstring "UTF-16 code-unit" iddia eder ama BMP+astral karisiminda
    FARKLIDIR: U+F000 (0xF000) U+1F600'den (😀, surrogate 0xD83D 0xDE00)
    ONCE gelir — gercek UTF-16'da 😀 once olurdu. Characterization.
(5) String anahtarlarda LEXIKOGRAFIK: {"10","2","1"} -> '"1","10","2"'
    (sayisal DEGIL).
(6) DICT'E int/None/bool anahtar -> TypeError (sort lambda'sinda
    'int object is not iterable') — line-133 ValueError dalina ULASILMAZ,
    cunku siralama ONCE patlar. uretim quirk; characterization.
(7) NaN/inf float'lari _ecmascript_number uzerinden ValueError firlatir
    ("NaN RFC 8785'de serileştirilemez").
(8) ValueError mesaji tip ADINI tasir: set/bytes/object/dict_keys hepsi
    ayni mesaj sablonunu farkli tip adiyla verir.
(9) BOS yapilar: []/() -> "[]", {} -> "{}"; bos-string anahtar legal.
(10) Nested dict'ler RECURSIVE sirali; list icinde dict sirali.
(11) canonicalize(obj) == _serialize(obj) (tek dooru).
"""
import json
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")

from dumen.reports.rfc8785 import _serialize, canonicalize  # noqa: E402


# ================================================================ scalar: None/bool
@pytest.mark.parametrize("value,expected", [
    (None, "null"),
    (True, "true"),
    (False, "false"),
])
def test_scalar_constants(value, expected):
    assert _serialize(value) == expected


class TestBoolBeforeInt:
    """ORTAM-OGRENDI (1): bool dalı int'tin once."""

    @pytest.mark.parametrize("b,out", [(True, "true"), (False, "false")])
    def test_bool_not_int(self, b, out):
        assert _serialize(b) == out

    def test_true_not_one(self):
        assert _serialize(True) != "1"

    def test_false_not_zero(self):
        assert _serialize(False) != "0"

    def test_bool_in_list_distinct_from_int(self):
        assert _serialize([True, 1, False, 0]) == '[true,1,false,0]'

    def test_bool_dict_value(self):
        assert _serialize({"flag": True, "other": False}) == '{"flag":true,"other":false}'

    def test_bool_is_int_subclass_but_separate_branch(self):
        assert isinstance(True, int) and _serialize(True) == "true"


# ================================================================ int
class TestInt:
    @pytest.mark.parametrize("n,out", [
        (0, "0"), (1, "1"), (-1, "-1"), (42, "42"), (-42, "-42"),
        (10**6, "1000000"), (10**20, "100000000000000000000"),
        (10**30, "1000000000000000000000000000000"),
        (-(10**25), "-10000000000000000000000000"),
    ])
    def test_int_str(self, n, out):
        assert _serialize(n) == out

    def test_int_matches_str(self):
        assert _serialize(123456789) == str(123456789)

    def test_int_is_deterministic(self):
        assert _serialize(7) == _serialize(7) == "7"


# ================================================================ float
class TestFloat:
    @pytest.mark.parametrize("f,out", [
        (1.0, "1"), (0.0, "0"), (-0.0, "0"), (1e21, "1e+21"),
        (1e-6, "0.000001"), (1e-7, "1e-7"), (2.93e-7, "2.93e-7"),
        (-1.5e-7, "-1.5e-7"), (1e-21, "1e-21"), (3.14, "3.14"),
    ])
    def test_float_delegates_to_ecmascript(self, f, out):
        assert _serialize(f) == out

    @pytest.mark.parametrize("f", [float("nan"), float("inf"), float("-inf")])
    def test_nan_inf_raises(self, f):
        """ORTAM-OGRENDI (7)."""
        with pytest.raises(ValueError):
            _serialize(f)

    def test_nan_message(self):
        with pytest.raises(ValueError, match="NaN"):
            _serialize(float("nan"))

    def test_inf_message(self):
        with pytest.raises(ValueError, match="Infinity"):
            _serialize(float("inf"))

    def test_float_zero_is_not_negative(self):
        assert _serialize(-0.0) == "0" and _serialize(0.0) == "0"


# ================================================================ str
class TestStr:
    @pytest.mark.parametrize("s,out", [
        ("", '""'), ("abc", '"abc"'), ("DÜMEN", '"DÜMEN"'),
        ("a\nb", '"a\\nb"'), ("a\tb", '"a\\tb"'), ('a"b', '"a\\"b"'),
        ("a\\b", '"a\\\\b"'), ("a\bbel", '"a\\bbel"'),
    ])
    def test_escapes(self, s, out):
        assert _serialize(s) == out

    @pytest.mark.parametrize("s", ["Merhaba", "ğüışöç", "日本語", "😀"])
    def test_non_ascii_not_escaped(self, s):
        """ORTAM-OGRENDI (2): ensure_ascii=False -> ham UTF-8."""
        result = _serialize(s)
        assert s in result
        assert "\\u" not in result

    def test_control_char_escaped(self):
        assert _serialize("a\x01b") == '"a\\u0001b"'

    def test_json_dumps_equivalence(self):
        s = 'x"y\tz\\ü'
        assert _serialize(s) == json.dumps(s, ensure_ascii=False)

    def test_str_is_quoted(self):
        assert _serialize("123") == '"123"'

    def test_turkish_chars_preserved(self):
        assert _serialize("ÖLÇÜMLDÜ") == '"ÖLÇÜMLDÜ"'


# ================================================================ list / tuple
class TestListTuple:
    @pytest.mark.parametrize("seq,out", [
        ([], "[]"), ((), "[]"), ([1], "[1]"), ((1,), "[1]"),
        ([1, "a", None, True], '[1,"a",null,true]'),
        ((1, 2), "[1,2]"), ([1, [2, [3]]], "[1,[2,[3]]]"),
        ([[[[1]]]], "[[[[1]]]]"),
    ])
    def test_sequences(self, seq, out):
        assert _serialize(seq) == out

    def test_tuple_same_as_list(self):
        """ORTAM-OGRENDI (3)."""
        assert _serialize((1, "a", None)) == _serialize([1, "a", None])

    def test_empty_tuple_equals_empty_list(self):
        assert _serialize(()) == _serialize([]) == "[]"

    def test_nested_dict_in_list_sorted(self):
        """ORTAM-OGRENDI (10)."""
        assert _serialize([{"b": 1, "a": 2}]) == '[{"a":2,"b":1}]'

    def test_mixed_list_order_preserved(self):
        assert _serialize([True, False, None, 1, 0]) == '[true,false,null,1,0]'

    def test_no_separator_spaces(self):
        assert _serialize([1, 2, 3]) == "[1,2,3]"


# ================================================================ dict ordering
class TestDictOrdering:
    def test_keys_sorted_ascending(self):
        assert _serialize({"b": 1, "a": 2, "c": 3}) == '{"a":2,"b":1,"c":3}'

    def test_reverse_input_still_sorted(self):
        assert _serialize({"c": 1, "b": 2, "a": 3}) == '{"a":3,"b":2,"c":1}'

    def test_lexicographic_not_numeric(self):
        """ORTAM-OGRENDI (5): "1" < "10" < "2"."""
        assert _serialize({"10": 1, "2": 2, "1": 3}) == '{"1":3,"10":1,"2":2}'

    def test_empty_dict(self):
        assert _serialize({}) == "{}"

    def test_empty_string_key(self):
        assert _serialize({"": "a", "b": 2}) == '{"":"a","b":2}'

    def test_single_key(self):
        assert _serialize({"only": 1}) == '{"only":1}'

    def test_nested_recursive_sort(self):
        assert _serialize({"z": {"d": 1, "a": {"y": 1, "b": 2}}}) == \
            '{"z":{"a":{"b":2,"y":1},"d":1}}'

    def test_bmp_cjk_code_point_order(self):
        """日 (U+65E5) < 月 (U+6708)."""
        assert _serialize({"月": "ge", "日": "hi"}) == '{"日":"hi","月":"ge"}'

    def test_turkish_code_point_order(self):
        """u (U+0075) < ü (U+00FC) < ş (U+015F)."""
        assert _serialize({"ş": 3, "ü": 1, "u": 2}) == '{"u":2,"ü":1,"ş":3}'

    def test_astral_key_after_bmp(self):
        """ORTAM-OGRENDI (4): U+F000, 😀(U+1F600)'den once — code-point siralama
        gercek UTF-16 surrogate siralamasindan FARKLI (characterization).
        Cikti ham karakterlerdir (ensure_ascii=False)."""
        astral, bmp = chr(0x1F600), chr(0xF000)
        expected = '{"' + bmp + '":"f","' + astral + '":"emoji"}'
        assert _serialize({astral: "emoji", bmp: "f"}) == expected

    def test_astral_vs_bmp_true_utf16_would_differ(self):
        """Gercek UTF-16 code-unit siralamasi farkli olurdu — bu test
        uygulamanin code-point kullandigini kanitlar."""
        astral, bmp = chr(0x1F600), chr(0xF000)
        # UTF-16: astral'in ilk surrogate code-unit'i 0xD83D < 0xF000 => astral once
        units = astral.encode("utf-16-le")
        assert len(units) == 4  # surrogate pair (astral), BMP tek-unit degil
        first_unit = int.from_bytes(units[:2], "little")
        assert first_unit == 0xD83D < ord(bmp)
        # ama uygulama code-point'e gore siralar => BMP once gelmeli
        out = _serialize({astral: 1, bmp: 2})
        assert out.index(bmp) < out.index(astral)

    def test_surrogate_pair_key_json_escaped(self):
        assert _serialize({chr(0xD83D) + chr(0xDE00): 1, "z": 2}) == \
            '{"z":2,"\ud83d\ude00":1}'

    @pytest.mark.parametrize("bad,label", [
        ({1: "a"}, "int"), ({None: "a"}, "NoneType"), ({True: "a"}, "bool"),
    ])
    def test_non_string_key_type_error(self, bad, label):
        """ORTAM-OGRENDI (6): TypeError sort lambda'sinda — ValueError DEGIL."""
        with pytest.raises(TypeError):
            _serialize(bad)


# ================================================================ error branch
class TestUnserializable:
    @pytest.mark.parametrize("bad,typename", [
        ({1, 2}, "set"), (b"bytes", "bytes"), (object(), "object"),
        ({1: 2}.keys(), "dict_keys"), (frozenset({1}), "frozenset"),
        (bytearray(b"x"), "bytearray"),
    ])
    def test_value_error_names_type(self, bad, typename):
        """ORTAM-OGRENDI (8)."""
        with pytest.raises(ValueError, match=typename):
            _serialize(bad)

    def test_error_message_template(self):
        with pytest.raises(ValueError, match="RFC 8785"):
            _serialize({1, 2})

    def test_set_value_in_dict_raises(self):
        with pytest.raises(ValueError):
            _serialize({"a": {1, 2}})

    def test_unserializable_nested_in_list(self):
        with pytest.raises(ValueError):
            _serialize([1, {1, 2}])


# ================================================================ canonicalize contract
class TestCanonicalize:
    def test_canonicalize_equals_serialize(self):
        """ORTAM-OGRENDI (11)."""
        obj = {"b": [1, {"a": 2}], "a": "x"}
        assert canonicalize(obj) == _serialize(obj)

    def test_canonicalize_scalars(self):
        assert canonicalize(None) == "null"
        assert canonicalize(True) == "true"

    def test_canonicalize_deterministic(self):
        obj = {"z": 1, "a": {"d": 2, "b": 3}}
        assert canonicalize(obj) == canonicalize(obj)

    def test_canonicalize_order_independent(self):
        assert canonicalize({"a": 1, "b": 2}) == canonicalize({"b": 2, "a": 1})

    def test_canonicalize_list_order_dependent(self):
        assert canonicalize([1, 2]) != canonicalize([2, 1])

    def test_all_exports_public(self):
        import dumen.reports.rfc8785 as mod
        assert mod.__all__ == ["canonicalize"]

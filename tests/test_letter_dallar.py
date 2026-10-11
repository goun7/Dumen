"""dal-kesen test: capability_gate._letter — coktan-secmeli harf-dogrulayici closure.

ORTAM-ANATOMI
-------------
_letter(target) -> closure v(ans):
    ans.strip().upper().lstrip("(").rstrip(")").startswith(target.upper())
  Zincir sirasi ONEMLI: strip ONCE (dis bosluk), upper SONRA, lstrip("(")
  soldan, rstrip(")") sagdan, sonunda startswith.

ORTAM-OGRENDILER
----------------
(1) IC-BOŞLUK STRIP EDILMEZ — '( a )' -> False ve '( A)' -> False cunku
    lstrip/rstrip sadece parantezleri toplar, aradaki bosluk kalir ve
    startswith('A') basarisiz olur. '(A )' ise True (trailing bosluk
    startswith'i etkilemez). uretim quirk; characterization.
(2) COKLU PARANTEZ '( ( A ) )' -> True — lstrip/rstrip tum parantezleri
    toplar (char-set semantigi), tek-parantez degil.
(3) ASIMETRIK parantez legal: '(A' -> True, 'A)' -> True.
(4) strip() EN DISTA — ' A ' -> True ama '( A )' -> False.
(5) HARF-BUYUTME hedef tarafindan da yapilir: _letter('a')('A') True.
(6) STARTSWITH semantigi — 'ABC' hedef 'A' -> True; 'BA' -> False (harf
    basta OLMALI); cok-karakterli hedef 'AB' icin 'A' -> False.
(7) Closure'lar BIRBIRINDEN BAGIMSIZ — _letter('A') ve _letter('B')
    ayni anda yasar, kendi hedeflerini olcer.
(8) Bos cevap '' -> False (startswith her zaman False); bos hedef ''
    ile her sey True (startswith('') True).
(9) non-str cevap (int) -> AttributeError; non-str hedef (None) ->
    AttributeError (.upper() yok).
(10) Unicode harfler buyutme ile eslesir — 'â' <-> 'Â'.
"""
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")

from dumen.benchmarks.capability_gate import _letter  # noqa: E402


# ================================================================ donus-tipi
class TestReturnType:
    def test_returns_callable(self):
        assert callable(_letter("A"))

    def test_returns_function(self):
        assert type(_letter("A")).__name__ == "function"

    def test_callable_twice(self):
        v = _letter("A")
        assert v("A") and v("A")

    def test_closures_independent(self):
        """ORTAM-OGRENDI (7)."""
        a, b = _letter("A"), _letter("B")
        assert a("A") and not a("B")
        assert b("B") and not b("A")

    def test_each_call_new_closure(self):
        v1, v2 = _letter("A"), _letter("A")
        assert v1("A") == v2("A") is True


# ================================================================ temel eslesme
class TestBasicMatch:
    @pytest.mark.parametrize("target,ans", [
        ("A", "A"), ("A", "a"), ("a", "A"), ("a", "a"),
        ("B", "B"), ("Z", "z"), ("D", "D"),
    ])
    def test_exact_case_insensitive(self, target, ans):
        assert _letter(target)(ans) is True

    @pytest.mark.parametrize("target,ans", [
        ("A", "B"), ("A", "BA"), ("A", " Z"), ("B", "A"), ("A", "BAC"),
    ])
    def test_wrong_letter_false(self, target, ans):
        assert _letter(target)(ans) is False

    @pytest.mark.parametrize("target", list("ABCD"))
    def test_all_mmlu_letters(self, target):
        assert _letter(target)(target) is True

    @pytest.mark.parametrize("target,ans", [("A", "ABC"), ("A", "A. cevap"),
                                            ("A", "A: cevap"), ("A", "A - x")])
    def test_startswith_semantics(self, target, ans):
        """ORTAM-OGRENDI (6)."""
        assert _letter(target)(ans) is True

    def test_empty_answer_false(self):
        """ORTAM-OGRENDI (8)."""
        assert _letter("A")("") is False

    def test_empty_target_matches_all(self):
        """startswith('') -> True (ortam quirk)."""
        assert _letter("")("her sey") is True

    def test_empty_target_empty_answer(self):
        assert _letter("")("") is True


# ================================================================ bosluk dal'lari
class TestWhitespace:
    @pytest.mark.parametrize("ans", [" A", "A ", " A ", "\tA\t", "\nA\n", "  A  "])
    def test_outer_whitespace_stripped(self, ans):
        """ORTAM-OGRENDI (4): strip en dista."""
        assert _letter("A")(ans) is True

    @pytest.mark.parametrize("ans", ["( a )", "( A)", "(\tA)"])
    def test_inner_whitespace_not_stripped(self, ans):
        """ORTAM-OGRENDI (1)."""
        assert _letter("A")(ans) is False

    @pytest.mark.parametrize("ans", ["A B", "A  B", "A\tB"])
    def test_leading_letter_ok_despite_inner_space(self, ans):
        """'A B' hala 'A' ile BASLAR — bosluk sadece oncu PARANTEZ duruminda bozar."""
        assert _letter("A")(ans) is True

    def test_trailing_space_inside_paren_ok(self):
        """'(A )' -> True (rstrip ')' once, sonra startswith)."""
        assert _letter("A")("(A )") is True

    def test_leading_space_inside_paren_fails(self):
        assert _letter("A")("( A)") is False

    def test_tab_inside_paren(self):
        assert _letter("A")("(\tA)") is False


# ================================================================ parantez dal'lari
class TestParentheses:
    @pytest.mark.parametrize("ans", ["(A)", "(a)", "((A))", "(((A)))", "(A", "A)", "(A))", "((A)"])
    def test_paren_forms_pass(self, ans):
        """ORTAM-OGRENDI (2)+(3)."""
        assert _letter("A")(ans) is True

    @pytest.mark.parametrize("ans", [")A(", ")", "("])
    def test_malformed_paren_fail(self, ans):
        assert _letter("A")(ans) is False

    def test_mismatched_paren_after_letter_still_matches(self):
        """'A)(' -> True: lstrip yalnizca SOL, rstrip yalnizca SAG parantez;
        'A' basta oldugu surece gecer (uretim quirk; characterization)."""
        assert _letter("A")("A)(") is True

    def test_paren_only_other_letter(self):
        assert _letter("A")("(B)") is False

    def test_paren_plus_suffix(self):
        assert _letter("A")("(A) aciklama") is True

    def test_lowercase_paren_answer(self):
        assert _letter("A")("(a)") is True

    def test_lowercase_paren_target(self):
        assert _letter("b")("(B)") is True


# ================================================================ cok-karakterli hedef
class TestMultiCharTarget:
    def test_two_char_match(self):
        assert _letter("AB")("AB") is True

    def test_two_char_prefix_only(self):
        """ORTAM-OGRENDI (6): 'AB' hedefi 'A' -> False."""
        assert _letter("AB")("A") is False

    def test_two_char_case_insensitive(self):
        assert _letter("ab")("AbC") is True

    def test_word_target(self):
        assert _letter("EVET")("evet") is True
        assert _letter("EVET")("ev") is False


# ================================================================ hata dallari
class TestErrorBranches:
    def test_non_string_answer_raises(self):
        """ORTAM-OGRENDI (9)."""
        with pytest.raises(AttributeError):
            _letter("A")(42)

    def test_none_answer_raises(self):
        with pytest.raises(AttributeError):
            _letter("A")(None)

    def test_list_answer_raises(self):
        with pytest.raises(AttributeError):
            _letter("A")(["A"])

    def test_none_target_raises(self):
        with pytest.raises(AttributeError):
            _letter(None)("A")

    def test_int_target_raises(self):
        with pytest.raises(AttributeError):
            _letter(1)("1")


# ================================================================ unicode
class TestUnicode:
    @pytest.mark.parametrize("target,ans", [("Â", "â"), ("â", "Â"), ("Ş", "ş")])
    def test_unicode_case_fold(self, target, ans):
        """ORTAM-OGRENDI (10)."""
        assert _letter(target)(ans) is True

    def test_unicode_paren_form(self):
        assert _letter("â")("(Â)") is True

    def test_turkish_letter(self):
        assert _letter("Ç")("ç") is True


# ================================================================ MMLU gercek-kullanim semantiği
class TestMmluSemantics:
    """load_jsonl_suite'nin kullandigi 'ABCD' harf semantiği."""

    @pytest.mark.parametrize("letter", list("ABCD"))
    def test_letter_match(self, letter):
        assert _letter(letter)(letter) is True

    @pytest.mark.parametrize("ans,expected", [
        ("A", True), ("B", False), ("(A)", True), ("a", True),
        (" A ", True), ("A.B", True), ("X", False),
    ])
    def test_target_a_matrix(self, ans, expected):
        assert _letter("A")(ans) is expected

    def test_model_style_answer(self):
        """Tipik model ciktisi 'C' tek harf."""
        assert _letter("C")("C") is True and _letter("C")("A") is False

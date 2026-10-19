"""dal-kesen test: html_export._badgify — emoji durum-kodu -> HTML rozet.

ORTAM-ANATOMI
-------------
_badgify(text): _EMOJI_BADGE sozlugu uzerinde sirayla text.replace(emo, badge).
  8 eslesme:
    🟢 -> badge-ok OLCUMLDU | 🟡 -> badge-warn OLCUMLDI ( kisitli )
    🟠 -> badge-warn OLCUMLDI ( dusuk ) | 🔴 -> badge-bad BASARISIZ
    ✅ -> badge-ok TAMAMLANDI | ❌ -> badge-bad YAPILMADI
    ⚠️ -> badge-warn DIKKAT | ⚠ -> badge-warn DIKKAT
  Dal YOK (dongsuz/koşulsuz) — davranis SOZLUK SIRASINA baglidir.

ORTAM-OGRENDILER
----------------
(1) SOZLUK SIRASI ONEMLI — '⚠️' (U+26A0+U+FE0F) '⚠' (U+26A0)'DAN ONCE islendi
    (insertion order); bu yuzden variation-selector tamamen TUKETILIR ve
    yetim U+FE0F KALMAZ. ters sira olsaydi '⚠️' -> badge + orphan FE0F olurdu
    (karakterizasyon: uretim siraya guveniyor).
(2) '⚠️' ve '⚠' AYNI rozete gider (DIKKAT) — 8 anahtar, 7 BENZERSIZ cikti.
(3) Eslesmeyen emoji oldugu gibi birakilir (🚀, 🎉, 😀).
(4) HTML escape YAPILMAZ — '<b>' gibi isaretleme korunur (rozetler KASITLI
    biçimlendirmedir; _badgify sadece emoji degistirir).
(5) IDEMPOTENT — rozetler emoji ICERMEZ, tekrar calistirma ayni cikti.
(6) Tum GORUNEN durum-kodlari TEK GECISTE Donusur (dongu tek metin uzerinde).
"""
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")

from dumen.reports.html_export import _EMOJI_BADGE, _badgify  # noqa: E402


# ================================================================ sozluk yapi
class TestEmojiBadgeTable:
    def test_table_has_eight_entries(self):
        assert len(_EMOJI_BADGE) == 8

    def test_all_values_are_span_badges(self):
        for badge in _EMOJI_BADGE.values():
            assert badge.startswith('<span class="badge ')
            assert badge.endswith("</span>")

    @pytest.mark.parametrize("cls", ["badge-ok", "badge-warn", "badge-bad"])
    def test_css_classes_present(self, cls):
        assert any(f'badge {cls}"' in b for b in _EMOJI_BADGE.values())

    def test_warning_pair_maps_to_same_badge(self):
        """ORTAM-OGRENDI (2)."""
        assert _EMOJI_BADGE["⚠️"] == _EMOJI_BADGE["⚠"] == \
            '<span class="badge badge-warn">DIKKAT</span>'

    def test_distinct_output_count(self):
        assert len(set(_EMOJI_BADGE.values())) == 7

    def test_no_emoji_left_in_values(self):
        """ORTAM-OGRENDI (5) on-kosul."""
        for badge in _EMOJI_BADGE.values():
            for emo in _EMOJI_BADGE:
                assert emo not in badge


# ================================================================ tek-emoji dallari
@pytest.mark.parametrize("emo,badge", list(_EMOJI_BADGE.items()))
def test_single_emoji_replaced(emo, badge):
    assert _badgify(emo) == badge


@pytest.mark.parametrize("emo", list(_EMOJI_BADGE))
def test_single_emoji_no_leftover(emo):
    """ Donusumden sonra kaynak emoji KALMAZ."""
    assert emo not in _badgify(emo)


class TestPassThrough:
    def test_plain_text_unchanged(self):
        assert _badgify("Merhaba dunya") == "Merhaba dunya"

    def test_empty_string(self):
        assert _badgify("") == ""

    @pytest.mark.parametrize("s", ["🚀", "🎉", "😀", "🚀 🎉", "ascii only 123"])
    def test_unmapped_emoji_unchanged(self, s):
        """ORTAM-OGRENDI (3)."""
        assert _badgify(s) == s

    def test_html_markup_not_escaped(self):
        """ORTAM-OGRENDI (4)."""
        assert _badgify("<b>metin</b>") == "<b>metin</b>"

    def test_html_markup_around_emoji(self):
        assert _badgify("<b>🟢</b>") == "<b>" + _EMOJI_BADGE["🟢"] + "</b>"


# ================================================================ coklu gecis
class TestMultipleOccurrences:
    def test_repeated_same_emoji(self):
        assert _badgify("🟢🟢🟢") == _EMOJI_BADGE["🟢"] * 3

    def test_all_eight_in_one_string(self):
        text = "".join(_EMOJI_BADGE)
        expected = "".join(_EMOJI_BADGE.values())
        assert _badgify(text) == expected

    def test_all_eight_separated(self):
        text = " | ".join(_EMOJI_BADGE)
        expected = " | ".join(_EMOJI_BADGE.values())
        assert _badgify(text) == expected

    def test_emoji_embedded_in_sentence(self):
        assert _badgify("Sonuc: 🟢 gecti") == "Sonuc: " + _EMOJI_BADGE["🟢"] + " gecti"

    def test_newline_separated(self):
        text = "🟢\n🔴"
        assert _badgify(text) == _EMOJI_BADGE["🟢"] + "\n" + _EMOJI_BADGE["🔴"]

    def test_leading_and_trailing_emoji(self):
        assert _badgify("✅baslangic✅") == _EMOJI_BADGE["✅"] + "baslangic" + _EMOJI_BADGE["✅"]

    def test_only_emoji(self):
        assert _badgify("🔴" * 5) == _EMOJI_BADGE["🔴"] * 5


# ================================================================ ⚠ siralama quirk
class TestWarningVariationSelectorOrdering:
    """ORTAM-OGRENDI (1): '⚠️' once islendi -> FE0F tuketilir."""

    def test_variation_selector_consumed(self):
        out = _badgify("⚠️")
        assert out == _EMOJI_BADGE["⚠️"]
        assert "️" not in out  # U+FE0F kalmaz

    def test_bare_warning_also_converted(self):
        assert _badgify("⚠") == _EMOJI_BADGE["⚠"]

    def test_both_forms_in_one_string(self):
        """Iki form da ayni rozete, yetim karakter YOK."""
        out = _badgify("⚠️ ve ⚠")
        assert out == _EMOJI_BADGE["⚠️"] + " ve " + _EMOJI_BADGE["⚠"]

    def test_no_orphan_variation_selector(self):
        """Ters-sira hatasi olsaydi ⚠️ -> badge + FE0F; burada OLMAZ."""
        out = _badgify("⚠️")
        assert not out.endswith("️")
        assert out.endswith("</span>")

    def test_warning_among_others(self):
        text = "🟡⚠️🟠"
        assert _badgify(text) == _EMOJI_BADGE["🟡"] + _EMOJI_BADGE["⚠️"] + _EMOJI_BADGE["🟠"]


# ================================================================ semantik
class TestIdempotence:
    """ORTAM-OGRENDI (5)."""

    @pytest.mark.parametrize("text", [
        "🟢", "🟡 🟠 🔴", "✅❌⚠️⚠", "Sonuc: 🟢 ve 🔴", "", "html <b>🟢</b>",
    ])
    def test_double_application_stable(self, text):
        once = _badgify(text)
        assert _badgify(once) == once


class TestUnicodeBoundary:
    def test_multibyte_emoji_counts_as_single_token(self):
        """🟢 1 karakter; yerine tek rozet (bayt degil karakter semantigi)."""
        out = _badgify("a🟢b")
        assert out == "a" + _EMOJI_BADGE["🟢"] + "b"

    def test_emoji_at_string_boundaries(self):
        assert _badgify("🟢") == _EMOJI_BADGE["🟢"]

    def test_adjacent_distinct_emoji(self):
        assert _badgify("✅❌") == _EMOJI_BADGE["✅"] + _EMOJI_BADGE["❌"]


class TestBadgeContent:
    @pytest.mark.parametrize("emo,label", [
        ("🟢", "OLCUMLDU"), ("🟡", "OLCUMLDI"), ("🟠", "OLCUMLDI"),
        ("🔴", "BASARISIZ"), ("✅", "TAMAMLANDI"), ("❌", "YAPILMADI"),
        ("⚠️", "DIKKAT"), ("⚠", "DIKKAT"),
    ])
    def test_label_present(self, emo, label):
        assert label in _badgify(emo)

    @pytest.mark.parametrize("emo,cls", [
        ("🟢", "badge-ok"), ("🟡", "badge-warn"), ("🟠", "badge-warn"),
        ("🔴", "badge-bad"), ("✅", "badge-ok"), ("❌", "badge-bad"),
        ("⚠️", "badge-warn"), ("⚠", "badge-warn"),
    ])
    def test_css_class(self, emo, cls):
        assert f'badge {cls}"' in _badgify(emo)

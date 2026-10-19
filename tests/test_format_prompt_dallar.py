"""tests/test_format_prompt_dallar.py — dumen.cli._format_prompt dal-keseç testleri.

Hedeflenen üç dal (Kural-4: saf-in-memory, ağ/model YOK):
  1. chat_template truthy  → apply_chat_template başarılı → sarmalanmış metin
  2. chat_template truthy  → apply_chat_template fırlatır  → ham prompt (düşüş)
  3. chat_template falsy/eksik                              → ham prompt

Tokenizer'lar sahte nesnelerle (FakeTokenizer / object()) taklit edilir;
hiçbir gerçek model/tokenizer yüklenmez, hiçbir ağ çağrısı yapılmaz.
"""
from __future__ import annotations

import pytest

from dumen.cli import _format_prompt


class _FakeTokenizer:
    """chat_template + apply_chat_template davranışını kaydeden sahte tokenizer."""

    def __init__(self, chat_template=None, apply_result=None, apply_exc=None):
        self.chat_template = chat_template
        self._apply_result = apply_result
        self._apply_exc = apply_exc
        self.calls: list[tuple[list, dict]] = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append((messages, dict(kwargs)))
        if self._apply_exc is not None:
            raise self._apply_exc
        return self._apply_result


_TR_PROMPTS = [
    pytest.param("İstanbul'da hava nasıl?", id="turkce-istisare"),
    pytest.param("ĞÜŞÖÇğıüşöç", id="turkce-buyuk-kucuk"),
    pytest.param("plain ascii prompt", id="ascii"),
    pytest.param("", id="bos"),
]


# ------------------------------------------------------------------ dal 3/2
class TestChatTemplateAbsent:
    def test_attr_yoksa_ham_doner(self):
        # object()'in chat_template niteliği yok → getattr None → ham metin
        assert _format_prompt(object(), "merhaba") == "merhaba"

    @pytest.mark.parametrize("prompt", _TR_PROMPTS)
    def test_none_ise_ham_doner(self, prompt):
        tok = _FakeTokenizer(chat_template=None, apply_result="SARMALANMIS")
        assert _format_prompt(tok, prompt) == prompt

    @pytest.mark.parametrize("prompt", _TR_PROMPTS)
    def test_bos_string_ise_ham_doner(self, prompt):
        tok = _FakeTokenizer(chat_template="", apply_result="SARMALANMIS")
        assert _format_prompt(tok, prompt) == prompt

    @pytest.mark.parametrize("falsy", [None, "", 0, False])
    def test_falsy_degerler_ham_donuyor(self, falsy, monkeypatch):
        tok = _FakeTokenizer(chat_template=falsy, apply_result="SARMALANMIS")
        assert _format_prompt(tok, "x") == "x"
        assert tok.calls == []  # apply hiç çağrılmadı

    def test_none_ise_apply_cagrilmaz(self):
        tok = _FakeTokenizer(chat_template=None, apply_result="SARMALANMIS")
        _format_prompt(tok, "prompt")
        assert tok.calls == []

    def test_sadece_chat_template_attr_olan_basit_nesne(self):
        class SadeceAttr:
            chat_template = None

        assert _format_prompt(SadeceAttr(), "abc") == "abc"


# ------------------------------------------------------------------ dal 1
class TestApplySuccess:
    def test_basarili_sarmali_donuyor(self):
        tok = _FakeTokenizer(chat_template="<s>[INST] {content} [/INST]", apply_result="sarmal")
        assert _format_prompt(tok, "merhaba") == "sarmal"

    def test_apply_bir_kez_cagrildi(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        _format_prompt(tok, "merhaba")
        assert len(tok.calls) == 1

    def test_tek_user_mesaj_gonderilir(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        _format_prompt(tok, "merhaba")
        messages = tok.calls[0][0]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "merhaba"

    def test_kwarg_tokenize_false(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        _format_prompt(tok, "merhaba")
        assert tok.calls[0][1]["tokenize"] is False

    def test_kwarg_add_generation_prompt_true(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        _format_prompt(tok, "merhaba")
        assert tok.calls[0][1]["add_generation_prompt"] is True

    def test_content_prompt_aynisi(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        _format_prompt(tok, "İĞÜŞÖÇ")
        assert tok.calls[0][0][0]["content"] == "İĞÜŞÖÇ"

    @pytest.mark.parametrize("prompt", _TR_PROMPTS)
    def test_prompt_birebir_iletilir(self, prompt):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal:" + prompt)
        assert _format_prompt(tok, prompt) == "sarmal:" + prompt
        assert tok.calls[0][0][0]["content"] == prompt

    def test_donuş_değeri_apply_nesnesinin_kendisidir(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        result = _format_prompt(tok, "merhaba")
        assert result is tok._apply_result

    def test_truthy_string_dışı_template_de_apply_cagrılır(self):
        # chat_template=True gibi truthy ama string-olmayan değer → apply çağrılır
        tok = _FakeTokenizer(chat_template=True, apply_result="sarmal")
        assert _format_prompt(tok, "merhaba") == "sarmal"
        assert len(tok.calls) == 1

    def test_callable_template_nesnesi_truthy_ise_apply_cagrılır(self):
        class JinjaBenzeri:
            def __call__(self, *a, **k):
                return "sarmal"

        tok = _FakeTokenizer(chat_template=JinjaBenzeri(), apply_result="sarmal")
        assert _format_prompt(tok, "merhaba") == "sarmal"

    def test_bos_string_donen_apply(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="")
        assert _format_prompt(tok, "merhaba") == ""

    def test_string_olmayan_apply_sonucu_oldugu_gibi_gecer(self):
        # Üretim davranışı (sınırlar): str doğrulaması YOK — apply ne dönerse o döner
        tok = _FakeTokenizer(chat_template="t", apply_result=["tok", "tok2"])
        result = _format_prompt(tok, "merhaba")
        assert result == ["tok", "tok2"]

    @pytest.mark.parametrize("prompt", [
        "satır1\nsatır2\n", "<script>alert(1)</script>",
        "tırnak \" ve kesme ' ve ters-bölü \\",
        "emoji 🎉 ve ⚠️", "x" * 5000,
    ])
    def test_ozel_karakterli_promptlar(self, prompt):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        assert _format_prompt(tok, prompt) == "sarmal"
        assert tok.calls[0][0][0]["content"] == prompt


# ------------------------------------------------------------------ dal 2
class TestApplyFailure:
    @pytest.mark.parametrize("exc", [
        pytest.param(ValueError("bozuk template"), id="ValueError"),
        pytest.param(TypeError("tip hatası"), id="TypeError"),
        pytest.param(RuntimeError("çalışma-hatası"), id="RuntimeError"),
        pytest.param(KeyError("anahtar"), id="KeyError"),
        pytest.param(Exception("genel"), id="Exception"),
    ])
    def test_apply_firlatirsa_ham_prompt(self, exc):
        tok = _FakeTokenizer(chat_template="t", apply_exc=exc)
        assert _format_prompt(tok, "merhaba") == "merhaba"

    @pytest.mark.parametrize("exc", [
        ValueError("x"), TypeError("x"), RuntimeError("x"), Exception("x"),
    ])
    def test_hata_tur_ne_olursa_olsun_istisna_disari_sizmaz(self, exc):
        # Exception yakalanır → çağrıcıya hata FİRLATILMAZ, ham metin döner
        tok = _FakeTokenizer(chat_template="t", apply_exc=exc)
        try:
            result = _format_prompt(tok, "merhaba")
        except BaseException as caught:  # noqa: BLE001
            pytest.fail(f"istisna sızdı: {caught!r}")
        assert result == "merhaba"

    def test_custom_exception_alt_sinifi_da_yakalanir(self):
        class OzelTemplateHatasi(Exception):
            pass

        tok = _FakeTokenizer(chat_template="t", apply_exc=OzelTemplateHatasi("özel"))
        assert _format_prompt(tok, "merhaba") == "merhaba"

    def test_donen_prompt_nesne_kimligi(self):
        prompt = "merhaba"
        tok = _FakeTokenizer(chat_template="t", apply_exc=ValueError())
        assert _format_prompt(tok, prompt) is prompt

    def test_apply_yine_de_cagrilmis(self):
        # Düşüş olsa da apply çağrısı gerçekleşti (yan-etki kayboldu değil)
        tok = _FakeTokenizer(chat_template="t", apply_exc=ValueError())
        _format_prompt(tok, "merhaba")
        assert len(tok.calls) == 1

    @pytest.mark.parametrize("prompt", _TR_PROMPTS)
    def test_dususte_unicode_korunur(self, prompt):
        tok = _FakeTokenizer(chat_template="t", apply_exc=ValueError())
        assert _format_prompt(tok, prompt) == prompt

    def test_dususte_kwarglar_yine_doğru(self):
        # Hata öncesi çağrı yine doğru kwarg'larla yapıldı
        tok = _FakeTokenizer(chat_template="t", apply_exc=ValueError())
        _format_prompt(tok, "merhaba")
        assert tok.calls[0][1]["tokenize"] is False
        assert tok.calls[0][1]["add_generation_prompt"] is True


# ------------------------------------------------------------------ ortak
class TestDeterminism:
    def test_ayni_tokenizer_iki_cagri_ayni_sonuc(self):
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        assert _format_prompt(tok, "a") == _format_prompt(tok, "a")
        assert len(tok.calls) == 2

    def test_prompt_mutasyona_ugramaz(self):
        prompt = "merhaba"
        tok = _FakeTokenizer(chat_template="t", apply_result="sarmal")
        _format_prompt(tok, prompt)
        assert prompt == "merhaba"

    @pytest.mark.parametrize("chat_template,apply_result,expected", [
        (None, "sarmal", "merhaba"),
        ("", "sarmal", "merhaba"),
        ("t", "sarmal", "sarmal"),
        ("t", None, None),
        (0, "sarmal", "merhaba"),
    ])
    def test_tablo(self, chat_template, apply_result, expected):
        tok = _FakeTokenizer(chat_template=chat_template, apply_result=apply_result)
        assert _format_prompt(tok, "merhaba") == expected

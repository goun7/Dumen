"""77-Dumen cli._format_prompt + _build_model_runner + _load_transformers_pair
dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (stub tokenizer/model — transformers import EDILMEZ).
Instruct-modeller chat-template ile sarilir; GPT-2 ham-metin.
"""
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from dumen.cli import _format_prompt, _build_model_runner, _load_transformers_pair  # noqa: E402


class _ChatTokenizer:
    """chat_template'li tokenizer stubu."""
    chat_template = "<|im_start|>user\\n{prompt}<|im_end|>"

    def apply_chat_template(self, mesajlar, tokenize=False,
                            add_generation_prompt=False):
        assert tokenize is False
        assert add_generation_prompt is True
        assert len(mesajlar) == 1
        assert mesajlar[0]["role"] == "user"
        return f"USER: {mesajlar[0]['content']}"


class _DuzTokenizer:
    """chat_template YOK (GPT-2 gibi)."""
    chat_template = None

    def encode(self, text):
        return [1, 2, 3]


class _HataliTokenizer:
    """chat_template VAR ama apply bozuk."""
    chat_template = "x"

    def apply_chat_template(self, *a, **k):
        raise RuntimeError("bozuk template")


class _Model:
    device = "cpu"
    input_ids = None

    def __init__(self, cikti="merhaba"):
        self._cikti = cikti
        self.cagrildi = []

    def generate(self, **kwargs):
        self.cagrildi.append(kwargs)
        # out[0] = tum-tokenler; [input_ids.shape[1]:] = yeni-kisim
        import torch

        class _T:
            def __init__(self, data):
                self.data = data

            def __getitem__(self, i):
                return _T(self.data[i])

            @property
            def shape(self):
                return (1, len(self.data))

            def to(self, d):
                return self
        self._son_inputs = kwargs.get("input_ids")
        return _T([[101, 102] + list(self._cikti.encode("utf-8"))])


# == _format_prompt: chat template ====================================================================

def test_chat_template_var():
    """ORTAM: chat_template -> apply_chat_template ile sarilir."""
    t = _ChatTokenizer()
    assert _format_prompt(t, "merhaba") == "USER: merhaba"


def test_chat_template_none():
    """ORTAM: chat_template None -> ham metin."""
    assert _format_prompt(_DuzTokenizer(), "merhaba") == "merhaba"


def test_chat_template_yok_attr():
    """ORTAM: getattr default -> None -> ham metin."""

    class _T:
        pass
    assert _format_prompt(_T(), "x") == "x"


def test_chat_template_false():
    """ORTAM: chat_template False -> falsy -> ham metin."""

    class _T:
        chat_template = False
    assert _format_prompt(_T(), "x") == "x"


def test_chat_template_bos_str():
    """ORTAM: chat_template '' -> falsy -> ham metin."""

    class _T:
        chat_template = ""
    assert _format_prompt(_T(), "x") == "x"


def test_chat_template_hatali():
    """ORTAM: apply exception -> ham metne dus (davranish korumasi)."""
    assert _format_prompt(_HataliTokenizer(), "x") == "x"


def test_chat_template_tokenize_false():
    """ORTAM: tokenize=False beklenir (string donus)."""
    yakalanan = {}

    class _T:
        chat_template = "x"

        def apply_chat_template(self, m, tokenize=False,
                                add_generation_prompt=False):
            yakalanan["tokenize"] = tokenize
            yakalanan["gen"] = add_generation_prompt
            return "ok"
    _format_prompt(_T(), "x")
    assert yakalanan["tokenize"] is False
    assert yakalanan["gen"] is True


def test_chat_template_role_user():
    """ORTAM: [{"role":"user","content":prompt}] tek-mesaj."""
    yakalanan = {}

    class _T:
        chat_template = "x"

        def apply_chat_template(self, m, tokenize=False,
                                add_generation_prompt=False):
            yakalanan["m"] = m
            return "ok"
    _format_prompt(_T(), "test123")
    assert yakalanan["m"] == [{"role": "user", "content": "test123"}]


def test_repeatable():
    t = _ChatTokenizer()
    assert _format_prompt(t, "x") == _format_prompt(t, "x")


def test_farkli_prompt_farkli_cikti():
    t = _ChatTokenizer()
    assert _format_prompt(t, "a") != _format_prompt(t, "b")


def test_turkce_prompt():
    """ORTAM: turkce-karakter korunur."""
    assert _format_prompt(_DuzTokenizer(), "DÜMEN merhaba") == "DÜMEN merhaba"


def test_bos_prompt():
    assert _format_prompt(_DuzTokenizer(), "") == ""


def test_cok_satirli_prompt():
    p = "satir1\nsatir2"
    assert _format_prompt(_DuzTokenizer(), p) == p


def test_uzun_prompt():
    p = "x" * 10000
    assert _format_prompt(_DuzTokenizer(), p) == p


@pytest.mark.parametrize("p", ["a", "1", "", "x y", "İİ"])
def test_duz_matrix(p):
    """ORTAM: chat-template YOK -> ham metin (her prompt)."""
    assert _format_prompt(_DuzTokenizer(), p) == p


@pytest.mark.parametrize("p", ["a", "1", "x y", "İİ", "emoji 🔒"])
def test_chat_matrix(p):
    """ORTAM: chat-template var -> sarilir."""
    assert _format_prompt(_ChatTokenizer(), p) == f"USER: {p}"


# == _load_transformers_pair ===========================================================================

def test_import_yok(monkeypatch):
    """ORTAM: transformers ImportError -> (None, None)."""
    import builtins

    gercek = builtins.__import__

    def _sahte(name, *a, **k):
        if name == "transformers" or name.startswith("transformers."):
            raise ImportError("yok")
        return gercek(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", _sahte)
    assert _load_transformers_pair("gpt2") == (None, None)


def test_load_hata(monkeypatch):
    """ORTAM: from_pretrained hata -> (None, None)."""

    class _HataliAuto:
        @staticmethod
        def from_pretrained(*a, **k):
            raise RuntimeError("ag hatasi")
    mod = type("transformers", (), {
        "AutoModelForCausalLM": _HataliAuto,
        "AutoTokenizer": _HataliAuto,
    })
    monkeypatch.setitem(sys.modules, "transformers", mod)
    assert _load_transformers_pair("gpt2") == (None, None)


class _YukluModel:
    """from_pretrained sonrasi .eval() cagrisini destekler."""
    def __init__(self, mid):
        self.mid = mid
        self.eval_cagrildi = False

    def eval(self):
        self.eval_cagrildi = True
        return self


def test_load_basari(monkeypatch):
    """ORTAM: basarili yukleme -> (tokenizer, model); model.eval() cagrilir."""
    mod = type("transformers", (), {
        "AutoModelForCausalLM": type("A", (), {
            "from_pretrained": staticmethod(lambda mid: _YukluModel(mid))}),
        "AutoTokenizer": type("A", (), {
            "from_pretrained": staticmethod(lambda mid: f"tok-{mid}")}),
    })
    monkeypatch.setitem(sys.modules, "transformers", mod)
    t, m = _load_transformers_pair("gpt2")
    assert t == "tok-gpt2"
    assert isinstance(m, _YukluModel)
    assert m.eval_cagrildi


# == _build_model_runner ===============================================================================

def test_runner_none(monkeypatch):
    """ORTAM: tokenizer None -> None."""
    monkeypatch.setattr("dumen.cli._load_transformers_pair",
                        lambda mid: (None, None))
    assert _build_model_runner("gpt2") is None


def test_runner_callable(monkeypatch):
    """ORTAM: basarili -> callable."""
    monkeypatch.setattr("dumen.cli._load_transformers_pair",
                        lambda mid: (_DuzTokenizer(), "model"))
    r = _build_model_runner("gpt2")
    assert callable(r)


def test_runner_cagri(monkeypatch):
    """ORTAM: runner(prompt) -> _generate(tokenizer, model, prompt)."""
    yakalanan = {}

    def _sahte_generate(tok, mdl, prompt, max_new_tokens=64):
        yakalanan["tok"] = tok
        yakalanan["mdl"] = mdl
        yakalanan["prompt"] = prompt
        return "uretim"
    monkeypatch.setattr("dumen.cli._load_transformers_pair",
                        lambda mid: (_DuzTokenizer(), "MODEL"))
    monkeypatch.setattr("dumen.cli._generate", _sahte_generate)
    r = _build_model_runner("gpt2")
    assert r("merhaba") == "uretim"
    assert yakalanan["prompt"] == "merhaba"
    assert yakalanan["mdl"] == "MODEL"


def test_runner_model_id_gecer(monkeypatch):
    """ORTAM: model_id _load_transformers_pair'e gecer."""
    yakalanan = {}
    monkeypatch.setattr(
        "dumen.cli._load_transformers_pair",
        lambda mid: (yakalanan.setdefault("mid", mid), None))
    _build_model_runner("gpt2-tr")
    assert yakalanan["mid"] == "gpt2-tr"

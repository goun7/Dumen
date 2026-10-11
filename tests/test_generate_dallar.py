"""dal-kesen test: cli._generate — greedy (deterministik) uretim hattinin dallari.

ORTAM-ANATOMI
-------------
_generate(tokenizer, hf_model, prompt, max_new_tokens=64):
  text = _format_prompt(tokenizer, prompt)          # chat-template varsa sarma
  inputs = {k: v.to(hf_model.device) for k,v in
            tokenizer(text, return_tensors='pt').items()}
  with torch.no_grad():
      out = hf_model.generate(**inputs, max_new_tokens=..., do_sample=False)
  return tokenizer.decode(out[0][inputs['input_ids'].shape[1]:],
                          skip_special_tokens=True)   # ONCELIK KISMI ATILIR

ORTAM-OGRENDILER
----------------
(1) Greedy ZORUNLU — do_sample=False her zaman (kanit yeniden-ureretilebilir;
    temperature yok, uretim hatti bunu SABIT gecer).
(2) max_new_tokens DEFAULT 64 — arguman verilmezse generate'e 64 gider.
(3) CIKTI-ONCELIKKI input UZUNLUGU KADAR ATILIR — decode yalnizca
    out[0][input_len:] parcasini alir (prompt-echo yok; input_ids.shape[1]
    kaynagi). uretilen parca kisa/uzun olsa da dilim input uzunlugundadir.
(4) skip_special_tokens=True SABIT gecilir (decode'a iletilir).
(5) TOKENizer'a GELEN METIN chat-template'e bagli: template YOKSA ham prompt,
    VARSA apply_chat_template ciktisi. sarma _format_prompt icindedir.
(6) TENSOR'LER hf_model.device'A TASINIR — her input degeri .to(device)
    cagrisi gormek zorunda; cihaz modelden gelir.
(7) apply_chat_template HATA verirse ham metne dusulur (gizli try/except,
    davranis-korunmasi) — _generate patlamaz.
(8) generate **inputs ile BUTUN sozlugu alir (sadece input_ids degil;
    attention_mask gibi ek tensor'ler de iletilir).
(9) return_tensors='pt' SABIT gecilir.
(10) chat_template FALSY (None/''/False) hepsi ham-metin davranisi.
"""
import sys

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")

from dumen.cli import _generate  # noqa: E402


# ---------------------------------------------------------------- stub'lar
class FakeT(list):
    """Tek-boyutlu tensor-benzeri: .shape[1] + .to(device)."""

    def __init__(self, seq, device="cpu", shape=None):
        super().__init__(seq)
        self.device = device
        self.shape = shape or (1, len(seq))
        self.moved_to = None

    def to(self, dev):
        self.moved_to = dev
        moved = FakeT(list(self), dev, self.shape)
        moved.moved_to = dev
        return moved


class FakeOut:
    def __init__(self, rows):
        self.rows = rows

    def __getitem__(self, i):
        return self.rows[i]


class FakeTok:
    def __init__(self, chat_template=None, gen_tail=(77, 88)):
        self.chat_template = chat_template
        self.calls = []
        self.decode_calls = []
        self._tail = list(gen_tail)

    def __call__(self, text, return_tensors="pt"):
        self.calls.append((text, return_tensors))
        return {"input_ids": FakeT([10, 20, 30])}

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "CHAT:" + messages[0]["content"]

    def decode(self, ids, skip_special_tokens=True):
        self.decode_calls.append((list(ids), skip_special_tokens))
        return "DECODED:" + ",".join(map(str, ids))


class FakeModel:
    def __init__(self, device="cpu", in_len=3):
        self.device = device
        self.gen = []
        self._in_len = in_len

    def generate(self, **kwargs):
        self.gen.append(kwargs)
        row = FakeT(list(range(100, 100 + self._in_len)) + self._gen_tail(),
                    shape=(1, self._in_len + 2))
        return FakeOut([row])

    def _gen_tail(self):
        return [77, 88]


class BadTemplateTok(FakeTok):
    def apply_chat_template(self, *a, **k):
        raise RuntimeError("bozuk template")


class MultiInputTok(FakeTok):
    """attention_mask gibi ek tensor de donduren tokenizer."""

    def __call__(self, text, return_tensors="pt"):
        self.calls.append((text, return_tensors))
        return {"input_ids": FakeT([10, 20, 30]),
                "attention_mask": FakeT([1, 1, 1])}


# ================================================================ greedy sabiti
class TestGreedyContract:
    def test_do_sample_false(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert mdl.gen[0]["do_sample"] is False

    def test_do_sample_false_with_custom_tokens(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru", max_new_tokens=4)
        assert mdl.gen[0]["do_sample"] is False

    def test_generate_called_once(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert len(mdl.gen) == 1

    @pytest.mark.parametrize("mnt", [1, 8, 64, 100])
    def test_max_new_tokens_forwarded(self, mnt):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru", max_new_tokens=mnt)
        assert mdl.gen[0]["max_new_tokens"] == mnt

    def test_max_new_tokens_default_is_64(self):
        """ORTAM-OGRENDI (2)."""
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert mdl.gen[0]["max_new_tokens"] == 64

    def test_no_temperature_or_sampling_keys(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert "temperature" not in mdl.gen[0]
        assert "top_k" not in mdl.gen[0]
        assert "top_p" not in mdl.gen[0]


# ================================================================ cikti-öncelik slicing
class TestPrefixStripping:
    def test_only_generated_part_decoded(self):
        """ORTAM-OGRENDI (3): input 3 -> decode yalnizca [77,88]."""
        tok, mdl = FakeTok(), FakeModel()
        out = _generate(tok, mdl, "soru")
        assert tok.decode_calls[0][0] == [77, 88]

    def test_prompt_prefix_not_in_decode(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert 100 not in tok.decode_calls[0][0]
        assert 101 not in tok.decode_calls[0][0]
        assert 102 not in tok.decode_calls[0][0]

    def test_slice_length_independent_of_max_new_tokens(self):
        """Dilim out[0] uzunlugundan degil, INPUT uzunlugundan hesaplanir."""
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru", max_new_tokens=50)
        # model 2 yeni token dondurdu -> decode 2 id alir (out uzunlugu belirler)
        assert len(tok.decode_calls[0][0]) == 2

    def test_longer_input_strips_more(self):
        class LongModel(FakeModel):
            def __init__(self):
                super().__init__(in_len=6)

            def __call__(self, text, return_tensors="pt"):
                self.calls.append((text, return_tensors))
                return {"input_ids": FakeT([1, 2, 3, 4, 5, 6])}

        class Tok(FakeTok):
            def __call__(self, text, return_tensors="pt"):
                self.calls.append((text, return_tensors))
                return {"input_ids": FakeT([1, 2, 3, 4, 5, 6])}

        tok, mdl = Tok(), LongModel()
        _generate(tok, mdl, "soru")
        assert tok.decode_calls[0][0] == [77, 88]

    def test_decode_returned_verbatim(self):
        tok, mdl = FakeTok(), FakeModel()
        assert _generate(tok, mdl, "soru").startswith("DECODED:")

    def test_skip_special_tokens_true(self):
        """ORTAM-OGRENDI (4)."""
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert tok.decode_calls[0][1] is True


# ================================================================ prompt-sarma
class TestPromptWrapping:
    def test_no_chat_template_uses_raw_prompt(self):
        """ORTAM-OGRENDI (5)(10)."""
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert tok.calls[0][0] == "soru"

    def test_chat_template_wraps_prompt(self):
        tok, mdl = FakeTok(chat_template="tmpl"), FakeModel()
        _generate(tok, mdl, "soru")
        assert tok.calls[0][0] == "CHAT:soru"

    def test_apply_chat_template_gets_user_role(self):
        seen = {}
        tok = FakeTok(chat_template="tmpl")

        def cap(messages, tokenize=False, add_generation_prompt=True):
            seen["messages"] = messages
            seen["tokenize"] = tokenize
            seen["add_gen"] = add_generation_prompt
            return "CHAT:" + messages[0]["content"]

        tok.apply_chat_template = cap
        _generate(tok, FakeModel(), "soru")
        assert seen["messages"] == [{"role": "user", "content": "soru"}]

    def test_apply_chat_template_tokenize_false(self):
        seen = {}
        tok = FakeTok(chat_template="tmpl")
        tok.apply_chat_template = lambda m, tokenize=False, add_generation_prompt=True: (
            seen.__setitem__("tokenize", tokenize), "CHAT:" + m[0]["content"])[1]
        _generate(tok, FakeModel(), "soru")
        assert seen["tokenize"] is False

    def test_apply_chat_template_add_generation_prompt_true(self):
        seen = {}
        tok = FakeTok(chat_template="tmpl")
        tok.apply_chat_template = lambda m, tokenize=False, add_generation_prompt=True: (
            seen.__setitem__("agp", add_generation_prompt), "CHAT:" + m[0]["content"])[1]
        _generate(tok, FakeModel(), "soru")
        assert seen["agp"] is True

    @pytest.mark.parametrize("tmpl", [None, "", False])
    def test_falsy_chat_templates_use_raw(self, tmpl):
        """ORTAM-OGRENDI (10)."""
        tok, mdl = FakeTok(chat_template=tmpl), FakeModel()
        _generate(tok, mdl, "soru")
        assert tok.calls[0][0] == "soru"

    def test_bad_template_falls_back_to_raw(self):
        """ORTAM-OGRENDI (7): apply_chat_template hata -> ham metin."""
        tok, mdl = BadTemplateTok(chat_template="bad"), FakeModel()
        out = _generate(tok, mdl, "soru")
        assert tok.calls[0][0] == "soru"
        assert out == "DECODED:77,88"

    def test_bad_template_does_not_raise(self):
        tok, mdl = BadTemplateTok(chat_template="bad"), FakeModel()
        _generate(tok, mdl, "soru")  # hata yutmali


# ================================================================ cihaz tasinmasi
class TestDeviceMove:
    def test_tensors_moved_to_model_device(self):
        """ORTAM-OGRENDI (6)."""
        tok = FakeTok()
        mdl = FakeModel(device="meta")
        _generate(tok, mdl, "soru")
        # tokenizer'dan donen input_ids .to('meta') gormeli
        assert mdl.gen[0]["input_ids"].moved_to == "meta"

    def test_device_attribute_is_source(self):
        tok, mdl = FakeTok(), FakeModel(device="cuda:0")
        _generate(tok, mdl, "soru")
        assert mdl.device == "cuda:0"

    def test_cpu_device_still_called_to(self):
        tok, mdl = FakeTok(), FakeModel(device="cpu")
        _generate(tok, mdl, "soru")
        assert mdl.gen[0]["input_ids"].moved_to == "cpu"

    def test_extra_tensors_also_moved(self):
        """ORTAM-OGRENDI (8): butun input degerleri tasinir."""
        tok, mdl = MultiInputTok(), FakeModel(device="meta")
        _generate(tok, mdl, "soru")
        assert mdl.gen[0]["attention_mask"].moved_to == "meta"


# ================================================================ inputs gecisi
class TestInputsForwarding:
    def test_return_tensors_pt(self):
        """ORTAM-OGRENDI (9)."""
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert tok.calls[0][1] == "pt"

    def test_generate_receives_all_input_keys(self):
        tok, mdl = MultiInputTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert set(mdl.gen[0]) >= {"input_ids", "attention_mask"}

    def test_generate_receives_input_values(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert list(mdl.gen[0]["input_ids"]) == [10, 20, 30]

    def test_tokenizer_called_once(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert len(tok.calls) == 1

    def test_decode_called_once(self):
        tok, mdl = FakeTok(), FakeModel()
        _generate(tok, mdl, "soru")
        assert len(tok.decode_calls) == 1


# ================================================================ tur-yok determinizm
class TestDeterminism:
    def test_same_prompt_same_output(self):
        tok, mdl = FakeTok(), FakeModel()
        a = _generate(tok, mdl, "soru")
        b = _generate(FakeTok(), FakeModel(), "soru")
        assert a == b

    def test_repeated_calls_stable(self):
        tok, mdl = FakeTok(), FakeModel()
        outs = {_generate(tok, mdl, "soru") for _ in range(5)}
        assert len(outs) == 1

    def test_special_token_names_not_requested(self):
        tok, mdl = FakeTok(), FakeModel()
        out = _generate(tok, mdl, "soru")
        assert out.count("DECODED:") == 1

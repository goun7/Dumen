"""tests/test_post_json_dallar.py — dumen.redteam.api_runner._post_json dal-keseç testleri.

Kural-4: saf-in-memory. httpx.post monkeypatch ile STUBLANIR — gerçek socket/HTTP YOK.

Hedeflenen dallar:
  1. api_key falsy        → Authorization başlığı YOK
  2. api_key truthy       → "Bearer <key>" başlığı
  3. httpx.post → HTTPError → EndpointError ("ulaşılamadı", __cause__ korumalı)
  4. status >= 400        → EndpointError (kod + url + text[:300] truncate)
  5. status < 400 + geçerli json → dict döner
  6. resp.json() → ValueError → EndpointError ("geçersiz JSON")
  7. HTTPError-DIŞI istisna → olduğu gibi dışarı sızar (sarılma yok)
"""
from __future__ import annotations

import json

import httpx
import pytest

from dumen.redteam.api_runner import EndpointError, _post_json


class _FakeResp:
    """Sahte httpx.Response: status_code / text / json() davranışı."""

    def __init__(self, status_code=200, text="", json_data=None, json_exc=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data
        self._json_exc = json_exc

    def json(self):
        if self._json_exc is not None:
            raise self._json_exc
        return self._json_data


class _Recorder:
    """httpx.post yerine geçer: çağrıları kaydeder, cevap veya istisna döner."""

    def __init__(self, resp=None, exc=None):
        self.resp = resp if resp is not None else _FakeResp(json_data={})
        self.exc = exc
        self.calls: list[tuple[tuple, dict]] = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, dict(kwargs)))
        if self.exc is not None:
            raise self.exc
        return self.resp


@pytest.fixture
def stub_post(monkeypatch):
    def _install(recorder):
        monkeypatch.setattr(httpx, "post", recorder)
        return recorder

    return _install


# ------------------------------------------------------------------ başlıklar
class TestHeaders:
    def test_api_key_yoksa_authorization_yok(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={"ok": True})))
        _post_json("http://x/v1/chat", {"a": 1}, None, 10.0)
        headers = rec.calls[0][1]["headers"]
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_api_key_bos_string_authorization_yok(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, "", 5.0)
        assert "Authorization" not in rec.calls[0][1]["headers"]

    def test_api_key_varsa_bearer_taşınır(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, "sk-test-123", 5.0)
        assert rec.calls[0][1]["headers"]["Authorization"] == "Bearer sk-test-123"

    def test_api_key_unicode_bearer(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, "sk-Ünİkod", 5.0)
        assert rec.calls[0][1]["headers"]["Authorization"] == "Bearer sk-Ünİkod"

    @pytest.mark.parametrize("falsy", [None, "", 0])
    def test_falsy_api_keyler_baslik_eklemez(self, stub_post, falsy):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, falsy, 5.0)
        assert "Authorization" not in rec.calls[0][1]["headers"]

    def test_content_type_her_zaman_var(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, "sk", 5.0)
        assert rec.calls[0][1]["headers"]["Content-Type"] == "application/json"

    def test_cagrida_basliklar_taze_dict(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, None, 5.0)
        _post_json("http://x/", {}, "sk", 5.0)
        assert "Authorization" not in rec.calls[0][1]["headers"]
        assert rec.calls[1][1]["headers"]["Authorization"] == "Bearer sk"


# ------------------------------------------------------------------ argümanlar
class TestCallArgs:
    def test_url_positional_iletilir(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://sunucu/v1/chat", {}, None, 5.0)
        assert rec.calls[0][0][0] == "http://sunucu/v1/chat"

    def test_payload_json_kwarg_olarak(self, stub_post):
        payload = {"model": "q", "messages": [{"role": "user", "content": "a"}]}
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", payload, None, 5.0)
        assert rec.calls[0][1]["json"] is payload

    @pytest.mark.parametrize("timeout", [0.5, 1.0, 15.0, 300.0])
    def test_timeout_iletilir(self, stub_post, timeout):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, None, timeout)
        assert rec.calls[0][1]["timeout"] == timeout

    def test_unicode_url(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/v1/sohbet?a=İ", {}, None, 5.0)
        assert rec.calls[0][0][0] == "http://x/v1/sohbet?a=İ"

    def test_unicode_payload(self, stub_post):
        payload = {"content": "İĞÜŞÖÇ ğüşıöç"}
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", payload, None, 5.0)
        assert rec.calls[0][1]["json"] == payload

    def test_bos_payload(self, stub_post):
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", {}, None, 5.0)
        assert rec.calls[0][1]["json"] == {}

    def test_icice_payload(self, stub_post):
        payload = {"a": {"b": {"c": [1, 2, {"d": "e"}]}}}
        rec = stub_post(_Recorder(resp=_FakeResp(json_data={})))
        _post_json("http://x/", payload, None, 5.0)
        assert rec.calls[0][1]["json"] == payload


# ------------------------------------------------------------------ dal 5: başarı
class TestSuccess:
    @pytest.mark.parametrize("status", [200, 201, 204, 301, 399])
    def test_dusuk_status_json_donuyor(self, stub_post, status):
        data = {"choices": [{"message": {"content": "merhaba"}}]}
        stub_post(_Recorder(resp=_FakeResp(status_code=status, json_data=data)))
        assert _post_json("http://x/", {}, None, 5.0) == data

    def test_donuş_json_nesnesinin_kendisi(self, stub_post):
        data = {"a": 1}
        stub_post(_Recorder(resp=_FakeResp(json_data=data)))
        assert _post_json("http://x/", {}, None, 5.0) is data

    def test_json_dict_degilse_de_oldugu_gibi_donuyor(self, stub_post):
        # Üretim sınırı: dönüş tipi Dict annotated ama isinstance doğrulaması YOK
        stub_post(_Recorder(resp=_FakeResp(json_data=[1, 2, 3])))
        assert _post_json("http://x/", {}, None, 5.0) == [1, 2, 3]

    def test_unicode_json_icerigi(self, stub_post):
        data = {" Yanıt": "İşte sonuç: örüntü"}
        stub_post(_Recorder(resp=_FakeResp(json_data=data)))
        assert _post_json("http://x/", {}, None, 5.0) == data


# ------------------------------------------------------------------ dal 4: HTTP hata
class TestHttpErrorStatus:
    @pytest.mark.parametrize("status", [400, 401, 403, 404, 500, 503, 599])
    def test_4xx_5xx_endpoint_error(self, stub_post, status):
        stub_post(_Recorder(resp=_FakeResp(status_code=status, text="bad")))
        with pytest.raises(EndpointError):
            _post_json("http://x/", {}, None, 5.0)

    def test_hata_mesaji_url_icerir(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=500, text="boom")))
        with pytest.raises(EndpointError, match=r"http://x/v1/chat"):
            _post_json("http://x/v1/chat", {}, None, 5.0)

    def test_hata_mesaji_status_kodu_icerir(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=403, text="yok")))
        with pytest.raises(EndpointError, match="403"):
            _post_json("http://x/", {}, None, 5.0)

    def test_hata_mesaji_metni_icerir(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=400, text="geçersiz istek")))
        with pytest.raises(EndpointError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        assert "geçersiz istek" in str(ei.value)

    def test_uzun_metin_300_karakter_truncated(self, stub_post):
        uzun = "A" * 500
        stub_post(_Recorder(resp=_FakeResp(status_code=500, text=uzun)))
        with pytest.raises(EndpointError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        msg = str(ei.value)
        assert "A" * 300 in msg          # ilk 300 karakter
        assert "A" * 400 not in msg      # 400+ karakter yok → truncate kanıtı

    def test_status_399_siniri_hata_degil(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=399, json_data={"ok": 1})))
        assert _post_json("http://x/", {}, None, 5.0) == {"ok": 1}

    def test_status_400_siniri_hata(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=400, json_data={"ok": 1})))
        # json geçerli olsa bile status >= 400 öncelikli → hata
        with pytest.raises(EndpointError):
            _post_json("http://x/", {}, None, 5.0)


# ------------------------------------------------------------------ dal 3: taşıma hatası
class TestTransportError:
    @pytest.mark.parametrize("exc", [
        pytest.param(httpx.ConnectError("bağlanamadı"), id="ConnectError"),
        pytest.param(httpx.ConnectTimeout("zaman aşımı"), id="ConnectTimeout"),
        pytest.param(httpx.ReadTimeout("okuma zaman aşımı"), id="ReadTimeout"),
        pytest.param(httpx.TimeoutException("zaman aşımı"), id="TimeoutException"),
        pytest.param(httpx.HTTPError("genel"), id="HTTPError"),
    ])
    def test_httperror_endpoint_error(self, stub_post, exc):
        stub_post(_Recorder(exc=exc))
        with pytest.raises(EndpointError):
            _post_json("http://x/", {}, None, 5.0)

    def test_hata_mesaji_ulasilamadi(self, stub_post):
        stub_post(_Recorder(exc=httpx.ConnectError("yok")))
        with pytest.raises(EndpointError, match="API sonuna ulaşılamadı"):
            _post_json("http://x/", {}, None, 5.0)

    def test_hata_mesaji_url_icerir(self, stub_post):
        stub_post(_Recorder(exc=httpx.ConnectError("yok")))
        with pytest.raises(EndpointError, match=r"http://x:11434/v1"):
            _post_json("http://x:11434/v1/chat", {}, None, 5.0)

    def test_hata_mesaji_orijinal_exc_mesaji_icerir(self, stub_post):
        exc = httpx.ConnectError("connection refused")
        stub_post(_Recorder(exc=exc))
        with pytest.raises(EndpointError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        assert "connection refused" in str(ei.value)

    def test_cause_zinciri_korunur(self, stub_post):
        exc = httpx.ConnectError("yok")
        stub_post(_Recorder(exc=exc))
        with pytest.raises(EndpointError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        assert ei.value.__cause__ is exc

    def test_endpoint_error_runtimeerror_alt_sinifi(self, stub_post):
        stub_post(_Recorder(exc=httpx.ConnectError("yok")))
        with pytest.raises(RuntimeError):
            _post_json("http://x/", {}, None, 5.0)


# ------------------------------------------------------------------ dal 6: bozuk json
class TestBadJson:
    def test_value_error_endpoint_error(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=200, json_exc=ValueError("no json"))))
        with pytest.raises(EndpointError):
            _post_json("http://x/", {}, None, 5.0)

    def test_json_decode_error_valueerror_alt_sinidi(self, stub_post):
        exc = json.JSONDecodeError("beklenmeyen", "doc", 0)
        stub_post(_Recorder(resp=_FakeResp(status_code=200, json_exc=exc)))
        with pytest.raises(EndpointError):
            _post_json("http://x/", {}, None, 5.0)

    def test_mesaj_gecersiz_json(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=200, json_exc=ValueError("x"))))
        with pytest.raises(EndpointError, match="geçersiz JSON"):
            _post_json("http://x/", {}, None, 5.0)

    def test_mesaj_url_icerir(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=200, json_exc=ValueError("x"))))
        with pytest.raises(EndpointError, match=r"http://x/api"):
            _post_json("http://x/api", {}, None, 5.0)

    def test_cause_zinciri_korunur(self, stub_post):
        exc = ValueError("bozuk")
        stub_post(_Recorder(resp=_FakeResp(status_code=200, json_exc=exc)))
        with pytest.raises(EndpointError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        assert ei.value.__cause__ is exc


# ------------------------------------------------------------------ dal 7: sızan istisna
class TestUnwrappedExceptions:
    @pytest.mark.parametrize("exc", [
        pytest.param(RuntimeError("rpc"), id="RuntimeError"),
        pytest.param(TypeError("tip"), id="TypeError"),
        pytest.param(KeyError("anahtar"), id="KeyError"),
    ])
    def test_httperror_disi_post_hatasi_sizar(self, stub_post, exc):
        # Kural-4'deki tasarım: Sadece httpx.HTTPError sarılır
        stub_post(_Recorder(exc=exc))
        with pytest.raises(type(exc)):
            _post_json("http://x/", {}, None, 5.0)

    def test_post_runtimeerror_endpoint_error_degil(self, stub_post):
        stub_post(_Recorder(exc=RuntimeError("rpc")))
        with pytest.raises(RuntimeError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        assert not isinstance(ei.value, EndpointError)

    def test_jsondan_valueerror_disi_hata_sizar(self, stub_post):
        stub_post(_Recorder(resp=_FakeResp(status_code=200, json_exc=RuntimeError("boom"))))
        with pytest.raises(RuntimeError) as ei:
            _post_json("http://x/", {}, None, 5.0)
        assert not isinstance(ei.value, EndpointError)

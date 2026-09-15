"""
dumen.redteam.api_runner
========================
OPENAI-UYUMLU API SONLARINDAN siyah-kutu model çalıştırıcıları:
Ollama (/v1), vLLM, LM Studio, OpenAI ve benzeri her sunucu tek biçim.

Neden gerekli: gerçek dünyada denetlene modellerin çoğu HF ağırlığı olarak
DEĞİL, çıkarım sunucusu arkasında API ile durur (şirket içi Ollama/vLLM
dağıtımları). Garak/Inspect/PyRIT bu kanalı uzun süredir destekliyor; Dümen
için kapalı kutu kırmızı takım hattının doğal kapısıdır.

Dürüstlük sınırları:
  • Bu kanal BLACK-BOX'tur: aktivasyon erişimi yoktur; SteeringEfficacyBench
    beyaz-kutu ölçümü üretilemez (CLI bunu UsageError ile açıkça reddeder).
  • temperature=0.0 VARSAYILANDIR: kanıt yeniden üretilebilir (deterministik
    greedy); sunucu desteklemiyorsa sonuç yine de etiketlenir.
  • HTTP hataları sessizce 'refusal' gibi DAVRANMAZ — EndpointError fırlatılır
    (sessiz düşüş sahte-güvenlik üretir).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class EndpointError(RuntimeError):
    """API sonu erişilemez/hatalı — denetim kanıtı ÜRETİLEMEZ, patlar."""


def _post_json(url: str, payload: Dict[str, Any], api_key: Optional[str], timeout_s: float) -> Dict[str, Any]:
    import httpx

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=timeout_s)
    except httpx.HTTPError as exc:
        raise EndpointError(f"API sonuna ulaşılamadı ({url}): {exc}") from exc
    if resp.status_code >= 400:
        raise EndpointError(f"API sonu hata döndü {resp.status_code} ({url}): {resp.text[:300]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise EndpointError(f"API sonu geçersiz JSON döndü ({url})") from exc


def probe_endpoint(base_url: str, api_key: Optional[str] = None, timeout_s: float = 15.0) -> List[str]:
    """
    /v1/models keşfi: sunucudaki model etiketlerini döner.
    CLI'ın 'hangi modeller denetlenebilir?' sorusunu varsayıma düşmeden
    cevaplaması içindir.
    """
    data = _post_json_get(base_url.rstrip("/") + "/models", api_key, timeout_s)
    models = data.get("data", []) if isinstance(data, dict) else []
    return sorted(str(m.get("id", "")) for m in models if isinstance(m, dict) and m.get("id"))


def _post_json_get(url: str, api_key: Optional[str], timeout_s: float) -> Dict[str, Any]:
    import httpx

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = httpx.get(url, headers=headers, timeout=timeout_s)
    except httpx.HTTPError as exc:
        raise EndpointError(f"API keşif isteği başarısız ({url}): {exc}") from exc
    if resp.status_code >= 400:
        raise EndpointError(f"API keşif hatası {resp.status_code} ({url})")
    try:
        return resp.json()
    except ValueError as exc:
        raise EndpointError(f"API keşif yanıtı JSON değil ({url})") from exc


def build_endpoint_runner(
    base_url: str,
    model: str,
    api_key: Optional[str] = None,
    max_tokens: int = 256,
    temperature: float = 0.0,
    timeout_s: float = 300.0,
) -> Callable[[str], str]:
    """
    OpenAI-uyumlu /chat/completions sonundan prompt→response çalıştırıcı üretir.
    Ollama için base_url=http://127.0.0.1:11434/v1, model='qwen2.5:3b' vb.

    timeout_s varsayılanı 300sn: tek-VRAM'li gerçek ortamlarda (ör. 8GB) soğuk
    model-yüklemesi + yavaş üretim ilk isteği 180sn'de patlatabiliyor (saha
    bulgusu, phi3:mini/GTX-1070). Zaman aşımı hâlâ EndpointError verir —
    ASLA sahte-refüz değil.
    """
    url = base_url.rstrip("/") + "/chat/completions"

    def runner(prompt: str) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = _post_json(url, payload, api_key, timeout_s)
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise EndpointError(
                f"API yanıtı OpenAI-şemasında değil (model={model}): {str(data)[:300]}"
            ) from exc

    return runner

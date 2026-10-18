#!/usr/bin/env python3
"""dumen MCP sunucusu - Model Context Protocol 2025-06-18 over stdio.

Dumen'in mekanistik-denetim / SAE-yorumlanabilirlik / aktivasyon-yonlendirme
cekirdegini AI ajanlarina MCP araclari olarak sunar.

Tasarim-ilkesi (tamga/sester/swarmax MCP sunuculari ile ayni sozlesme):
  * SAF STDLIB cephe - modul-tepesinde HICBIR pip bagimliligi; `from dumen ...`
    ICMDE, arac-govdesinde. Sunucu torch'suz dahi AYAKLANIR; agir-bagimlilik
    gerektiren bir arac cagrilirsa temiz bir RED nedeni doner ("bakamadi"
    degil, kanit).
  * HICBIR ZAMAN exception - her arac JSON kaniti dondurur; traceback DEGIL
    "ok:false, reason:..." (tamga AT-192 message-RED disiplini).
  * CALISMAZSA-KAPALI - her yol bir kanittir.
  * Workspace-izolasyonu (docs/MCP_WORKSPACE_IZOLASYON_DERSI.md, veridict
    2026-10-19): HICBIR arac repo-alti varsayilan yere YAZMAZ. Yazan tek arac
    olan `archive` yalnizca CAGIRANIN verdigi acik yolu (output_path
    argumani veya DUMEN_MCP_ARCHIVE_DIR env'i) yazar; ikisi de yoksa RED -
    sessizce repo-alti bir dosya URETMEZ. Testlerde daima tmp_path.

Araclar:
  version            dumen --version + torch-yer-tespiti
  amplification_scan TLCM amplifikasyon-rejim tespiti (core/amplification.py)
  sae_summary        SAE ileri-gecisi + yeniden-insa kalitesi (core/sae_engine.py)
  steering_status    kayitli yonlendirme-vektor durumu (core/steering.py)
  kv_drift           birikimli KV-sapma metrikleri (core/kv_drift.py)
  archive            zlib-sikistirilmis JSON kanit-arsivi (output_path ZORUNLU)

Calistirma:
  python3 mcp/server.py                              # stdio JSON-RPC
  DUMEN_MCP_ARCHIVE_DIR=/yol python3 mcp/server.py
  (istemci tarafi: "command": "python",
    "args": ["<repo>/mcp/server.py"],
    "env": {"DUMEN_MCP_ARCHIVE_DIR": "/yol"})
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3  # noqa: F401 - _jsonable'in sqlite3.Row kolu icin (standart)
import sys
import zlib
from pathlib import Path

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "dumen"
SERVER_VERSION = "0.1.0"

ROOT = Path(__file__).resolve().parents[1]
# dumen/ paketini ice-aktarmak icin (src-layout YOK - paket dogrudan ROOT'ta).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


def _result(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id, code: int, msg: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}


def _jsonable(obj):
    """Ozyineli JSON'a-cevirici - kanit-sozlesmesinin son-kapisindan once.

    Her seyi guvenli-ture cevirir: dict/list/tuple derinlemesine, sqlite3.Row
    keys() ile dict, Path string'e, numpy skaleri/dizisi duz listeye, gerisi
    oldugu gibi birakilir (json.dumps karar verir).
    """
    if isinstance(obj, sqlite3.Row):  # pragma: no cover - swarmax kolu
        return {k: _jsonable(obj[k]) for k in obj.keys()}  # noqa: SIM118
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    try:  # numpy yuklu olabilir de olmayabilir de - her durumda calisir
        import numpy  # noqa: PLC0415 - bilincli gecikmeli import
    except ImportError:  # pragma: no cover - numpy'siz ortam
        return obj
    if isinstance(obj, numpy.ndarray):
        return _jsonable(obj.tolist())
    if isinstance(obj, numpy.generic):
        return obj.item()
    return obj


def _text(payload: dict) -> dict:
    """Asla-exception sozlesmesinin-son-kapisi: serilestirme-basarisizligi
    bile JSON kaniti dondurur (tamga AT-192 message-RED disiplini)."""
    try:
        text = json.dumps(_jsonable(payload), ensure_ascii=False)
    except Exception as e:  # noqa: BLE001 - son-kapi, traceback-YASAK
        text = json.dumps({"ok": False, "reason": f"serilestirme-hatasi: {type(e).__name__}: {e}"})
    return {"content": [{"type": "text", "text": text}]}


def _torch_version() -> tuple[bool, str]:
    """torch var mi, surumu kac - yoksun False, sunucu yine de ayakta."""
    try:
        import torch  # noqa: F401, PLC0415

        return True, torch.__version__
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


# --- arac implementasyonlari ----------------------------------------------------


def _tool_version(_args: dict) -> dict:
    """dumen --version ciktisi: dumen.__version__ + torch-yer-tespiti."""
    try:
        from dumen import __version__ as dumen_version
    except Exception as e:  # noqa: BLE001 - sunucu hep ayakta
        return {"ok": False, "reason": f"dumen-import-hatasi: {type(e).__name__}: {e}"}
    torch_ok, torch_info = _torch_version()
    return {"ok": True, "dumen_version": dumen_version, "torch_ok": torch_ok, "torch": torch_info}


def _tool_amplification_scan(args: dict) -> dict:
    """TLCM amplifikasyon-rejim tesbiti (dumen.core.amplification)."""
    alpha_max = args.get("alpha_max", 3.0)
    steps = args.get("steps", 12)
    seed = args.get("seed", 42)
    if not isinstance(alpha_max, (int, float)) or isinstance(alpha_max, bool) or not alpha_max > 0:
        return {"ok": False, "reason": "alpha_max-0'dan-buyuk-olmali (sayi)"}
    if not isinstance(steps, int) or isinstance(steps, bool) or not 2 <= steps <= 256:
        return {"ok": False, "reason": "steps-2..256-araliginda-tamsayi-olmali"}
    if not isinstance(seed, int) or isinstance(seed, bool):
        return {"ok": False, "reason": "seed-tamsayi-olmali"}
    try:
        import torch  # noqa: PLC0415

        from dumen.core.amplification import refine_alpha, scan_amplification, select_alpha  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"agir-bagimlilik-eksik (torch~2GB-dahil): {type(e).__name__}: {e}"}
    try:
        g = torch.Generator().manual_seed(seed)
        h = torch.randn(64, generator=g)
        v = torch.randn(64, generator=g)
        alphas = [round(alpha_max * i / steps, 4) for i in range(1, steps + 1)]
        scan = scan_amplification(h, v, alphas=alphas)
        chosen = select_alpha(scan)
        refined = refine_alpha(h, v, scan) if chosen is not None else None
        return {
            "ok": True,
            "alpha_max": alpha_max,
            "steps": steps,
            "seed": seed,
            "mode": "synthetic-64d (CLI: dumen amplification-scan ile ayni)",
            "cos_before": scan.cos_before,
            "cos_after_min": min(abs(c) for c in scan.cos_afters),
            "cos_after_max": max(abs(c) for c in scan.cos_afters),
            "monotone_reducing": scan.monotone_reducing,
            "amplified": scan.amplified,
            "first_amplified_alpha": scan.first_amplified_alpha,
            "safe_alpha_max": scan.safe_alpha_max,
            "recommended_alpha": refined if refined is not None else chosen,
            "recommended_alpha_note": "grid-optimal + altin-arama; sentetik vektorler - canli modelde dogrulanmadi",
            "notes": scan.notes,
        }
    except Exception as e:  # noqa: BLE001 - hicbir yol exception'a dusmez
        return {"ok": False, "reason": f"amplification-scan-hatasi: {type(e).__name__}: {e}"}


def _tool_sae_summary(args: dict) -> dict:
    """SAE ileri-gecisi + yeniden-insa kalitesi (dumen.core.sae_engine).

    SALT-HESAP - kaydetmez. (save_pretrained bilincli olarak burada YOK:
    o bir yazma-yoludur ve workspace-izolasyonu gerektirir.)
    """
    d_model = args.get("d_model", 64)
    n_features = args.get("n_features", 128)
    k_sparsity = args.get("k_sparsity", 16)
    seed = args.get("seed", 42)
    if not isinstance(d_model, int) or d_model < 1:
        return {"ok": False, "reason": "d_model-1-veya-daha-buyuk-tamsayi-olmali"}
    if not isinstance(n_features, int) or n_features < 1:
        return {"ok": False, "reason": "n_features-1-veya-daha-buyuk-tamsayi-olmali"}
    if not isinstance(k_sparsity, int) or not 1 <= k_sparsity <= n_features:
        return {"ok": False, "reason": "k_sparsity-1..n_features-araliginda-olmali"}
    if not isinstance(seed, int):
        return {"ok": False, "reason": "seed-tamsayi-olmali"}
    try:
        import torch  # noqa: PLC0415

        from dumen.core.sae_engine import SparseAutoencoderEngine  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"agir-bagimlilik-eksik (torch~2GB-dahil): {type(e).__name__}: {e}"}
    try:
        torch.manual_seed(seed)
        sae = SparseAutoencoderEngine(d_model=d_model, n_features=n_features, k_sparsity=k_sparsity, device="cpu")
        sae.eval()
        x = torch.randn(d_model)
        with torch.no_grad():
            x_hat, _f = sae(x)
            top = sae.inspect_activations(x, top_n=5)
            mse = float(torch.mean((x_hat - x) ** 2).item())
            cos = float(torch.nn.functional.cosine_similarity(x_hat, x, dim=0).item())
        return {
            "ok": True,
            "d_model": d_model,
            "n_features": n_features,
            "k_sparsity": k_sparsity,
            "seed": seed,
            "mean_squared_error": mse,
            "cosine_reconstruction": cos,
            "top_features": top,
            "note": "rastgele-baslatilmis agirliklarla gosterim - egitilmis bir kontrol-noktasi icin kanit yetmez",
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"sae-summary-hatasi: {type(e).__name__}: {e}"}


def _tool_steering_status(args: dict) -> dict:
    """Kayitli yonlendirme-vektor durumu + tek-vektor StTP davranisi."""
    dim = args.get("dim", 64)
    seed = args.get("seed", 42)
    alpha = args.get("alpha", 1.0)
    if not isinstance(dim, int) or isinstance(dim, bool) or not 1 <= dim <= 8192:
        return {"ok": False, "reason": "dim-1..8192-araliginda-tamsayi-olmali"}
    if not isinstance(seed, int) or isinstance(seed, bool):
        return {"ok": False, "reason": "seed-tamsayi-olmali"}
    if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or alpha < 0:
        return {"ok": False, "reason": "alpha-0-veya-daha-buyuk-olmali (sayi)"}
    try:
        import torch  # noqa: PLC0415

        from dumen.core.steering import SteeringEngine  # noqa: PLC0415
        from dumen.core.types import RiskCategory, SteeringMethod, SteeringVector  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"agir-bagimlilik-eksik (torch~2GB-dahil): {type(e).__name__}: {e}"}
    try:
        g = torch.Generator().manual_seed(seed)
        x = torch.randn(dim, generator=g)
        harmful_v = torch.randn(dim, generator=g)
        harmful_v = harmful_v / torch.norm(harmful_v)
        engine = SteeringEngine(device="cpu")
        vec = SteeringVector.from_tensor(
            name="probe-deception",
            layer_idx=6,
            tensor=harmful_v * 2.0,
            target_risk=RiskCategory.DECEPTION,
            method=SteeringMethod.STTP,
            threshold=0.5,
            strength=alpha,
        )
        engine.register_vector(vec)
        registered = []
        for _layer, vecs in engine.registered_vectors.items():
            for sv in vecs:
                registered.append(
                    {
                        "name": sv.name,
                        "layer_idx": sv.layer_idx,
                        "method": sv.method.value,
                        "target_risk": sv.target_risk.value,
                        "threshold": sv.threshold,
                        "strength": sv.strength,
                        "dim": sv.dimension,
                    }
                )
        steered = engine.project_sttp(x, harmful_v, alpha=alpha)
        cos_before = float(torch.dot(x / torch.norm(x), harmful_v).item())
        cos_after = float(torch.dot(steered / torch.norm(steered), harmful_v).item())
        return {
            "ok": True,
            "dim": dim,
            "seed": seed,
            "alpha": alpha,
            "engine_settings": {
                "device": engine.device,
                "adaptive_alpha": engine.adaptive_alpha,
                "quantization": engine.quantization.value,
                "kv_drift_guard": engine.kv_drift_guard is None,
            },
            "registered_vectors": registered,
            "cos_before": cos_before,
            "cos_after": cos_after,
            "|cos|-reduced": abs(cos_after) < abs(cos_before),
            "invariant_holds": abs(cos_after) <= abs(cos_before) + 1e-6,
            "probe": "sentetik (StTP + OV-maske CLI'da: dumen steer-test)",
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"steering-status-hatasi: {type(e).__name__}: {e}"}


def _tool_kv_drift(args: dict) -> dict:
    """Birikimli KV-sapma metrikleri (dumen.core.kv_drift.KVDriftGuard).

    Parametreler TAMAMEN gecicidir - guard bellek-icinde yasar, hicbir
    dosyaya DEGMEZ (izolasyon-dersi: arac repo-alti hicbir state yaratmaz).
    """
    decay = args.get("decay_factor", 0.95)
    max_drift = args.get("max_drift_threshold", 0.85)
    window = args.get("history_window", 128)
    steps = args.get("steps", 5)
    dim = args.get("dim", 64)
    seed = args.get("seed", 42)
    if not isinstance(decay, (int, float)) or isinstance(decay, bool) or not 0.0 < decay <= 1.0:
        return {"ok": False, "reason": "decay_factor-(0,1]-araliginda-olmali"}
    if not isinstance(max_drift, (int, float)) or isinstance(max_drift, bool) or not 0.0 < max_drift:
        return {"ok": False, "reason": "max_drift_threshold-0'dan-buyuk-olmali"}
    if not isinstance(window, int) or window < 1:
        return {"ok": False, "reason": "history_window-1-veya-daha-buyuk-olmali"}
    if not isinstance(steps, int) or not 1 <= steps <= 1024:
        return {"ok": False, "reason": "steps-1..1024-araliginda-tamsayi-olmali"}
    if not isinstance(dim, int) or dim < 1:
        return {"ok": False, "reason": "dim-1-veya-daha-buyuk-tamsayi-olmali"}
    if not isinstance(seed, int):
        return {"ok": False, "reason": "seed-tamsayi-olmali"}
    try:
        import torch  # noqa: PLC0415

        from dumen.core.kv_drift import KVDriftGuard  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"agir-bagimlilik-eksik (torch~2GB-dahil): {type(e).__name__}: {e}"}
    try:
        g = torch.Generator().manual_seed(seed)
        guard = KVDriftGuard(decay_factor=decay, max_drift_threshold=max_drift, history_window=window)
        norms = []
        effective_norms = []
        for _ in range(steps):
            h = torch.randn(dim, generator=g)
            delta = torch.randn(dim, generator=g) * 0.3
            eff, drift = guard.record_and_decay(0, h, delta)
            norms.append(drift)
            effective_norms.append(float(torch.norm(eff - h).item()))
        metrics = guard.get_drift_metrics(0)
        return {
            "ok": True,
            "params": {"decay_factor": decay, "max_drift_threshold": max_drift, "history_window": window},
            "steps_simulated": steps,
            "dim": dim,
            "seed": seed,
            "layer": 0,
            "drift_norms": [round(n, 4) for n in norms],
            "effective_delta_norms": [round(n, 4) for n in effective_norms],
            "final_metrics": metrics,
            "soft_clip_engaged": any(n >= max_drift - 1e-6 for n in norms),
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"kv-drift-hatasi: {type(e).__name__}: {e}"}


def _resolve_output_path(args: dict) -> tuple[str | None, str | None]:
    """Arsiv-yolunu SADECE cagirandan al - repo-alti varsayilan YOK.

    (docs/MCP_WORKSPACE_IZOLASYON_DERSI.md: MCP araclari repo-lokal
    varsayilan-state'e YAZMAMALI; her yazan arac acik bir yol-argumani
    gerektirmeli.)
    """
    explicit = args.get("output_path")
    if isinstance(explicit, str) and explicit:
        return explicit, None
    env_dir = os.environ.get("DUMEN_MCP_ARCHIVE_DIR")
    if isinstance(env_dir, str) and env_dir:
        return str(Path(env_dir) / "evidence.jsonz"), None
    return None, (
        "output_path-zorunlu (string) - repo-alti varsayilan "
        "yazilmaz; ya output_path verin ya da DUMEN_MCP_ARCHIVE_DIR "
        "env'ini ayarlayin"
    )


def _tool_archive(args: dict) -> dict:
    """Cagirici-belirli yola zlib JSON arsivi yaz (izole)."""
    payload = args.get("payload")
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "payload-zorunlu (JSON-nesnesi)"}
    out, why = _resolve_output_path(args)
    if out is None:
        return {"ok": False, "reason": why}
    try:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob = json.dumps(_jsonable(payload), ensure_ascii=False).encode()
        if len(blob) > MAX_ARCHIVE_BYTES:
            return {"ok": False, "reason": f"payload-cok-buyuk: {len(blob)} > {MAX_ARCHIVE_BYTES} bayt"}
        packed = zlib.compress(blob, 9)
        with open(out_path, "wb") as f:
            f.write(packed)
            wrote = f.tell()
        # Tutmasa-ac: geri-oku ve kanita-cevir.
        with open(out_path, "rb") as f:
            ok_blob = zlib.decompress(f.read())
        intact = ok_blob == blob
        return {
            "ok": bool(wrote == len(packed) and intact),
            "output_path": str(out_path),
            "bytes": wrote,
            "uncompressed_bytes": len(blob),
            "sha256_prefix": hashlib.sha256(blob).hexdigest()[:16],
            "roundtrip_ok": intact,
            "reason": (None if intact else "geri-okuma-uyumsuzlugu"),
        }
    except OSError as e:
        return {"ok": False, "reason": f"yazma-hatasi: {type(e).__name__}: {e}"}
    except zlib.error as e:
        return {"ok": False, "reason": f"sikistirma-hatasi: {type(e).__name__}: {e}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"arsiv-hatasi: {type(e).__name__}: {e}"}


TOOLS = {
    "version": {
        "handler": _tool_version,
        "description": (
            "dumen --version karsiligi: dumen.__version__ + torch-yer-tespiti "
            "(sunucu agir bagimliliklar olmadan da ayakta kalir; torch eksikse "
            "torch_ok=false olarak isaretlenir). SALT-OKUMA. "
            "Donus: {ok, dumen_version, torch_ok, torch} - ok=false RED."
        ),
        "schema": {"type": "object", "properties": {}, "required": []},
    },
    "amplification_scan": {
        "handler": _tool_amplification_scan,
        "description": (
            "TLCM amplifikasyon-rejim tesbitini calistirir (dumen.core."
            "amplification.scan_amplification + select_alpha + refine_alpha; "
            "arXiv:2609.07876). Alpha taramasi boyunca |cos| egrisini olcer, "
            "|cos_after| > |cos_before| rejimini isaretler ve guvenli-alpha "
            "sinirini (safe_alpha_max) dondurur. SALT-HESAP - hicbir dosyaya "
            "degmez, sentetik 64-boyutlu vektorlerle (CLI: dumen "
            "amplification-scan). Donus: {ok, amplified, "
            "first_amplified_alpha, safe_alpha_max, recommended_alpha, ...} "
            "- amplifiye durumlarda ok yine true'dur (bu bir TESPIT "
            "aracidir, amplifikasyonu onlemez)."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "alpha_max": {
                    "type": "number",
                    "description": "taramanin maksimum alfa'si (varsayilan 3.0)",
                },
                "steps": {
                    "type": "integer",
                    "description": "alfa izgara adim sayisi, 2..256 (varsayilan 12)",
                },
                "seed": {
                    "type": "integer",
                    "description": "torch tohumu (varsayilan 42)",
                },
            },
            "required": [],
        },
    },
    "sae_summary": {
        "handler": _tool_sae_summary,
        "description": (
            "SAE (SparseAutoencoderEngine) ileri-gecisini + yeniden-insa "
            "kalitesini ozetler: MSE, kosinus-yeniden-insa ve en-aktif TopK "
            "ozellikler (inspect_activations). SALT-HESAP - save_pretrained "
            "YOK (yazma-yolu izolasyon gerektirir). Donus: {ok, n_features, "
            "k_sparsity, mean_squared_error, cosine_reconstruction, "
            "top_features, ...}"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "d_model": {
                    "type": "integer",
                    "description": "aktivasyon boyutu (varsayilan 64)",
                },
                "n_features": {
                    "type": "integer",
                    "description": "SAE sozluk boyutu (varsayilan 128)",
                },
                "k_sparsity": {
                    "type": "integer",
                    "description": "TopK seyrekleme (varsayilan 16)",
                },
                "seed": {
                    "type": "integer",
                    "description": "torch tohumu (varsayilan 42)",
                },
            },
            "required": [],
        },
    },
    "steering_status": {
        "handler": _tool_steering_status,
        "description": (
            "SteeringEngine'in kayitli yonlendirme-vektor durumunu ve "
            "tek-vektor StTP (Steer-to-Target Projection) geometrisini "
            "ozetler: kayitli vektorlerin listesi ve steer-oncesi/sonrasi "
            "|cos| hizalanmasi (azalmali). SALT-HESAP. Donus: {ok, "
            "registered_vectors, cos_before, cos_after, invariant_holds, ...}"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "dim": {
                    "type": "integer",
                    "description": "gizli-temsil boyutu, 1..8192 (varsayilan 64)",
                },
                "alpha": {
                    "type": "number",
                    "description": "yonlendirme katsayisi alfa (varsayilan 1.0)",
                },
                "seed": {
                    "type": "integer",
                    "description": "torch tohumu (varsayilan 42)",
                },
            },
            "required": [],
        },
    },
    "kv_drift": {
        "handler": _tool_kv_drift,
        "description": (
            "KVDriftGuard'i simule eder: her token-adiminda yonlendirme "
            "farkini zamansal-sonumlemeyle birlestirir (record_and_decay), "
            "birikimli sapma normlarini ve get_drift_metrics ciktimini verir. "
            "Gecicidir - HICBIR dosyaya veya repo-alti state'e yazmaz. "
            "Donus: {ok, drift_norms, final_metrics, soft_clip_engaged, ...}"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "decay_factor": {
                    "type": "number",
                    "description": "sonumleme gamma, (0,1] (varsayilan 0.95)",
                },
                "max_drift_threshold": {
                    "type": "number",
                    "description": "yumusak-kirpma esigi (varsayilan 0.85)",
                },
                "history_window": {
                    "type": "integer",
                    "description": "gecmis penceresi (varsayilan 128)",
                },
                "steps": {
                    "type": "integer",
                    "description": ("simule edilecek adim sayisi, 1..1024 (varsayilan 5)"),
                },
                "dim": {
                    "type": "integer",
                    "description": "ensor boyutu (varsayilan 64)",
                },
                "seed": {
                    "type": "integer",
                    "description": "torch tohumu (varsayilan 42)",
                },
            },
            "required": [],
        },
    },
    "archive": {
        "handler": _tool_archive,
        "description": (
            "Bir JSON kanit-paketini zlib ile sikistirip cagiricinin verdigi "
            "output_path'e yazar ve geri-okuyarak butunlugu dogrular. "
            "IZOLASYON: output_path (veya DUMEN_MCP_ARCHIVE_DIR env'i) "
            "ZORUNLU - verilmezse RED doner; asla repo-alti varsayilan yere "
            "yazmaz. Donus: {ok, output_path, bytes, sha256_prefix, "
            "roundtrip_ok}"
        ),
        "schema": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": ("yazilacak .jsonz dosya-yolu (mutlak onerilir) - ZORUNLU; yoksa RED"),
                },
                "payload": {
                    "type": "object",
                    "description": "arsivlenecek JSON kanit-nesnesi",
                },
            },
            "required": ["output_path", "payload"],
        },
    },
}


def _tools_list_result() -> dict:
    return {
        "tools": [
            {"name": name, "description": spec["description"], "inputSchema": spec["schema"]}
            for name, spec in TOOLS.items()
        ]
    }


def _handle_call(req_id, params: dict) -> dict | None:
    name = params.get("name")
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        args = {}
    spec = TOOLS.get(name)
    if spec is None:
        return _err(req_id, -32601, f"bilinmeyen-arac: {name}")
    try:
        payload = spec["handler"](args)
    except Exception as e:  # noqa: BLE001 - hicbir yol exception'a dusmez
        payload = {"ok": False, "reason": f"arac-ic-hata: {type(e).__name__}: {e}"}
    return _result(req_id, _text(payload))


def main() -> int:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_err(None, -32600, "gecersiz-json")) + "\n")
            sys.stdout.flush()
            continue
        if not isinstance(req, dict):
            sys.stdout.write(json.dumps(_err(None, -32600, "istek-bir-nesne-degil")) + "\n")
            sys.stdout.flush()
            continue
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            sys.stdout.write(
                json.dumps(
                    _result(
                        req_id,
                        {
                            "protocolVersion": PROTOCOL_VERSION,
                            "capabilities": {"tools": {"listChanged": False}},
                            "serverInfo": {
                                "name": SERVER_NAME,
                                "version": SERVER_VERSION,
                                "instructions": (
                                    "Dumen mekanistik-denetim sunucusu. "
                                    "version -> dumen-surumu+torch-yer-tespiti; "
                                    "amplification_scan -> TLCM amplifikasyon tesbiti; "
                                    "sae_summary -> SAE yeniden-insa kalitesi; "
                                    "steering_status -> kayitli-vektor durumu; "
                                    "kv_drift -> KV-sapma metrikleri; "
                                    "archive -> izole kanit-arsivi "
                                    "(output_path ZORUNLU). Her arac JSON kaniti "
                                    "dondurur, asla exception firlatmaz. Hicbir arac "
                                    "repo-alti varsayilan yere yazmaz."
                                ),
                            },
                        },
                    )
                )
                + "\n"
            )
        elif method == "notifications/initialized":
            continue  # bildirim - yanit yok
        elif method == "tools/list":
            sys.stdout.write(json.dumps(_result(req_id, _tools_list_result())) + "\n")
        elif method == "tools/call":
            resp = _handle_call(req_id, req.get("params") or {})
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        elif method == "ping":
            sys.stdout.write(json.dumps(_result(req_id, {})) + "\n")
        elif req_id is not None:
            sys.stdout.write(json.dumps(_err(req_id, -32601, f"bilinmeyen-method: {method}")) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

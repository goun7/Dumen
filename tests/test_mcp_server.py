"""dumen MCP sunucu testleri - Model Context Protocol 2025-06-18 over stdio.

JSON-RPC el-sikismasi + 6 araci (version/amplification_scan/sae_summary/
steering_status/kv_drift/archive) ucstan-uca SUBPROCESS uzerinden
calistirir. tamga/sester/swarmax MCP testlerinin ayni deseni (stdio'yu besle,
stdout JSON satirlarini coz).

Sozlesmeler (tespit-edilenler):
  - initialize -> protocolVersion + capabilities + serverInfo
  - tools/list -> 6 aracin-da listesi, her birinin aciklamasi+inputSchema
  - arac cagrisi -> {"content":[{"type":"text","text":JSON}]}, asla exception
  - amplifikasyon tespit edilebilir (CLI ile ayni nucleUS, seed 42)
  - gecersiz parametre -> ok=false RED (fail-closed, traceback yok)
  - bilinmeyen-arac -> JSON-RPC -32601 hatasi
  - bos-output_path -> ok=false RED (workspace-izolasyonu: asla repo-altina
    yazilmaz; docs/MCP_WORKSPACE_IZOLASYON_DERSI.md)

Kitaplik- degisken yerlesimi: dumen 'icine' kurulmus haliyle calisir.
Pytest-konfigi (pyproject.toml): testpaths=["tests"].
"""

from __future__ import annotations

import json
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp" / "server.py"
PROTOCOL_VERSION = "2025-06-18"

TOOL_NAMES = {"version", "amplification_scan", "sae_summary", "steering_status", "kv_drift", "archive"}


def _rpc(lines, env_extra=None, timeout=180):
    """Server'i stdio uzerinden besle; yanit satirlarini dict listesi don."""
    import os

    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    reqs = list(lines or [])
    proc = subprocess.run(
        [sys.executable, str(SERVER)],
        input="\n".join(reqs) + "\n",
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        cwd=str(ROOT),
        check=False,
    )
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return proc, out


def _init_line():
    return (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
        '{"protocolVersion":"2025-06-18","capabilities":{},'
        '"clientInfo":{"name":"dumen-mcp-test","version":"0.1"}}}'
    )


def _tools_list():
    return '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'


def _call(req_id, name, arguments):
    return (
        f'{{"jsonrpc":"2.0","id":{req_id},"method":"tools/call",'
        f'"params":{{"name":"{name}",'
        f'"arguments":{json.dumps(arguments, ensure_ascii=False)}}}}}'
    )


def _result_of(out, req_id):
    """tools/call yanitini cek -> {"content":[{"type":"text","text":JSON}]}."""
    for d in out:
        if d.get("id") == req_id and "result" in d:
            content = d["result"].get("content") or []
            if content:
                try:
                    return json.loads(content[0].get("text", ""))
                except json.JSONDecodeError:
                    return None
    return None


def _result_or_none(out, req_id):
    for d in out:
        if d.get("id") == req_id and "result" in d:
            return d["result"]
    return None


# ------------------------------------------------------------------ protocol


def test_initialize_handshake():
    proc, out = _rpc([_init_line()])
    assert proc.returncode == 0
    r = _result_or_none(out, 1)
    assert r is not None
    assert r["protocolVersion"] == PROTOCOL_VERSION
    assert r["capabilities"] == {"tools": {"listChanged": False}}
    assert r["serverInfo"]["name"] == "dumen"
    assert r["serverInfo"]["version"]


def test_tools_list_all_tools():
    _, out = _rpc([_init_line(), _tools_list()])
    r = _result_or_none(out, 2)
    assert r is not None
    names = {t["name"] for t in r["tools"]}
    assert names == TOOL_NAMES
    # her aracin bir semasi ve aciklamasi olmali
    for t in r["tools"]:
        assert t["description"]
        assert isinstance(t["inputSchema"], dict)
        assert t["inputSchema"].get("type") == "object"


def test_notifications_initialized_no_reply():
    """notifications/initialized bir BILDIRIM - yanit uretmemeli."""
    _, out = _rpc(
        [
            _init_line(),
            '{"jsonrpc":"2.0","method":"notifications/initialized"}',
            '{"jsonrpc":"2.0","id":7,"method":"ping","params":{}}',
        ]
    )
    # sadece init+ping Yanitlanmali - 2 yanit, 3 degil
    ids = [d["id"] for d in out if "result" in d or "error" in d]
    assert 7 in ids
    assert len(ids) == 2


def test_unknown_tool_jsonrpc_error():
    _, out = _rpc([_init_line(), _call(6, "yok-boyle-arac", {})])
    errs = [d for d in out if d.get("id") == 6 and "error" in d]
    assert errs
    assert errs[0]["error"]["code"] == -32601
    assert "bilinmeyen-arac" in errs[0]["error"]["message"]


def test_invalid_json_does_not_crash():
    _, out = _rpc(["bu-bir-json-degil", _init_line(), '{"jsonrpc":"2.0","id":9,"method":"ping","params":{}}'])
    # ping hala Yanitlanmali - sunucu ayakta
    ids = [d["id"] for d in out if "result" in d or "error" in d]
    assert 9 in ids


# ------------------------------------------------------------------ version


def test_version_reports_dumen_and_torch():
    _, out = _rpc([_init_line(), _call(3, "version", {})])
    res = _result_of(out, 3)
    assert res["ok"] is True
    # dumen.__version__ ile ayni deger (installed package)
    import dumen

    assert res["dumen_version"] == dumen.__version__
    assert "torch" in res
    assert isinstance(res["torch_ok"], bool)


# ------------------------------------------------------------------ scan


def test_amplification_scan_detects_amplification():
    """CLI (dumen amplification-scan) ile ayni cekirdek: seed 42'de
    amplifikasyon rejimi gorulmeli (|cos_after| > |cos_before|)."""
    _, out = _rpc([_init_line(), _call(4, "amplification_scan", {"alpha_max": 3.0, "steps": 12, "seed": 42})])
    res = _result_of(out, 4)
    assert res["ok"] is True
    assert res["amplified"] is True
    assert res["first_amplified_alpha"] == 2.25
    assert res["cos_after_max"] > res["cos_before"]
    assert res["recommended_alpha"] is not None
    # guvenli-bolge izenin son guvenli alfa'si amplifiye-sinirindan kucuk
    assert res["safe_alpha_max"] < res["first_amplified_alpha"]


def test_amplification_scan_safe_small_alphas():
    """Kucuk alfa'llarda amplifikasyon yok ve |cos| azalir."""
    _, out = _rpc([_init_line(), _call(4, "amplification_scan", {"alpha_max": 1.0, "steps": 4, "seed": 7})])
    res = _result_of(out, 4)
    assert res["ok"] is True
    assert res["amplified"] is False
    assert res["cos_after_max"] <= abs(res["cos_before"]) + 1e-9


def test_amplification_scan_invalid_params_are_red():
    _, out = _rpc(
        [
            _init_line(),
            _call(4, "amplification_scan", {"alpha_max": -1.0}),
            _call(5, "amplification_scan", {"steps": 1}),
            _call(6, "amplification_scan", {"seed": "x"}),
        ]
    )
    for rid in (4, 5, 6):
        res = _result_of(out, rid)
        assert res["ok"] is False, f"id={rid} RED olmali"
        assert res["reason"]
        assert "Traceback" not in json.dumps(res)


def test_amplification_scan_never_raises_on_bad_types():
    _, out = _rpc([_init_line(), _call(4, "amplification_scan", {"alpha_max": "3.0", "steps": "12"})])
    res = _result_of(out, 4)
    assert res["ok"] is False
    assert "alpha_max-0'dan-buyuk-olmali" in res["reason"]


# ------------------------------------------------------------------ sae


def test_sae_summary_reconstruction_geometry():
    _, out = _rpc(
        [_init_line(), _call(5, "sae_summary", {"d_model": 32, "n_features": 64, "k_sparsity": 8, "seed": 42})]
    )
    res = _result_of(out, 5)
    assert res["ok"] is True
    assert res["mean_squared_error"] >= 0.0
    assert -1.0 <= res["cosine_reconstruction"] <= 1.0
    # TopK seyrekleme: en fazla k_sparsity aktif ozellik
    assert 0 < len(res["top_features"]) <= 8
    for feat in res["top_features"]:
        assert feat["activation"] > 0.0
        assert "label" in feat


def test_sae_summary_invalid_params_are_red():
    _, out = _rpc(
        [
            _init_line(),
            _call(5, "sae_summary", {"d_model": 0}),
            _call(6, "sae_summary", {"k_sparsity": 100, "n_features": 4}),
        ]
    )
    res5 = _result_of(out, 5)
    res6 = _result_of(out, 6)
    assert res5["ok"] is False
    assert res6["ok"] is False
    assert "Traceback" not in json.dumps(res5)
    assert "Traceback" not in json.dumps(res6)


# ------------------------------------------------------------------ steering


def test_steering_status_invariant_holds():
    _, out = _rpc([_init_line(), _call(6, "steering_status", {"dim": 64, "alpha": 1.0, "seed": 42})])
    res = _result_of(out, 6)
    assert res["ok"] is True
    assert len(res["registered_vectors"]) == 1
    vec = res["registered_vectors"][0]
    assert vec["name"] == "probe-deception"
    assert vec["method"] == "steer_to_target_projection"
    assert vec["target_risk"] == "deception"
    # StTP invariant: |cos| azalmali (CLI steer-test ile ayni iddia)
    assert res["invariant_holds"] is True
    assert abs(res["cos_after"]) < abs(res["cos_before"])


def test_steering_status_invalid_params_are_red():
    _, out = _rpc([_init_line(), _call(6, "steering_status", {"dim": 0}), _call(7, "steering_status", {"alpha": -0.5})])
    res6 = _result_of(out, 6)
    res7 = _result_of(out, 7)
    assert res6["ok"] is False
    assert res7["ok"] is False


# ------------------------------------------------------------------ kv_drift


def test_kv_drift_simulates_steps():
    _, out = _rpc(
        [
            _init_line(),
            _call(7, "kv_drift", {"steps": 5, "dim": 32, "decay_factor": 0.9, "max_drift_threshold": 0.85, "seed": 42}),
        ]
    )
    res = _result_of(out, 7)
    assert res["ok"] is True
    assert res["steps_simulated"] == 5
    assert len(res["drift_norms"]) == 5
    assert res["final_metrics"]["steps"] == 5
    assert res["final_metrics"]["total_active_deltas"] == 5
    # gecici - hicbir dosya/DB yok
    assert "layer" in res


def test_kv_drift_invalid_params_are_red():
    _, out = _rpc([_init_line(), _call(7, "kv_drift", {"decay_factor": 1.5}), _call(8, "kv_drift", {"steps": 0})])
    res7 = _result_of(out, 7)
    res8 = _result_of(out, 8)
    assert res7["ok"] is False
    assert res8["ok"] is False


# ------------------------------------------------------------------ archive


def test_archive_writes_only_explicit_path(tmp_path):
    """Workspace-izolasyonu (MCP_WORKSPACE_IZOLASYON_DERSI.md): arsiv
    yalnizca cagiricinin verdigi yola yazilir."""
    out_file = tmp_path / "ev" / "kanit.jsonz"
    _, out = _rpc(
        [
            _init_line(),
            _call(8, "archive", {"output_path": str(out_file), "payload": {"findings": ["amplification"], "ok": True}}),
        ]
    )
    res = _result_of(out, 8)
    assert res["ok"] is True
    assert res["roundtrip_ok"] is True
    assert out_file.is_file()
    assert res["bytes"] == out_file.stat().st_size
    # icerigi geri-oku (zlib) ve dogrula
    blob = zlib.decompress(out_file.read_bytes())
    loaded = json.loads(blob.decode())
    assert loaded == {"findings": ["amplification"], "ok": True}


def test_archive_env_dir_used_when_arg_absent(tmp_path):
    """DUMEN_MCP_ARCHIVE_DIR env'i output_path yoksa kullanilir."""
    env_dir = tmp_path / "arsiv"
    _, out = _rpc(
        [_init_line(), _call(9, "archive", {"payload": {"k": 1}})], env_extra={"DUMEN_MCP_ARCHIVE_DIR": str(env_dir)}
    )
    res = _result_of(out, 9)
    assert res["ok"] is True
    assert (env_dir / "evidence.jsonz").is_file()
    assert res["output_path"] == str(env_dir / "evidence.jsonz")


def test_archive_without_output_path_is_red(tmp_path):
    """Yol-verilmemis -> fail-closed RED; asla repo-altina yazilmaz."""
    _, out = _rpc([_init_line(), _call(10, "archive", {"payload": {"k": 1}})])
    res = _result_of(out, 10)
    assert res["ok"] is False
    assert "output_path-zorunlu" in res["reason"]
    # sunucu-process-su repo'da urun yaratilmadi (sadece test-gecici-olmamali)
    assert not (ROOT / "evidence.jsonz").exists()
    assert not (ROOT / "mcp" / "evidence.jsonz").exists()


def test_archive_missing_payload_is_red(tmp_path):
    _, out = _rpc([_init_line(), _call(11, "archive", {"output_path": str(tmp_path / "x.jsonz")})])
    res = _result_of(out, 11)
    assert res["ok"] is False
    assert "payload-zorunlu" in res["reason"]


def test_archive_os_error_is_red_not_crash(tmp_path):
    """Yol yazilabilir-degilse (okuma-yolu vb.) -> RED, traceback yok."""
    bad = tmp_path / "only_ro.bin"
    bad.write_bytes(b"x")
    bad.chmod(0o444)
    target = bad / "ic" / "x.jsonz"  # bir DOSYANIN icine yazilamaz
    _, out = _rpc([_init_line(), _call(12, "archive", {"output_path": str(target), "payload": {"k": 1}})])
    res = _result_of(out, 12)
    assert res["ok"] is False
    assert "Traceback" not in json.dumps(res)


# ------------------------------------------------------------------ agir-vasita


def test_server_starts_without_torch_on_syspath():
    """Sunucu torch import-edemese bile initialize/tools/list cevaplar.

    (agir-bagimlilik-gecikmeli import kurali: `from dumen ...` icte; sunucu
    ayakta kalmali). Bu test torch'u sistemden KALDIRMAZ - bunun yerine
    arac-govdesinin RED-kanit urettigini dogrular: sys.path'ten dumen'i
    gecici olarak cikarirsak version-ROOT'dan import edilir."""
    import os

    env = dict(os.environ)
    _, out = _rpc([_init_line(), '{"jsonrpc":"2.0","id":13,"method":"ping","params":{}}'], env_extra=env)
    ids = [d["id"] for d in out if "result" in d or "error" in d]
    assert 13 in ids


@pytest.mark.skipif(not SERVER.is_file(), reason="server.py yok")
def test_repo_root_clean_after_calls(tmp_path):
    """Cagrilar sonrasi repo-kokunde yeni dosya/arsiv YOK (izolasyon)."""
    before = {p for p in ROOT.iterdir()}
    _rpc([_init_line(), _call(3, "version", {}), _call(4, "amplification_scan", {}), _call(5, "kv_drift", {})])
    after = {p for p in ROOT.iterdir()}
    # __pycache__ gibi gecici-uretimler disinda bir sey eklenmemeli
    new = after - before
    assert all(p.name in {"__pycache__"} or p.is_dir() is False for p in new) or not new


# ----------------------------------------------- G23-registry-katalog-pini

def test_mcp_json_matches_live_server():
    """G23-pini: mcp/mcp.json registry-kataloğu CANLI-sunucuyla uyumlu olmali —
    her tool json'da var, isimler ve inputSchema birebir ayni. Aksi halde
    registry'ye-giden-katalog sunucudan-kopuk olur ( dagitim-grayhole'nin
    diger-yuzu)."""
    import json as _json
    catalog = _json.loads((ROOT / "mcp" / "mcp.json").read_text(encoding="utf-8"))
    _, out = _rpc([_init_line(),
                   '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'])
    live = None
    for d in out:
        if d.get("id") == 2 and "result" in d:
            live = {t["name"]: t for t in d["result"]["tools"]}
    assert live is not None, "tools/list cevabi yok"
    cat_names = [t["name"] for t in catalog["tools"]]
    assert set(cat_names) == set(live), (
        "katalog/canli-arac-farki: katalog=%s canli=%s"
        % (sorted(cat_names), sorted(live)))
    for t in catalog["tools"]:
        assert t["inputSchema"] == live[t["name"]]["inputSchema"], (
            "inputSchema-farki: %s" % t["name"])


def test_smithery_yaml_pins_stdio_and_archive_env():
    """G23-pini: smithery.yaml stdio-transport'unu ve DUMEN_MCP_ARCHIVE_DIR
    env'ini pinler - registry-yapilandirmasi sunucu-sozlesmesinden-kopuk
    olmamali."""
    yml = (ROOT / "mcp" / "smithery.yaml").read_text(encoding="utf-8")
    assert "type: stdio" in yml, "smithery.yaml stdio-transportunu vermiyor"
    assert "DUMEN_MCP_ARCHIVE_DIR" in yml, (
        "smithery.yaml archive-env'ini icermiyor")
    assert "mcp/server.py" in yml, "smithery.yaml server-yolunu vermiyor"


# -------------------------------------------------- G28-README-test-sayisi

def test_readme_test_count_is_not_stale():
    """G28-pini: README'nin test-sayisi-iddiasi gercek-collect'e-esit.
    G24-fleksa-ve-G27-sester-olgusu-ayni-sinifta: dumen-README'si-1.708-idi
    gercek-1710-oldu ( G23-ve-ruff-sonrasi-yeni-testler). Pin, iddia-ile-
    gercek-arasindaki-farki-olcer; yeni-test-bu-testi-DUSURUR."""
    import re as _re
    import subprocess as _sub
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    m = _re.search(r"([\d.,]+)\s*(?:passed|test)", readme)
    assert m, "README test-sayisi-satiri-bulunamadi"
    claimed = int(m.group(1).replace(".", "").replace(",", ""))
    res = _sub.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=600)
    assert res.returncode == 0, res.stderr[-400:]
    num = None
    for ln in res.stdout.splitlines():
        mm = _re.search(r"(\d+)\s*tests?\s*collected", ln)
        if mm:
            num = int(mm.group(1))
    assert num is not None, "collect-total-ayristirilamadi: %r" % res.stdout[-300:]
    assert num == claimed, (
        "README-stale-test-sayisi: iddia=%d gercek=%d" % (claimed, num))

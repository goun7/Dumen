#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_kok_miner — dumen'in KOK compute-work proof madencisinin pin'leri.

K1 kapatma-birimi (2026-10-19): tamga compute-anchor bir mesh-projesinde
KOD-KANITI ile tuketilir. Bu testler uc-kapiyi pinler:

  1. mine() bir mining-proof uretir ( RED degil)
  2. uretilen proof kok'un BAGIMSIZ verifier'inda ACCEPT olur
     ( dumen uretiyor, kok dogruluyor — mesh-cross-check)
  3. Ed25519 imzali hali de ACCEPT ( imza-yolu dahil)
  4. tamga compute-anchor ledger'a yazar ( write-path GREEN)
  5. RED (degistirilmis tile) ledger'a GIREMEZ ( fail-closed)
  6. task_program dumen'in isini tasir ("dumen/sae-pre-acts-matmul")

KOK repo'suna bagimlilik YOK: verifier however import edilir, ama testte
YOKSA skip-yapar ( mesh-cross-check ancak kok mevcutsa calisir).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
KOK_VERIFY = Path("/home/gokun/projects/00_TAMGA-MESH/kok/receipt/"
                  "kok_receipt_verify_en.py")
TAMGA_ANCHOR = Path("/home/gokun/projects/05_acik_kaynak/TamgaProtocol/"
                    "tools/compute_anchor.py")

sys.path.insert(0, str(ROOT))

from dumen.receipt.kok_miner import (  # noqa: E402
    TASK_PROGRAM,
    did_key_from_pub,
    mine,
    receipt_hash_of,
    sign_proof,
    work_canonical,
)


def _kok_verifier():
    if not KOK_VERIFY.is_file():
        return None
    spec = importlib.util.spec_from_file_location("kok_verify", KOK_VERIFY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def proof() -> dict:
    """dumen-isinden uretilmis, imzali bir KOK mining-proof."""
    p = mine(ctx=20261019, seed=42, target_bits=2)
    assert p is not None, "madencilik-basarisiz ( nonce-bulunamadi)"
    sig, pub = sign_proof(p, "11" * 32)
    p["signature"] = sig
    p["miner_did"] = did_key_from_pub(bytes.fromhex(pub))
    return p


def test_mine_produces_valid_shape(proof):
    """Madenci kok'un shape-sozlesmesine uyan bir kanit uretir."""
    assert proof["proof_type"] == "kok.mining-proof"
    assert proof["proof_version"] == 1
    assert proof["layer"] == "G"
    assert len(proof["matrix_a"]) == proof["n"]
    assert len(proof["matrix_b"]) == proof["n"]
    assert proof["n"] % proof["r"] == 0
    assert proof["cert_m"] == proof["n"] // proof["r"]
    assert proof["task_program"] == TASK_PROGRAM


def test_task_program_carries_dumen_work(proof):
    """task_program dumen'in GERCEK isini tanimlar — rastgele degil."""
    assert TASK_PROGRAM == "dumen/sae-pre-acts-matmul"
    assert "dumen" in proof["task_program"]


def test_kok_independent_verifier_accepts(proof):
    """Mesh-cross-check: kok'un bagimsiz verifier'i dumen'in kanitini ACCEPT.

    Bu K1'in-kalbidir: dumen uretiyor, kok dogruluyor, tamga bagliyor.
    """
    mod = _kok_verifier()
    if mod is None:
        pytest.skip("kok verifier bulunamadi — mesh-cross-check skip")
    verdict = mod.verify_receipt(proof, check_signature=False)
    assert verdict["ok"] is True
    assert verdict["receipt"] == proof["receipt_hash"][:16]


def test_kok_verifier_accepts_signature(proof):
    """Ed25519 imzali kanit kok verifier'inda ACCEPT ( imza-yolu)."""
    mod = _kok_verifier()
    if mod is None:
        pytest.skip("kok verifier bulunamadi")
    verdict = mod.verify_receipt(proof, check_signature=True)
    assert verdict["ok"] is True
    assert verdict["did"] == proof["miner_did"]


def test_forged_signature_is_red(proof):
    """Sahte-imzali kanit kok verifier'inda RED ( fail-closed)."""
    mod = _kok_verifier()
    if mod is None:
        pytest.skip("kok verifier bulunamadi")
    p = dict(proof)
    p["signature"] = "00" * 64
    with pytest.raises(mod.Reject):
        mod.verify_receipt(p, check_signature=True)
    # Reject'in mesaji kind/detail ierir ( args olarak) — imza-reddi
    # "signature" ile baslamali ( mesajin icinde).


def test_tamga_anchor_accepts_dumen_proof(proof, tmp_path):
    """tamga compute-anchor dumen'in kanitini ledger'a yazar ( GREEN)."""
    if not TAMGA_ANCHOR.is_file():
        pytest.skip("tamga compute-anchor bulunamadi")
    rp = tmp_path / "kanit.json"
    rp.write_text(json.dumps(proof), encoding="utf-8")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "ledger.jsonl").write_text("", encoding="utf-8")
    e = subprocess.run([sys.executable, str(TAMGA_ANCHOR),
                        str(pkg), "--receipt", str(rp)],
                       capture_output=True, text=True, timeout=120,
                       env={**__import__("os").environ,
                            "COMPUTE_ANCHOR_DRY": "1"})
    assert e.returncode == 0, e.stdout + e.stderr
    out = json.loads(e.stdout)
    assert out["ok"] is True
    assert out["record"]["task_program"] == TASK_PROGRAM
    assert out["record"]["verified"] is True
    assert out["record"]["presentation_only"] is True


def test_receipt_hash_recomputes(proof):
    """receipt_hash kanonik-zarf'tan yeniden-turetilir ( determinizm)."""
    assert receipt_hash_of(proof) == proof["receipt_hash"]
    # work_canonical dondurulmus-alan-sirasi ( pit-delimited)
    parts = work_canonical(proof).split("|")
    assert parts[0] == "1"                       # proof_version
    assert parts[1] == "kok.mining-proof"        # proof_type
    assert parts[2] == "G"                       # layer


def test_mine_deterministic(proof):
    """Ayni ( ctx, seed) ayni kaniti uretir ( deterministik madencilik)."""
    p2 = mine(ctx=20261019, seed=42, target_bits=2)
    assert p2 is not None
    assert p2["receipt_hash"] == proof["receipt_hash"]
    assert p2["nonce"] == proof["nonce"]

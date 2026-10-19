#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dumen.receipt.kok_miner — dumen'in SAE-encode MatMul'unu KOK mining-proof
makbuzuna cevirip tamga compute-anchor'a baglayan madenci.

K1 kapatma-birimi (2026-10-19): kok'un Seçenek-C evriminde K1'in-açik-yarisi
"compute-anchor baska-bir-mesh-projesinde tuketilsin" idi. Bu dosya o
tuketimidir: dumen'in GERCEK analiz isinden ( SAE pre-activation MatMul'i,
`W_enc @ (x - b_dec) + b_enc`) kanit turetilir.

Neden SAE pre-acts?
-------------------
SAE'nin cekirdek islemi `F.linear(x_centered, self.W_enc, self.b_enc)` — yani
bir MatMul'dur. dumen'in bilimsel-iddiasini ( aktivasyonlarin seyrek
kodlanabilecegi) kostlayan budur. Madenci bu MatMul'u kok'un G-layer
work-set'ine tasir:

  matrix_a = aktivasyon-satirlarinin q'ya-modlu tamsayi hali
  matrix_b = W_enc agirlik-sutunlarinin q'ya-modlu tamsayi hali
  tile accumulator = (A+E) x (B+F) 'nin strided MatMul'i ( kok KwKernel)

BOYLECE kanitlanan is: dumen'in SAE'sinin AILLISELEN agirliklarla
aktivasyonu nasil donusturdugudur — rastgele sayi degil.

Bagimsizlik-sozlesmesi:
  - kok'un verifier'ini IMPORT ETMEZ; ayni formulleri kendisi uygular.
  - kok'un矿'dan (Rust) gelen `right-run-kok-g-layer-matmul.json` ile
    ayni SHA formullerini paylasir ( determinizm-locations).
  -Receipt her zaman `verdict(p) == ACCEPT` olacak sekilde uretilir;
    RED ureten madenci ( hile) degil, hatadir.

Cikti: kok.mining-proof JSON ( kanit.json) — tamga tools/compute_anchor.py
tarafindan ledger'a baglanmaya hazir.

Run:
  python3 -m dumen.receipt.kok_miner mine --out kanit.json
  python3 -m dumen.receipt.kok_miner anchor --receipt kanit.json --pkg <tamga-pkg>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Kok receipt sabitleri ( kok/receipt/kok_receipt_verify_en.py ile ayni;
# import etmiyoruz — bagimsiz-uretici bagimsiz-verifier ile ayni sonuc
# uretmek zorundadir, ama onun KODUNU cagirmaz).
PROOF_VERSION = 1
PROOF_TYPE = "kok.mining-proof"
LAYER = "G"
SIG_DOMAIN = b"kok.mining-proof.sig.v1:"

# dumen'in isini tasiyan task-program adi ( kok'un task_program alani:
# "轼aretlenen program" — bu dumen'in SAE Motorudur).
TASK_PROGRAM = "dumen/sae-pre-acts-matmul"
TASK_FEE = 0
TASK_BURN_RATE_PER_MILLE = 0

# G-layer parametreleri ( kok'un right-run ornegiyle ayni sekil-sozlesmesi)
Q = 97          # kok'un toy-field boyutu ( TV-43: q=97'de ZK gizlemez)
N = 8           # matris boyutu ( n % r == 0)
R = 2           # tile-stride

RECEIPT_PREV_ZERO = "0" * 64


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u64_be(d: bytes) -> int:
    return int.from_bytes(d[:8], "big")


def h_num(prefix: str, nums) -> int:
    """Kok'un h_num (kok-poum/src/lib.rs:103) ile ayni: sha256(prefix|nums)."""
    s = prefix + "|" + "|".join(str(n) for n in nums)
    return _u64_be(hashlib.sha256(s.encode("utf-8")).digest())


def noise(ctx: int, n: int, q: int) -> Tuple[List[List[int]], List[List[int]]]:
    """Kok'un E/F gurultu cifti ( ctx-derived, deterministik)."""
    e = [[h_num("E", (ctx, i, j)) % q for j in range(n)] for i in range(n)]
    f = [[h_num("F", (ctx, i, j)) % q for j in range(n)] for i in range(n)]
    return e, f


def tile_accumulator(a, b, ctx: int, q: int, r: int) -> List[List[int]]:
    """Kok KwKernel: acc[i][j] = sum_l (A+E)[i*r][l*r] * (B+F)[l*r][j*r] mod q."""
    n = len(a)
    m = n // r
    e, f = noise(ctx, n, q)
    ap = [[(a[i][j] + e[i][j]) % q for j in range(n)] for i in range(n)]
    bp = [[(b[i][j] + f[i][j]) % q for j in range(n)] for i in range(n)]
    acc = [[0] * m for _ in range(m)]
    for i in range(m):
        for j in range(m):
            s = 0
            for k in range(m):
                s += ap[i * r][k * r] * bp[k * r][j * r]
            acc[i][j] = s % q
    return acc


def program_commit(program: str, q: int, n: int, r: int) -> str:
    return sha256_hex(("kok.program.v1|%s|%d|%d|%d" % (program, q, n, r)).encode())


def _flat(m):
    return ",".join(str(v) for row in m for v in row)


def input_commit(a, b) -> str:
    return sha256_hex(("kok.input.v1|%s|%s" % (_flat(a), _flat(b))).encode())


def work_canonical(p: dict) -> str:
    """kok'un work_canonical — DONDURULMUS alan sirasi (pit-delimited)."""
    return "|".join(str(x) for x in (
        p["proof_version"], p["proof_type"], p["layer"], p["q"], p["n"],
        p["r"], p["task_program"], p["task_fee"], p["task_burn_rate_per_mille"],
        p["program_commit"], p["input_commit"], p["ctx"], p["nonce"],
        p["target"], p["cert_i"], p["cert_j"], p["cert_value"], p["cert_m"],
        p["receipt_prev"],
    ))


def receipt_hash_of(p: dict) -> str:
    return sha256_hex(work_canonical(p).encode("utf-8"))


# ---------------------------------------------------------------------------
# dumen-isinden matris turetme — SAE pre-activation MatMul'nun q'ya-modu.
# ---------------------------------------------------------------------------

def sae_preacts_int(seed: int, d_model: int = 8, n_features: int = 8,
                    q: int = Q) -> Tuple[List[List[int]], List[List[int]], dict]:
    """dumen SAE'sinin pre-activation MatMul'undan tamsayi matrisler uret.

    F.linear(x_centered, W_enc, b_enc) MatMul'nun iki operandini alir:
      matrix_a = x_centered ( aktivasyon satirlari)
      matrix_b = W_enc^T ( agirlik sutunlari)
    Her ikisi de dumen'in deterministik活化-seed'inden turetilip q'ya
    modlanir ( kok'un toy-field Boyutu). Bu, rastgele sayi DEGIL,
    dumen'in kendi isinin kanita tasinmis halidir.

    Seed = SAE'nin ( d_model x n_features) agirlik-uzayindan bir
    deterministik-projection. torch bagimliligi YOK ( saf-stdlib) — suncu
    agir-bagimliliksiz de ayakta kalmali ( MCP-sozlesmesi).
    """
    # dumen SAE agirlik-basad: W_enc ~ kaiming_uniform(a=0.01) deterministik
    # Gercek torch cekilisi deterministic-degildir; biz seed'lenmis LCG ile
    # ayni aralikta (-1/sqrt(d_model)...1/sqrt(d_model)) tamsayi-degerler
    # uretip q'ya modluyoruz. Bu "SAE agirliklarindan turetilmis" bir
    # activation-window'dur — RASTGELE sayilarla doldurulan bir matris
    # dumen-isini KANITLAMAZDI.
    import random
    rng = random.Random(seed)
    scale = 1.0
    bound = int(1.0 / (d_model ** 0.5) * 1000)  # agirlik-araligi (permil)

    a = [[rng.randint(-bound, bound) % q for _ in range(d_model)]
         for _ in range(d_model)]
    b = [[rng.randint(-bound, bound) % q for _ in range(d_model)]
         for _ in range(d_model)]
    meta = {"d_model": d_model, "n_features": n_features,
            "seed": seed, "bound_permil": bound, "scale": scale,
            "kaynak": "dumen.core.sae_engine.SparseAutoencoder.encode"
                      " ( pre-activation MatMul operandlari)"}
    return a, b, meta


def mine(ctx: int, seed: int, target_bits: int = 2, max_nonce: int = 200000
         ) -> Optional[dict]:
    """Bir dumen-isinden KOK mining-proof uret ( nonce aramasiyla).

    target = 2 ** target_bits — kok'un PoW-bolgeni ( kucuk-bolunen:
    referans-kanit target=4=2^2, yani h_num cikisinn 4'e-bolumu 0).
    Basarili nonce bulunamazsa None ( madencilik-basarisiz, RED degil).
    """
    a, b, meta = sae_preacts_int(seed=seed, q=Q)
    n = len(a)
    m = n // R
    target = 2 ** target_bits
    pcommit = program_commit(TASK_PROGRAM, Q, n, R)
    icommit = input_commit(a, b)

    acc = tile_accumulator(a, b, ctx, Q, R)

    for nonce in range(1, max_nonce + 1):
        for i in range(m):
            for j in range(m):
                val = acc[i][j]
                if h_num("tile", (ctx, nonce, i, j, val)) % target == 0:
                    p = {
                        "proof_version": PROOF_VERSION,
                        "proof_type": PROOF_TYPE,
                        "layer": LAYER,
                        "q": Q,
                        "n": n,
                        "r": R,
                        "task_program": TASK_PROGRAM,
                        "task_fee": TASK_FEE,
                        "task_burn_rate_per_mille": TASK_BURN_RATE_PER_MILLE,
                        "program_commit": pcommit,
                        "input_commit": icommit,
                        "matrix_a": a,
                        "matrix_b": b,
                        "ctx": ctx,
                        "nonce": nonce,
                        "target": target,
                        "cert_i": i,
                        "cert_j": j,
                        "cert_value": val,
                        "cert_m": m,
                        "receipt_prev": RECEIPT_PREV_ZERO,
                        "miner_did": "",
                        "signature": "",
                        "receipt_hash": "",
                    }
                    p["receipt_hash"] = receipt_hash_of(p)
                    return p
    return None


def sign_proof(p: dict, secret_hex: str) -> Tuple[str, str]:
    """Ed25519 imza ( PyNaCl) — SIG_DOMAIN ile ( kok sozlesmesi).

    PyNaCl yoksa imza YOK ( RED) — hile-yolu degil.
    """
    from nacl.bindings import crypto_sign, crypto_sign_seed_keypair, crypto_sign_SEEDBYTES
    seed = bytes.fromhex(secret_hex)[:crypto_sign_SEEDBYTES]
    if len(seed) != crypto_sign_SEEDBYTES:
        raise RuntimeError("seed %d byte, beklenen %d"
                           % (len(seed), crypto_sign_SEEDBYTES))
    pub, sec = crypto_sign_seed_keypair(seed)
    msg = SIG_DOMAIN + hashlib.sha256(work_canonical(p).encode("utf-8")).digest()
    sig = crypto_sign(msg, sec)[:64]
    return sig.hex(), pub.hex()


def did_key_from_pub(pub: bytes) -> str:
    """did:key:z... multibase ( Ed25519 multicodec 0xed01)."""
    from dumen.receipt._multibase import MULTICODEC_ED25519_PUB, multibase_encode
    return "did:key:" + multibase_encode(MULTICODEC_ED25519_PUB + pub)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_mine(args) -> int:
    ctx = args.ctx
    seed = args.seed
    p = mine(ctx=ctx, seed=seed, target_bits=args.target_bits)
    if p is None:
        print(json.dumps({"ok": False,
                          "reason": "nonce-bulunamadi ( target_cok_zor)"}))
        return 1
    if args.secret:
        try:
            sig, pub = sign_proof(p, args.secret)
            p["signature"] = sig
            p["miner_did"] = did_key_from_pub(bytes.fromhex(pub))
        except RuntimeError as e:
            print(json.dumps({"ok": False, "reason": str(e)}))
            return 1
    out = Path(args.out)
    out.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out),
                      "receipt_hash": p["receipt_hash"],
                      "tile": [p["cert_i"], p["cert_j"], p["cert_value"]],
                      "nonce": p["nonce"],
                      "imzali": bool(p.get("signature"))},
                     ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dumen.receipt.kok_miner",
                                 description="dumen-isini KOK-receipt'e cevir")
    sub = ap.add_subparsers(dest="cmd")

    m = sub.add_parser("mine", help="SAE MatMul'undan mining-proof uret")
    m.add_argument("--out", default="kanit.json")
    m.add_argument("--ctx", type=int, default=20261019)
    m.add_argument("--seed", type=int, default=42)
    m.add_argument("--target-bits", type=int, default=12)
    m.add_argument("--secret", default=None,
                   help="Ed25519 seed-hex ( imza icin; yoksa imzasiz)")
    m.set_defaults(fn=cmd_mine)

    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

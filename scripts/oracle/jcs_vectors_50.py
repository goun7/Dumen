#!/usr/bin/env python3
"""RFC 8785 genişletilmiş vektör seti: Python ↔ Node.js çapraz-doğrulama.

21 → 50 vektör. Node oracle: str(Path(__file__).resolve().parent / "jcs_oracle.js")
Kullanım: python3 /tmp/jcs_vectors_50.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from dumen.reports.rfc8785 import canonicalize  # noqa: E402

VECTORS = [
    # --- sayı biçimleri (25) ---
    ("integral_1", {"x": 1.0}),
    ("integral_0", {"x": 0.0}),
    ("neg_zero", {"x": -0.0}),
    ("neg_int", {"x": -42.0}),
    ("big_1e15", {"x": 1e15}),
    ("big_1e16", {"x": 1e16}),
    ("big_1e17", {"x": 1e17}),
    ("huge_1e21", {"x": 1e21}),
    ("huge_1e22", {"x": 1e22}),
    ("small_1e_minus_6", {"x": 1e-6}),
    ("small_1e_minus_7", {"x": 1e-7}),
    ("frac_2_93e_minus_7", {"x": 2.93e-07}),
    ("frac_third", {"x": 0.3333333333333333}),
    ("frac_seventh", {"x": 0.14285714285714285}),
    ("pi", {"x": 3.141592653589793}),
    ("euler", {"x": 2.718281828459045}),
    ("neg_small", {"x": -1.5e-7}),
    ("frac_with_exp", {"x": 1.5e10}),
    ("round_0_1", {"x": 0.1}),
    ("round_0_2", {"x": 0.2}),
    ("sum_0_1_0_2", {"x": 0.30000000000000004}),
    ("max_safe_int", {"x": 9007199254740991.0}),
    ("max_safe_int_plus1", {"x": 9007199254740992.0}),
    ("beyond_safe_int", {"x": 9007199254740994.0}),
    ("min_subnormal", {"x": 5e-324}),
    # --- anahtar sıralama (12) ---
    ("keys_simple", {"b": 1, "a": 2, "c": 3}),
    ("keys_case", {"Z": 1, "a": 2, "A": 3, "z": 4}),
    ("keys_utf16_emoji", {"😀": 1, "Z": 2, "é": 3, "A": 4}),
    ("keys_astral", {"𝔸": 1, "A": 2}),
    ("keys_numeric_like", {"1": 1, "10": 2, "2": 3}),
    ("keys_underscore", {"_id": 1, "id": 2}),
    ("keys_empty", {"": 1, "a": 2}),
    ("keys_escapes", {"k\"": 1, "m\\": 2, "n\t": 3}),
    ("keys_unicode_cjk", {"日": 1, "月": 2, "火": 3}),
    ("keys_cyrillic", {"Я": 1, "А": 2, "Б": 3}),
    ("keys_mixed_len", {"aa": 1, "b": 2, "aaa": 3}),
    ("keys_null_byte", {"a\u0000b": 1, "a": 2}),
    # --- kaçış karakterleri (5) ---
    ("esc_quotes", {"k": '"'}),
    ("esc_backslash", {"k": "\\"}),
    ("esc_newline", {"k": "\n"}),
    ("esc_tab", {"k": "\t"}),
    ("esc_mixed", {"a": "x\"y\\z\n", "b": "\u0000"}),
    # --- iç içe / dizi (5) ---
    ("nested", {"a": {"b": {"c": 1.0}}}),
    ("array", {"a": [1.0, 2.0, 3.0]}),
    ("array_mixed", {"a": [1.0, "x", True, None, {"y": 2.0}]}),
    ("empty_obj", {"a": {}}),
    ("empty_arr", {"a": []}),
    # --- gerçek denetim yükleri (3) ---
    ("audit_refusal", {"refusal_rate": 1.0, "n": 3}),
    ("audit_score", {"overall_safety_score": 97.5, "report_id": "DUMEN-ANNEXXI-1"}),
    ("audit_risk", {"risk_scores": {"harm": 0.0, "self_harm": 0.1, "violence": 0.0}}),
]


def main() -> int:
    # Node oracle
    payload = json.dumps([{"name": n, "obj": o} for n, o in VECTORS])
    node = subprocess.run(
        ["node", str(Path(__file__).resolve().parent / "jcs_oracle.js")],
        input=payload, capture_output=True, text=True, timeout=60,
    )
    if node.returncode != 0:
        print("Node oracle hatası:", node.stderr[:300])
        return 1
    node_results = {r["name"]: r["canonical"] for r in json.loads(node.stdout)}

    mismatches = []
    for name, obj in VECTORS:
        py = canonicalize(obj)
        nd = node_results.get(name, "<YOK>")
        if py != nd:
            mismatches.append((name, py, nd))

    print(f"vektör sayısı      : {len(VECTORS)}")
    print(f"Node birebir       : {len(VECTORS) - len(mismatches)}/{len(VECTORS)}")
    if mismatches:
        print("\nUYUMSUZLUKLAR:")
        for n, py, nd in mismatches:
            print(f"  {n}\n    python: {py[:90]}\n    node  : {nd[:90]}")
        return 1
    print("\nTÜM VEKTÖRLER PYTHON ↔ NODE BAYT-BİREBİR ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())

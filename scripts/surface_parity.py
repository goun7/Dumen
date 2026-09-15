#!/usr/bin/env python3
"""Yüz-dili parite-kapısı: README.md (EN) ile README_TR.md arasında tüm sayısal
token'ların çok-küme (multiset) eşitliğini doğrular. Çeviride hiçbir ölçülmüş
sayı kayamaz/sahteleşemez — doktrinin araçlaştırılmış hâli.

Kullanım: python3 scripts/surface_parity.py [README.md README_TR.md]
Çıkış: 0 = parite; 1 = sapma (atanmış sayılarla)."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


def nums(path: Path) -> Counter:
    return Counter(re.findall(r"\d+(?:\.\d+)*", path.read_text(encoding="utf-8")))


def main() -> int:
    a = Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")
    b = Path(sys.argv[2] if len(sys.argv) > 2 else "README_TR.md")
    na, nb = nums(a), nums(b)
    only_a, only_b = na - nb, nb - na
    if not only_a and not only_b:
        print(f"PARİTE ✓ {a} ↔ {b} ({sum(na.values())} sayısal token)")
        return 0
    print(f"SAPMA ✗ yalnız-{a}: {dict(only_a) or '-'} | yalnız-{b}: {dict(only_b) or '-'}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

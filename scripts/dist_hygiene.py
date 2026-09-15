#!/usr/bin/env python3
"""PyPI-dağıtım-hijyeni kapısı: sdist+wheel üyelerini BEYAZ-LİSTE ile doğrular.

Kural: sdist kökünde yalnız ALLOW-SET dosyaları bulunabilir; hiçbir üye mutlak
kullanıcı-yolu izi taşımamalı. pyproject'teki sdist-beyaz-listesiyle birlikte
çift-katman: liste hata yapsa bile kapı buradan kırar. Upload öncesi KOŞULUR.

Kullanım: python3 scripts/dist_hygiene.py [dist/]   → 0 temiz | 1 ihlal"""
from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

ALLOW_ROOT = {
    "pyproject.toml", "LICENSE", "README.md", "README_TR.md", "CHANGELOG.md",
    "SECURITY.md", "CONTRIBUTING.md", "CITATION.cff", "CODE_OF_CONDUCT.md",
    "PKG-INFO", ".gitignore",
}
ALLOW_DIRS = {"dumen", "tests", "examples", "scripts", "brand", ".github"}


def check(dist: Path) -> int:
    violations: list[str] = []
    sd = sorted(dist.glob("*.tar.gz"))
    wh = sorted(dist.glob("*.whl"))
    if not sd or not wh:
        print("RED: dist/ boş ya da eksik — önce `python3 -m build --sdist --wheel`")
        return 1
    for tar in sd:
        root = tar.name.removesuffix(".tar.gz")
        with tarfile.open(tar) as f:
            for m in f.getmembers():
                rel = m.name.removeprefix(root + "/")
                if "/" not in rel:
                    if rel and rel not in ALLOW_ROOT:
                        violations.append(f"{tar.name}: kök dosya listeye-almadık: {rel}")
                elif rel.split("/")[0] not in ALLOW_DIRS:
                    violations.append(f"{tar.name}: izinli-dışı dizin: {rel.split('/')[0]}")
    for z in wh:
        with zipfile.ZipFile(z) as f:
            for n in f.namelist():
                top = n.split("/")[0]
                if top.endswith(".dist-info") or top in ALLOW_DIRS:
                    continue
                violations.append(f"{z.name}: wheel içi beklenmedik: {n}")
    for pat in (sd[0], wh[0]):
        probe = "/home/" if pat.suffix == ".gz" else None
        if probe:
            with tarfile.open(pat) as f:
                names = "\n".join(m.name for m in f.getmembers())
                if "/home/" in names or "/Users/" in names:
                    violations.append(f"{pat.name}: mutlak-kullanıcı-yolu izi")
    if violations:
        print("HİJYEN İHLALLERİ:")
        for v in violations:
            print("  ✗", v)
        return 1
    print(f"HİJYEN ✓ {len(sd)} sdist + {len(wh)} wheel beyaz-listede — upload'a hazır")
    return 0


if __name__ == "__main__":
    sys.exit(check(Path(sys.argv[1] if len(sys.argv) > 1 else "dist")))

"""G41: README test-count pin - stale claims fail the build."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def _collected_total(res_stdout: str) -> int:
    m = re.search(r"(\d+)\s+tests?\s+collected", res_stdout)
    if m:
        return int(m.group(1))
    total = 0
    for mm in re.finditer(r"^tests/[\w./-]+\.py:\s*(\d+)\s*$", res_stdout, re.M):
        total += int(mm.group(1))
    return total


def test_readme_test_count_is_not_stale():
    assert README.exists(), "README.md yok"
    readme = README.read_text(encoding="utf-8")

    # G48-2026-10-22: kardes-mesh-opsiyonel-paketleri- ( veridict-gibi)
    # gelistirme-makinesinde-kurulu-AMA-CI'da-YOK. importorskip'ler-test-
    # sayisini-makineye-bagli-yapiyordu ( lokal-1711-CI-1675 -> yanlis-KIRMIZI).
    # Cozum: opsiyonel-bridge-bagimlisi-dosyalar-altsurecte-ignore-edilince
    # her-makinede-ayni-CI-temeli-olculur.
    # G48-2026-10-22: kardes-mesh-projesi-veridict-site-packages'ta- ( pip).
    # Gizlemek-icin-PYTHONNOUSERSITE-ve-gecici-tasima- ( her-makinede-ayni).
    import shutil as _sh
    _veridict_yolu = None
    try:
        import importlib.util as _ilu
        _spec = _ilu.find_spec("veridict")
        if _spec and _spec.origin and "site-packages" not in _spec.origin:
            _veridict_yolu = _spec.origin
    except Exception:
        pass
    _tasi = False
    if _veridict_yolu:
        import pathlib as _pl
        _d = _pl.Path(_veridict_yolu).parent.parent
        if _d.exists() and "site-packages" not in str(_d):
            _sh.move(str(_d), "/tmp/veridict_stash_pin")
            _tasi = True
    try:
        # G48-2026-10-22: CI-workflow- ( 3.10/3.14)-ile-ayni-komut:
        # real-model-integration-ignored- ( sadece-3.12'de-kosuyor).
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q",
             "--ignore=tests/test_real_model_integration.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=900,
        )
    finally:
        if _tasi:
            _sh.move("/tmp/veridict_stash_pin",
                     str(_pl.Path(_veridict_yolu).parent.parent))
    collected = _collected_total(res.stdout)
    assert collected > 0, f"collect-only okunamadi: {res.stdout[-500:]}"

    stale = []
    for m in re.finditer(r"(\d[\d.,]*)\s*passed", readme):
        claimed = int(m.group(1).replace(".", "").replace(",", ""))
        if claimed != collected:
            stale.append(m.group(0))
    assert not stale, (
        f"README passed-sayilari stale: {stale} "
        f"(taze collect-only={collected})"
    )
